import React, { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';
import { cn } from '@/utils';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  showPasswordToggle?: boolean;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  className,
  type,
  showPasswordToggle,
  ...props
}) => {
  const [showPassword, setShowPassword] = useState(false);
  const isPassword = type === 'password';
  const effectiveType = isPassword && (showPasswordToggle ?? true)
    ? (showPassword ? 'text' : 'password')
    : type;

  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-gray-700 dark:text-foreground-secondary mb-2">
          {label}
        </label>
      )}
      <div className="relative">
        <input
          type={effectiveType}
          className={cn(
            'w-full h-10 px-4 rounded-lg border border-gray-200 dark:border-border-primary bg-white dark:bg-background-secondary',
            'focus:outline-none focus:ring-2 focus:ring-banana-500 focus:border-transparent',
            'placeholder:text-gray-400 dark:placeholder:text-gray-500 transition-all',
            'text-gray-900 dark:text-foreground-primary',
            isPassword && (showPasswordToggle ?? true) && 'pr-11',
            error && 'border-red-500 focus:ring-red-500',
            className
          )}
          {...props}
        />
        {isPassword && (showPasswordToggle ?? true) && (
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors p-1"
            title={showPassword ? 'Ẩn' : 'Hiện'}
            aria-label={showPassword ? 'Ẩn' : 'Hiện'}
            tabIndex={-1}
          >
            {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        )}
      </div>
      {error && (
        <p className="mt-1 text-sm text-red-500">{error}</p>
      )}
    </div>
  );
};
