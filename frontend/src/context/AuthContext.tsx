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
const DEFAULT_CLIENT_ID = '334779236698-h5npe9dpulcm2vfo2c7kh7vuur6hsbvs.apps.googleusercontent.com';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState<User | null>(() => {
    try {
      const saved = localStorage.getItem(USER_KEY);
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [googleClientId, setGoogleClientId] = useState<string>(
    import.meta.env.VITE_GOOGLE_CLIENT_ID || DEFAULT_CLIENT_ID
  );

  // Fetch auth config from backend
  useEffect(() => {
    apiClient.get('/api/auth/config')
      .then(res => {
        const id = res.data?.data?.google_client_id;
        if (id) {
          setGoogleClientId(id);
        }
      })
      .catch(() => {
        // Fallback to default
      });
  }, []);

  // Sync current user profile on startup if token exists
  useEffect(() => {
    if (!token) {
      setIsLoading(false);
      return;
    }

    apiClient.get('/api/auth/me')
      .then(res => {
        if (res.data?.data?.user) {
          const freshUser = res.data.data.user;
          setUser(freshUser);
          localStorage.setItem(USER_KEY, JSON.stringify(freshUser));
        }
      })
      .catch(err => {
        if (err.response?.status === 401) {
          // Token expired or invalid
          setToken(null);
          setUser(null);
          localStorage.removeItem(TOKEN_KEY);
          localStorage.removeItem(USER_KEY);
        }
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [token]);

  const loginWithGoogleCredential = useCallback(async (credential: string): Promise<boolean> => {
    try {
      const res = await apiClient.post('/api/auth/google', { credential });
      const data = res.data?.data;
      if (data?.token && data?.user) {
        setToken(data.token);
        setUser(data.user);
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
      const res = await apiClient.post('/api/auth/dev-login', { email: email || 'vutrunganh1@gmail.com' });
      const data = res.data?.data;
      if (data?.token && data?.user) {
        setToken(data.token);
        setUser(data.user);
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
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    apiClient.post('/api/auth/logout').catch(() => {});
  }, []);

  const renderGoogleButton = useCallback((elementId: string) => {
    if (typeof window === 'undefined') return;
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

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
