import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/api/client';

export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  role: 'user' | 'admin';
  login_count: number;
  generation_count: number;
  tokens_in: number;
  tokens_out: number;
  created_at?: string;
  last_login_at?: string;
}

export interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthConfigLoading: boolean;
  isSyncingSession: boolean;
  isBackendReady: boolean;
  googleClientId: string;
  loginWithGoogleCredential: (credential: string) => Promise<boolean>;
  devLogin: (email?: string) => Promise<boolean>;
  logout: () => void;
  openLoginModal: () => void;
  closeLoginModal: () => void;
  isLoginModalOpen: boolean;
  renderGoogleButton: (elementId: string) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'banana-auth-token';
const USER_KEY = 'banana-auth-user';
const DEFAULT_CLIENT_ID = '';
const MAX_COLD_START_RETRIES = 6;
const COLD_START_RETRY_DELAY_MS = 2500;
const TRANSIENT_STATUS_CODES = new Set([502, 503, 504, 522, 524]);

function isTransientBackendError(err: unknown): boolean {
  const response = (err as { response?: { status?: number } })?.response;
  if (!response) return true;
  return typeof response.status === 'number' && TRANSIENT_STATUS_CODES.has(response.status);
}

function readCachedUser(): User | null {
  try {
    const saved = localStorage.getItem(USER_KEY);
    return saved ? JSON.parse(saved) : null;
  } catch {
    return null;
  }
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState<User | null>(() => readCachedUser());
  const [isLoading, setIsLoading] = useState<boolean>(() => {
    const savedToken = localStorage.getItem(TOKEN_KEY);
    if (!savedToken) return false;
    return !readCachedUser();
  });
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [googleClientId, setGoogleClientId] = useState<string>(
    import.meta.env.VITE_GOOGLE_CLIENT_ID || DEFAULT_CLIENT_ID
  );
  const [isAuthConfigLoading, setIsAuthConfigLoading] = useState<boolean>(
    () => !(import.meta.env.VITE_GOOGLE_CLIENT_ID || DEFAULT_CLIENT_ID)
  );
  const [isSyncingSession, setIsSyncingSession] = useState<boolean>(
    () => Boolean(localStorage.getItem(TOKEN_KEY))
  );
  const [isBackendReady, setIsBackendReady] = useState<boolean>(false);

  // Fetch auth config from backend (retrying transparently during cold start)
  useEffect(() => {
    let cancelled = false;
    let retryTimer: number | null = null;

    const loadAuthConfig = (retryCount = 0) => {
      if (retryCount === 0 && !googleClientId) {
        setIsAuthConfigLoading(true);
      }

      apiClient.get('/api/auth/config')
        .then(res => {
          if (cancelled) return;
          const id = res.data?.data?.google_client_id;
          if (id) {
            setGoogleClientId(id);
          }
          setIsBackendReady(true);
          setIsAuthConfigLoading(false);
        })
        .catch(err => {
          if (cancelled) return;
          if (isTransientBackendError(err) && retryCount < MAX_COLD_START_RETRIES) {
            retryTimer = window.setTimeout(() => {
              if (!cancelled) {
                loadAuthConfig(retryCount + 1);
              }
            }, COLD_START_RETRY_DELAY_MS);
            return;
          }
          setIsAuthConfigLoading(false);
        });
    };

    loadAuthConfig(0);

    return () => {
      cancelled = true;
      if (retryTimer !== null) {
        window.clearTimeout(retryTimer);
      }
    };
  }, []);

  // Sync current user profile on startup if token exists
  useEffect(() => {
    if (!token) {
      setIsSyncingSession(false);
      setIsLoading(false);
      return;
    }

    let cancelled = false;
    let retryTimer: number | null = null;

    setIsSyncingSession(true);

    const syncSession = (retryCount = 0) => {
      apiClient.get('/api/auth/me')
        .then(res => {
          if (cancelled) return;
          if (res.data?.data?.user) {
            const freshUser = res.data.data.user;
            setUser(freshUser);
            localStorage.setItem(USER_KEY, JSON.stringify(freshUser));
          }
          setIsBackendReady(true);
          setIsSyncingSession(false);
          setIsLoading(false);
        })
        .catch(err => {
          if (cancelled) return;
          if (err.response?.status === 401) {
            // Token expired or invalid
            setToken(null);
            setUser(null);
            localStorage.removeItem(TOKEN_KEY);
            localStorage.removeItem(USER_KEY);
            setIsBackendReady(true);
            setIsSyncingSession(false);
            setIsLoading(false);
            return;
          }

          if (isTransientBackendError(err) && retryCount < MAX_COLD_START_RETRIES) {
            retryTimer = window.setTimeout(() => {
              if (!cancelled) {
                syncSession(retryCount + 1);
              }
            }, COLD_START_RETRY_DELAY_MS);
            return;
          }

          setIsSyncingSession(false);
          setIsLoading(false);
        });
    };

    syncSession(0);

    return () => {
      cancelled = true;
      if (retryTimer !== null) {
        window.clearTimeout(retryTimer);
      }
    };
  }, [token]);

  const loginWithGoogleCredential = useCallback(async (credential: string): Promise<boolean> => {
    try {
      const res = await apiClient.post('/api/auth/google', { credential });
      const data = res.data?.data;
      if (data?.token && data?.user) {
        setToken(data.token);
        setUser(data.user);
        setIsBackendReady(true);
        setIsLoading(false);
        localStorage.setItem(TOKEN_KEY, data.token);
        localStorage.setItem(USER_KEY, JSON.stringify(data.user));
        setIsLoginModalOpen(false);
        return true;
      }
      return false;
    } catch (err) {
      console.error('Google login error:', err);
      return false;
    }
  }, []);

  const devLogin = useCallback(async (email?: string): Promise<boolean> => {
    try {
      const res = await apiClient.post('/api/auth/dev-login', { email: email || '' });
      const data = res.data?.data;
      if (data?.token && data?.user) {
        setToken(data.token);
        setUser(data.user);
        setIsBackendReady(true);
        setIsLoading(false);
        localStorage.setItem(TOKEN_KEY, data.token);
        localStorage.setItem(USER_KEY, JSON.stringify(data.user));
        setIsLoginModalOpen(false);
        return true;
      }
      return false;
    } catch (err) {
      console.error('Dev login error:', err);
      return false;
    }
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    setIsSyncingSession(false);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    apiClient.post('/api/auth/logout').catch(() => {});
  }, []);

  const renderGoogleButton = useCallback((elementId: string) => {
    if (typeof window === 'undefined' || !googleClientId) return;
    const g = (window as any).google;
    if (!g?.accounts?.id) {
      // Script not loaded yet, retry in 300ms
      setTimeout(() => renderGoogleButton(elementId), 300);
      return;
    }

    const target = document.getElementById(elementId);
    if (!target) return;

    g.accounts.id.initialize({
      client_id: googleClientId,
      callback: (response: any) => {
        if (response.credential) {
          loginWithGoogleCredential(response.credential);
        }
      }
    });

    g.accounts.id.renderButton(target, {
      theme: 'outline',
      size: 'large',
      text: 'signin_with',
      shape: 'rectangular',
      width: 280
    });
  }, [googleClientId, loginWithGoogleCredential]);

  const openLoginModal = useCallback(() => setIsLoginModalOpen(true), []);
  const closeLoginModal = useCallback(() => setIsLoginModalOpen(false), []);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isAuthConfigLoading,
        isSyncingSession,
        isBackendReady,
        googleClientId,
        loginWithGoogleCredential,
        devLogin,
        logout,
        openLoginModal,
        closeLoginModal,
        isLoginModalOpen,
        renderGoogleButton
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

const defaultAuthContext: AuthContextType = {
  user: null,
  token: null,
  isLoading: false,
  isAuthConfigLoading: false,
  isSyncingSession: false,
  isBackendReady: true,
  googleClientId: '',
  loginWithGoogleCredential: async () => false,
  devLogin: async () => false,
  logout: () => {},
  openLoginModal: () => {},
  closeLoginModal: () => {},
  isLoginModalOpen: false,
  renderGoogleButton: () => {},
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  return context || defaultAuthContext;
};
