import React, { useEffect, useState } from 'react';
import { Modal } from './Modal';
import { useAuth } from '@/context/AuthContext';
import { LogIn, Sparkles, ShieldCheck } from 'lucide-react';

export const LoginModal: React.FC = () => {
  const { isLoginModalOpen, closeLoginModal, renderGoogleButton, devLogin } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (isLoginModalOpen) {
      // Delay slightly for DOM element to mount
      const timer = setTimeout(() => {
        renderGoogleButton('google-modal-btn');
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [isLoginModalOpen, renderGoogleButton]);

  const handleDevLogin = async () => {
    setIsSubmitting(true);
    await devLogin();
    setIsSubmitting(false);
  };

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

        <div className="flex flex-col items-center justify-center gap-4 min-h-[50px] mb-6">
          <div id="google-modal-btn" className="flex justify-center" />
        </div>

        <div className="border-t border-gray-100 dark:border-zinc-800 pt-4 mt-2">
          <div className="flex items-center justify-center gap-1.5 text-xs text-gray-400 mb-3">
            <ShieldCheck className="w-3.5 h-3.5 text-green-500" />
            <span>Xác thực an toàn qua Google OAuth 2.0</span>
          </div>

          <button
            type="button"
            onClick={handleDevLogin}
            disabled={isSubmitting}
            className="w-full text-xs text-gray-500 hover:text-amber-600 dark:text-gray-400 dark:hover:text-amber-400 py-1.5 px-3 rounded-lg border border-dashed border-gray-200 dark:border-zinc-700 hover:border-amber-400 transition-colors"
          >
            Đăng nhập nhanh Admin (Môi trường Dev)
          </button>
        </div>
      </div>
    </Modal>
  );
};
