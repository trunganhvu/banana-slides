import { SettingsAdvanced, SettingsActions } from '@/components/settings/SettingsLayout';
import { SettingsPageFrame } from '@/components/settings/SettingsPageFrame';
import { SettingsProviderPicker } from '@/components/settings/SettingsProviderPicker';
import { SettingsActiveProviderForm } from '@/components/settings/SettingsActiveProviderForm';
import { SettingsModelConfigSection } from '@/components/settings/SettingsModelConfigSection';
import { SettingsInlineServiceTest } from '@/components/settings/SettingsInlineServiceTest';
import { SettingsApiGuidance } from '@/components/settings/SettingsApiGuidance';
import { SettingsField } from '@/components/settings/SettingsField';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Key, Image, Zap, Save, RotateCcw, Globe, FileText, Brain, ArrowUp, ArrowUpRight, Link2, Volume2, Info, RefreshCw, CheckCircle, Lightbulb, Sparkles, Layers } from 'lucide-react';
import { useT } from '@/hooks/useT';
import { appVersion } from '@/utils/appVersion';
import { isDesktop } from '@/utils';
import { startOpenAIOAuthMonitor } from '@/utils/openaiOAuthMonitor';
import { DataStorageSettings } from '@/components/settings/DataStorageSettings';
import type {
  DesktopAutoUpdateSettings,
  DesktopUpdateCheckResult,
  DesktopUpdateElectronApi,
} from '@/types/desktopUpdate';

// Component translations
import { settingsI18n } from '@/components/settings/settingsI18n';
import { Button, Input, Loading, Markdown, Modal, useToast, useConfirm } from '@/components/shared';
import * as api from '@/api/endpoints';
import type { OutputLanguage, UpdateCheckInfo } from '@/api/endpoints';
import { OUTPUT_LANGUAGE_OPTIONS } from '@/api/endpoints';
import type { Settings as SettingsType } from '@/types';

// Configuration item type definition
type FieldType = 'text' | 'password' | 'number' | 'select' | 'buttons' | 'switch';

interface FieldConfig {
  key: keyof typeof initialFormData;
  label: string;
  type: FieldType;
  placeholder?: string;
  description?: string;
  sensitiveField?: boolean;  // Sensitive field flag (e.g. API Key)
  lengthKey?: keyof SettingsType;  // Key for displaying existing length
  options?: { value: string; label: string }[];  // Options for select type
  min?: number;
  max?: number;
  link?: string;  // Application link URL
}

interface SectionConfig {
  title: string;
  icon: React.ReactNode;
  fields: FieldConfig[];
}

type TestStatus = 'idle' | 'loading' | 'success' | 'error';

interface ServiceTestState {
  status: TestStatus;
  message?: string;
  detail?: string;
}

const INFERERA_AFFILIATE_URL = 'https://api.inferera.com/?aff=17EC';
const VOLCENGINE_AGENTPLANS_CN_URL = 'https://www.volcengine.com/activity/ai618?utm_campaign=hw&utm_content=hw&utm_medium=devrel_tool_web&utm_source=OWO&utm_term=banana-slides';
const VOLCENGINE_AGENTPLANS_EN_URL = 'https://www.byteplus.com/en/product/modelark?utm_campaign=hw&utm_content=banana-slides&utm_medium=devrel_tool_web&utm_source=OWO&utm_term=banana-slides';

// List of supported LazyLLM vendors
const LAZYLLM_SOURCES = [
  { value: 'qwen', label: 'Qwen (Tongyi Qianwen)' },
  { value: 'doubao', label: 'Doubao (Volcengine)' },
  { value: 'deepseek', label: 'DeepSeek' },
  { value: 'glm', label: 'GLM (Zhipu)' },
  { value: 'siliconflow', label: 'SiliconFlow' },
  { value: 'sensenova', label: 'SenseNova (SenseNova)' },
  { value: 'minimax', label: 'MiniMax' },
  { value: 'openai', label: 'OpenAI' },
  { value: 'kimi', label: 'Kimi' },
  { value: 'ppio', label: 'PPIO (PPIO Cloud)' },
  { value: 'aiping', label: 'AIPing (Aipin)' },
];

// All available provider options (Gemini/OpenAI/Codex + LazyLLM vendors)
const getAllProviderSources = (isVi: boolean) => [
  { value: 'gemini', label: 'Gemini' },
  { value: 'openai', label: 'OpenAI' },
  { value: 'volcengine', label: 'Volcengine Agent Plan' },
  { value: 'doubao', label: 'Doubao / ModelArk' },
  { value: 'codex', label: 'Codex (OpenAI OAuth)' },
  ...LAZYLLM_SOURCES.filter(s => !['openai', 'doubao', 'ppio', 'aiping'].includes(s.value)), // avoid duplicate or non-partner providers
];

// Providers requiring API Key + Base URL (non-LazyLLM)
const API_KEY_PROVIDERS = new Set(['gemini', 'openai', 'volcengine']);
// Quality tiers only apply to the GPT Image family (matches the backend's
// _is_gpt_image_model); DALL-E, Seedream and Gemini models ignore the setting.
const GPT_IMAGE_MODEL_PATTERN = /^(gpt-image|chatgpt-image)/i;
// Volcengine Agent Plans: dedicated Base URL and model names
const VOLCENGINE_AGENTPLANS_BASE_URL = 'https://ark.cn-beijing.volces.com/api/plan/v3';
const VOLCENGINE_AGENTPLANS_RECOMMENDED_MODELS = {
  text: 'doubao-seed-2.1-turbo',
  caption: 'doubao-seed-2.1-turbo',
  image: 'doubao-seedream-5.0-lite',
};
// ModelArk (standard ModelArk): endpoint ID format
const VOLCENGINE_MODELARK_RECOMMENDED_MODELS = {
  text: 'doubao-seed-2-1-pro-260628',
  caption: 'doubao-seed-2-1-pro-260628',
  image: 'doubao-seedream-5-0-260128',
};
// Default endpoints per provider
const KNOWN_DEFAULT_BASE_URLS = new Set([
  '',
  'https://api.inferera.com/v1',
  'https://api.openai.com/v1',
  'https://api.apimart.ai/v1',
  'https://api.inferera.com/gemini',
  'https://generativelanguage.googleapis.com',
  'https://ark.cn-beijing.volces.com/api/v3',
  'https://api.anthropic.com',
]);
// Stale endpoints when leaving Agent Plans
const VOLCENGINE_DEFAULT_BASE_URLS = new Set([
  'https://ark.cn-beijing.volces.com/api/plan/v3',
  'https://ark.cn-beijing.volces.com/api/v3',
]);

// LazyLLM vendor names set
const LAZYLLM_VENDOR_SET = new Set(LAZYLLM_SOURCES.map(s => s.value));

// LazyLLM 0.7.x vendors that actually register an image-generation (text2image)
// supplier; image-model source options are filtered to this set so a selection
// cannot point at a vendor without image capability.
const IMAGE_CAPABLE_LAZYLLM_SOURCES = new Set([
  'qwen', 'doubao', 'siliconflow', 'aiping', 'glm', 'minimax',
]);

// Whether a source value can appear in the image-model source dropdown:
// real OpenAI provider plus LazyLLM vendors that register a text2image
// supplier. Non-LazyLLM sources (gemini/volcengine/codex) always pass.
const isImageModelSourceSelectable = (value: string) =>
  value === 'openai'
  || !LAZYLLM_VENDOR_SET.has(value)
  || IMAGE_CAPABLE_LAZYLLM_SOURCES.has(value);

// Initial form data
const initialFormData = {
  ai_provider_format: 'gemini' as string,
  api_base_url: '',
  api_key: '',
  text_model: '',
  image_model: '',
  image_caption_model: '',
  mineru_api_base: '',
  mineru_token: '',
  image_resolution: '2K',
  image_quality: 'auto',
  enable_image_quality_control: false,
  max_description_workers: 5,
  max_image_workers: 8,
  output_language: 'zh' as OutputLanguage,
  // Reasoning mode configurations
  enable_text_reasoning: false,
  text_max_output_tokens: 32768,
  text_thinking_budget: 1024,
  enable_image_reasoning: false,
  image_thinking_budget: 1024,
  baidu_api_key: '',
  // LazyLLM configurations
  text_model_source: '',
  image_model_source: '',
  image_caption_model_source: '',
  lazyllm_api_keys: {} as Record<string, string>,
  // Per-model API credentials (for gemini/openai per-model overrides)
  text_api_key: '',
  text_api_base_url: '',
  image_api_key: '',
  image_api_base_url: '',
  image_caption_api_key: '',
  image_caption_api_base_url: '',
  openai_image_api_protocol: 'auto',
  // ElevenLabs TTS
  elevenlabs_api_key: '',
};

const isLazyllmVendor = (vendor: string) =>
  LAZYLLM_VENDOR_SET.has(vendor) && vendor !== 'openai';

// When backend returns "lazyllm", infer specific vendor from configured keys
const resolveLazyllmVendor = (format: string, keysInfo?: Record<string, number>): string => {
  if (format !== 'lazyllm') return format;
  if (keysInfo) {
    const vendor = LAZYLLM_SOURCES.find(s => isLazyllmVendor(s.value) && keysInfo[s.value]);
    if (vendor) return vendor.value;
  }
  return LAZYLLM_SOURCES.find(s => isLazyllmVendor(s.value))?.value || 'deepseek';
};

const GlobalVendorKeyInput: React.FC<{
  vendor: string; formData: typeof initialFormData;
  setFormData: React.Dispatch<React.SetStateAction<typeof initialFormData>>;
  settings: SettingsType | null; t: ReturnType<typeof useT>;
}> = ({ vendor, formData, setFormData, settings, t }) => {
  const vendorLabel = LAZYLLM_SOURCES.find(s => s.value === vendor)?.label || vendor.toUpperCase();
  const keyLength = settings?.lazyllm_api_keys_info?.[vendor] || 0;
  const placeholder = keyLength > 0
    ? t('settings.fields.vendorApiKeySet', { length: keyLength })
    : t('settings.fields.vendorApiKeyPlaceholder', { vendor: vendorLabel });
  return (
    <div className="pl-3 border-l-2 border-amber-300 dark:border-amber-600">
      <Input
        label={t('settings.fields.vendorApiKey', { vendor: vendorLabel })}
        type="password"
        placeholder={placeholder}
        value={formData.lazyllm_api_keys[vendor] || ''}
        onChange={(e) => {
          setFormData(prev => ({
            ...prev,
            lazyllm_api_keys: { ...prev.lazyllm_api_keys, [vendor]: e.target.value }
          }));
        }}
      />
      <p className="mt-1 text-sm text-gray-500 dark:text-foreground-tertiary">{t('settings.fields.vendorApiKeyDesc')}</p>
    </div>
  );
};

type SettingsTranslator = ReturnType<typeof useT>;

interface UpdateResultView {
  status: 'up_to_date' | 'update_available' | 'downloading' | 'update_downloaded' | 'unknown';
  updateAvailable: boolean;
  version: string;
  downloadUrl?: string;
  canAutoUpdate?: boolean;
  progress?: number;
  notes?: string;
}

function getLatestVersion(info: UpdateCheckInfo): string {
  const sha = info.latest?.sha;
  if (sha) {
    return sha.length > 7 ? sha.slice(0, 7) : sha;
  }
  return info.latest?.tag || '';
}

function toUpdateResultView(info: UpdateCheckInfo): UpdateResultView {
  return {
    status: info.status,
    updateAvailable: info.update_available,
    version: getLatestVersion(info),
  };
}

function toDesktopUpdateResultView(info: DesktopUpdateCheckResult): UpdateResultView {
  if (
    (
      info.status === 'update_available'
      || info.status === 'downloading'
      || info.status === 'update_downloaded'
      || info.status === 'error'
    )
    && info.update
  ) {
    return {
      status: info.status === 'error' ? 'update_available' : info.status,
      updateAvailable: true,
      version: info.update.version,
      downloadUrl: info.update.url,
      canAutoUpdate: info.canAutoUpdate,
      progress: info.progress?.percent,
      notes: info.update.notes,
    };
  }

  if (info.status !== 'up_to_date') {
    return {
      status: 'unknown',
      updateAvailable: false,
      version: info.latestVersion,
    };
  }

  return {
    status: 'up_to_date',
    updateAvailable: false,
    version: info.latestVersion,
  };
}

function formatUpdateMessage(t: SettingsTranslator, info: UpdateResultView): string {
  if (info.status === 'up_to_date') return t('settings.about.upToDate');
  if (info.status === 'update_available') return t('settings.about.updateAvailable', { version: info.version });
  if (info.status === 'downloading') {
    return t('settings.about.updateDownloading', {
      version: info.version,
      progress: String(Math.round(info.progress || 0)),
    });
  }
  if (info.status === 'update_downloaded') return t('settings.about.updateReady', { version: info.version });
  return t('settings.about.unknown');
}

export const SettingsAbout: React.FC<{ t: SettingsTranslator }> = ({ t }) => {
  const [checkingUpdate, setCheckingUpdate] = useState(false);
  const [updateActionPending, setUpdateActionPending] = useState(false);
  const [updateInfo, setUpdateInfo] = useState<UpdateResultView | null>(null);
  const [updateError, setUpdateError] = useState('');
  const [updateDialogOpen, setUpdateDialogOpen] = useState(false);
  const [automaticUpdatesEnabled, setAutomaticUpdatesEnabled] = useState(true);
  const [automaticUpdatesSupported, setAutomaticUpdatesSupported] = useState(true);
  const [automaticUpdatesLoading, setAutomaticUpdatesLoading] = useState(isDesktop);
  const [automaticUpdatesSaving, setAutomaticUpdatesSaving] = useState(false);
  const [automaticUpdatesError, setAutomaticUpdatesError] = useState('');

  const desktopUpdateApi = isDesktop
    ? (window as typeof window & { electronAPI?: DesktopUpdateElectronApi }).electronAPI
    : undefined;

  useEffect(() => {
    if (!desktopUpdateApi) return;
    let disposed = false;
    const applySettings = (settings: DesktopAutoUpdateSettings) => {
      if (!disposed) {
        setAutomaticUpdatesEnabled(settings.automaticUpdatesEnabled);
        setAutomaticUpdatesSupported(settings.canAutoUpdate !== false);
      }
    };
    const applyUpdateState = (state: DesktopUpdateCheckResult) => {
      if (!disposed) setUpdateInfo(toDesktopUpdateResultView(state));
    };
    const unsubscribe = desktopUpdateApi.onUpdateStatus?.(applyUpdateState);

    if (desktopUpdateApi.getAutoUpdateSettings) {
      desktopUpdateApi.getAutoUpdateSettings()
        .then(applySettings)
        .catch((error) => {
          if (!disposed) setAutomaticUpdatesError(error?.message || t('settings.about.automaticUpdatesSaveFailed'));
        })
        .finally(() => {
          if (!disposed) setAutomaticUpdatesLoading(false);
        });
    } else {
      setAutomaticUpdatesLoading(false);
    }

    return () => {
      disposed = true;
      unsubscribe?.();
    };
  }, [desktopUpdateApi, t]);

  const handleAutomaticUpdatesChange = async () => {
    if (!desktopUpdateApi?.setAutomaticUpdatesEnabled || automaticUpdatesSaving) return;
    const nextEnabled = !automaticUpdatesEnabled;
    setAutomaticUpdatesSaving(true);
    setAutomaticUpdatesError('');
    try {
      const settings = await desktopUpdateApi.setAutomaticUpdatesEnabled(nextEnabled);
      setAutomaticUpdatesEnabled(settings.automaticUpdatesEnabled);
    } catch (error: any) {
      setAutomaticUpdatesError(error?.message || t('settings.about.automaticUpdatesSaveFailed'));
    } finally {
      setAutomaticUpdatesSaving(false);
    }
  };

  const handleCheckUpdate = async () => {
    setCheckingUpdate(true);
    setUpdateError('');
    try {
      if (isDesktop) {
        const response = await desktopUpdateApi!.checkForUpdates();
        setUpdateInfo(toDesktopUpdateResultView(response));
      } else {
        const response = await api.checkForUpdates();
        setUpdateInfo(response.data ? toUpdateResultView(response.data) : null);
      }
      setUpdateDialogOpen(true);
    } catch (error: any) {
      setUpdateInfo(null);
      setUpdateError(error?.response?.data?.error?.message || error?.message || t('settings.about.failed'));
      setUpdateDialogOpen(true);
    } finally {
      setCheckingUpdate(false);
    }
  };

  const handleDesktopUpdateAction = async () => {
    if (!desktopUpdateApi || !updateInfo || updateActionPending) return;
    setUpdateActionPending(true);
    setUpdateError('');
    try {
      if (updateInfo.status === 'update_downloaded' && desktopUpdateApi.installUpdate) {
        const result = await desktopUpdateApi.installUpdate();
        if (!result.success) throw new Error(result.error || 'UPDATE_INSTALL_FAILED');
      } else if (updateInfo.canAutoUpdate && desktopUpdateApi.downloadUpdate) {
        const response = await desktopUpdateApi.downloadUpdate();
        setUpdateInfo(toDesktopUpdateResultView(response));
      } else if (updateInfo.downloadUrl) {
        await desktopUpdateApi.openExternal(updateInfo.downloadUrl);
      }
    } catch (error: any) {
      setUpdateError(error?.message || t('settings.about.failed'));
    } finally {
      setUpdateActionPending(false);
    }
  };

  const showSuccessCheck = updateInfo?.status === 'up_to_date';

  return (
    <>
      <div className="pt-4 border-t border-gray-200 dark:border-border-primary">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-foreground-primary mb-3 flex items-center">
          <Info size={20} />
          <span className="ml-2">{t('settings.sections.about')}</span>
        </h2>
        {isDesktop && (
          <div className="mb-4 flex items-center justify-between gap-4 rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 dark:border-border-primary dark:bg-background-secondary">
            <div className="min-w-0">
              <div className="font-medium text-gray-900 dark:text-foreground-primary">
                {automaticUpdatesSupported
                  ? t('settings.about.automaticUpdates')
                  : t('settings.about.automaticUpdateChecks')}
              </div>
              <p className="mt-0.5 text-sm text-gray-500 dark:text-foreground-tertiary">
                {automaticUpdatesSupported
                  ? t('settings.about.automaticUpdatesDesc')
                  : t('settings.about.automaticUpdateChecksDesc')}
              </p>
              {automaticUpdatesError && (
                <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                  {t('settings.about.automaticUpdatesSaveFailed')}: {automaticUpdatesError}
                </p>
              )}
            </div>
            <button
              type="button"
              role="switch"
              aria-checked={automaticUpdatesEnabled}
              aria-label={automaticUpdatesSupported
                ? t('settings.about.automaticUpdates')
                : t('settings.about.automaticUpdateChecks')}
              disabled={automaticUpdatesLoading || automaticUpdatesSaving || !desktopUpdateApi?.setAutomaticUpdatesEnabled}
              onClick={handleAutomaticUpdatesChange}
              className={`relative inline-flex h-6 w-11 shrink-0 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-banana-500 focus:ring-offset-2 disabled:cursor-wait disabled:opacity-50 ${
                automaticUpdatesEnabled ? 'bg-banana-500' : 'bg-gray-300 dark:bg-gray-600'
              }`}
            >
              <span
                className={`pointer-events-none inline-block h-5 w-5 translate-y-0.5 rounded-full bg-white shadow transition-transform ${
                  automaticUpdatesEnabled ? 'translate-x-[22px]' : 'translate-x-0.5'
                }`}
              />
            </button>
          </div>
        )}
        <div className="flex flex-col gap-3 text-sm text-gray-600 dark:text-foreground-tertiary sm:flex-row sm:items-start sm:justify-between">
          <div className="space-y-1">
            <div title={appVersion.detail} aria-label={`${t('settings.about.version')} ${appVersion.detail}`}>
              {t('settings.about.version')}: {appVersion.display}
            </div>
            <a
              href="https://github.com/Anionex/banana-slides"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-banana-700 dark:text-banana hover:underline"
            >
              {t('settings.about.source')}
            </a>
            {updateInfo && (
              <div className={updateInfo.updateAvailable ? 'text-orange-600 dark:text-orange-400' : 'text-gray-600 dark:text-foreground-tertiary'}>
                <div>{formatUpdateMessage(t, updateInfo)}</div>
              </div>
            )}
            {updateError && (
              <div className="text-red-600 dark:text-red-400">
                {t('settings.about.failed')}: {updateError}
              </div>
            )}
          </div>
          <Button
            variant="secondary"
            size="sm"
            icon={<RefreshCw size={16} className={checkingUpdate ? 'animate-spin' : ''} />}
            onClick={handleCheckUpdate}
            loading={checkingUpdate}
          >
            {checkingUpdate ? t('settings.about.checking') : t('settings.about.checkUpdate')}
          </Button>
        </div>
      </div>

      <Modal isOpen={updateDialogOpen} onClose={() => setUpdateDialogOpen(false)} title={t('settings.about.resultTitle')}>
        <div className="space-y-4">
          {updateInfo && (
            <div className="space-y-2 text-sm text-gray-700 dark:text-foreground-secondary">
              <div className="flex flex-col items-center gap-3 py-2 text-center">
                {showSuccessCheck && (
                  <CheckCircle
                    size={44}
                    data-testid="update-success-icon"
                    className="text-green-600 dark:text-green-400"
                    aria-hidden="true"
                  />
                )}
                {updateInfo.updateAvailable && (
                  <ArrowUp
                    size={44}
                    data-testid="update-available-icon"
                    className="text-orange-600 dark:text-orange-400"
                    aria-hidden="true"
                  />
                )}
                <p className={updateInfo.updateAvailable
                  ? 'text-xl font-semibold text-orange-600 dark:text-orange-400'
                  : 'text-xl font-semibold text-gray-900 dark:text-foreground-primary'
                }>
                  {formatUpdateMessage(t, updateInfo)}
                </p>
              </div>
              {updateInfo.updateAvailable && updateInfo.notes?.trim() && (
                <section aria-label={t('settings.about.summary')} className="space-y-2">
                  <h3 className="font-semibold text-gray-900 dark:text-foreground-primary">
                    {t('settings.about.summary')}
                  </h3>
                  <div className="max-h-52 overflow-y-auto rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 dark:border-border-primary dark:bg-background-secondary">
                    <Markdown>{updateInfo.notes.trim()}</Markdown>
                  </div>
                </section>
              )}
              {updateInfo.updateAvailable && updateInfo.downloadUrl && (
                <button
                  type="button"
                  onClick={() => desktopUpdateApi?.openExternal(updateInfo.downloadUrl!)}
                  className="inline-flex items-center gap-1.5 font-medium text-banana-700 hover:text-banana-800 hover:underline dark:text-banana-300 dark:hover:text-banana-200"
                >
                  {t('settings.about.changelog')}
                  <ArrowUpRight size={15} aria-hidden="true" />
                </button>
              )}
            </div>
          )}
          {updateError && (
            <p className="text-sm text-red-600 dark:text-red-400">
              {t('settings.about.failed')}: {updateError}
            </p>
          )}
          <div className="flex justify-end gap-2">
            {isDesktop && updateInfo?.updateAvailable && updateInfo.status !== 'downloading' && (
              <Button
                size="sm"
                onClick={handleDesktopUpdateAction}
                loading={updateActionPending}
              >
                {updateInfo.status === 'update_downloaded'
                  ? t('settings.about.restart')
                  : updateInfo.canAutoUpdate
                    ? t('settings.about.download')
                    : t('settings.about.fallbackDownload')}
              </Button>
            )}
            <Button variant="secondary" size="sm" onClick={() => setUpdateDialogOpen(false)}>
              {updateInfo?.updateAvailable ? t('settings.about.later') : t('settings.about.close')}
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
};

const formDataFromSettings = (data: SettingsType): typeof initialFormData => {
  const providerFormat = resolveLazyllmVendor(data.ai_provider_format || 'gemini', data.lazyllm_api_keys_info).toLowerCase();
  const textModelSource = (data.text_model_source || '').toLowerCase();
  const imageModelSource = (data.image_model_source || '').toLowerCase();
  const imageCaptionModelSource = (data.image_caption_model_source || '').toLowerCase();

  return {
    ai_provider_format: providerFormat,
    api_base_url: data.api_base_url || '',
    api_key: '',
    image_resolution: data.image_resolution || '2K',
    image_quality: data.image_quality || 'auto',
    enable_image_quality_control: data.enable_image_quality_control ?? false,
    max_description_workers: data.max_description_workers || 5,
    max_image_workers: data.max_image_workers || 8,
    text_model: data.text_model || '',
    image_model: data.image_model || '',
    mineru_api_base: data.mineru_api_base || '',
    mineru_token: '',
    image_caption_model: data.image_caption_model || '',
    output_language: data.output_language || 'zh',
    enable_text_reasoning: data.enable_text_reasoning || false,
    text_max_output_tokens: data.text_max_output_tokens ?? 32768,
    text_thinking_budget: data.text_thinking_budget || 1024,
    enable_image_reasoning: data.enable_image_reasoning || false,
    image_thinking_budget: data.image_thinking_budget || 1024,
    baidu_api_key: '',
    text_model_source: textModelSource,
    image_model_source: imageModelSource,
    image_caption_model_source: imageCaptionModelSource,
    lazyllm_api_keys: {},
    text_api_key: '',
    text_api_base_url: data.text_api_base_url || '',
    image_api_key: '',
    image_api_base_url: data.image_api_base_url || '',
    image_caption_api_key: '',
    image_caption_api_base_url: data.image_caption_api_base_url || '',
    openai_image_api_protocol: data.openai_image_api_protocol || 'auto',
    elevenlabs_api_key: '',
  };
};

// Settings component - embeddable mode
export const Settings: React.FC = () => {
  const t = useT(settingsI18n);
  const { i18n } = useTranslation();
  const isVi = i18n.language?.startsWith('zh') ?? true;
  const { show, ToastContainer } = useToast();
  const { confirm, ConfirmDialog } = useConfirm();

  const copyToClipboard = (text: string) => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text);
    } else {
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
    }
    show({ message: !i18n.language?.startsWith('en') ? 'Đã sao chép liên kết vào clipboard' : 'Link copied to clipboard', type: 'success' });
  };

  const [settings, setSettings] = useState<SettingsType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [formData, setFormData] = useState(initialFormData);
  const [serviceTestStates, setServiceTestStates] = useState<Record<string, ServiceTestState>>({});
  const [oauthConnecting, setOauthConnecting] = useState(false);
  const [oauthDialogOpen, setOauthDialogOpen] = useState(false);
  const pendingCodexSelection = useRef<(() => void) | null>(null);
  const oauthPopupRef = useRef<Window | null>(null);
  const [manualCallbackUrl, setManualCallbackUrl] = useState('');
  const [manualCallbackOpen, setManualCallbackOpen] = useState(false);
  const [manualCallbackSubmitting, setManualCallbackSubmitting] = useState(false);
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const oauthMonitorStopRef = useRef<(() => void) | null>(null);
  const oauthAttemptRef = useRef(0);
  const allProviderSources = getAllProviderSources(isVi);
  const globalProviderSources = [
    allProviderSources[0],
    allProviderSources[2],
    allProviderSources[1],
    ...allProviderSources.slice(3),
  ];
  const volcengineAgentPlansUrl = isVi ? VOLCENGINE_AGENTPLANS_CN_URL : VOLCENGINE_AGENTPLANS_EN_URL;
  const volcengineLogoUrl = isVi ? '/volcengine/huoshan.png' : '/volcengine/byteplus.png';
  const usesVolcengineCampaignPromo = formData.ai_provider_format === 'volcengine' || formData.ai_provider_format === 'doubao';
  const selectedGlobalProvider = formData.ai_provider_format;
  const activeVolcenginePromoKey = formData.ai_provider_format === 'doubao'
    ? 'settings.doubaoVolcenginePromo'
    : 'settings.volcenginePromo';
  const activeApiKeyHelpKey = formData.ai_provider_format === 'volcengine'
    ? 'settings.volcengineKeyHelp'
    : formData.ai_provider_format === 'doubao'
      ? 'settings.doubaoKeyHelp'
      : 'settings.apiKeyHelp';
  const activeApiKeyHelpUrl = INFERERA_AFFILIATE_URL;
  const activeApiKeyTipKey = 'settings.apiKeyTip';
  const stopOAuthMonitor = useCallback(() => {
    oauthAttemptRef.current += 1;
    oauthMonitorStopRef.current?.();
    oauthMonitorStopRef.current = null;
  }, []);

  useEffect(() => {
    return () => {
      stopOAuthMonitor();
    };
  }, [stopOAuthMonitor]);

  useEffect(() => {
    if (settings) {
      try {
        sessionStorage.setItem('banana-settings', JSON.stringify(settings));
      } catch (error) {
        console.warn('Failed to persist settings in sessionStorage:', error);
      }
    }
  }, [settings]);

  const applyOAuthStatus = useCallback((connected: boolean, accountId: string | null) => {
    if (connected && pendingCodexSelection.current) {
      pendingCodexSelection.current();
      pendingCodexSelection.current = null;
      setOauthDialogOpen(false);
    }
    setSettings(prev => {
      if (!prev) return prev;
      return {
        ...prev,
        openai_oauth_connected: connected,
        openai_oauth_account_id: accountId,
      };
    });
  }, []);

  const handleOAuthLogin = async () => {
    stopOAuthMonitor();
    const attemptId = oauthAttemptRef.current;
    setOauthConnecting(true);
    // Reserve the browser popup while the login button still has user activation.
    const reservedPopup = isDesktop ? null : window.open('about:blank', 'openai-oauth', 'width=600,height=700');
    oauthPopupRef.current = reservedPopup;
    if (!isDesktop && (!reservedPopup || reservedPopup.closed)) {
      setOauthConnecting(false);
      show({ message: t('settings.openaiOAuth.popupBlocked'), type: 'error' });
      return;
    }
    try {
      const resp = await api.getOpenAIOAuthUrl();
      if (attemptId !== oauthAttemptRef.current) return;
      if (resp.success && resp.data?.auth_url) {
        if (resp.data.callback_server_available === false) {
          setManualCallbackOpen(true);
          show({ message: t('settings.openaiOAuth.callbackPortBusy'), type: 'warning' });
        }
        const popup = isDesktop
          ? window.open(resp.data.auth_url, 'openai-oauth', 'width=600,height=700')
          : reservedPopup;
        if (reservedPopup) reservedPopup.location.href = resp.data.auth_url;
        if ((!popup || popup.closed) && !isDesktop) {
          setOauthConnecting(false);
          show({ message: t('settings.openaiOAuth.popupBlocked'), type: 'error' });
          return;
        }

        const monitor = startOpenAIOAuthMonitor({
          desktop: isDesktop,
          popup,
          getStatus: async () => {
            const statusResp = await api.getOpenAIOAuthStatus();
            return statusResp.success && statusResp.data ? statusResp.data : null;
          },
          onConnected: status => {
            oauthMonitorStopRef.current = null;
            setOauthConnecting(false);
            applyOAuthStatus(true, status.account_id || null);
            show({ message: t('settings.openaiOAuth.manualCallbackSuccess'), type: 'success' });
          },
          onFailure: (reason, message) => {
            oauthMonitorStopRef.current = null;
            setOauthConnecting(false);
            const errorMessage = reason === 'timeout'
              ? t('settings.openaiOAuth.connectTimeout')
              : message || t('settings.openaiOAuth.connectFailed');
            show({ message: errorMessage, type: 'error' });
          },
        });
        oauthMonitorStopRef.current = monitor.stop;
      } else {
        reservedPopup?.close();
        setOauthConnecting(false);
        show({ message: t('settings.openaiOAuth.connectFailed'), type: 'error' });
      }
    } catch {
      if (attemptId !== oauthAttemptRef.current) return;
      stopOAuthMonitor();
      reservedPopup?.close();
      setOauthConnecting(false);
      show({ message: t('settings.openaiOAuth.connectFailed'), type: 'error' });
    }
  };

  const handleOAuthDisconnect = async () => {
    try {
      const resp = await api.disconnectOpenAIOAuth();
      if (resp.success) {
        setSettings(prev => prev ? {
          ...prev,
          openai_oauth_connected: false,
          openai_oauth_account_id: null,
        } : prev);
        show({ message: t('settings.openaiOAuth.disconnectSuccess'), type: 'success' });
      }
    } catch {
      show({ message: t('settings.openaiOAuth.disconnectFailed'), type: 'error' });
    }
  };

  const handleManualCallback = async () => {
    if (!manualCallbackUrl.trim()) return;
    setManualCallbackSubmitting(true);
    try {
      const resp = await api.submitOAuthManualCallback(manualCallbackUrl.trim());
      if (resp.success) {
        stopOAuthMonitor();
        setOauthConnecting(false);
        setManualCallbackUrl('');
        setManualCallbackOpen(false);
        applyOAuthStatus(true, resp.data?.account_id || null);
        show({ message: t('settings.openaiOAuth.manualCallbackSuccess'), type: 'success' });
      } else {
        show({ message: t('settings.openaiOAuth.connectFailed'), type: 'error' });
      }
    } catch {
      show({ message: t('settings.openaiOAuth.connectFailed'), type: 'error' });
    } finally {
      setManualCallbackSubmitting(false);
    }
  };

  // Configuration-driven form sections
  const settingsSections: SectionConfig[] = [
    // Global API config & Model config are rendered separately above
    {
      title: t('settings.sections.mineruConfig'),
      icon: <FileText size={20} />,
      fields: [
        {
          key: 'mineru_api_base',
          label: t('settings.fields.mineruApiBase'),
          type: 'text',
          placeholder: t('settings.fields.mineruApiBasePlaceholder'),
          description: t('settings.fields.mineruApiBaseDesc'),
        },
        {
          key: 'mineru_token',
          label: t('settings.fields.mineruToken'),
          type: 'password',
          placeholder: t('settings.fields.mineruTokenPlaceholder'),
          sensitiveField: true,
          lengthKey: 'mineru_token_length',
          description: t('settings.fields.mineruTokenDesc'),
          link: 'https://mineru.net/apiManage/token',
        },
      ],
    },
    {
      title: t('settings.sections.imageConfig'),
      icon: <Image size={20} />,
      fields: [
        {
          key: 'image_resolution',
          label: t('settings.fields.imageResolution'),
          type: 'select',
          description: t('settings.fields.imageResolutionDesc'),
          options: [
            { value: '1K', label: '1K (1024px)' },
            { value: '2K', label: '2K (2048px)' },
            { value: '4K', label: '4K (4096px)' },
          ],
        },
        {
          key: 'enable_image_quality_control',
          label: t('settings.fields.enableImageQualityControl'),
          type: 'switch',
          description: t('settings.fields.enableImageQualityControlDesc'),
        },
      ],
    },
    {
      title: t('settings.sections.performanceConfig'),
      icon: <Zap size={20} />,
      fields: [
        {
          key: 'text_max_output_tokens',
          label: t('settings.fields.textMaxOutputTokens'),
          type: 'number',
          min: 1,
          max: 2147483647,
          description: t('settings.fields.textMaxOutputTokensDesc'),
        },
        {
          key: 'max_description_workers',
          label: t('settings.fields.maxDescriptionWorkers'),
          type: 'number',
          min: 1,
          max: 20,
          description: t('settings.fields.maxDescriptionWorkersDesc'),
        },
        {
          key: 'max_image_workers',
          label: t('settings.fields.maxImageWorkers'),
          type: 'number',
          min: 1,
          max: 20,
          description: t('settings.fields.maxImageWorkersDesc'),
        },
      ],
    },
    {
      title: t('settings.sections.outputLanguage'),
      icon: <Globe size={20} />,
      fields: [
        {
          key: 'output_language',
          label: t('settings.fields.defaultOutputLanguage'),
          type: 'buttons',
          description: t('settings.fields.defaultOutputLanguageDesc'),
          options: OUTPUT_LANGUAGE_OPTIONS,
        },
      ],
    },
    {
      title: t('settings.sections.textReasoning'),
      icon: <Brain size={20} />,
      fields: [
        {
          key: 'enable_text_reasoning',
          label: t('settings.fields.enableTextReasoning'),
          type: 'switch',
          description: t('settings.fields.enableTextReasoningDesc'),
        },
        {
          key: 'text_thinking_budget',
          label: t('settings.fields.textThinkingBudget'),
          type: 'number',
          min: 1,
          max: 8192,
          description: t('settings.fields.textThinkingBudgetDesc'),
        },
      ],
    },
    {
      title: t('settings.sections.imageReasoning'),
      icon: <Brain size={20} />,
      fields: [
        {
          key: 'enable_image_reasoning',
          label: t('settings.fields.enableImageReasoning'),
          type: 'switch',
          description: t('settings.fields.enableImageReasoningDesc'),
        },
        {
          key: 'image_thinking_budget',
          label: t('settings.fields.imageThinkingBudget'),
          type: 'number',
          min: 1,
          max: 8192,
          description: t('settings.fields.imageThinkingBudgetDesc'),
        },
      ],
    },
    {
      title: t('settings.sections.baiduOcr'),
      icon: <FileText size={20} />,
      fields: [
        {
          key: 'baidu_api_key',
          label: t('settings.fields.baiduOcrApiKey'),
          type: 'password',
          placeholder: t('settings.fields.baiduOcrApiKeyPlaceholder'),
          sensitiveField: true,
          lengthKey: 'baidu_api_key_length',
          description: t('settings.fields.baiduOcrApiKeyDesc'),
          link: 'https://console.bce.baidu.com/iam/#/iam/apikey/list',
        },
      ],
    },
    {
      title: t('settings.sections.elevenlabs'),
      icon: <Volume2 size={20} />,
      fields: [
        {
          key: 'elevenlabs_api_key',
          label: t('settings.fields.elevenLabsApiKey'),
          type: 'password',
          placeholder: t('settings.fields.elevenLabsApiKeyPlaceholder'),
          sensitiveField: true,
          lengthKey: 'elevenlabs_api_key_length',
          description: t('settings.fields.elevenLabsApiKeyDesc'),
          link: 'https://elevenlabs.io/app/settings/api-keys',
        },
      ],
    },
  ];

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setIsLoading(true);
    try {
      const response = await api.getSettings();
      if (response.data) {
        setSettings(response.data);
        setFormData(formDataFromSettings(response.data));
      }
    } catch (error: any) {
      console.error('Tải cài đặt thất bại:', error);
      show({
        message: t('settings.messages.loadFailed') + ': ' + (error?.message || t('settings.messages.unknownError')),
        type: 'error'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const markOpenAIOAuthDisconnected = () => {
    setSettings(prev => {
      if (!prev) return prev;
      return {
        ...prev,
        openai_oauth_connected: false,
        openai_oauth_account_id: null,
      };
    });
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const {
        api_key, mineru_token, baidu_api_key, elevenlabs_api_key, lazyllm_api_keys,
        text_api_key, image_api_key, image_caption_api_key,
        ...otherData
      } = formData;
      const payload: Parameters<typeof api.updateSettings>[0] = {
        ...otherData,
        ai_provider_format: otherData.ai_provider_format,
      };

      // Only send sensitive fields if user entered a new value
      if (api_key) payload.api_key = api_key;
      if (mineru_token) payload.mineru_token = mineru_token;
      if (baidu_api_key) payload.baidu_api_key = baidu_api_key;
      if (elevenlabs_api_key) payload.elevenlabs_api_key = elevenlabs_api_key;
      if (text_api_key) payload.text_api_key = text_api_key;
      if (image_api_key) payload.image_api_key = image_api_key;
      if (image_caption_api_key) payload.image_caption_api_key = image_caption_api_key;

      // Send lazyllm API keys (only non-empty values)
      const nonEmptyKeys = Object.fromEntries(
        Object.entries(lazyllm_api_keys).filter(([, v]) => v)
      );
      if (Object.keys(nonEmptyKeys).length > 0) {
        payload.lazyllm_api_keys = nonEmptyKeys;
      }

      const response = await api.updateSettings(payload);
      if (response.data) {
        setSettings(response.data);
        show({ message: t('settings.messages.saveSuccess'), type: 'success' });
        show({ message: t('settings.messages.testServiceTip'), type: 'info' });
        // Clear all sensitive fields after save
        setFormData(prev => ({
          ...prev,
          api_key: '', mineru_token: '', baidu_api_key: '', elevenlabs_api_key: '',
          lazyllm_api_keys: {},
          text_api_key: '', image_api_key: '', image_caption_api_key: '',
        }));
      }
    } catch (error: any) {
      console.error('Lưu cài đặt thất bại:', error);
      show({
        message: t('settings.messages.saveFailed') + ': ' + (error?.response?.data?.error?.message || error?.message || t('settings.messages.unknownError')),
        type: 'error'
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    confirm(
      t('settings.messages.resetConfirm'),
      async () => {
        setIsSaving(true);
        try {
          const response = await api.resetSettings();
          if (response.data) {
            setSettings(response.data);
            setFormData(formDataFromSettings(response.data));
            show({ message: t('settings.messages.resetSuccess'), type: 'success' });
          }
        } catch (error: any) {
          console.error('Đặt lại cài đặt thất bại:', error);
          show({
            message: t('settings.messages.resetFailed') + ': ' + (error?.message || t('settings.messages.unknownError')),
            type: 'error'
          });
        } finally {
          setIsSaving(false);
        }
      },
      {
        title: t('settings.messages.resetTitle'),
        confirmText: t('settings.messages.resetConfirmBtn'),
        cancelText: t('settings.messages.resetCancelBtn'),
        variant: 'warning',
      }
    );
  };

  const handleFieldChange = (key: string, value: any, oauthConnected = settings?.openai_oauth_connected) => {
    if (value === 'codex' && ['ai_provider_format', 'text_model_source', 'image_model_source', 'image_caption_model_source'].includes(key) && !oauthConnected) {
      pendingCodexSelection.current = () => handleFieldChange(key, value, true);
      setOauthDialogOpen(true);
      return;
    }
    setFormData(prev => {
      const next = { ...prev, [key]: value };

      // Per-model source key → its API base URL field, for stale-default replacement
      const perModelBaseKeys: Record<string, string> = {
        text_model_source: 'text_api_base_url',
        image_model_source: 'image_api_base_url',
        image_caption_model_source: 'image_caption_api_base_url',
      };

      if (key === 'ai_provider_format') {
        if (value === 'volcengine') {
          // Agent Plans requires dedicated endpoint
          // Preserve custom user Base URL
          if (KNOWN_DEFAULT_BASE_URLS.has(next.api_base_url)) {
            next.api_base_url = VOLCENGINE_AGENTPLANS_BASE_URL;
          }
        } else if (VOLCENGINE_DEFAULT_BASE_URLS.has(next.api_base_url)) {
          // Reset stale plan/v3 endpoint when leaving Agent Plans
          // Fall back to environment defaults
          next.api_base_url = '';
        }
      } else if (perModelBaseKeys[key]) {
        const baseKey = perModelBaseKeys[key];
        if (value === 'volcengine') {
          // Replace stale endpoint for single model
          // Model API base takes precedence
          if (KNOWN_DEFAULT_BASE_URLS.has(next[baseKey])) {
            next[baseKey] = VOLCENGINE_AGENTPLANS_BASE_URL;
          }
        } else if (VOLCENGINE_DEFAULT_BASE_URLS.has(next[baseKey])) {
          // Clear stale plan/v3 endpoint
          // Model API base precedence check
          next[baseKey] = '';
        }
      }

      return next;
    });
  };

  const applyVolcengineRecommendedModels = () => {
    const isAgentPlans = formData.ai_provider_format === 'volcengine';
    const provider = isAgentPlans ? 'volcengine' : 'doubao';
    const models = isAgentPlans ? VOLCENGINE_AGENTPLANS_RECOMMENDED_MODELS : VOLCENGINE_MODELARK_RECOMMENDED_MODELS;
    setFormData(prev => {
      // Agent Plans endpoint replacement
      // Prevent hitting hardcoded cn-beijing address
      const agentPlansBaseOrDefault = (current: string) =>
        KNOWN_DEFAULT_BASE_URLS.has(current) ? VOLCENGINE_AGENTPLANS_BASE_URL : current;
      // Per-model inherits global endpoint when empty
      // Resolution priority check
      const resolvedGlobalBase = agentPlansBaseOrDefault(prev.api_base_url);
      const perModelBase = (current: string) =>
        KNOWN_DEFAULT_BASE_URLS.has(current) ? resolvedGlobalBase : current;
      return {
        ...prev,
        text_model: models.text,
        image_caption_model: models.caption,
        image_model: models.image,
        text_model_source: provider,
        image_caption_model_source: provider,
        image_model_source: provider,
        api_base_url: isAgentPlans ? agentPlansBaseOrDefault(prev.api_base_url) : prev.api_base_url,
        // Per-model base replaces stale defaults
        text_api_base_url: isAgentPlans ? perModelBase(prev.text_api_base_url) : prev.text_api_base_url,
        image_caption_api_base_url: isAgentPlans ? perModelBase(prev.image_caption_api_base_url) : prev.image_caption_api_base_url,
        image_api_base_url: isAgentPlans ? perModelBase(prev.image_api_base_url) : prev.image_api_base_url,
        openai_image_api_protocol: 'images',
      };
    });
  };

  const selectVolcenginePlan = () => {
    handleFieldChange('ai_provider_format', 'volcengine');
  };

  const selectGlobalProvider = (provider: string, oauthConnected = settings?.openai_oauth_connected) => {
    handleFieldChange('ai_provider_format', provider, oauthConnected);
  };

  const isVolcenginePlanActive = formData.ai_provider_format === 'volcengine';

  const providerPromotions = [
    {
      key: 'volcengine',
      testId: 'provider-plan-volcengine',
      active: isVolcenginePlanActive,
      name: t('settings.providerComparison.volcengine.name'),
      tagline: t('settings.providerComparison.volcengine.tagline'),
      suitedFor: t('settings.providerComparison.volcengine.suitedFor'),
      points: [
        t('settings.providerComparison.volcengine.point1'),
        t('settings.providerComparison.volcengine.point2'),
        t('settings.providerComparison.volcengine.point3'),
      ],
      cta: t('settings.providerComparison.volcengine.cta'),
      activeLabel: t('settings.providerComparison.volcengine.active'),
      note: t('settings.providerComparison.volcengine.note'),
      onSelect: selectVolcenginePlan,
      href: volcengineAgentPlansUrl,
      linkLabel: t('settings.providerComparison.volcengine.link'),
    },
  ];

  const updateServiceTest = (key: string, nextState: ServiceTestState) => {
    setServiceTestStates(prev => ({ ...prev, [key]: nextState }));
  };

  const handleServiceTest = async (
    key: string,
    action: (settings?: any) => Promise<any>,
    formatDetail: (data: any) => string
  ) => {
    updateServiceTest(key, { status: 'loading' });
    try {
      // Prepare settings for test
      const testSettings: any = {};

      // Only pass non-empty filled values
      if (formData.api_key) testSettings.api_key = formData.api_key;
      if (formData.api_base_url) testSettings.api_base_url = formData.api_base_url;
      if (formData.ai_provider_format) {
        testSettings.ai_provider_format = formData.ai_provider_format;
      }
      // If lazyllm vendor selected, supply its key
      const activeLazyKey = formData.lazyllm_api_keys?.[formData.ai_provider_format];
      if (activeLazyKey) {
        testSettings.api_key = activeLazyKey;
      }
      if (formData.lazyllm_api_keys && Object.keys(formData.lazyllm_api_keys).length > 0) {
        testSettings.lazyllm_api_keys = formData.lazyllm_api_keys;
      }
      if (formData.text_model) testSettings.text_model = formData.text_model;
      if (formData.image_model) testSettings.image_model = formData.image_model;
      if (formData.image_caption_model) testSettings.image_caption_model = formData.image_caption_model;
      if (formData.mineru_api_base) testSettings.mineru_api_base = formData.mineru_api_base;
      if (formData.mineru_token) testSettings.mineru_token = formData.mineru_token;
      if (formData.baidu_api_key) testSettings.baidu_api_key = formData.baidu_api_key;
      if (formData.image_resolution) testSettings.image_resolution = formData.image_resolution;
      if (formData.image_quality) testSettings.image_quality = formData.image_quality;

      // Per-model provider source overrides (always send, even empty, to clear saved values)
      testSettings.text_model_source = formData.text_model_source || '';
      testSettings.image_model_source = formData.image_model_source || '';
      testSettings.image_caption_model_source = formData.image_caption_model_source || '';

      // Per-model API credentials
      if (formData.text_api_key) testSettings.text_api_key = formData.text_api_key;
      if (formData.text_api_base_url) testSettings.text_api_base_url = formData.text_api_base_url;
      if (formData.image_api_key) testSettings.image_api_key = formData.image_api_key;
      if (formData.image_api_base_url) testSettings.image_api_base_url = formData.image_api_base_url;
      if (formData.image_caption_api_key) testSettings.image_caption_api_key = formData.image_caption_api_key;
      if (formData.image_caption_api_base_url) testSettings.image_caption_api_base_url = formData.image_caption_api_base_url;

      // Reasoning mode settings
      if (formData.enable_text_reasoning !== undefined) {
        testSettings.enable_text_reasoning = formData.enable_text_reasoning;
      }
      testSettings.text_max_output_tokens = formData.text_max_output_tokens;
      if (formData.text_thinking_budget !== undefined) {
        testSettings.text_thinking_budget = formData.text_thinking_budget;
      }
      if (formData.enable_image_reasoning !== undefined) {
        testSettings.enable_image_reasoning = formData.enable_image_reasoning;
      }
      if (formData.image_thinking_budget !== undefined) {
        testSettings.image_thinking_budget = formData.image_thinking_budget;
      }

      // Start async test and get task ID
      const response = await action(testSettings);
      const taskId = response.data.task_id;

      // isActive tracks whether this test round is still pending — avoids stale closure
      let isActive = true;
      // eslint-disable-next-line prefer-const
      let pollInterval: ReturnType<typeof setInterval>;
      const finish = (nextState: ServiceTestState, toastMsg: string, toastType: 'success' | 'error') => {
        if (!isActive) return;
        isActive = false;
        clearInterval(pollInterval);
        updateServiceTest(key, nextState);
        show({ message: toastMsg, type: toastType });
      };

      // Start polling task status
      pollInterval = setInterval(async () => {
        try {
          const statusResponse = await api.getTestStatus(taskId);
          const statusData = statusResponse?.data;
          if (!statusData) {
            throw new Error(t('settings.serviceTest.testFailed'));
          }
          const taskStatus = statusData.status;

          if (taskStatus === 'COMPLETED') {
            const detail = formatDetail(statusData.result || {});
            const message = statusData.message || t('settings.messages.testSuccess');
            finish({ status: 'success', message, detail }, message, 'success');
          } else if (taskStatus === 'FAILED') {
            const errorMessage = statusData.error || t('settings.serviceTest.testFailed');
            if (statusData.openai_oauth_disconnected) {
              markOpenAIOAuthDisconnected();
            }
            finish({ status: 'error', message: errorMessage }, `${t('settings.serviceTest.testFailed')}: ${errorMessage}`, 'error');
          }
          // Continue polling if PENDING or PROCESSING
        } catch (pollError: any) {
          const errorMessage = pollError?.response?.data?.error?.message || pollError?.message || t('settings.serviceTest.testFailed');
          finish({ status: 'error', message: errorMessage }, `${t('settings.serviceTest.testFailed')}: ${errorMessage}`, 'error');
        }
      }, 2000); // Poll every 2 seconds

      // Set max polling timeout
      setTimeout(() => {
        finish({ status: 'error', message: t('settings.serviceTest.testTimeout') }, t('settings.serviceTest.testTimeout'), 'error');
      }, 600000); // 10 minutes timeout for slow models

    } catch (error: any) {
      const errorMessage = error?.response?.data?.error?.message || error?.message || t('common.unknownError');
      updateServiceTest(key, { status: 'error', message: errorMessage });
      show({ message: `${t('settings.serviceTest.testFailed')}: ${errorMessage}`, type: 'error' });
    }
  };

  const TEST_CONFIGS: Record<string, {
    key: string;
    action: (settings?: any) => Promise<any>;
    formatDetail: (data: any) => string;
  }> = {
    'baidu-ocr': {
      key: 'baidu-ocr',
      action: api.testBaiduOcr,
      formatDetail: (data: any) => (data?.recognized_text ? t('settings.serviceTest.results.recognizedText', { text: data.recognized_text }) : ''),
    },
    'text-model': {
      key: 'text-model',
      action: api.testTextModel,
      formatDetail: (data: any) => (data?.reply ? t('settings.serviceTest.results.modelReply', { reply: data.reply }) : ''),
    },
    'caption-model': {
      key: 'caption-model',
      action: api.testCaptionModel,
      formatDetail: (data: any) => (data?.caption ? t('settings.serviceTest.results.captionDesc', { caption: data.caption }) : ''),
    },
    'baidu-inpaint': {
      key: 'baidu-inpaint',
      action: api.testBaiduInpaint,
      formatDetail: (data: any) => (data?.image_size ? t('settings.serviceTest.results.imageSize', { width: data.image_size[0], height: data.image_size[1] }) : ''),
    },
    'image-model': {
      key: 'image-model',
      action: api.testImageModel,
      formatDetail: (data: any) => (data?.image_size ? t('settings.serviceTest.results.imageSize', { width: data.image_size[0], height: data.image_size[1] }) : ''),
    },
    'mineru-pdf': {
      key: 'mineru-pdf',
      action: api.testMineruPdf,
      formatDetail: (data: any) => (data?.content_preview ? t('settings.serviceTest.results.parsePreview', { preview: data.content_preview }) : data?.message || ''),
    },
  };

  const triggerTest = (testKey: string) => {
    const config = TEST_CONFIGS[testKey];
    if (config) {
      handleServiceTest(config.key, config.action, config.formatDetail);
    }
  };

  const dismissTest = (testKey: string) => {
    updateServiceTest(testKey, { status: 'idle' });
  };

  const renderField = (field: FieldConfig) => <SettingsField
    key={field.key} field={field} value={formData[field.key] as string | number | boolean}
    placeholder={field.sensitiveField && settings && field.lengthKey && (settings[field.lengthKey] as number) > 0
      ? t('settings.fields.apiKeySet', { length: settings[field.lengthKey] as number }) : field.placeholder || ''}
    isDisabled={(field.key === 'text_thinking_budget' && !formData.enable_text_reasoning)
      || (field.key === 'image_thinking_budget' && !formData.enable_image_reasoning)}
    onChange={value => handleFieldChange(field.key, value)} t={t}
  />;

  // Model configuration item definitions
  const modelConfigItems = [
    {
      modelKey: 'text_model' as keyof typeof initialFormData,
      sourceKey: 'text_model_source' as keyof typeof initialFormData,
      apiKeyKey: 'text_api_key' as keyof typeof initialFormData,
      apiBaseKey: 'text_api_base_url' as keyof typeof initialFormData,
      apiKeyLengthKey: 'text_api_key_length' as keyof SettingsType,
      label: t('settings.fields.textModel'),
      placeholder: t('settings.fields.textModelPlaceholder'),
      description: t('settings.fields.textModelDesc'),
      sourceLabel: t('settings.fields.textModelSource'),
    },
    {
      modelKey: 'image_model' as keyof typeof initialFormData,
      sourceKey: 'image_model_source' as keyof typeof initialFormData,
      apiKeyKey: 'image_api_key' as keyof typeof initialFormData,
      apiBaseKey: 'image_api_base_url' as keyof typeof initialFormData,
      apiKeyLengthKey: 'image_api_key_length' as keyof SettingsType,
      label: t('settings.fields.imageModel'),
      placeholder: t('settings.fields.imageModelPlaceholder'),
      description: t('settings.fields.imageModelDesc'),
      sourceLabel: t('settings.fields.imageModelSource'),
    },
    {
      modelKey: 'image_caption_model' as keyof typeof initialFormData,
      sourceKey: 'image_caption_model_source' as keyof typeof initialFormData,
      apiKeyKey: 'image_caption_api_key' as keyof typeof initialFormData,
      apiBaseKey: 'image_caption_api_base_url' as keyof typeof initialFormData,
      apiKeyLengthKey: 'image_caption_api_key_length' as keyof SettingsType,
      label: t('settings.fields.imageCaptionModel'),
      placeholder: t('settings.fields.imageCaptionModelPlaceholder'),
      description: t('settings.fields.imageCaptionModelDesc'),
      sourceLabel: t('settings.fields.imageCaptionModelSource'),
    },
  ];

  // Render single model configuration group
  const renderModelConfigGroup = (item: typeof modelConfigItems[0]) => {
    const sourceValue = formData[item.sourceKey] as string;
    const isApiKeyProvider = API_KEY_PROVIDERS.has(sourceValue);
    const isLazyllm = sourceValue && isLazyllmVendor(sourceValue);
    // Image generation options: the images/chat protocol only applies to
    // OpenAI-compatible HTTP providers, while the quality tier also applies to
    // Codex (OAuth), which builds its own image_generation request.
    const imageProviderValue = sourceValue || formData.ai_provider_format;
    const isOpenAiCompatibleImageSource = item.sourceKey === 'image_model_source'
      && (imageProviderValue === 'openai' || imageProviderValue === 'volcengine');
    const isCodexImageSource = item.sourceKey === 'image_model_source'
      && imageProviderValue === 'codex';
    const showsQualityTier = (isOpenAiCompatibleImageSource || isCodexImageSource)
      && GPT_IMAGE_MODEL_PATTERN.test(formData.image_model || '');
    // 'openai' in source dropdown means OpenAI format (API key provider), not lazyllm openai vendor
    // lazyllm openai vendor is handled separately

    return (
      <div key={item.modelKey} className="pb-6 border-b border-gray-200 dark:border-border-primary last:border-b-0 last:pb-0 space-y-3">
        {/* Model name */}
        <Input
          label={item.label}
          type="text"
          placeholder={item.placeholder}
          value={formData[item.modelKey] as string}
          onChange={(e) => handleFieldChange(item.modelKey, e.target.value)}
        />
        {item.description && (
          <p className="-mt-1 text-sm text-gray-500 dark:text-foreground-tertiary">{item.description}</p>
        )}

        {/* Provider selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-foreground-secondary mb-2">
            {item.sourceLabel}
          </label>
          <select
            data-testid={`${String(item.sourceKey)}-select`}
            value={sourceValue}
            onChange={(e) => handleFieldChange(item.sourceKey, e.target.value)}
            className="w-full h-10 px-4 rounded-lg border border-gray-200 dark:border-border-primary bg-white dark:bg-background-secondary focus:outline-none focus:ring-2 focus:ring-banana-500 focus:border-transparent"
          >
            <option value="">{t('settings.fields.modelProviderPlaceholder')}</option>
            {allProviderSources
              .filter(option =>
                item.sourceKey !== 'image_model_source'
                || isImageModelSourceSelectable(option.value)
              )
              .map((option) => (
                <option
                  key={option.value}
                  value={option.value}
                >
                  {option.label}{option.value === 'codex' && !settings?.openai_oauth_connected ? ` (${t('settings.openaiOAuth.disconnected')})` : ''}
                </option>
              ))
              .concat(
                // A previously saved image source may no longer be selectable
                // (vendor without image capability). Keep it visible so users
                // can see the current value instead of a silently-empty
                // dropdown that would round-trip the stale value on save.
                item.sourceKey === 'image_model_source'
                && formData.image_model_source
                && (
                  !allProviderSources.some(o => o.value === formData.image_model_source)
                  || !isImageModelSourceSelectable(formData.image_model_source)
                )
                  ? [(
                    <option key={formData.image_model_source} value={formData.image_model_source}>
                      {LAZYLLM_SOURCES.find(s => s.value === formData.image_model_source)?.label || formData.image_model_source} ({t('settings.fields.imageSourceUnavailable')})
                    </option>
                  )]
                  : []
              )}
          </select>
          <p className="mt-1 text-sm text-gray-500 dark:text-foreground-tertiary">
            {t('settings.fields.modelProviderDesc')}
          </p>
          {item.sourceKey === 'image_model_source' && sourceValue === 'sensenova' && (
            <p data-testid="sensenova-image-model-hint" className="mt-1 text-xs text-amber-700 dark:text-amber-300">
              {t('settings.fields.sensenovaImageHint')}
            </p>
          )}
        </div>

        {/* Gemini/OpenAI/Volcengine provider: API Key + Base URL */}
        {isApiKeyProvider && (
          <div className="space-y-3 pl-3 border-l-2 border-banana-300 dark:border-banana-600">
            <Input
              label={t('settings.fields.perModelApiBaseUrl')}
              type="text"
              placeholder={t('settings.fields.perModelApiBaseUrlPlaceholder')}
              value={formData[item.apiBaseKey] as string}
              onChange={(e) => handleFieldChange(item.apiBaseKey, e.target.value)}
            />
            <div>
              <Input
                label={t('settings.fields.perModelApiKey')}
                type="password"
                placeholder={
                  settings && (settings[item.apiKeyLengthKey] as number) > 0
                    ? t('settings.fields.perModelApiKeySet', { length: settings[item.apiKeyLengthKey] as number })
                    : t('settings.fields.perModelApiKeyPlaceholder')
                }
                value={formData[item.apiKeyKey] as string}
                onChange={(e) => handleFieldChange(item.apiKeyKey, e.target.value)}
              />
              <p className="mt-1 text-sm text-gray-500 dark:text-foreground-tertiary">
                {t('settings.fields.perModelApiKeyDesc')}
              </p>
            </div>
          </div>
        )}

        {/* Image request options for the effective image provider */}
        {(isOpenAiCompatibleImageSource || isCodexImageSource) && (
          <>
            {/* Image API Protocol: OpenAI-compatible HTTP endpoints only */}
            {isOpenAiCompatibleImageSource && (
              <div className="pl-3 border-l-2 border-banana-300 dark:border-banana-600">
                <label className="block text-sm font-medium text-gray-700 dark:text-foreground-secondary mb-2">
                  {t('settings.fields.imageApiProtocol')}
                </label>
                <select
                  data-testid="openai-image-api-protocol-select"
                  value={formData.openai_image_api_protocol}
                  onChange={(e) => handleFieldChange('openai_image_api_protocol', e.target.value)}
                  className="w-full h-10 px-4 rounded-lg border border-gray-200 dark:border-border-primary bg-white dark:bg-background-secondary focus:outline-none focus:ring-2 focus:ring-banana-500 focus:border-transparent"
                >
                  <option value="auto">{t('settings.fields.imageApiProtocolAuto')}</option>
                  <option value="images">{t('settings.fields.imageApiProtocolImages')}</option>
                  <option value="chat">{t('settings.fields.imageApiProtocolChat')}</option>
                </select>
                <p className="mt-1 text-sm text-gray-500 dark:text-foreground-tertiary">
                  {t('settings.fields.imageApiProtocolDesc')}
                </p>
              </div>
            )}

            {/* Quality tier: only GPT Image models accept this parameter, so hide
                the control for Seedream and other models where it has no effect. */}
            {showsQualityTier && (
              <div className="pl-3 border-l-2 border-banana-300 dark:border-banana-600">
                <label className="block text-sm font-medium text-gray-700 dark:text-foreground-secondary mb-2">
                  {t('settings.fields.imageQuality')}
                </label>
                <select
                  data-testid="openai-image-quality-select"
                  value={formData.image_quality}
                  onChange={(e) => handleFieldChange('image_quality', e.target.value)}
                  className="w-full h-10 px-4 rounded-lg border border-gray-200 dark:border-border-primary bg-white dark:bg-background-secondary focus:outline-none focus:ring-2 focus:ring-banana-500 focus:border-transparent"
                >
                  <option value="auto">{t('settings.fields.imageQualityAuto')}</option>
                  <option value="low">{t('settings.fields.imageQualityLow')}</option>
                  <option value="medium">{t('settings.fields.imageQualityMedium')}</option>
                  <option value="high">{t('settings.fields.imageQualityHigh')}</option>
                  <option value="xhigh">{t('settings.fields.imageQualityXhigh')}</option>
                  <option value="max">{t('settings.fields.imageQualityMax')}</option>
                </select>
                <p className="mt-1 text-sm text-gray-500 dark:text-foreground-tertiary">
                  {t('settings.fields.imageQualityDesc')}
                </p>
              </div>
            )}
          </>
        )}

        {/* LazyLLM vendor: Vendor API Key */}
        {isLazyllm && (() => {
          const vendorLabel = LAZYLLM_SOURCES.find(s => s.value === sourceValue)?.label || sourceValue.toUpperCase();
          const keyLength = settings?.lazyllm_api_keys_info?.[sourceValue] || 0;
          const placeholder = keyLength > 0
            ? t('settings.fields.vendorApiKeySet', { length: keyLength })
            : t('settings.fields.vendorApiKeyPlaceholder', { vendor: vendorLabel });
          return (
            <div className="pl-3 border-l-2 border-amber-300 dark:border-amber-600">
              <Input
                label={t('settings.fields.vendorApiKey', { vendor: vendorLabel })}
                type="password"
                placeholder={placeholder}
                value={formData.lazyllm_api_keys[sourceValue] || ''}
                onChange={(e) => {
                  setFormData(prev => ({
                    ...prev,
                    lazyllm_api_keys: { ...prev.lazyllm_api_keys, [sourceValue]: e.target.value }
                  }));
                }}
              />
              <p className="mt-1 text-sm text-gray-500 dark:text-foreground-tertiary">
                {t('settings.fields.vendorApiKeyDesc')}
              </p>
            </div>
          );
        })()}
      </div>
    );
  };

  const oauthPanel = (<>
              {/* OpenAI OAuth connection block */}
              <div>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-foreground-primary mb-1 flex items-center">
                  <Link2 size={20} />
                  <span className="ml-2">{t('settings.openaiOAuth.title')}</span>
                </h2>
                <p className="text-sm text-gray-500 dark:text-foreground-tertiary mb-4">{t('settings.openaiOAuth.description')}</p>
                <div className="p-4 border border-gray-200 dark:border-border-primary rounded-lg">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`w-2.5 h-2.5 rounded-full ${settings?.openai_oauth_connected ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'}`} />
                      <div>
                        <span className="text-sm font-medium text-gray-700 dark:text-foreground-secondary">
                          {settings?.openai_oauth_connected ? t('settings.openaiOAuth.connected') : t('settings.openaiOAuth.disconnected')}
                        </span>
                        {settings?.openai_oauth_connected && settings?.openai_oauth_account_id && (
                          <span className="ml-2 text-sm text-gray-500 dark:text-foreground-tertiary">
                            ({settings.openai_oauth_account_id})
                          </span>
                        )}
                      </div>
                    </div>
                    <div>
                      {settings?.openai_oauth_connected ? (
                        <button
                          onClick={handleOAuthDisconnect}
                          className="px-4 py-2 text-sm font-medium text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
                        >
                          {t('settings.openaiOAuth.disconnectBtn')}
                        </button>
                      ) : (
                        <button
                          onClick={handleOAuthLogin}
                          disabled={oauthConnecting}
                          className="px-4 py-2 text-sm font-medium text-white bg-gray-900 dark:bg-white dark:text-gray-900 rounded-lg hover:bg-gray-800 dark:hover:bg-gray-100 transition-colors disabled:opacity-50"
                        >
                          {oauthConnecting ? t('settings.openaiOAuth.connecting') : t('settings.openaiOAuth.loginBtn')}
                        </button>
                      )}
                    </div>
                  </div>
                  <p className="mt-3 text-xs text-gray-500 dark:text-foreground-tertiary">{t('settings.openaiOAuth.hint')}</p>
                  {!settings?.openai_oauth_connected && (
                    <div className="mt-3">
                      <button
                        onClick={() => setManualCallbackOpen(v => !v)}
                        className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                      >
                        {t('settings.openaiOAuth.manualCallbackLabel')}
                      </button>
                      {manualCallbackOpen && (
                        <div className="mt-2 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
                          <p className="text-xs text-amber-700 dark:text-amber-300 mb-2">{t('settings.openaiOAuth.manualCallbackHint')}</p>
                          <div className="flex gap-2">
                            <input
                              type="text"
                              value={manualCallbackUrl}
                              onChange={(e) => setManualCallbackUrl(e.target.value)}
                              placeholder={t('settings.openaiOAuth.manualCallbackPlaceholder')}
                              className="flex-1 px-3 py-1.5 text-xs border border-gray-300 dark:border-border-primary rounded-md bg-white dark:bg-background-secondary text-gray-900 dark:text-foreground-primary placeholder-gray-400"
                            />
                            <button
                              onClick={handleManualCallback}
                              disabled={manualCallbackSubmitting || !manualCallbackUrl.trim()}
                              className="px-3 py-1.5 text-xs font-medium text-white bg-gray-900 dark:bg-white dark:text-gray-900 rounded-md hover:bg-gray-800 dark:hover:bg-gray-100 transition-colors disabled:opacity-50"
                            >
                              {t('settings.openaiOAuth.manualCallbackSubmit')}
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>

  </>);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loading message={t('common.loading')} />
      </div>
    );
  }

  return (
    <>
      <ToastContainer />
      {ConfirmDialog}
      <Modal isOpen={oauthDialogOpen} title={t('settings.openaiOAuth.title')} onClose={() => {
        pendingCodexSelection.current = null;
        stopOAuthMonitor();
        oauthPopupRef.current?.close();
        setOauthConnecting(false);
        setOauthDialogOpen(false);
      }}>
        {oauthPanel}
      </Modal>
      <div className="space-y-8">
        {/* Quick Guide Banner */}
        <div className="rounded-xl border border-banana-200 bg-banana-50/80 p-4 dark:border-banana-800/60 dark:bg-banana-950/20">
          <div className="flex items-start gap-3">
            <div className="rounded-lg bg-banana-400/20 p-2 text-banana-700 dark:bg-banana-400/10 dark:text-banana-300 shrink-0 mt-0.5">
              <Sparkles size={20} />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-foreground-primary">
                {isVi ? 'Hướng dẫn cấu hình nhanh' : 'Quick Configuration Guide'}
              </h3>
              <p className="mt-1 text-xs text-gray-700 dark:text-foreground-secondary leading-relaxed">
                {isVi
                  ? 'Để tạo slide, bạn chỉ cần chọn 1 Nhà cung cấp AI (khuyên dùng Google Gemini vì có gói miễn phí và tạo được cả văn bản lẫn hình ảnh) và điền API Key tương ứng. Các dịch vụ bổ trợ bên dưới (MinerU, Baidu OCR, ElevenLabs) là tùy chọn nâng cao không bắt buộc.'
                  : 'To generate slides, you only need to configure 1 AI Provider (Google Gemini is recommended with its free tier and text + image support) and enter its API key. Auxiliary services below (MinerU, Baidu OCR, ElevenLabs) are optional.'}
              </p>
            </div>
          </div>
        </div>

        {/* AI Provider & Active Key Form Section */}
        <div data-testid="global-api-config-section" className="space-y-4">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-foreground-primary mb-1 flex items-center">
              <Key size={20} />
              <span className="ml-2">{isVi ? 'Nhà cung cấp AI & API Key' : 'AI Provider & API Key'}</span>
            </h2>
            <p className="text-sm text-gray-500 dark:text-foreground-tertiary">
              {isVi
                ? 'Chọn nhà cung cấp AI bạn muốn sử dụng (qua dropdown hoặc tab) để hiển thị form điền key tương ứng.'
                : 'Select the AI provider you want to use (via dropdown or tabs) to display its credential form.'}
            </p>
          </div>

          {/* Provider Selector (Dropdown + Tabs) */}
          <SettingsProviderPicker
            label={t('settings.fields.aiProviderFormat')}
            globalProviderSources={globalProviderSources.map(option => ({
              ...option,
              hint: option.value === 'volcengine' ? t('settings.volcenginePromo.providerHint') : null,
            }))}
            selectedGlobalProvider={selectedGlobalProvider}
            providerPromotions={providerPromotions}
            selectGlobalProvider={selectGlobalProvider}
            disabledLabel={t('settings.openaiOAuth.disconnected')}
            isVi={isVi}
          />

          {/* Form điền Key của riêng Provider được chọn */}
          <SettingsActiveProviderForm
            provider={formData.ai_provider_format}
            formData={formData}
            setFormData={setFormData}
            settings={settings}
            handleFieldChange={handleFieldChange}
            t={t}
            isVi={isVi}
            oauthConnecting={oauthConnecting}
            handleOAuthLogin={handleOAuthLogin}
            handleOAuthDisconnect={handleOAuthDisconnect}
            manualCallbackOpen={manualCallbackOpen}
            setManualCallbackOpen={setManualCallbackOpen}
            manualCallbackUrl={manualCallbackUrl}
            setManualCallbackUrl={setManualCallbackUrl}
            manualCallbackSubmitting={manualCallbackSubmitting}
            handleManualCallback={handleManualCallback}
            applyVolcengineRecommendedModels={applyVolcengineRecommendedModels}
            volcengineAgentPlansUrl={volcengineAgentPlansUrl}
            volcengineLogoUrl={volcengineLogoUrl}
            copyToClipboard={copyToClipboard}
            serviceTestStates={serviceTestStates}
            triggerTest={triggerTest}
            dismissTest={dismissTest}
          />
        </div>

        {/* Model config block */}
        <SettingsModelConfigSection
          modelConfigItems={modelConfigItems}
          renderModelConfigGroup={renderModelConfigGroup}
          formData={formData}
          isVi={isVi}
          t={t}
          serviceTestStates={serviceTestStates}
          triggerTest={triggerTest}
          dismissTest={dismissTest}
        />

        {/* General & Output Config */}
        <div className="space-y-6">
          {settingsSections.filter((section) =>
            section.title === t('settings.sections.imageConfig') ||
            section.title === t('settings.sections.outputLanguage')
          ).map((section) => (
            <div key={section.title}>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-foreground-primary mb-3 flex items-center">
                {section.icon}
                <span className="ml-2">{section.title}</span>
              </h2>
              <div className="space-y-4">
                {section.fields.map((field) => renderField(field))}
              </div>
            </div>
          ))}
        </div>

        {/* Auxiliary Services (Optional - Not required for slides) */}
        <div className="rounded-xl border border-gray-200 bg-gray-50/60 p-5 dark:border-border-primary dark:bg-background-secondary/50 space-y-6">
          <div>
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-foreground-primary flex items-center">
                <Layers size={20} className="text-gray-500" />
                <span className="ml-2">{isVi ? 'Dịch vụ bổ trợ (Tùy chọn)' : 'Auxiliary Services (Optional)'}</span>
              </h2>
              <span className="text-xs px-2.5 py-0.5 rounded-full font-medium bg-gray-200/70 text-gray-600 dark:bg-gray-800 dark:text-gray-300">
                {isVi ? 'Không bắt buộc' : 'Optional'}
              </span>
            </div>
            <p className="text-xs text-gray-500 dark:text-foreground-tertiary mt-1">
              {isVi
                ? 'Các dịch vụ chuyên biệt cho việc phân tích tài liệu PDF phức tạp (MinerU), nhận diện chữ trong ảnh (Baidu OCR) và thuyết minh âm thanh (ElevenLabs). Hoàn toàn không bắt buộc đối với việc tạo slide thông thường.'
                : 'Specialized services for complex PDF parsing (MinerU), OCR text recognition (Baidu OCR), and voice narration (ElevenLabs). Not required for standard slide generation.'}
            </p>
          </div>

          <div className="space-y-6 pt-2 border-t border-gray-200/80 dark:border-border-primary/80">
            {settingsSections.filter((section) =>
              section.title === t('settings.sections.mineruConfig') ||
              section.title === t('settings.sections.baiduOcr') ||
              section.title === t('settings.sections.elevenlabs')
            ).map((section) => (
              <div key={section.title} className="bg-white dark:bg-background-secondary p-4 rounded-lg border border-gray-200/60 dark:border-border-primary/60">
                <h3 className="text-base font-medium text-gray-800 dark:text-foreground-primary mb-3 flex items-center">
                  {section.icon}
                  <span className="ml-2">{section.title}</span>
                </h3>
                <div className="space-y-4">
                  {section.fields.map((field) => renderField(field))}
                </div>

                {/* Inline Service Test for MinerU */}
                {section.title === t('settings.sections.mineruConfig') && (
                  <div className="pt-3 mt-4 border-t border-gray-100 dark:border-border-primary/60">
                    <SettingsInlineServiceTest
                      testKey="mineru-pdf"
                      label={isVi ? 'Kiểm tra phân tích PDF MinerU' : 'Test MinerU PDF Parsing'}
                      description={t('settings.serviceTest.tests.mineruPdf.description')}
                      icon={<FileText size={13} />}
                      testState={serviceTestStates['mineru-pdf']}
                      onTest={() => triggerTest('mineru-pdf')}
                      onDismiss={() => dismissTest('mineru-pdf')}
                      isVi={isVi}
                      disabled={!formData.mineru_token && !settings?.mineru_token_length}
                      disabledReason={isVi ? 'Chưa cấu hình MinerU token' : 'MinerU token not set'}
                    />
                  </div>
                )}

                {/* Inline Service Tests for Baidu OCR & Inpainting */}
                {section.title === t('settings.sections.baiduOcr') && (
                  <div className="pt-3 mt-4 border-t border-gray-100 dark:border-border-primary/60 space-y-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <SettingsInlineServiceTest
                        testKey="baidu-ocr"
                        label={isVi ? 'Kiểm tra Baidu OCR' : 'Test Baidu OCR'}
                        description={t('settings.serviceTest.tests.baiduOcr.description')}
                        icon={<FileText size={13} />}
                        testState={serviceTestStates['baidu-ocr']}
                        onTest={() => triggerTest('baidu-ocr')}
                        onDismiss={() => dismissTest('baidu-ocr')}
                        isVi={isVi}
                        disabled={!formData.baidu_api_key && !settings?.baidu_api_key_length}
                        disabledReason={isVi ? 'Chưa cấu hình Baidu API Key' : 'Baidu API Key not set'}
                      />
                      <SettingsInlineServiceTest
                        testKey="baidu-inpaint"
                        label={isVi ? 'Kiểm tra vá ảnh Baidu' : 'Test Baidu Inpaint'}
                        description={t('settings.serviceTest.tests.baiduInpaint.description')}
                        icon={<Image size={13} />}
                        testState={serviceTestStates['baidu-inpaint']}
                        onTest={() => triggerTest('baidu-inpaint')}
                        onDismiss={() => dismissTest('baidu-inpaint')}
                        isVi={isVi}
                        disabled={!formData.baidu_api_key && !settings?.baidu_api_key_length}
                        disabledReason={isVi ? 'Chưa cấu hình Baidu API Key' : 'Baidu API Key not set'}
                      />
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Advanced settings (collapsible) */}
        <SettingsAdvanced open={advancedOpen} onToggle={() => setAdvancedOpen(!advancedOpen)} label={t('settings.sections.advancedSettings')}>
              {isDesktop && <DataStorageSettings />}

              {!oauthDialogOpen && oauthPanel}

              {/* Performance + reasoning mode */}
              {settingsSections.filter((section) =>
                section.title === t('settings.sections.performanceConfig') ||
                section.title === t('settings.sections.textReasoning') ||
                section.title === t('settings.sections.imageReasoning')
              ).map((section) => (
                <div key={section.title}>
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-foreground-primary mb-4 flex items-center">
                    {section.icon}
                    <span className="ml-2">{section.title}</span>
                  </h2>
                  <div className="space-y-4">
                    {section.fields.map((field) => renderField(field))}
                  </div>
                </div>
              ))}
        </SettingsAdvanced>

        {/* Action buttons */}
        <SettingsActions>
          <Button
            variant="secondary"
            icon={<RotateCcw size={18} />}
            onClick={handleReset}
            disabled={isSaving}
          >
            {t('settings.actions.resetToDefault')}
          </Button>
          <Button
            variant="primary"
            icon={<Save size={18} />}
            onClick={handleSave}
            loading={isSaving}
          >
            {isSaving ? t('settings.actions.saving') : t('settings.actions.save')}
          </Button>
        </SettingsActions>

        <SettingsAbout t={t} />
      </div>
    </>
  );
};

// SettingsPage component - full page wrapper
export const SettingsPage: React.FC = () => <SettingsPageFrame><Settings /></SettingsPageFrame>;