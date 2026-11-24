import { useState, useEffect, useCallback, useRef, type ReactNode } from 'react';
import { checkAccessCode, verifyAccessCode } from '@/api/endpoints';
import { useT } from '@/hooks/useT';
import { Button } from './Button';
import { Input } from './Input';

const STORAGE_KEY = 'banana-access-code';
const MAX_COLD_START_RETRIES = 6;
const COLD_START_RETRY_DELAY_MS = 2500;
const TRANSIENT_STATUS_CODES = new Set([502, 503, 504, 522, 524]);

function isTransientBackendError(err: unknown): boolean {
  const response = (err as { response?: { status?: number } })?.response;
  if (!response) return true;
  return typeof response.status === 'number' && TRANSIENT_STATUS_CODES.has(response.status);
}

const translations = {
  zh: {
    title: 'Vui lòng nhập mã truy cập',
    placeholder: 'Nhập mã truy cập',
    submit: 'Xác nhận',
    error: 'Sai mã truy cập, Vui lòng thử lại',
    networkError: 'Lỗi mạng, vui lòng thử lại sau',
    connectError: 'Không thể kết nối máy chủ',
    connectHint: 'Vui lòng kiểm tra dịch vụ backend có đang hoạt động bình thường không',
    retry: 'Thử lại',
  },
  en: {
    title: 'Enter Access Code',
    placeholder: 'Enter code',
    submit: 'Submit',
    error: 'Invalid code, please try again',
    networkError: 'Network error, please try later',
    connectError: 'Unable to reach server',
    connectHint: 'Please check if the backend service is running',
    retry: 'Retry',
  },
};

export function AccessCodeGuard({ children }: { children: ReactNode }) {
  const t = useT(translations);
  const [status, setStatus] = useState<'checking' | 'prompt' | 'pass' | 'connectError'>('checking');
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [verifying, setVerifying] = useState(false);

  const isMountedRef = useRef(true);
  const attemptIdRef = useRef(0);
  const retryTimerRef = useRef<number | null>(null);

  const clearRetryTimer = useCallback(() => {
    if (retryTimerRef.current !== null) {
      window.clearTimeout(retryTimerRef.current);
      retryTimerRef.current = null;
    }
  }, []);

  const checkAccess = useCallback(async (retryCount = 0) => {
    clearRetryTimer();
    const attemptId = ++attemptIdRef.current;
    if (retryCount === 0) {
      setStatus('checking');
    }

    try {
      const res = await checkAccessCode();
      if (!isMountedRef.current || attemptId !== attemptIdRef.current) return;

      if (!res.data.enabled) {
        setStatus('pass');
        return;
      }

      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        try {
          const v = await verifyAccessCode(saved);
          if (!isMountedRef.current || attemptId !== attemptIdRef.current) return;
          if (v.data.valid) {
            setStatus('pass');
            return;
          }
          localStorage.removeItem(STORAGE_KEY);
        } catch (verifyErr) {
          if (!isMountedRef.current || attemptId !== attemptIdRef.current) return;
          const verifyStatus = (verifyErr as { response?: { status?: number } })?.response?.status;
          if (verifyStatus === 403) {
            localStorage.removeItem(STORAGE_KEY);
          } else {
            throw verifyErr;
          }
        }
      }

      setStatus('prompt');
    } catch (err) {
      if (!isMountedRef.current || attemptId !== attemptIdRef.current) return;

      if (isTransientBackendError(err) && retryCount < MAX_COLD_START_RETRIES) {
        retryTimerRef.current = window.setTimeout(() => {
          if (isMountedRef.current && attemptId === attemptIdRef.current) {
            void checkAccess(retryCount + 1);
          }
        }, COLD_START_RETRY_DELAY_MS);
        return;
      }

      if (!isTransientBackendError(err)) {
        localStorage.removeItem(STORAGE_KEY);
      }
      setStatus('connectError');
    }
  }, [clearRetryTimer]);

  useEffect(() => {
    isMountedRef.current = true;
    void checkAccess(0);
    return () => {
      isMountedRef.current = false;
      clearRetryTimer();
    };
  }, [checkAccess, clearRetryTimer]);

  const handleSubmit = async () => {
    if (!code.trim()) return;
    setVerifying(true);
    setError('');
    try {
      const res = await verifyAccessCode(code.trim());
      if (res.data.valid) {
        localStorage.setItem(STORAGE_KEY, code.trim());
        setStatus('pass');
      } else {
        setError(t('error'));
      }
    } catch (e: unknown) {
      const status = (e as { response?: { status?: number } })?.response?.status;
      setError(status === 403 ? t('error') : t('networkError'));
    } finally {
      setVerifying(false);
    }
  };

  if (status === 'checking' || status === 'pass') return <>{children}</>;

  if (status === 'connectError') {
    return (
      <>
        {children}
        <div
          role="status"
          aria-live="polite"
          className="fixed bottom-4 right-4 z-50 flex items-center gap-3 px-4 py-2.5 rounded-xl bg-white/95 dark:bg-slate-900/95 backdrop-blur-md shadow-lg border border-amber-200 dark:border-amber-800/60 text-xs sm:text-sm"
        >
          <span className="text-slate-700 dark:text-slate-200 font-medium">
            {t('connectError')}
          </span>
          <Button size="sm" variant="secondary" onClick={() => void checkAccess(0)}>
            {t('retry')}
          </Button>
        </div>
      </>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background-primary">
      <div className="w-80 p-6 rounded-2xl bg-white dark:bg-background-secondary shadow-lg border border-gray-200 dark:border-border-primary">
        <h2 className="text-lg font-semibold text-center mb-4 text-gray-900 dark:text-foreground-primary">
          {t('title')}
        </h2>
        <form onSubmit={e => { e.preventDefault(); handleSubmit(); }} className="space-y-4">
          <Input
            type="password"
            placeholder={t('placeholder')}
            value={code}
            onChange={e => setCode(e.target.value)}
            error={error}
            autoFocus
          />
          <Button type="submit" className="w-full" loading={verifying}>
            {t('submit')}
          </Button>
        </form>
      </div>
    </div>
  );
}