import React from 'react';
import {
  CheckCircle2,
  AlertCircle,
  Loader2,
  X,
  RotateCcw,
} from 'lucide-react';
import { Button } from '@/components/shared';

export interface InlineServiceTestState {
  status: 'idle' | 'loading' | 'success' | 'error';
  message?: string;
  detail?: string;
}

export interface SettingsInlineServiceTestProps {
  testKey: string;
  label: string;
  description?: string;
  testState?: InlineServiceTestState;
  onTest: () => void;
  onDismiss?: () => void;
  isVi?: boolean;
  icon?: React.ReactNode;
  disabled?: boolean;
  disabledReason?: string;
  size?: 'sm' | 'md';
  variant?: 'primary' | 'secondary';
  className?: string;
}

export const SettingsInlineServiceTest: React.FC<SettingsInlineServiceTestProps> = ({
  testKey,
  label,
  description,
  testState = { status: 'idle' },
  onTest,
  onDismiss,
  isVi = true,
  icon,
  disabled = false,
  disabledReason,
  size = 'sm',
  variant = 'secondary',
  className = '',
}) => {
  const isLoading = testState.status === 'loading';
  const isSuccess = testState.status === 'success';
  const isError = testState.status === 'error';

  return (
    <div className={`space-y-2.5 ${className}`} data-testid={`inline-test-${testKey}`}>
      <div className="flex flex-wrap items-center gap-2.5">
        <Button
          type="button"
          variant={variant}
          size={size}
          loading={isLoading}
          disabled={disabled || isLoading}
          onClick={onTest}
          icon={!isLoading ? icon : undefined}
          title={disabled && disabledReason ? disabledReason : label}
          className="transition-all shadow-xs"
        >
          {isLoading
            ? isVi
              ? 'Đang kiểm tra...'
              : 'Testing...'
            : label}
        </Button>

        {description && (
          <span className="text-xs text-gray-500 dark:text-foreground-tertiary">
            {description}
          </span>
        )}

        {disabled && disabledReason && (
          <span className="text-xs text-amber-600 dark:text-amber-400">
            ({disabledReason})
          </span>
        )}
      </div>

      {/* Loading state indicator */}
      {isLoading && (
        <div className="flex items-center gap-2 p-3 rounded-lg border border-banana-200 bg-banana-50/60 dark:border-banana-800/60 dark:bg-banana-950/20 text-xs text-banana-900 dark:text-banana-200 animate-pulse">
          <Loader2 size={15} className="animate-spin text-banana-600 dark:text-banana-400 shrink-0" />
          <span>
            {isVi
              ? 'Đang gửi yêu cầu thử nghiệm và chờ phản hồi từ dịch vụ... (Có thể mất 5-30 giây)'
              : 'Sending test request and waiting for response... (May take 5-30 seconds)'}
          </span>
        </div>
      )}

      {/* Success feedback card */}
      {isSuccess && (
        <div className="relative p-3.5 rounded-lg border border-emerald-200 bg-emerald-50/70 dark:border-emerald-800/80 dark:bg-emerald-950/30 text-xs text-emerald-900 dark:text-emerald-200 transition-all">
          {onDismiss && (
            <button
              type="button"
              onClick={onDismiss}
              className="absolute top-2.5 right-2.5 p-1 rounded-md text-emerald-600 hover:text-emerald-800 dark:text-emerald-400 dark:hover:text-emerald-200 hover:bg-emerald-100 dark:hover:bg-emerald-900/40 transition-colors"
              title={isVi ? 'Đóng thông báo' : 'Dismiss'}
            >
              <X size={14} />
            </button>
          )}

          <div className="flex items-start gap-2 pr-6">
            <CheckCircle2 size={16} className="text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="font-semibold text-emerald-800 dark:text-emerald-300">
                {testState.message || (isVi ? 'Kiểm tra thành công! Dịch vụ hoạt động tốt.' : 'Test passed! Service is operating normally.')}
              </p>
              {testState.detail && (
                <div className="mt-1 p-2 rounded bg-white/80 dark:bg-background-secondary/80 border border-emerald-200/60 dark:border-emerald-800/40 font-mono text-[11px] text-emerald-800 dark:text-emerald-300 break-words max-h-28 overflow-y-auto">
                  {testState.detail}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Error feedback card */}
      {isError && (
        <div className="relative p-3.5 rounded-lg border border-red-200 bg-red-50/70 dark:border-red-800/80 dark:bg-red-950/30 text-xs text-red-900 dark:text-red-200 transition-all">
          <div className="absolute top-2.5 right-2.5 flex items-center gap-1">
            <button
              type="button"
              onClick={onTest}
              className="p-1 rounded-md text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-200 hover:bg-red-100 dark:hover:bg-red-900/40 transition-colors flex items-center gap-1 text-[11px]"
              title={isVi ? 'Thử lại' : 'Retry'}
            >
              <RotateCcw size={12} />
              <span>{isVi ? 'Thử lại' : 'Retry'}</span>
            </button>
            {onDismiss && (
              <button
                type="button"
                onClick={onDismiss}
                className="p-1 rounded-md text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-200 hover:bg-red-100 dark:hover:bg-red-900/40 transition-colors"
                title={isVi ? 'Đóng thông báo' : 'Dismiss'}
              >
                <X size={14} />
              </button>
            )}
          </div>

          <div className="flex items-start gap-2 pr-16">
            <AlertCircle size={16} className="text-red-600 dark:text-red-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="font-semibold text-red-800 dark:text-red-300">
                {isVi ? 'Kiểm tra thất bại' : 'Service Test Failed'}
              </p>
              <p className="text-red-700 dark:text-red-300 break-words leading-relaxed">
                {testState.message}
              </p>
              <p className="text-[11px] text-gray-500 dark:text-foreground-tertiary pt-0.5">
                {isVi
                  ? 'Gợi ý: Hãy kiểm tra xem API Key đã nhập chính xác, tài khoản còn hạn ngạch mức sử dụng và API Base URL có cần cấu hình không.'
                  : 'Tip: Check if the API key is correct, account quota is available, and if API Base URL requires configuration.'}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
