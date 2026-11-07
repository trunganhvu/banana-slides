import React, { useState } from 'react';
import {
  Key,
  Sparkles,
  ExternalLink,
  Eye,
  EyeOff,
  CheckCircle2,
  AlertCircle,
  RotateCcw,
  Link2,
  Zap,
  HelpCircle,
  Copy,
  Check,
} from 'lucide-react';
import { Button, Input } from '@/components/shared';
import { SettingsInlineServiceTest, type InlineServiceTestState } from './SettingsInlineServiceTest';
import type { Settings as SettingsType } from '@/types';
import type { useT } from '@/hooks/useT';

export interface SettingsActiveProviderFormProps {
  provider: string;
  formData: {
    ai_provider_format: string;
    api_base_url: string;
    api_key: string;
    lazyllm_api_keys: Record<string, string>;
    [key: string]: any;
  };
  setFormData: React.Dispatch<React.SetStateAction<any>>;
  settings: SettingsType | null;
  handleFieldChange: (key: string, value: any) => void;
  t: ReturnType<typeof useT>;
  isVi: boolean;
  oauthConnecting: boolean;
  handleOAuthLogin: () => void;
  handleOAuthDisconnect: () => void;
  manualCallbackOpen: boolean;
  setManualCallbackOpen: React.Dispatch<React.SetStateAction<boolean>>;
  manualCallbackUrl: string;
  setManualCallbackUrl: React.Dispatch<React.SetStateAction<string>>;
  manualCallbackSubmitting: boolean;
  handleManualCallback: () => void;
  applyVolcengineRecommendedModels: () => void;
  volcengineAgentPlansUrl: string;
  volcengineLogoUrl: string;
  copyToClipboard: (text: string) => void;
  serviceTestStates?: Record<string, InlineServiceTestState>;
  triggerTest?: (testKey: string) => void;
  dismissTest?: (testKey: string) => void;
}

const PROVIDER_METADATA: Record<
  string,
  {
    name: string;
    portalName: string;
    portalUrl: string;
    defaultBaseUrl?: string;
    isApiKeyProvider: boolean;
    isOAuth?: boolean;
    description: { vi: string; en: string };
    highlight?: { vi: string; en: string };
  }
> = {
  gemini: {
    name: 'Google Gemini',
    portalName: 'Google AI Studio',
    portalUrl: 'https://aistudio.google.com/app/apikey',
    defaultBaseUrl: 'https://generativelanguage.googleapis.com',
    isApiKeyProvider: true,
    description: {
      vi: 'Khuyên dùng để bắt đầu. Hỗ trợ đầy đủ văn bản và hình ảnh, miễn phí từ Google AI Studio.',
      en: 'Recommended to get started. Supports both text and image generation, free from Google AI Studio.',
    },
    highlight: {
      vi: 'Google Gemini là giải pháp toàn diện: Tự động tạo dàn ý, soạn nội dung trang và vẽ tranh minh họa trực tiếp mà không cần cấu hình thêm bất kỳ dịch vụ hay API phụ nào.',
      en: 'Google Gemini provides complete coverage: Automatically creates outlines, drafts content, and generates illustrations directly without any extra services.',
    },
  },
  openai: {
    name: 'OpenAI',
    portalName: 'OpenAI Platform',
    portalUrl: 'https://platform.openai.com/api-keys',
    defaultBaseUrl: 'https://api.openai.com/v1',
    isApiKeyProvider: true,
    description: {
      vi: 'Sử dụng GPT-4o, GPT-4o-mini và tạo hình ảnh DALL-E 3 / GPT Image qua OpenAI API.',
      en: 'Uses GPT-4o, GPT-4o-mini, and DALL-E 3 / GPT Image generation via OpenAI API.',
    },
  },
  volcengine: {
    name: 'Volcengine Agent Plan',
    portalName: 'Volcengine Console',
    portalUrl: 'https://ai.volcengine.com/console/apikey',
    defaultBaseUrl: 'https://ark.cn-beijing.volces.com/api/plan/v3',
    isApiKeyProvider: true,
    description: {
      vi: 'Gói Volcengine Agent Plan kết nối trực tiếp, tối ưu chi phí và hỗ trợ mô hình Doubao.',
      en: 'Volcengine Agent Plan offers direct connection, cost optimization, and Doubao models.',
    },
  },
  doubao: {
    name: 'Doubao / ModelArk',
    portalName: 'ModelArk Console',
    portalUrl: 'https://console.volcengine.com/ark/',
    defaultBaseUrl: 'https://ark.cn-beijing.volces.com/api/v3',
    isApiKeyProvider: true,
    description: {
      vi: 'Mô hình Doubao qua nền tảng ByteDance ModelArk.',
      en: 'Doubao models via ByteDance ModelArk platform.',
    },
  },
  codex: {
    name: 'OpenAI Codex (OAuth)',
    portalName: 'OpenAI',
    portalUrl: 'https://chatgpt.com',
    isApiKeyProvider: false,
    isOAuth: true,
    description: {
      vi: 'Đăng nhập tài khoản ChatGPT/OpenAI qua OAuth. Không cần nhập API Key thủ công.',
      en: 'Sign in to your ChatGPT/OpenAI account via OAuth. No manual API key required.',
    },
  },
  deepseek: {
    name: 'DeepSeek',
    portalName: 'DeepSeek Open Platform',
    portalUrl: 'https://platform.deepseek.com/api_keys',
    isApiKeyProvider: false,
    description: {
      vi: 'Mô hình DeepSeek V3 và R1 tối ưu hóa chi phí và năng lực suy luận sâu.',
      en: 'DeepSeek V3 and R1 models optimized for cost and deep reasoning.',
    },
  },
  qwen: {
    name: 'Qwen (Tongyi Qianwen)',
    portalName: 'Alibaba Cloud DashScope',
    portalUrl: 'https://dashscope.console.aliyun.com/',
    isApiKeyProvider: false,
    description: {
      vi: 'Mô hình Tongyi Qianwen qua nền tảng DashScope của Alibaba Cloud.',
      en: 'Tongyi Qianwen models via Alibaba Cloud DashScope platform.',
    },
  },
  glm: {
    name: 'GLM (Zhipu AI)',
    portalName: 'Zhipu AI BigModel',
    portalUrl: 'https://open.bigmodel.cn/usercenter/apikeys',
    isApiKeyProvider: false,
    description: {
      vi: 'Mô hình GLM qua nền tảng Zhipu AI BigModel.',
      en: 'GLM models via Zhipu AI BigModel platform.',
    },
  },
  siliconflow: {
    name: 'SiliconFlow',
    portalName: 'SiliconFlow Cloud',
    portalUrl: 'https://cloud.siliconflow.cn/account/ak',
    isApiKeyProvider: false,
    description: {
      vi: 'Nền tảng SiliconFlow tổng hợp các mô hình mã nguồn mở hiệu năng cao.',
      en: 'SiliconFlow platform aggregating high-performance open-source models.',
    },
  },
  kimi: {
    name: 'Kimi (Moonshot)',
    portalName: 'Moonshot AI Console',
    portalUrl: 'https://platform.moonshot.cn/console/api-keys',
    isApiKeyProvider: false,
    description: {
      vi: 'Mô hình Moonshot Kimi với khả năng xử lý ngữ cảnh dài.',
      en: 'Moonshot Kimi models with long-context capabilities.',
    },
  },
  minimax: {
    name: 'MiniMax',
    portalName: 'MiniMax Open Platform',
    portalUrl: 'https://platform.minimaxi.com/user-center/basic-information/interface-key',
    isApiKeyProvider: false,
    description: {
      vi: 'Mô hình ngôn ngữ lớn và đa phương tiện từ MiniMax.',
      en: 'Large language and multimodal models from MiniMax.',
    },
  },
  sensenova: {
    name: 'SenseNova (SenseTime)',
    portalName: 'SenseNova Open Platform',
    portalUrl: 'https://platform.sensenova.cn/',
    isApiKeyProvider: false,
    description: {
      vi: 'Mô hình Nhật Nhật Tân SenseNova từ SenseTime.',
      en: 'SenseNova models from SenseTime.',
    },
  },
};

export const SettingsActiveProviderForm: React.FC<SettingsActiveProviderFormProps> = ({
  provider,
  formData,
  setFormData,
  settings,
  handleFieldChange,
  t,
  isVi,
  oauthConnecting,
  handleOAuthLogin,
  handleOAuthDisconnect,
  manualCallbackOpen,
  setManualCallbackOpen,
  manualCallbackUrl,
  setManualCallbackUrl,
  manualCallbackSubmitting,
  handleManualCallback,
  applyVolcengineRecommendedModels,
  volcengineAgentPlansUrl,
  volcengineLogoUrl,
  copyToClipboard,
  serviceTestStates = {},
  triggerTest,
  dismissTest,
}) => {
  const [showApiKey, setShowApiKey] = useState(false);
  const [copiedLink, setCopiedLink] = useState(false);

  const meta = PROVIDER_METADATA[provider] || {
    name: provider.toUpperCase(),
    portalName: `${provider} Console`,
    portalUrl: '',
    isApiKeyProvider: false,
    description: { vi: `Nhà cung cấp ${provider}`, en: `${provider} provider` },
  };

  const isGemini = provider === 'gemini';
  const isOpenAi = provider === 'openai';
  const isVolcengine = provider === 'volcengine';
  const isDoubao = provider === 'doubao';
  const isCodex = provider === 'codex';
  const isDirectKeyProvider = meta.isApiKeyProvider;

  // Determine key status
  let isKeyConfigured = false;
  let keyLength = 0;
  let currentKeyValue = '';

  if (isDirectKeyProvider) {
    keyLength = (settings?.api_key_length as number) || 0;
    currentKeyValue = formData.api_key;
    isKeyConfigured = keyLength > 0 || currentKeyValue.length > 0;
  } else if (isCodex) {
    isKeyConfigured = Boolean(settings?.openai_oauth_connected);
  } else {
    keyLength = (settings?.lazyllm_api_keys_info?.[provider] as number) || 0;
    currentKeyValue = formData.lazyllm_api_keys[provider] || '';
    isKeyConfigured = keyLength > 0 || currentKeyValue.length > 0;
  }

  const handleCopyLink = (url: string) => {
    copyToClipboard(url);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  };

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-border-primary dark:bg-background-secondary space-y-5">
      {/* Provider Header Card */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-gray-100 dark:border-border-primary">
        <div className="flex items-center gap-3">
          <div
            className={`w-10 h-10 rounded-lg flex items-center justify-center font-bold text-base ${
              isGemini
                ? 'bg-gradient-to-tr from-blue-500 via-indigo-500 to-banana-400 text-white shadow-sm'
                : isOpenAi
                ? 'bg-emerald-600 text-white'
                : isCodex
                ? 'bg-purple-600 text-white'
                : isVolcengine || isDoubao
                ? 'bg-red-500 text-white'
                : 'bg-banana-500 text-gray-900'
            }`}
          >
            {isGemini ? (
              <Sparkles size={20} />
            ) : isCodex ? (
              <Link2 size={20} />
            ) : isVolcengine || isDoubao ? (
              <Zap size={20} />
            ) : (
              <Key size={20} />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-semibold text-gray-900 dark:text-foreground-primary">
                {meta.name}
              </h3>
              {isGemini && (
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-banana-100 text-banana-900 border border-banana-300 dark:bg-banana-950/60 dark:text-banana-300 dark:border-banana-700">
                  {isVi ? 'Khuyên dùng' : 'Recommended'}
                </span>
              )}
              {isCodex && (
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-950/50 dark:text-purple-300">
                  OAuth
                </span>
              )}
            </div>
            <p className="text-xs text-gray-500 dark:text-foreground-tertiary mt-0.5">
              {isVi ? meta.description.vi : meta.description.en}
            </p>
          </div>
        </div>

        {/* Configuration Status Badge */}
        <div className="flex items-center self-start sm:self-center">
          {isCodex ? (
            settings?.openai_oauth_connected ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800">
                <CheckCircle2 size={13} className="text-emerald-500" />
                {isVi ? 'Đã kết nối OAuth' : 'OAuth Connected'}
                {settings.openai_oauth_account_id && ` (${settings.openai_oauth_account_id})`}
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600 border border-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-700">
                <AlertCircle size={13} className="text-gray-400" />
                {isVi ? 'Chưa kết nối tài khoản' : 'Not Connected'}
              </span>
            )
          ) : isKeyConfigured ? (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800">
              <CheckCircle2 size={13} className="text-emerald-500" />
              {currentKeyValue
                ? isVi ? 'Đã nhập key mới (chưa lưu)' : 'New key entered (unsaved)'
                : isVi ? `Đã thiết lập (${keyLength} ký tự)` : `Configured (${keyLength} chars)`}
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800">
              <AlertCircle size={13} className="text-amber-500" />
              {isVi ? 'Chưa có API Key' : 'API Key Not Set'}
            </span>
          )}
        </div>
      </div>

      {/* Gemini Highlight Box */}
      {isGemini && meta.highlight && (
        <div className="rounded-lg bg-gradient-to-r from-blue-50 to-banana-50 dark:from-blue-950/30 dark:to-banana-950/30 border border-blue-200/70 dark:border-blue-900/40 p-3.5 flex items-start gap-2.5">
          <Sparkles size={18} className="text-banana-600 dark:text-banana-400 shrink-0 mt-0.5" />
          <p className="text-xs text-gray-700 dark:text-foreground-secondary leading-relaxed">
            {isVi ? meta.highlight.vi : meta.highlight.en}
          </p>
        </div>
      )}

      {/* FORM FIELDS */}
      {isCodex ? (
        /* Codex OAuth Login Panel */
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-lg border border-gray-200 dark:border-border-primary bg-gray-50/50 dark:bg-background-tertiary">
            <div>
              <p className="text-sm font-medium text-gray-800 dark:text-foreground-primary">
                {isVi ? 'Xác thực tài khoản OpenAI qua trình duyệt' : 'Authenticate OpenAI account via browser'}
              </p>
              <p className="text-xs text-gray-500 dark:text-foreground-tertiary mt-1">
                {isVi
                  ? 'Banana Slides sẽ mở cửa sổ đăng nhập OpenAI. Sau khi xác thực, hệ thống sẽ tự động liên kết tài khoản của bạn.'
                  : 'Banana Slides will open an OpenAI sign-in window. Once authorized, your account will be linked automatically.'}
              </p>
            </div>
            <div>
              {settings?.openai_oauth_connected ? (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleOAuthDisconnect}
                  className="text-red-600 hover:text-red-700 dark:text-red-400"
                >
                  {isVi ? 'Ngắt kết nối' : 'Disconnect'}
                </Button>
              ) : (
                <Button
                  variant="primary"
                  size="sm"
                  loading={oauthConnecting}
                  onClick={handleOAuthLogin}
                >
                  {oauthConnecting
                    ? isVi ? 'Đang kết nối...' : 'Connecting...'
                    : isVi ? 'Đăng nhập với OpenAI' : 'Sign in with OpenAI'}
                </Button>
              )}
            </div>
          </div>

          {!settings?.openai_oauth_connected && (
            <div>
              <button
                type="button"
                onClick={() => setManualCallbackOpen(v => !v)}
                className="text-xs text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
              >
                {isVi ? 'Kết nối thất bại hoặc không mở được cửa sổ?' : 'Connection failed or popup blocked?'}
              </button>
              {manualCallbackOpen && (
                <div className="mt-2 p-3 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg">
                  <p className="text-xs text-amber-700 dark:text-amber-300 mb-2">
                    {isVi
                      ? 'Dán toàn bộ URL trên thanh địa chỉ của cửa sổ đăng nhập vào đây nếu quá trình callback tự động bị chặn:'
                      : 'Paste the full redirect URL from the popup window address bar here:'}
                  </p>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={manualCallbackUrl}
                      onChange={(e) => setManualCallbackUrl(e.target.value)}
                      placeholder="http://localhost:1455/callback?code=..."
                      className="flex-1 px-3 py-1.5 text-xs border border-gray-300 dark:border-border-primary rounded-md bg-white dark:bg-background-secondary text-gray-900 dark:text-foreground-primary placeholder-gray-400"
                    />
                    <button
                      type="button"
                      onClick={handleManualCallback}
                      disabled={manualCallbackSubmitting || !manualCallbackUrl.trim()}
                      className="px-3 py-1.5 text-xs font-medium text-white bg-gray-900 dark:bg-white dark:text-gray-900 rounded-md hover:bg-gray-800 dark:hover:bg-gray-100 transition-colors disabled:opacity-50"
                    >
                      {manualCallbackSubmitting
                        ? isVi ? 'Đang gửi...' : 'Submitting...'
                        : isVi ? 'Gửi URL' : 'Submit'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      ) : (
        /* API Key and Base URL inputs */
        <div className="space-y-4">
          {/* API Key Input */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="block text-sm font-medium text-gray-700 dark:text-foreground-secondary">
                {isDirectKeyProvider
                  ? isGemini
                    ? 'Google Gemini API Key'
                    : isOpenAi
                    ? 'OpenAI API Key'
                    : isVolcengine
                    ? 'Volcengine Agent Plan API Key'
                    : 'Doubao ModelArk API Key'
                  : `${meta.name} API Key`}
              </label>
              {meta.portalUrl && (
                <a
                  href={meta.portalUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 hover:underline"
                >
                  <span>{isVi ? `Lấy API Key tại ${meta.portalName}` : `Get API Key at ${meta.portalName}`}</span>
                  <ExternalLink size={12} />
                </a>
              )}
            </div>

            <div className="relative">
              <input
                type={showApiKey ? 'text' : 'password'}
                placeholder={
                  keyLength > 0
                    ? isVi ? `Đã thiết lập (${keyLength} ký tự) - Nhập giá trị mới để thay thế` : `Configured (${keyLength} chars) - Enter new key to replace`
                    : isGemini
                    ? 'AIzaSy...'
                    : isOpenAi
                    ? 'sk-...'
                    : isVi ? `Nhập API Key của ${meta.name}` : `Enter ${meta.name} API Key`
                }
                value={isDirectKeyProvider ? formData.api_key : formData.lazyllm_api_keys[provider] || ''}
                onChange={(e) => {
                  const val = e.target.value;
                  if (isDirectKeyProvider) {
                    handleFieldChange('api_key', val);
                  } else {
                    setFormData(prev => ({
                      ...prev,
                      lazyllm_api_keys: { ...prev.lazyllm_api_keys, [provider]: val },
                    }));
                  }
                }}
                className="w-full h-10 pl-4 pr-12 rounded-lg border border-gray-200 dark:border-border-primary bg-white dark:bg-background-secondary focus:outline-none focus:ring-2 focus:ring-banana-500 focus:border-transparent text-gray-900 dark:text-foreground-primary text-sm placeholder:text-gray-400 dark:placeholder:text-gray-500 transition-all font-mono"
              />
              <button
                type="button"
                onClick={() => setShowApiKey(!showApiKey)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1 rounded"
                title={showApiKey ? (isVi ? 'Ẩn key' : 'Hide key') : (isVi ? 'Hiện key' : 'Show key')}
              >
                {showApiKey ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            <p className="mt-1 text-xs text-gray-500 dark:text-foreground-tertiary">
              {isVi
                ? 'Để trống nếu muốn giữ nguyên key hiện tại. Nhập key mới và nhấn "Lưu cài đặt" ở cuối trang để cập nhật.'
                : 'Leave blank to keep existing key. Enter a new key and click "Save Settings" below to update.'}
            </p>
          </div>

          {/* API Base URL Input (for Gemini, OpenAI, Volcengine) */}
          {isDirectKeyProvider && (
            <div className="pt-2 border-t border-gray-100 dark:border-border-primary/60 space-y-2">
              <div className="flex items-center justify-between">
                <label className="block text-sm font-medium text-gray-700 dark:text-foreground-secondary">
                  API Base URL <span className="text-xs text-gray-400 font-normal">({isVi ? 'Tùy chọn' : 'Optional'})</span>
                </label>
                {meta.defaultBaseUrl && (
                  <button
                    type="button"
                    onClick={() => {
                      if (isVolcengine) {
                        handleFieldChange('api_base_url', meta.defaultBaseUrl);
                      } else {
                        handleFieldChange('api_base_url', '');
                      }
                    }}
                    className="inline-flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                    title={isVi ? 'Khôi phục về điểm cuối chính thức' : 'Reset to official endpoint'}
                  >
                    <RotateCcw size={12} />
                    <span>{isVi ? 'Khôi phục mặc định' : 'Reset to default'}</span>
                  </button>
                )}
              </div>

              <input
                type="text"
                placeholder={meta.defaultBaseUrl || 'https://api.example.com'}
                value={formData.api_base_url}
                onChange={(e) => handleFieldChange('api_base_url', e.target.value)}
                className="w-full h-10 px-4 rounded-lg border border-gray-200 dark:border-border-primary bg-white dark:bg-background-secondary focus:outline-none focus:ring-2 focus:ring-banana-500 focus:border-transparent text-gray-900 dark:text-foreground-primary text-sm placeholder:text-gray-400 dark:placeholder:text-gray-500 transition-all font-mono"
              />
              <p className="text-xs text-gray-500 dark:text-foreground-tertiary">
                {isVi
                  ? `Mặc định để trống để sử dụng điểm cuối chính thức (${meta.defaultBaseUrl || 'nhà cung cấp'}). Chỉ thay đổi nếu bạn sử dụng reverse proxy hoặc máy chủ doanh nghiệp.`
                  : `Leave empty to use official endpoint (${meta.defaultBaseUrl || 'provider'}). Only change if using a reverse proxy or enterprise gateway.`}
              </p>

              {/* Volcengine endpoint warning & reset */}
              {isVolcengine &&
                formData.api_base_url &&
                formData.api_base_url !== 'https://ark.cn-beijing.volces.com/api/plan/v3' && (
                  <div className="flex flex-wrap items-center gap-2 rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 dark:border-amber-700 dark:bg-amber-950/40">
                    <p className="flex-1 text-xs text-amber-800 dark:text-amber-200">
                      {isVi
                        ? 'Base URL hiện tại không phải điểm cuối chính thức của Volcengine Agent Plans (https://ark.cn-beijing.volces.com/api/plan/v3)'
                        : 'Current Base URL is not the official Volcengine Agent Plans endpoint'}
                    </p>
                    <button
                      type="button"
                      onClick={() => handleFieldChange('api_base_url', 'https://ark.cn-beijing.volces.com/api/plan/v3')}
                      className="shrink-0 rounded-md bg-amber-500 px-2.5 py-1 text-xs font-medium text-white hover:bg-amber-600"
                    >
                      {isVi ? 'Dùng điểm cuối chính thức' : 'Use Official Endpoint'}
                    </button>
                  </div>
                )}
            </div>
          )}

          {/* Volcengine Promo & Recommended Models Action */}
          {(isVolcengine || isDoubao) && (
            <div className="pt-3 border-t border-gray-100 dark:border-border-primary/60 flex flex-wrap items-center gap-3">
              <Button
                variant="secondary"
                size="sm"
                onClick={applyVolcengineRecommendedModels}
                icon={<Sparkles size={14} className="text-amber-500" />}
              >
                {isVi ? 'Áp dụng mô hình khuyến nghị của Volcengine' : 'Apply Volcengine Recommended Models'}
              </Button>
              {volcengineAgentPlansUrl && (
                <a
                  href={volcengineAgentPlansUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-xs text-amber-700 hover:text-amber-800 dark:text-amber-300 underline font-medium"
                >
                  <span>{isVi ? 'Xem ưu đãi Volcengine Agent Plan' : 'View Volcengine Agent Plan Promotion'}</span>
                  <ExternalLink size={12} />
                </a>
              )}
            </div>
          )}

          {/* SenseNova image hint */}
          {provider === 'sensenova' && (
            <div className="p-3 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg">
              <p data-testid="sensenova-global-image-hint" className="text-xs text-amber-700 dark:text-amber-300">
                {t('settings.fields.sensenovaImageHint')}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Provider Connectivity & Service Testing */}
      {triggerTest && (
        <div className="pt-4 border-t border-gray-100 dark:border-border-primary/60 space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-700 dark:text-foreground-primary flex items-center gap-1.5">
                <Zap size={13} className="text-amber-500" />
                {isVi ? 'Kiểm tra kết nối dịch vụ' : 'Test Service Connection'}
              </h4>
              <p className="text-[11px] text-gray-500 dark:text-foreground-tertiary mt-0.5">
                {isVi
                  ? 'Kiểm tra ngay API Key và điểm cuối của nhà cung cấp này để xác minh kết nối hoạt động bình thường.'
                  : 'Verify this provider credentials and endpoints to ensure connection is working properly.'}
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <SettingsInlineServiceTest
                testKey="text-model"
                label={isVi ? 'Kiểm tra văn bản' : 'Test Text Model'}
                icon={<Zap size={13} className="text-amber-500" />}
                testState={serviceTestStates['text-model']}
                onTest={() => triggerTest('text-model')}
                onDismiss={dismissTest ? () => dismissTest('text-model') : undefined}
                isVi={isVi}
                disabled={!isKeyConfigured}
                disabledReason={isVi ? 'Chưa cấu hình key' : 'Key not set'}
              />

              <SettingsInlineServiceTest
                testKey="image-model"
                label={isVi ? 'Kiểm tra tạo ảnh' : 'Test Image Model'}
                icon={<Sparkles size={13} className="text-purple-500" />}
                testState={serviceTestStates['image-model']}
                onTest={() => triggerTest('image-model')}
                onDismiss={dismissTest ? () => dismissTest('image-model') : undefined}
                isVi={isVi}
                disabled={!isKeyConfigured}
                disabledReason={isVi ? 'Chưa cấu hình key' : 'Key not set'}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
