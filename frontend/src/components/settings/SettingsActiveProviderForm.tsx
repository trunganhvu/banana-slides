import React, { useState } from 'react';
import {
  Sparkles,
  ExternalLink,
  Eye,
  EyeOff,
  CheckCircle2,
  AlertCircle,
  RotateCcw,
  Zap,
  FileText,
  Image as ImageIcon,
  Save,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { Button } from '@/components/shared';
import { SettingsInlineServiceTest, type InlineServiceTestState } from './SettingsInlineServiceTest';
import type { Settings as SettingsType } from '@/types';
import type { useT } from '@/hooks/useT';

export interface SettingsActiveProviderFormProps {
  formData: {
    api_base_url: string;
    api_key: string;
    text_model: string;
    image_model: string;
    image_caption_model: string;
    [key: string]: any;
  };
  setFormData: React.Dispatch<React.SetStateAction<any>>;
  settings: SettingsType | null;
  handleFieldChange: (key: string, value: any) => void;
  t: ReturnType<typeof useT>;
  isVi: boolean;
  serviceTestStates?: Record<string, InlineServiceTestState>;
  triggerTest?: (testKey: string) => void;
  dismissTest?: (testKey: string) => void;
  onSave?: () => void;
  isSaving?: boolean;
}

interface ModelPresetOption {
  id: string;
  label: string;
  badgeVi?: string;
  badgeEn?: string;
}

const GOOGLE_GEMINI_METADATA: {
  name: string;
  portalName: string;
  portalUrl: string;
  defaultBaseUrl: string;
  description: { vi: string; en: string };
  textModels: ModelPresetOption[];
  imageModels: ModelPresetOption[];
  captionModels: ModelPresetOption[];
} = {
  name: 'Google Gemini',
  portalName: 'Google AI Studio',
  portalUrl: 'https://aistudio.google.com/app/apikey',
  defaultBaseUrl: 'https://generativelanguage.googleapis.com',
  description: {
    vi: 'Hỗ trợ cả tạo văn bản, dàn ý, nhận diện hình ảnh và vẽ ảnh minh họa trực tiếp từ Google AI Studio.',
    en: 'Supports text outlines, image captioning, and slide image generation directly from Google AI Studio.',
  },
  textModels: [
    { id: 'gemini-2.0-flash', label: 'gemini-2.0-flash', badgeVi: 'Khuyên dùng', badgeEn: 'Recommended' },
    { id: 'gemini-2.5-flash', label: 'gemini-2.5-flash', badgeVi: 'Thông minh', badgeEn: 'Smart' },
    { id: 'gemini-1.5-flash', label: 'gemini-1.5-flash', badgeVi: 'Ổn định & Nhẹ', badgeEn: 'Fast & Stable' },
    { id: 'gemini-3-flash-preview', label: 'gemini-3-flash-preview', badgeVi: 'Mặc định', badgeEn: 'Default' },
  ],
  imageModels: [
    { id: 'gemini-2.0-flash-preview-image-generation', label: 'gemini-2.0-flash-image', badgeVi: 'Nhanh', badgeEn: 'Fast' },
    { id: 'gemini-3-pro-image-preview', label: 'gemini-3-pro-image-preview', badgeVi: 'Mặc định', badgeEn: 'Default' },
    { id: 'imagen-3.0-generate-002', label: 'imagen-3.0-generate-002', badgeVi: 'Imagen 3', badgeEn: 'Imagen 3' },
  ],
  captionModels: [
    { id: 'gemini-2.0-flash', label: 'gemini-2.0-flash', badgeVi: 'Khuyên dùng', badgeEn: 'Recommended' },
    { id: 'gemini-2.5-flash', label: 'gemini-2.5-flash', badgeVi: 'Thông minh', badgeEn: 'Smart' },
    { id: 'gemini-1.5-flash', label: 'gemini-1.5-flash', badgeVi: 'Ổn định & Nhẹ', badgeEn: 'Fast & Stable' },
    { id: 'gemini-3-flash-preview', label: 'gemini-3-flash-preview', badgeVi: 'Mặc định', badgeEn: 'Default' },
  ],
};

export const SettingsActiveProviderForm: React.FC<SettingsActiveProviderFormProps> = ({
  formData,
  setFormData,
  settings,
  handleFieldChange,
  t,
  isVi,
  serviceTestStates = {},
  triggerTest,
  dismissTest,
  onSave,
  isSaving = false,
}) => {
  const [showApiKey, setShowApiKey] = useState(false);
  const [showBaseUrl, setShowBaseUrl] = useState(Boolean(formData.api_base_url));

  const meta = GOOGLE_GEMINI_METADATA;
  const keyLength = (settings?.api_key_length as number) || 0;
  const currentKeyValue = formData.api_key || '';
  const isKeyConfigured = keyLength > 0 || currentKeyValue.length > 0;

  const handleSelectTextModel = (modelId: string) => {
    setFormData((prev: any) => ({
      ...prev,
      text_model: modelId,
      image_caption_model:
        !prev.image_caption_model || prev.image_caption_model === prev.text_model
          ? modelId
          : prev.image_caption_model,
    }));
  };

  const handleSelectImageModel = (modelId: string) => {
    handleFieldChange('image_model', modelId);
  };

  const handleSelectCaptionModel = (modelId: string) => {
    handleFieldChange('image_caption_model', modelId);
  };

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-3.5 sm:p-5 shadow-sm dark:border-border-primary dark:bg-background-secondary space-y-4 sm:space-y-6">
      {/* 1. Google Gemini Header Card */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 sm:pb-4 border-b border-gray-100 dark:border-border-primary">
        <div className="flex items-center gap-2.5 sm:gap-3">
          <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-lg flex items-center justify-center font-bold text-base bg-gradient-to-tr from-blue-500 via-indigo-500 to-banana-400 text-white shadow-sm shrink-0">
            <Sparkles size={18} className="sm:w-5 sm:h-5" />
          </div>
          <div className="min-w-0">
            <h3 className="text-sm sm:text-base font-semibold text-gray-900 dark:text-foreground-primary">
              {meta.name}
            </h3>
            <p className="text-xs text-gray-500 dark:text-foreground-tertiary mt-0.5 line-clamp-2 sm:line-clamp-none">
              {isVi ? meta.description.vi : meta.description.en}
            </p>
          </div>
        </div>

        {/* Configuration Status Badge */}
        <div className="flex items-center self-start sm:self-center shrink-0">
          {isKeyConfigured ? (
            <span className="inline-flex items-center gap-1.5 px-2.5 sm:px-3 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800">
              <CheckCircle2 size={13} className="text-emerald-500 shrink-0" />
              <span>
                {currentKeyValue
                  ? isVi
                    ? `Đã nhập (${currentKeyValue.length} ký tự)`
                    : `Entered (${currentKeyValue.length} chars)`
                  : isVi
                  ? `Đã lưu (${keyLength} ký tự)`
                  : `Saved (${keyLength} chars)`}
              </span>
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-2.5 sm:px-3 py-1 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800">
              <AlertCircle size={13} className="text-amber-500 shrink-0" />
              <span>{isVi ? 'Chưa có API Key' : 'API Key Not Set'}</span>
            </span>
          )}
        </div>
      </div>

      {/* 2. Google API Key & Base URL */}
      <div className="space-y-3 sm:space-y-4">
        <div>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-1.5">
            <label className="block text-xs sm:text-sm font-semibold text-gray-900 dark:text-foreground-primary">
              {isVi ? 'Nhập API Key' : 'API Key'}
              <span className="ml-1 text-xs font-normal text-gray-500">
                ({meta.name})
              </span>
            </label>
            <a
              href={meta.portalUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 hover:underline self-start sm:self-auto"
            >
              <span>
                {isVi ? `Lấy API Key tại ${meta.portalName}` : `Get API Key at ${meta.portalName}`}
              </span>
              <ExternalLink size={11} />
            </a>
          </div>

          <div className="relative">
            <input
              type={showApiKey ? 'text' : 'password'}
              placeholder={
                keyLength > 0
                  ? isVi
                    ? `Đã lưu key (${keyLength} ký tự) - Nhập key mới để đổi`
                    : `Saved (${keyLength} chars) - Enter new key to change`
                  : 'AIzaSy...'
              }
              value={formData.api_key}
              onChange={(e) => handleFieldChange('api_key', e.target.value)}
              className="w-full h-10 pl-3.5 pr-11 rounded-lg border border-gray-300 dark:border-border-primary bg-white dark:bg-background-secondary focus:outline-none focus:ring-2 focus:ring-banana-500 focus:border-transparent text-gray-900 dark:text-foreground-primary text-xs sm:text-sm placeholder:text-gray-400 dark:placeholder:text-gray-500 transition-all font-mono"
            />
            <button
              type="button"
              onClick={() => setShowApiKey(!showApiKey)}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1 rounded"
              title={showApiKey ? (isVi ? 'Ẩn key' : 'Hide key') : (isVi ? 'Hiện key' : 'Show key')}
            >
              {showApiKey ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>

          {/* Collapsible API Base URL */}
          <div className="mt-2">
            <button
              type="button"
              onClick={() => setShowBaseUrl(!showBaseUrl)}
              className="inline-flex items-center gap-1 text-xs text-gray-500 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200 text-left"
            >
              {showBaseUrl ? <ChevronUp size={13} className="shrink-0" /> : <ChevronDown size={13} className="shrink-0" />}
              <span className="break-all">
                {isVi ? 'Máy chủ API Base URL' : 'API Base URL'}:{' '}
                <code className="font-mono text-gray-700 dark:text-gray-300">
                  {formData.api_base_url || meta.defaultBaseUrl}
                </code>
              </span>
            </button>

            {(showBaseUrl || Boolean(formData.api_base_url)) && (
              <div className="mt-2 p-3 rounded-lg bg-gray-50 dark:bg-background-tertiary border border-gray-200/70 dark:border-border-primary space-y-2">
                <div className="flex items-center justify-between">
                  <label className="block text-xs font-medium text-gray-700 dark:text-foreground-secondary">
                    API Base URL <span className="text-gray-400 font-normal">({isVi ? 'Tùy chọn' : 'Optional'})</span>
                  </label>
                  <button
                    type="button"
                    onClick={() => handleFieldChange('api_base_url', '')}
                    className="inline-flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                  >
                    <RotateCcw size={11} />
                    <span>{isVi ? 'Mặc định' : 'Reset'}</span>
                  </button>
                </div>
                <input
                  type="text"
                  placeholder={meta.defaultBaseUrl}
                  value={formData.api_base_url}
                  onChange={(e) => handleFieldChange('api_base_url', e.target.value)}
                  className="w-full h-9 px-3 rounded-lg border border-gray-200 dark:border-border-primary bg-white dark:bg-background-secondary focus:outline-none focus:ring-2 focus:ring-banana-500 text-gray-900 dark:text-foreground-primary text-xs font-mono"
                />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 4. Google Gemini Model Configuration (Text, Image, Caption) */}
      <div className="pt-4 border-t border-gray-100 dark:border-border-primary space-y-4">
        <div>
          <h4 className="text-sm font-semibold text-gray-900 dark:text-foreground-primary">
            {isVi ? 'Cấu hình Mô hình Google Gemini (Model)' : 'Google Gemini Model Configuration'}
          </h4>
          <p className="text-xs text-gray-500 dark:text-foreground-tertiary">
            {isVi
              ? 'Bấm chọn nhanh mô hình gợi ý bên dưới hoặc tự nhập tên model Google Gemini bất kỳ.'
              : 'Click a recommended model chip below or type any custom Google Gemini model ID.'}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* 4A: Text Model */}
          <div className="p-3.5 rounded-xl border border-gray-200 dark:border-border-primary bg-gray-50/50 dark:bg-background-tertiary/50 space-y-2.5">
            <label className="block text-xs font-semibold text-gray-800 dark:text-foreground-primary flex items-center gap-1.5">
              <FileText size={14} className="text-blue-500" />
              {t('settings.fields.textModel')}
            </label>

            <div className="flex flex-wrap gap-1.5">
              {meta.textModels.map((m) => {
                const isActive = formData.text_model === m.id;
                return (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => handleSelectTextModel(m.id)}
                    className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium transition-all cursor-pointer border ${
                      isActive
                        ? 'bg-blue-600 text-white border-blue-600 shadow-xs'
                        : 'bg-white dark:bg-background-secondary text-gray-700 dark:text-gray-200 border-gray-200 dark:border-border-primary hover:border-blue-400'
                    }`}
                  >
                    <span className="font-mono text-[11px]">{m.label}</span>
                    {(m.badgeVi || m.badgeEn) && (
                      <span
                        className={`text-[10px] px-1 py-0.2 rounded ${
                          isActive
                            ? 'bg-blue-700 text-blue-100'
                            : 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300'
                        }`}
                      >
                        {isVi ? m.badgeVi : m.badgeEn}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>

            <input
              type="text"
              aria-label={t('settings.fields.textModel')}
              placeholder={meta.textModels[0]?.id || t('settings.fields.textModelPlaceholder')}
              value={formData.text_model}
              onChange={(e) => handleSelectTextModel(e.target.value)}
              className="w-full h-9 px-3 rounded-lg border border-gray-200 dark:border-border-primary bg-white dark:bg-background-secondary focus:outline-none focus:ring-2 focus:ring-banana-500 text-xs font-mono text-gray-900 dark:text-foreground-primary"
            />
            <p className="text-xs text-gray-500 dark:text-foreground-tertiary">
              {isVi
                ? 'Dùng để tạo dàn ý, nội dung chi tiết từng trang và tự động thiết kế bố cục.'
                : 'Used for generating outlines, slide descriptions, and layout styles.'}
            </p>
          </div>

          {/* 4B: Image Model */}
          <div className="p-3 sm:p-3.5 rounded-xl border border-gray-200 dark:border-border-primary bg-gray-50/50 dark:bg-background-tertiary/50 space-y-2.5">
            <label className="block text-xs font-semibold text-gray-800 dark:text-foreground-primary flex items-center gap-1.5">
              <ImageIcon size={14} className="text-emerald-500" />
              {t('settings.fields.imageModel')}
            </label>

            <div className="flex flex-wrap gap-1.5">
              {meta.imageModels.map((m) => {
                const isActive = formData.image_model === m.id;
                return (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => handleSelectImageModel(m.id)}
                    className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium transition-all cursor-pointer border ${
                      isActive
                        ? 'bg-emerald-600 text-white border-emerald-600 shadow-xs'
                        : 'bg-white dark:bg-background-secondary text-gray-700 dark:text-gray-200 border-gray-200 dark:border-border-primary hover:border-emerald-400'
                    }`}
                  >
                    <span className="font-mono text-[11px]">{m.label}</span>
                    {(m.badgeVi || m.badgeEn) && (
                      <span
                        className={`text-[10px] px-1 py-0.2 rounded ${
                          isActive
                            ? 'bg-emerald-700 text-emerald-100'
                            : 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300'
                        }`}
                      >
                        {isVi ? m.badgeVi : m.badgeEn}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>

            <input
              type="text"
              aria-label={t('settings.fields.imageModel')}
              placeholder={meta.imageModels[0]?.id || t('settings.fields.imageModelPlaceholder')}
              value={formData.image_model}
              onChange={(e) => handleSelectImageModel(e.target.value)}
              className="w-full h-9 px-3 rounded-lg border border-gray-200 dark:border-border-primary bg-white dark:bg-background-secondary focus:outline-none focus:ring-2 focus:ring-banana-500 text-xs font-mono text-gray-900 dark:text-foreground-primary"
            />
            <p className="text-xs text-gray-500 dark:text-foreground-tertiary">
              {isVi
                ? 'Dùng để vẽ hình ảnh slide hoàn chỉnh bằng Google Gemini / Imagen.'
                : 'Used for rendering slide images via Google Gemini / Imagen.'}
            </p>
          </div>

          {/* 4C: Image Caption Model */}
          <div className="p-3 sm:p-3.5 rounded-xl border border-gray-200 dark:border-border-primary bg-gray-50/50 dark:bg-background-tertiary/50 space-y-2.5">
            <label className="block text-xs font-semibold text-gray-800 dark:text-foreground-primary flex items-center gap-1.5">
              <Eye size={14} className="text-purple-500" />
              {t('settings.fields.imageCaptionModel')}
            </label>

            <div className="flex flex-wrap gap-1.5">
              {meta.captionModels.map((m) => {
                const isActive = formData.image_caption_model === m.id;
                return (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => handleSelectCaptionModel(m.id)}
                    className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium transition-all cursor-pointer border ${
                      isActive
                        ? 'bg-purple-600 text-white border-purple-600 shadow-xs'
                        : 'bg-white dark:bg-background-secondary text-gray-700 dark:text-gray-200 border-gray-200 dark:border-border-primary hover:border-purple-400'
                    }`}
                  >
                    <span className="font-mono text-[11px]">{m.label}</span>
                    {(m.badgeVi || m.badgeEn) && (
                      <span
                        className={`text-[10px] px-1 py-0.2 rounded ${
                          isActive
                            ? 'bg-purple-700 text-purple-100'
                            : 'bg-purple-100 text-purple-800 dark:bg-purple-950/60 dark:text-purple-300'
                        }`}
                      >
                        {isVi ? m.badgeVi : m.badgeEn}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>

            <input
              type="text"
              aria-label={t('settings.fields.imageCaptionModel')}
              placeholder={meta.captionModels[0]?.id || t('settings.fields.imageCaptionModelPlaceholder')}
              value={formData.image_caption_model}
              onChange={(e) => handleSelectCaptionModel(e.target.value)}
              className="w-full h-9 px-3 rounded-lg border border-gray-200 dark:border-border-primary bg-white dark:bg-background-secondary focus:outline-none focus:ring-2 focus:ring-banana-500 text-xs font-mono text-gray-900 dark:text-foreground-primary"
            />
            <p className="text-xs text-gray-500 dark:text-foreground-tertiary">
              {isVi
                ? 'Dùng để nhận diện hình ảnh trong tài liệu tham khảo và kiểm soát chất lượng ảnh.'
                : 'Used for analyzing reference images and image quality control.'}
            </p>
          </div>
        </div>
      </div>

      {/* 5. Quick Save & Test Connection Bar */}
      <div className="pt-4 border-t border-gray-100 dark:border-border-primary flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
          {triggerTest && (
            <>
              <SettingsInlineServiceTest
                testKey="text-model"
                label={isVi ? 'Test Văn bản' : 'Test Text'}
                icon={<Zap size={13} className="text-amber-500" />}
                testState={serviceTestStates['text-model']}
                onTest={() => triggerTest('text-model')}
                onDismiss={dismissTest ? () => dismissTest('text-model') : undefined}
                isVi={isVi}
                disabled={!isKeyConfigured}
                disabledReason={isVi ? 'Chưa nhập API Key' : 'Key not set'}
              />

              <SettingsInlineServiceTest
                testKey="image-model"
                label={isVi ? 'Test Tạo ảnh' : 'Test Image'}
                icon={<Sparkles size={13} className="text-purple-500" />}
                testState={serviceTestStates['image-model']}
                onTest={() => triggerTest('image-model')}
                onDismiss={dismissTest ? () => dismissTest('image-model') : undefined}
                isVi={isVi}
                disabled={!isKeyConfigured}
                disabledReason={isVi ? 'Chưa nhập API Key' : 'Key not set'}
              />

              <SettingsInlineServiceTest
                testKey="caption-model"
                label={isVi ? 'Test Nhận diện ảnh' : 'Test Vision'}
                icon={<Eye size={13} className="text-blue-500" />}
                testState={serviceTestStates['caption-model']}
                onTest={() => triggerTest('caption-model')}
                onDismiss={dismissTest ? () => dismissTest('caption-model') : undefined}
                isVi={isVi}
                disabled={!isKeyConfigured}
                disabledReason={isVi ? 'Chưa nhập API Key' : 'Key not set'}
              />
            </>
          )}
        </div>

        {onSave && (
          <Button
            variant="primary"
            size="sm"
            icon={<Save size={15} />}
            onClick={onSave}
            loading={isSaving}
            className="w-full sm:w-auto justify-center"
          >
            {isSaving
              ? isVi
                ? 'Đang lưu...'
                : 'Saving...'
              : isVi
              ? 'Lưu cấu hình ngay'
              : 'Save Configuration'}
          </Button>
        )}
      </div>
    </div>
  );
};
