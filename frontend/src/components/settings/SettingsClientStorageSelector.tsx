import React from 'react';
import { ShieldCheck, Globe, Lock, Trash2, CheckCircle2 } from 'lucide-react';
import {
  getClientStorageMode,
  setClientStorageMode,
  hasClientKeyConfigured,
  clearClientKeys,
} from '@/utils/clientKeyStorage';

interface SettingsClientStorageSelectorProps {
  storageMode: 'client' | 'server';
  onStorageModeChange: (mode: 'client' | 'server') => void;
  onClientKeysCleared?: () => void;
}

export const SettingsClientStorageSelector: React.FC<SettingsClientStorageSelectorProps> = ({
  storageMode,
  onStorageModeChange,
  onClientKeysCleared,
}) => {
  const hasClientKey = hasClientKeyConfigured();

  const handleSelectMode = (mode: 'client' | 'server') => {
    setClientStorageMode(mode);
    onStorageModeChange(mode);
  };

  const handleClearClientKeys = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (window.confirm('Bạn có chắc muốn xóa API Key đã lưu trên thiết bị này không?')) {
      clearClientKeys();
      onClientKeysCleared?.();
    }
  };

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm dark:border-border-primary dark:bg-background-secondary space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-gray-100 dark:border-border-primary pb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
            <Lock size={16} />
          </div>
          <div>
            <h3 className="text-sm font-bold text-gray-900 dark:text-white flex items-center gap-2">
              Phạm vi lưu trữ API Key & Bảo mật
              <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 dark:bg-emerald-950/70 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                AES-256 GCM
              </span>
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Chọn lưu API Key an toàn tại trình duyệt cá nhân hoặc lưu chung trên máy chủ
            </p>
          </div>
        </div>

        {hasClientKey && (
          <button
            type="button"
            onClick={handleClearClientKeys}
            className="inline-flex items-center gap-1.5 text-xs text-rose-600 hover:text-rose-700 dark:text-rose-400 hover:underline px-2 py-1 rounded-md hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors self-start sm:self-auto"
            title="Xóa Key đã mã hóa trên máy này"
          >
            <Trash2 size={13} />
            <span>Xóa Key trên máy này</span>
          </button>
        )}
      </div>

      {/* Two Mode Options */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
        {/* Option 1: Client Storage */}
        <div
          onClick={() => handleSelectMode('client')}
          className={`relative flex items-start gap-3.5 p-4 rounded-xl border-2 cursor-pointer transition-all duration-200 ${
            storageMode === 'client'
              ? 'border-emerald-500 bg-emerald-50/50 dark:border-emerald-500 dark:bg-emerald-950/20 shadow-sm'
              : 'border-gray-200 hover:border-gray-300 dark:border-border-primary dark:hover:border-gray-700 bg-gray-50/40 dark:bg-background-tertiary/40'
          }`}
        >
          <div className="pt-0.5">
            <input
              type="radio"
              name="storage_mode"
              checked={storageMode === 'client'}
              onChange={() => handleSelectMode('client')}
              className="w-4 h-4 text-emerald-600 focus:ring-emerald-500 cursor-pointer"
            />
          </div>
          <div className="flex-1 space-y-1">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              <span className="text-xs font-bold text-gray-900 dark:text-white">
                Lưu trên thiết bị này (Client Storage)
              </span>
              <span className="text-[10px] font-semibold text-emerald-700 dark:text-emerald-300 bg-emerald-100/70 dark:bg-emerald-900/60 px-1.5 py-0.2 rounded">
                Khuyên dùng
              </span>
            </div>
            <p className="text-[11px] text-gray-600 dark:text-gray-300 leading-relaxed">
              API Key được mã hóa AES-256 bằng Web Crypto API và lưu riêng tại trình duyệt này. Server KHÔNG lưu Key vào cơ sở dữ liệu.
            </p>
            {hasClientKey && (
              <div className="pt-1 flex items-center gap-1.5 text-[11px] font-medium text-emerald-700 dark:text-emerald-400">
                <CheckCircle2 size={13} />
                <span>Đang có API Key mã hóa hoạt động trên trình duyệt này</span>
              </div>
            )}
          </div>
        </div>

        {/* Option 2: Server Storage */}
        <div
          onClick={() => handleSelectMode('server')}
          className={`relative flex items-start gap-3.5 p-4 rounded-xl border-2 cursor-pointer transition-all duration-200 ${
            storageMode === 'server'
              ? 'border-banana-500 bg-banana-50/50 dark:border-banana-500 dark:bg-banana-950/20 shadow-sm'
              : 'border-gray-200 hover:border-gray-300 dark:border-border-primary dark:hover:border-gray-700 bg-gray-50/40 dark:bg-background-tertiary/40'
          }`}
        >
          <div className="pt-0.5">
            <input
              type="radio"
              name="storage_mode"
              checked={storageMode === 'server'}
              onChange={() => handleSelectMode('server')}
              className="w-4 h-4 text-banana-600 focus:ring-banana-500 cursor-pointer"
            />
          </div>
          <div className="flex-1 space-y-1">
            <div className="flex items-center gap-2">
              <Globe className="w-4 h-4 text-banana-600 dark:text-banana-400" />
              <span className="text-xs font-bold text-gray-900 dark:text-white">
                Lưu chung trên Server (Server Database)
              </span>
            </div>
            <p className="text-[11px] text-gray-600 dark:text-gray-300 leading-relaxed">
              Lưu tập trung vào cơ sở dữ liệu của máy chủ. Thích hợp khi bạn dựng server cá nhân/nội bộ và muốn tất cả các máy truy cập đều dùng chung 1 bộ key.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
