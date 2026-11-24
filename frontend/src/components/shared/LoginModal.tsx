import React, { useEffect } from 'react';
import { Modal } from './Modal';
import { useAuth } from '@/context/AuthContext';
import { useT } from '@/hooks/useT';
import { Sparkles } from 'lucide-react';

const loginModalI18n = {
  zh: {
    loading: 'Đang tải dữ liệu...',
    unavailable: 'Tạm thời chưa thể tải đăng nhập Google. Vui lòng thử lại sau.',
  },
  en: {
    loading: 'Loading...',
    unavailable: 'Google Sign-In is temporarily unavailable. Please try again later.',
  },
};

export const LoginModal: React.FC = () => {
  const { isLoginModalOpen, closeLoginModal, renderGoogleButton, googleClientId, isAuthConfigLoading } = useAuth();
  const t = useT(loginModalI18n);

  useEffect(() => {
    if (isLoginModalOpen && googleClientId) {
      // Delay slightly for DOM element to mount
      const timer = setTimeout(() => {
        renderGoogleButton('google-modal-btn');
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [isLoginModalOpen, googleClientId, renderGoogleButton]);

  return (
    <Modal
      isOpen={isLoginModalOpen}
      onClose={closeLoginModal}
      title="Đăng nhập tài khoản"
      maxWidth="max-w-md"
    >
      <div className="py-2 text-center">
        <div className="mx-auto w-14 h-14 bg-amber-500/10 text-amber-600 rounded-2xl flex items-center justify-center mb-4">
          <Sparkles className="w-7 h-7" />
        </div>

        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
          Chào mừng đến với Banana Slides
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-6 px-4">
          Đăng nhập với Google để tách biệt dữ liệu, lưu trữ lịch sử tạo slide và đồng bộ dự án cá nhân.
        </p>

        <div className="w-full flex justify-center items-center my-6 min-h-[50px]">
          {!googleClientId && isAuthConfigLoading ? (
            <div className="flex items-center gap-2.5 text-sm text-gray-600 dark:text-gray-300">
              <span className="w-4 h-4 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
              <span>{t('loading')}</span>
            </div>
          ) : !googleClientId ? (
            <p className="text-xs text-gray-500 dark:text-gray-400 px-4">
              {t('unavailable')}
            </p>
          ) : (
            <div
              id="google-modal-btn"
              className="flex justify-center items-center w-full [&>div]:!mx-auto [&>iframe]:!mx-auto"
            />
          )}
        </div>
      </div>
    </Modal>
  );
};
