import React, { useRef, useState } from 'react';
import {
  Sparkles,
  Server,
  ExternalLink,
  Eye,
  EyeOff,
  RotateCcw,
  Zap,
  FileText,
  Image as ImageIcon,
  ChevronDown,
  ChevronUp,
  RefreshCw,
} from 'lucide-react';
import { SettingsInlineServiceTest, type InlineServiceTestState } from './SettingsInlineServiceTest';
import * as api from '@/api/endpoints';
import { normalizeProviderFormat } from '@/utils/clientKeyStorage';
import type { Settings as SettingsType } from '@/types';
import type { useT } from '@/hooks/useT';

export interface SettingsActiveProviderFormProps {
  formData: {
    ai_provider_format?: string;
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
}

interface ModelPresetOption {
  id: string;
  label: string;
  badgeVi?: string;
  badgeEn?: string;
}

interface ProviderDraft {
  api_base_url: string;
  api_key: string;
  text_model: string;
  image_model: string;
  image_caption_model: string;
}

const LOCAL_ENDPOINT_PRESETS: Array<{ label: string; url: string }> = [
  { label: 'Ollama', url: 'http://localhost:11434/v1' },
  { label: 'LM Studio', url: 'http://localhost:1234/v1' },
  { label: 'vLLM', url: 'http://localhost:8000/v1' },
  { label: 'llama.cpp', url: 'http://localhost:8080/v1' },
  { label: 'LocalAI', url: 'http://localhost:8080/v1' },
];

const GOOGLE_GEMINI_METADATA: {
  name: string;
  portalName: string;
  portalUrl: string;
  defaultBaseUrl: string;
  textModels: ModelPresetOption[];
  imageModels: ModelPresetOption[];
  captionModels: ModelPresetOption[];
} = {
  name: 'Google Gemini',
  portalName: 'Google AI Studio',
  portalUrl: 'https://aistudio.google.com/app/apikey',
  defaultBaseUrl: 'https://generativelanguage.googleapis.com',
  textModels: [
    { id: 'gemini-3.5-flash-lite', label: 'gemini-3.5-flash-lite', badgeVi: 'Mặc định', badgeEn: 'Default' },
  ],
  imageModels: [
    { id: 'gemini-3.1-flash-lite-image', label: 'gemini-3.1-flash-lite-image', badgeVi: 'Mặc định', badgeEn: 'Default' },
  ],
  captionModels: [
    { id: 'gemini-3.5-flash-lite', label: 'gemini-3.5-flash-lite', badgeVi: 'Mặc định', badgeEn: 'Default' },
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
}) => {
  const [showApiKey, setShowApiKey] = useState(false);
  const [showBaseUrl, setShowBaseUrl] = useState(Boolean(formData.api_base_url));
  const [discoveredModels, setDiscoveredModels] = useState<string[]>([]);
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [discoverStatus, setDiscoverStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const draftCacheRef = useRef<Record<string, ProviderDraft>>({});

  const activeProvider = normalizeProviderFormat(formData.ai_provider_format);
  const isSelfHosted = activeProvider === 'openai';
  const meta = GOOGLE_GEMINI_METADATA;

  const savedMatchesActive = normalizeProviderFormat(settings?.ai_provider_format) === activeProvider;
  const keyLength = savedMatchesActive ? ((settings?.api_key_length as number) || 0) : 0;
  const currentKeyValue = formData.api_key || '';
  const isKeyConfigured = keyLength > 0 || currentKeyValue.trim().length > 0;
  const isEndpointReady = isSelfHosted
    ? Boolean(formData.api_base_url?.trim()) || isKeyConfigured
    : isKeyConfigured;

  const handleSwitchProvider = (nextProvider: 'gemini' | 'openai') => {
    if (nextProvider === activeProvider) return;
    draftCacheRef.current[activeProvider] = {
      api_base_url: formData.api_base_url || '',
      api_key: formData.api_key || '',
      text_model: formData.text_model || '',
      image_model: formData.image_model || '',
      image_caption_model: formData.image_caption_model || '',
    };

    const cached = draftCacheRef.current[nextProvider];
    const nextDraft: ProviderDraft =
      cached ||
      (nextProvider === 'openai'
        ? {
            api_base_url: '',
            api_key: '',
            text_model: '',
            image_model: '',
            image_caption_model: '',
          }
        : {
            api_base_url: '',
            api_key: '',
            text_model: 'gemini-3.5-flash-lite',
            image_model: 'gemini-3.1-flash-lite-image',
            image_caption_model: 'gemini-3.5-flash-lite',
          });

    setDiscoverStatus(null);
    setFormData((prev: any) => ({
      ...prev,
      ai_provider_format: nextProvider,
      ...nextDraft,
    }));
  };

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

  const handleDiscoverModels = async () => {
    setIsDiscovering(true);
    setDiscoverStatus(null);
    try {
      const response = await api.discoverLocalModels({
        api_base_url: formData.api_base_url || '',
        api_key: formData.api_key || undefined,
      });
      const data = response.data;
      const models = data?.models || [];
      setDiscoveredModels(models);

      if (models.length > 0 && !formData.text_model?.trim()) {
        handleSelectTextModel(models[0]);
      }

      if (models.length > 0) {
        setDiscoverStatus({
          type: 'success',
          message: isVi
            ? `Tìm thấy ${models.length} model tại ${data.effective_base_url}`
            : `Found ${models.length} models at ${data.effective_base_url}`,
        });
      } else {
        setDiscoverStatus({
          type: 'error',
          message: isVi
            ? 'Kết nối thành công nhưng server chưa trả về model nào.'
            : 'Connected cleanly, but server returned no models.',
        });
      }
    } catch (error: any) {
      const message =
        error?.response?.data?.error?.message ||
        error?.message ||
        (isVi ? 'Không thể lấy danh sách model' : 'Failed to fetch models');
      setDiscoverStatus({ type: 'error', message });
    } finally {
      setIsDiscovering(false);
    }
  };

  const renderModelChip = (
    modelId: string,
    label: string,
    isActive: boolean,
    onClick: () => void,
    activeClass: string,
    hoverClass: string,
    badge?: string,
    badgeClass?: string
  ) => (
    <button
      key={modelId}
      type="button"
      onClick={onClick}
      className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium transition-all cursor-pointer border ${
        isActive
          ? `${activeClass} text-white shadow-xs`
          : `bg-white dark:bg-background-secondary text-gray-700 dark:text-gray-200 border-gray-200 dark:border-border-primary ${hoverClass}`
      }`}
    >
      <span className="font-mono text-[11px]">{label}</span>
      {badge && (
        <span className={`text-[10px] px-1 py-0.2 rounded ${badgeClass || ''}`}>
          {badge}
        </span>
      )}
    </button>
  );

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-3.5 sm:p-5 shadow-sm dark:border-border-primary dark:bg-background-secondary space-y-4 sm:space-y-6">
      {/* 1. Provider Header & Minimalist Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 sm:pb-4 border-b border-gray-100 dark:border-border-primary">
        <div className="flex items-center gap-2.5 sm:gap-3">
          <div
            className={`w-9 h-9 sm:w-10 sm:h-10 rounded-lg flex items-center justify-center font-bold text-base text-white shadow-sm shrink-0 ${
              isSelfHosted
                ? 'bg-gradient-to-tr from-slate-700 via-emerald-600 to-teal-500'
                : 'bg-gradient-to-tr from-blue-500 via-indigo-500 to-banana-400'
            }`}
          >
            {isSelfHosted ? (
              <Server size={18} className="sm:w-5 sm:h-5" />
            ) : (
              <Sparkles size={18} className="sm:w-5 sm:h-5" />
            )}
          </div>
          <div className="min-w-0">
            <h3 className="text-sm sm:text-base font-semibold text-gray-900 dark:text-foreground-primary">
              {isSelfHosted
                ? isVi
                  ? 'Self-Hosted / Local LLM'
                  : 'Self-Hosted / Local LLM'
                : meta.name}
            </h3>
            <p className="text-xs text-gray-500 dark:text-foreground-tertiary truncate">
              {isSelfHosted
                ? isVi
                  ? 'Tương thích OpenAI /v1 (Ollama, LM Studio, vLLM, llama.cpp...)'
                  : 'OpenAI-compatible /v1 (Ollama, LM Studio, vLLM, llama.cpp...)'
                : isVi
                ? 'Google AI Studio / Gemini API'
                : 'Google AI Studio / Gemini API'}
            </p>
          </div>
        </div>

        {/* Minimalist 2-tab provider toggle */}
        <div
          role="tablist"
          aria-label="AI Provider"
          className="inline-flex p-1 rounded-lg bg-gray-100 dark:bg-background-tertiary border border-gray-200 dark:border-border-primary self-start sm:self-auto"
        >
          <button
            type="button"
            role="tab"
            aria-selected={!isSelfHosted}
            onClick={() => handleSwitchProvider('gemini')}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all cursor-pointer ${
              !isSelfHosted
                ? 'bg-white dark:bg-background-secondary text-gray-900 dark:text-foreground-primary shadow-xs'
                : 'text-gray-600 dark:text-foreground-tertiary hover:text-gray-900 dark:hover:text-foreground-primary'
            }`}
          >
            <Sparkles size={13} className={!isSelfHosted ? 'text-indigo-500' : ''} />
            <span>Google Gemini</span>
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={isSelfHosted}
            onClick={() => handleSwitchProvider('openai')}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all cursor-pointer ${
              isSelfHosted
                ? 'bg-white dark:bg-background-secondary text-gray-900 dark:text-foreground-primary shadow-xs'
                : 'text-gray-600 dark:text-foreground-tertiary hover:text-gray-900 dark:hover:text-foreground-primary'
            }`}
          >
            <Server size={13} className={isSelfHosted ? 'text-emerald-600' : ''} />
            <span>{isVi ? 'Self-Hosted / Local' : 'Self-Hosted / Local'}</span>
          </button>
        </div>
      </div>

      {/* 2. Provider Endpoint & Credentials */}
      {isSelfHosted ? (
        <div className="space-y-3.5">
          {/* 1-click presets */}
          <div className="space-y-1.5">
            <span className="block text-xs font-semibold text-gray-700 dark:text-foreground-secondary">
              {isVi ? 'Chọn nhanh máy chủ local' : 'Quick Local Presets'}
            </span>
            <div className="flex flex-wrap gap-1.5">
              {LOCAL_ENDPOINT_PRESETS.map((preset) => {
                const isSelected = (formData.api_base_url || '').trim() === preset.url;
                return (
                  <button
                    key={preset.label}
                    type="button"
                    onClick={() => {
                      handleFieldChange('api_base_url', preset.url);
                      setDiscoverStatus(null);
                    }}
                    className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-all cursor-pointer border ${
                      isSelected
                        ? 'bg-emerald-600 text-white border-emerald-600 shadow-xs'
                        : 'bg-gray-50 dark:bg-background-tertiary text-gray-700 dark:text-gray-200 border-gray-200 dark:border-border-primary hover:border-emerald-400'
                    }`}
                  >
                    <span>{preset.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Endpoint Base URL + Fetch Models */}
          <div>
            <label className="block text-xs sm:text-sm font-semibold text-gray-900 dark:text-foreground-primary mb-1.5">
              {isVi ? 'Server Endpoint URL' : 'Server Endpoint URL'}
              <span className="ml-1 text-xs font-normal text-gray-500">(/v1)</span>
            </label>
            <div className="flex flex-col sm:flex-row gap-2">
              <input
                type="text"
                aria-label="Server Endpoint URL"
                placeholder="http://localhost:11434/v1"
                value={formData.api_base_url}
                onChange={(e) => {
                  handleFieldChange('api_base_url', e.target.value);
                  if (discoverStatus) setDiscoverStatus(null);
                }}
                className="flex-1 h-10 px-3.5 rounded-lg border border-gray-300 dark:border-border-primary bg-white dark:bg-background-secondary focus:outline-none focus:ring-2 focus:ring-banana-500 focus:border-transparent text-gray-900 dark:text-foreground-primary text-xs sm:text-sm placeholder:text-gray-400 dark:placeholder:text-gray-500 transition-all font-mono"
              />
              <button
                type="button"
                onClick={handleDiscoverModels}
                disabled={isDiscovering || (!formData.api_base_url?.trim() && !savedMatchesActive)}
                className="h-10 px-3.5 rounded-lg border border-gray-300 dark:border-border-primary bg-gray-50 hover:bg-gray-100 dark:bg-background-tertiary dark:hover:bg-background-secondary text-xs font-medium text-gray-800 dark:text-foreground-primary inline-flex items-center justify-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer shrink-0 transition-colors"
              >
                <RefreshCw size={13} className={isDiscovering ? 'animate-spin' : ''} />
                <span>
                  {isDiscovering
                    ? isVi
                      ? 'Đang tải...'
                      : 'Fetching...'
                    : isVi
                    ? 'Tải model'
                    : 'Fetch models'}
                </span>
              </button>
            </div>

            {discoverStatus && (
              <p
                className={`mt-1.5 text-xs ${
                  discoverStatus.type === 'success'
                    ? 'text-emerald-600 dark:text-emerald-400'
                    : 'text-red-600 dark:text-red-400'
                }`}
              >
                {discoverStatus.message}
              </p>
            )}

            <p className="mt-1.5 text-xs text-gray-500 dark:text-foreground-tertiary">
              {isVi
                ? 'Hỗ trợ mọi server chuẩn OpenAI /v1. Khi chạy Docker, localhost sẽ tự ánh xạ sang host.docker.internal.'
                : 'Supports any OpenAI-compatible /v1 server. Inside Docker, localhost automatically maps to host.docker.internal.'}
            </p>
          </div>

          {/* Optional API Key */}
          <div>
            <label className="block text-xs sm:text-sm font-semibold text-gray-900 dark:text-foreground-primary mb-1.5">
              API Key{' '}
              <span className="text-xs font-normal text-gray-500">
                ({isVi ? 'Tùy chọn' : 'Optional'})
              </span>
            </label>
            <div className="relative">
              <input
                type={showApiKey ? 'text' : 'password'}
                placeholder={
                  keyLength > 0
                    ? isVi
                      ? 'Đã lưu key - Nhập key mới để đổi'
                      : 'Saved key - Enter new key to change'
                    : isVi
                    ? 'Để trống nếu server local không yêu cầu (Ollama, LM Studio, llama.cpp...)'
                    : 'Leave blank for keyless local servers (Ollama, LM Studio, llama.cpp...)'
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
          </div>
        </div>
      ) : (
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
                      ? 'Đã lưu key - Nhập key mới để đổi'
                      : 'Saved key - Enter new key to change'
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
      )}

      {/* 4. Model Configuration (Text, Image, Caption) */}
      <div className="pt-4 border-t border-gray-100 dark:border-border-primary space-y-4">
        <div>
          <h4 className="text-sm font-semibold text-gray-900 dark:text-foreground-primary">
            {isSelfHosted
              ? isVi
                ? 'Cấu hình Mô hình Self-Hosted (Model)'
                : 'Self-Hosted Model Configuration'
              : isVi
              ? 'Cấu hình Mô hình Google Gemini (Model)'
              : 'Google Gemini Model Configuration'}
          </h4>
          <p className="text-xs text-gray-500 dark:text-foreground-tertiary">
            {isSelfHosted
              ? isVi
                ? 'Nhấn "Tải model" ở trên để chọn nhanh từ server hoặc tự nhập tên model (ví dụ qwen2.5:14b, llama3.3).'
                : 'Click "Fetch models" above to pick from your server or enter any model ID manually (e.g. qwen2.5:14b, llama3.3).'
              : isVi
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

            {isSelfHosted ? (
              discoveredModels.length > 0 && (
                <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto">
                  {discoveredModels.slice(0, 12).map((modelId) =>
                    renderModelChip(
                      modelId,
                      modelId,
                      formData.text_model === modelId,
                      () => handleSelectTextModel(modelId),
                      'bg-blue-600 border-blue-600',
                      'hover:border-blue-400'
                    )
                  )}
                </div>
              )
            ) : (
              <div className="flex flex-wrap gap-1.5">
                {meta.textModels.map((m) =>
                  renderModelChip(
                    m.id,
                    m.label,
                    formData.text_model === m.id,
                    () => handleSelectTextModel(m.id),
                    'bg-blue-600 border-blue-600',
                    'hover:border-blue-400',
                    isVi ? m.badgeVi : m.badgeEn,
                    formData.text_model === m.id
                      ? 'bg-blue-700 text-blue-100'
                      : 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300'
                  )
                )}
              </div>
            )}

            <input
              type="text"
              aria-label={t('settings.fields.textModel')}
              placeholder={
                isSelfHosted
                  ? 'qwen2.5:14b, llama3.3, deepseek-r1...'
                  : meta.textModels[0]?.id || t('settings.fields.textModelPlaceholder')
              }
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
              {isSelfHosted && (
                <span className="text-[11px] font-normal text-gray-400">
                  ({isVi ? 'Tùy chọn' : 'Optional'})
                </span>
              )}
            </label>

            {!isSelfHosted && (
              <div className="flex flex-wrap gap-1.5">
                {meta.imageModels.map((m) =>
                  renderModelChip(
                    m.id,
                    m.label,
                    formData.image_model === m.id,
                    () => handleSelectImageModel(m.id),
                    'bg-emerald-600 border-emerald-600',
                    'hover:border-emerald-400',
                    isVi ? m.badgeVi : m.badgeEn,
                    formData.image_model === m.id
                      ? 'bg-emerald-700 text-emerald-100'
                      : 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300'
                  )
                )}
              </div>
            )}

            <input
              type="text"
              aria-label={t('settings.fields.imageModel')}
              placeholder={
                isSelfHosted
                  ? isVi
                    ? 'Tùy chọn (flux, sdxl, dall-e-3...)'
                    : 'Optional (flux, sdxl, dall-e-3...)'
                  : meta.imageModels[0]?.id || t('settings.fields.imageModelPlaceholder')
              }
              value={formData.image_model}
              onChange={(e) => handleSelectImageModel(e.target.value)}
              className="w-full h-9 px-3 rounded-lg border border-gray-200 dark:border-border-primary bg-white dark:bg-background-secondary focus:outline-none focus:ring-2 focus:ring-banana-500 text-xs font-mono text-gray-900 dark:text-foreground-primary"
            />
            <p className="text-xs text-gray-500 dark:text-foreground-tertiary">
              {isSelfHosted
                ? isVi
                  ? 'Chỉ cần khi muốn vẽ ảnh AI (/images/generations). Tạo dàn ý và HTML slide vẫn chạy không cần mục này.'
                  : 'Only needed for AI image rendering (/images/generations). Outlines and HTML slide workflows work without it.'
                : isVi
                ? 'Dùng để vẽ hình ảnh slide hoàn chỉnh bằng Google Gemini / Imagen.'
                : 'Used for rendering slide images via Google Gemini / Imagen.'}
            </p>
          </div>

          {/* 4C: Image Caption Model */}
          <div className="p-3 sm:p-3.5 rounded-xl border border-gray-200 dark:border-border-primary bg-gray-50/50 dark:bg-background-tertiary/50 space-y-2.5">
            <label className="block text-xs font-semibold text-gray-800 dark:text-foreground-primary flex items-center gap-1.5">
              <Eye size={14} className="text-purple-500" />
              {t('settings.fields.imageCaptionModel')}
              {isSelfHosted && (
                <span className="text-[11px] font-normal text-gray-400">
                  ({isVi ? 'Tùy chọn' : 'Optional'})
                </span>
              )}
            </label>

            {isSelfHosted ? (
              discoveredModels.length > 0 && (
                <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto">
                  {discoveredModels.slice(0, 12).map((modelId) =>
                    renderModelChip(
                      modelId,
                      modelId,
                      formData.image_caption_model === modelId,
                      () => handleSelectCaptionModel(modelId),
                      'bg-purple-600 border-purple-600',
                      'hover:border-purple-400'
                    )
                  )}
                </div>
              )
            ) : (
              <div className="flex flex-wrap gap-1.5">
                {meta.captionModels.map((m) =>
                  renderModelChip(
                    m.id,
                    m.label,
                    formData.image_caption_model === m.id,
                    () => handleSelectCaptionModel(m.id),
                    'bg-purple-600 border-purple-600',
                    'hover:border-purple-400',
                    isVi ? m.badgeVi : m.badgeEn,
                    formData.image_caption_model === m.id
                      ? 'bg-purple-700 text-purple-100'
                      : 'bg-purple-100 text-purple-800 dark:bg-purple-950/60 dark:text-purple-300'
                  )
                )}
              </div>
            )}

            <input
              type="text"
              aria-label={t('settings.fields.imageCaptionModel')}
              placeholder={
                isSelfHosted
                  ? isVi
                    ? 'Mặc định dùng Text Model'
                    : 'Defaults to Text Model'
                  : meta.captionModels[0]?.id || t('settings.fields.imageCaptionModelPlaceholder')
              }
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
                disabled={!isEndpointReady || (isSelfHosted && !formData.text_model?.trim())}
                disabledReason={
                  !isEndpointReady
                    ? isSelfHosted
                      ? isVi
                        ? 'Chưa nhập Base URL'
                        : 'Endpoint not set'
                      : isVi
                      ? 'Chưa nhập API Key'
                      : 'Key not set'
                    : isVi
                    ? 'Chưa nhập Text Model'
                    : 'Text Model not set'
                }
              />

              <SettingsInlineServiceTest
                testKey="image-model"
                label={isVi ? 'Test Tạo ảnh' : 'Test Image'}
                icon={<Sparkles size={13} className="text-purple-500" />}
                testState={serviceTestStates['image-model']}
                onTest={() => triggerTest('image-model')}
                onDismiss={dismissTest ? () => dismissTest('image-model') : undefined}
                isVi={isVi}
                disabled={!isEndpointReady || (isSelfHosted && !formData.image_model?.trim())}
                disabledReason={
                  !isEndpointReady
                    ? isSelfHosted
                      ? isVi
                        ? 'Chưa nhập Base URL'
                        : 'Endpoint not set'
                      : isVi
                      ? 'Chưa nhập API Key'
                      : 'Key not set'
                    : isVi
                    ? 'Chưa nhập Image Model'
                    : 'Image Model not set'
                }
              />

              <SettingsInlineServiceTest
                testKey="caption-model"
                label={isVi ? 'Test Nhận diện ảnh' : 'Test Vision'}
                icon={<Eye size={13} className="text-blue-500" />}
                testState={serviceTestStates['caption-model']}
                onTest={() => triggerTest('caption-model')}
                onDismiss={dismissTest ? () => dismissTest('caption-model') : undefined}
                isVi={isVi}
                disabled={
                  !isEndpointReady ||
                  (isSelfHosted && !formData.image_caption_model?.trim() && !formData.text_model?.trim())
                }
                disabledReason={
                  !isEndpointReady
                    ? isSelfHosted
                      ? isVi
                        ? 'Chưa nhập Base URL'
                        : 'Endpoint not set'
                      : isVi
                      ? 'Chưa nhập API Key'
                      : 'Key not set'
                    : isVi
                    ? 'Chưa nhập Vision/Text Model'
                    : 'Vision/Text Model not set'
                }
              />
            </>
          )}
        </div>
      </div>
    </div>
  );
};
