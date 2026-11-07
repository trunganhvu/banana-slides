import React, { useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { KeyRound, Settings, AlertTriangle, ArrowRight, Clock, X, Sparkles, CheckCircle2 } from 'lucide-react';
import { Modal } from './Modal';
import { Button } from './Button';
import { useApiKeyReminderStore } from '@/store/useApiKeyReminderStore';

const reminderI18n = {
  zh: {
    title: 'Chưa cấu hình API Key',
    subtitle: 'Để tạo bài thuyết trình bằng AI, bạn cần cấu hình ít nhất một API Key hợp lệ',
    desc: 'Hệ thống cần API Key để phân tích chủ đề, xây dựng dàn ý cấu trúc và vẽ minh họa từng trang slide.',
    guideTitle: 'Hướng dẫn cấu hình nhanh',
    guideStep1: 'Nhấp vào biểu tượng bánh răng Cài đặt ở góc trên bên phải màn hình (đang phát sáng báo hiệu).',
    guideStep2: 'Hoặc nhấp trực tiếp vào nút "Đi tới Cài đặt cấu hình" bên dưới.',
    recommendationTitle: 'Các nhà cung cấp AI được khuyên dùng:',
    geminiRec: 'Google Gemini: Khuyên dùng, có gói miễn phí, tốc độ cao, hỗ trợ cả dàn ý văn bản và tạo ảnh slide trực tiếp.',
    otherRec: 'OpenAI / DeepSeek / SiliconFlow: Hỗ trợ văn bản sắc nét và suy luận sâu.',
    btnGoSettings: 'Đi tới Cài đặt cấu hình',
    btnRemindLater: 'Nhắc tôi sau',
    pillText: 'Chưa cấu hình API Key • Nhấp để cấu hình',
    pillDismiss: 'Tạm ẩn nhắc nhở',
  },
  en: {
    title: 'API Key Not Configured',
    subtitle: 'To generate presentations with AI, you need to configure at least one valid API Key',
    desc: 'The system requires an API Key to analyze topics, generate slide outlines, and render slide illustrations.',
    guideTitle: 'Quick Setup Guide',
    guideStep1: 'Click the glowing Settings gear icon at the top right of the screen.',
    guideStep2: 'Or click the "Go to Settings" button below directly.',
    recommendationTitle: 'Recommended AI Providers:',
    geminiRec: 'Google Gemini: Highly recommended, free tier available, fast, supports both text outlines and direct slide image generation.',
    otherRec: 'OpenAI / DeepSeek / SiliconFlow: High quality text and deep reasoning.',
    btnGoSettings: 'Go to Settings',
    btnRemindLater: 'Remind me later',
    pillText: 'API Key Not Configured • Click to setup',
    pillDismiss: 'Dismiss reminder',
  },
};

export const ApiKeyReminderModal: React.FC = () => {
  const { i18n } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();

  const isEn = i18n.language?.startsWith('en');
  const t = isEn ? reminderI18n.en : reminderI18n.zh;

  const {
    isConfigured,
    isModalOpen,
    isFloatingDismissed,
    checkSettings,
    openModal,
    closeModal,
    dismissFloating,
  } = useApiKeyReminderStore();

  // Run initial check on mount
  useEffect(() => {
    checkSettings();
  }, [checkSettings]);

  // If user is currently on /settings, hide both modal and floating pill
  const isSettingsPage = location.pathname === '/settings';

  const handleNavigateToSettings = () => {
    closeModal();
    navigate('/settings');
  };

  if (isSettingsPage || isConfigured === true || isConfigured === null) {
    return null;
  }

  return (
    <>
      {/* 1. Detail Popup Reminder Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={closeModal}
        size="md"
        showCloseButton={true}
      >
        <div className="space-y-5 py-1">
          {/* Header Banner */}
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-2xl bg-amber-100 dark:bg-amber-950/50 border border-amber-300 dark:border-amber-700/60 flex items-center justify-center shrink-0 shadow-inner">
              <KeyRound className="w-6 h-6 text-amber-600 dark:text-amber-400" />
            </div>
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                  {t.title}
                </h3>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 dark:bg-amber-900/60 dark:text-amber-300 border border-amber-200 dark:border-amber-700/50">
                  <AlertTriangle className="w-3 h-3 mr-1 inline" />
                  Cần thiết
                </span>
              </div>
              <p className="text-xs text-gray-600 dark:text-gray-300 leading-relaxed">
                {t.subtitle}
              </p>
            </div>
          </div>

          {/* Description */}
          <div className="text-xs text-gray-600 dark:text-gray-300 bg-gray-50 dark:bg-gray-800/40 p-3.5 rounded-xl border border-gray-200 dark:border-border-primary">
            {t.desc}
          </div>

          {/* Guide Box */}
          <div className="rounded-xl border border-amber-200 bg-amber-50/70 p-4 dark:border-amber-800/60 dark:bg-amber-950/20 space-y-3">
            <div className="flex items-center gap-2 text-xs font-semibold text-amber-900 dark:text-amber-200">
              <Sparkles className="w-4 h-4 text-amber-600 dark:text-amber-400" />
              <span>{t.guideTitle}</span>
            </div>
            <ul className="text-xs text-amber-800 dark:text-amber-300/90 space-y-2 list-none pl-0">
              <li className="flex items-start gap-2">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-amber-200 dark:bg-amber-800/80 text-[11px] font-bold text-amber-900 dark:text-amber-100">
                  1
                </span>
                <span className="pt-0.5">{t.guideStep1}</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-amber-200 dark:bg-amber-800/80 text-[11px] font-bold text-amber-900 dark:text-amber-100">
                  2
                </span>
                <span className="pt-0.5">{t.guideStep2}</span>
              </li>
            </ul>

            {/* Recommendations */}
            <div className="pt-2 border-t border-amber-200/70 dark:border-amber-800/50 space-y-1.5">
              <p className="text-[11px] font-semibold text-amber-900 dark:text-amber-200">
                {t.recommendationTitle}
              </p>
              <div className="flex items-start gap-1.5 text-[11px] text-amber-800/90 dark:text-amber-300/80">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                <span>{t.geminiRec}</span>
              </div>
              <div className="flex items-start gap-1.5 text-[11px] text-amber-800/90 dark:text-amber-300/80">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                <span>{t.otherRec}</span>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col-reverse sm:flex-row items-center justify-end gap-2.5 pt-2">
            <Button
              variant="secondary"
              size="sm"
              icon={<Clock size={15} />}
              onClick={closeModal}
              className="w-full sm:w-auto text-xs"
            >
              {t.btnRemindLater}
            </Button>
            <Button
              variant="primary"
              size="sm"
              icon={<Settings size={15} />}
              onClick={handleNavigateToSettings}
              className="w-full sm:w-auto text-xs font-semibold shadow-md shadow-banana-500/20"
            >
              {t.btnGoSettings}
              <ArrowRight size={14} className="ml-1 inline" />
            </Button>
          </div>
        </div>
      </Modal>

      {/* 2. Sleek Floating Pill Reminder (visible when modal is closed but key still not configured) */}
      {!isModalOpen && !isFloatingDismissed && (
        <div
          role="status"
          aria-live="polite"
          className="fixed bottom-6 right-6 z-40 flex items-center gap-2.5 bg-gradient-to-r from-amber-500 via-amber-600 to-amber-700 hover:from-amber-600 hover:to-amber-800 text-white pl-4 pr-2.5 py-2.5 rounded-full shadow-xl hover:shadow-2xl transition-all duration-300 ring-2 ring-white/50 dark:ring-amber-400/30 group animate-in fade-in slide-in-from-bottom-3"
        >
          <button
            type="button"
            onClick={openModal}
            className="flex items-center gap-2 text-left font-medium text-xs sm:text-sm hover:underline focus:outline-none"
            title={t.title}
          >
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-80" />
              <span className="relative inline-flex rounded-full h-3 w-3 bg-white" />
            </span>
            <KeyRound size={15} className="shrink-0 text-white/95" />
            <span className="font-semibold">{t.pillText}</span>
          </button>

          <button
            type="button"
            onClick={handleNavigateToSettings}
            className="p-1 rounded-full bg-white/20 hover:bg-white/30 text-white transition-colors"
            title={t.btnGoSettings}
          >
            <Settings size={14} />
          </button>

          <button
            type="button"
            onClick={dismissFloating}
            className="p-1 rounded-full bg-white/10 hover:bg-white/25 text-white/80 hover:text-white transition-colors"
            title={t.pillDismiss}
          >
            <X size={13} />
          </button>
        </div>
      )}
    </>
  );
};
