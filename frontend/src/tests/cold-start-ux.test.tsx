import '@/i18n';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, act, waitFor } from '@testing-library/react';
import { AccessCodeGuard } from '@/components/shared/AccessCodeGuard';
import { AuthProvider, useAuth } from '@/context/AuthContext';
import { LoginModal } from '@/components/shared/LoginModal';

const { checkAccessCodeMock, verifyAccessCodeMock, apiGetMock, apiPostMock } = vi.hoisted(() => ({
  checkAccessCodeMock: vi.fn(),
  verifyAccessCodeMock: vi.fn(),
  apiGetMock: vi.fn(),
  apiPostMock: vi.fn(),
}));

vi.mock('@/api/endpoints', () => ({
  checkAccessCode: checkAccessCodeMock,
  verifyAccessCode: verifyAccessCodeMock,
}));

vi.mock('@/api/client', () => ({
  apiClient: {
    get: apiGetMock,
    post: apiPostMock,
  },
}));

function AuthStateProbe() {
  const { user, isLoading, isSyncingSession, openLoginModal } = useAuth();
  return (
    <div>
      <span data-testid="auth-loading">{String(isLoading)}</span>
      <span data-testid="auth-syncing">{String(isSyncingSession)}</span>
      <span data-testid="auth-user">{user ? user.email : 'anonymous'}</span>
      <button onClick={openLoginModal}>Open Login</button>
    </div>
  );
}

describe('Cold-start UX resilience', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_GOOGLE_CLIENT_ID', '');
    localStorage.clear();
    sessionStorage.clear();
    vi.clearAllMocks();
    (window as unknown as { google?: unknown }).google = {
      accounts: {
        id: {
          initialize: vi.fn(),
          renderButton: vi.fn(),
        },
      },
    };
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.useRealTimers();
  });

  it('renders children immediately while access code check is pending and retries transient 502', async () => {
    vi.useFakeTimers();

    checkAccessCodeMock
      .mockRejectedValueOnce({ response: { status: 502 } })
      .mockResolvedValueOnce({ data: { enabled: true } });

    render(
      <AccessCodeGuard>
        <div>Landing Content</div>
      </AccessCodeGuard>
    );

    // Zero white screen on initial mount while access-code request is still in-flight / failing transiently
    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
    });
    expect(screen.getByText('Landing Content')).toBeInTheDocument();
    expect(screen.queryByText('Nhập mã truy cập')).not.toBeInTheDocument();

    // Cold-start retry fires after 2500ms and discovers access code is required
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2500);
    });
    expect(checkAccessCodeMock).toHaveBeenCalledTimes(2);
    expect(screen.getByPlaceholderText('Nhập mã truy cập')).toBeInTheDocument();
  });

  it('shows neutral loading indicator in LoginModal while auth config is waking up, then renders Google button', async () => {
    let resolveConfig!: (value: unknown) => void;
    apiGetMock.mockImplementation((url: string) => {
      if (url === '/api/auth/config') {
        return new Promise((resolve) => {
          resolveConfig = resolve;
        });
      }
      return Promise.resolve({ data: {} });
    });

    render(
      <AuthProvider>
        <AuthStateProbe />
        <LoginModal />
      </AuthProvider>
    );

    expect(screen.getByTestId('auth-loading')).toHaveTextContent('false');
    await act(async () => {
      screen.getByText('Open Login').click();
    });

    expect(screen.getByText('Đang tải dữ liệu...')).toBeInTheDocument();

    await act(async () => {
      resolveConfig({ data: { data: { google_client_id: 'client-123.apps.googleusercontent.com' } } });
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(document.getElementById('google-modal-btn')).toBeInTheDocument();
    });
    expect(screen.queryByText('Đang tải dữ liệu...')).not.toBeInTheDocument();
  });

  it('unblocks cached user session immediately, syncs in background, and clears on 401', async () => {
    localStorage.setItem('banana-auth-token', 'jwt-token-1');
    localStorage.setItem(
      'banana-auth-user',
      JSON.stringify({
        id: 'u-1',
        email: 'cached@example.com',
        name: 'Cached User',
        role: 'user',
        login_count: 1,
        generation_count: 0,
        tokens_in: 0,
        tokens_out: 0,
      })
    );

    let rejectMe!: (err: unknown) => void;
    apiGetMock.mockImplementation((url: string) => {
      if (url === '/api/auth/config') {
        return Promise.resolve({ data: { data: { google_client_id: 'client-123' } } });
      }
      if (url === '/api/auth/me') {
        return new Promise((_resolve, reject) => {
          rejectMe = reject;
        });
      }
      return Promise.resolve({ data: {} });
    });

    render(
      <AuthProvider>
        <AuthStateProbe />
      </AuthProvider>
    );

    // Cached session is immediately usable without blocking full-screen spinner
    expect(screen.getByTestId('auth-loading')).toHaveTextContent('false');
    expect(screen.getByTestId('auth-syncing')).toHaveTextContent('true');
    expect(screen.getByTestId('auth-user')).toHaveTextContent('cached@example.com');

    await act(async () => {
      rejectMe({ response: { status: 401 } });
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(screen.getByTestId('auth-syncing')).toHaveTextContent('false');
      expect(screen.getByTestId('auth-user')).toHaveTextContent('anonymous');
    });
    expect(localStorage.getItem('banana-auth-token')).toBeNull();
  });
});
