import { SettingsAdvanced, SettingsActions } from '@/components/settings/SettingsLayout';
import { SettingsPageFrame } from '@/components/settings/SettingsPageFrame';
import { SettingsActiveProviderForm } from '@/components/settings/SettingsActiveProviderForm';
import { SettingsField } from '@/components/settings/SettingsField';
import {
  saveClientKeys,
  loadClientKeys,
  getCachedClientConfig,
} from '@/utils/clientKeyStorage';
import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Image, Zap, Save, RotateCcw, Globe, Brain, ArrowUp, ArrowUpRight, Info, RefreshCw, CheckCircle } from 'lucide-react';
import { useT } from '@/hooks/useT';
import { appVersion } from '@/utils/appVersion';
import { isDesktop } from '@/utils';
import { DataStorageSettings } from '@/components/settings/DataStorageSettings';
import type {
  DesktopAutoUpdateSettings,
  DesktopUpdateCheckResult,
  DesktopUpdateElectronApi,
} from '@/types/desktopUpdate';

// Component translations
import { settingsI18n } from '@/components/settings/settingsI18n';
import { Button, Loading, Markdown, Modal, useToast, useConfirm } from '@/components/shared';
import * as api from '@/api/endpoints';
import type { OutputLanguage, UpdateCheckInfo } from '@/api/endpoints';
import { OUTPUT_LANGUAGE_OPTIONS } from '@/api/endpoints';
import type { Settings as SettingsType } from '@/types';
import { useApiKeyReminderStore } from '@/store/useApiKeyReminderStore';

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

const NON_GOOGLE_BASE_URL_HOSTS = [
  'openai.com',
  'openrouter.ai',
  'groq.com',
  'deepseek.com',
  'volces.com',
  'inferera.com',
  'apimart.ai',
  'anthropic.com',
  'siliconflow',
];

const isNonGoogleBaseUrl = (url: string | null | undefined): boolean => {
  if (!url) return false;
  const lower = url.toLowerCase();
  return NON_GOOGLE_BASE_URL_HOSTS.some((host) => lower.includes(host));
};

const isGoogleModelName = (model: string | null | undefined): boolean => {
  if (!model) return false;
  const lower = model.trim().toLowerCase();
  return (
    lower.startsWith('gemini') ||
    lower.startsWith('imagen') ||
    lower.startsWith('gemma') ||
    lower.startsWith('learnlm') ||
    lower.startsWith('models/')
  );
};

const normalizeGoogleModel = (model: string | undefined, fallback: string): string => {
  if (!model || !model.trim()) return '';
  return isGoogleModelName(model) ? model : fallback;
};

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
  enable_image_quality_control: false,
  max_description_workers: 5,
  max_image_workers: 8,
  output_language: 'vi' as OutputLanguage,
  // Reasoning mode configurations
  enable_text_reasoning: false,
  text_max_output_tokens: 32768,
  text_thinking_budget: 1024,
  enable_image_reasoning: false,
  image_thinking_budget: 1024,
  baidu_api_key: '',
  text_model_source: '',
  image_model_source: '',
  image_caption_model_source: '',
  lazyllm_api_keys: {} as Record<string, string>,
  // ElevenLabs TTS
  elevenlabs_api_key: '',
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
        <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-foreground-primary mb-2.5 sm:mb-3 flex items-center">
          <Info size={18} className="sm:w-5 sm:h-5 shrink-0" />
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
            className="w-full sm:w-auto justify-center"
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

const resolveFormBaseUrl = (rawBase: string | null | undefined, effectiveBase: string | undefined): string => {
  if (rawBase !== undefined) {
    return rawBase || '';
  }
  if (!effectiveBase || effectiveBase === 'https://generativelanguage.googleapis.com') {
    return '';
  }
  return effectiveBase;
};

const formDataFromSettings = (data: SettingsType): typeof initialFormData => {
  const wasNonGemini = Boolean(
    data.ai_provider_format && data.ai_provider_format.toLowerCase() !== 'gemini'
  );
  const resolvedBase = resolveFormBaseUrl(data.raw_api_base_url, data.api_base_url);
  const apiBaseUrl = wasNonGemini || isNonGoogleBaseUrl(resolvedBase) ? '' : resolvedBase;

  return {
    ai_provider_format: 'gemini',
    api_base_url: apiBaseUrl,
    api_key: '',
    image_resolution: data.image_resolution || '2K',
    enable_image_quality_control: data.enable_image_quality_control ?? false,
    max_description_workers: data.max_description_workers || 5,
    max_image_workers: data.max_image_workers || 8,
    text_model: normalizeGoogleModel(data.text_model, 'gemini-2.5-flash'),
    image_model: normalizeGoogleModel(data.image_model, 'gemini-3-pro-image-preview'),
    mineru_api_base: data.mineru_api_base || '',
    mineru_token: '',
    image_caption_model: normalizeGoogleModel(data.image_caption_model, 'gemini-2.5-flash'),
    output_language: (data.output_language as OutputLanguage) || 'vi',
    enable_text_reasoning: data.enable_text_reasoning || false,
    text_max_output_tokens: data.text_max_output_tokens ?? 32768,
    text_thinking_budget: data.text_thinking_budget || 1024,
    enable_image_reasoning: data.enable_image_reasoning || false,
    image_thinking_budget: data.image_thinking_budget || 1024,
    baidu_api_key: '',
    text_model_source: '',
    image_model_source: '',
    image_caption_model_source: '',
    lazyllm_api_keys: {},
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

  const [settings, setSettings] = useState<SettingsType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [formData, setFormData] = useState(initialFormData);
  const [storageMode, setStorageMode] = useState<'client' | 'server'>('client');
  const [serviceTestStates, setServiceTestStates] = useState<Record<string, ServiceTestState>>({});
  const [advancedOpen, setAdvancedOpen] = useState(false);

  useEffect(() => {
    if (settings) {
      try {
        sessionStorage.setItem('banana-settings', JSON.stringify(settings));
      } catch (error) {
        console.warn('Failed to persist settings in sessionStorage:', error);
      }
    }
  }, [settings]);

  // Configuration-driven form sections
  const settingsSections: SectionConfig[] = [
    // Global API config & Model config are rendered separately above
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
  ];

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setIsLoading(true);
    try {
      const clientConfig = await loadClientKeys();
      if (clientConfig && clientConfig.storageMode) {
        setStorageMode(clientConfig.storageMode);
      }
      const response = await api.getSettings();
      if (response.data) {
        setSettings(response.data);
        const form = formDataFromSettings(response.data);

        // Restore keys from clientConfig or session cache so inputs are never empty
        const isClientGemini = !clientConfig?.ai_provider_format || clientConfig.ai_provider_format.toLowerCase() === 'gemini';
        if (clientConfig) {
          if (isClientGemini && clientConfig.api_key) form.api_key = clientConfig.api_key;
          if (clientConfig.api_base_url !== undefined && !isNonGoogleBaseUrl(clientConfig.api_base_url)) {
            form.api_base_url = clientConfig.api_base_url;
          }
          if (clientConfig.mineru_token) form.mineru_token = clientConfig.mineru_token;
          if (clientConfig.baidu_api_key) form.baidu_api_key = clientConfig.baidu_api_key;
          if (clientConfig.elevenlabs_api_key) form.elevenlabs_api_key = clientConfig.elevenlabs_api_key;
        }

        try {
          const sessionSaved = sessionStorage.getItem('banana_saved_keys');
          if (sessionSaved) {
            const parsed = JSON.parse(sessionSaved);
            const isSessionGemini = !parsed.ai_provider_format || String(parsed.ai_provider_format).toLowerCase() === 'gemini';
            if (isSessionGemini && !form.api_key && parsed.api_key) form.api_key = parsed.api_key;
            if (parsed.api_base_url !== undefined && !isNonGoogleBaseUrl(parsed.api_base_url) && !form.api_base_url) {
              form.api_base_url = parsed.api_base_url;
            }
            if (!form.mineru_token && parsed.mineru_token) form.mineru_token = parsed.mineru_token;
            if (!form.baidu_api_key && parsed.baidu_api_key) form.baidu_api_key = parsed.baidu_api_key;
            if (!form.elevenlabs_api_key && parsed.elevenlabs_api_key) form.elevenlabs_api_key = parsed.elevenlabs_api_key;
          }
        } catch (_) {}

        setFormData(form);
        useApiKeyReminderStore.getState().updateSettings(response.data);
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

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const {
        api_key, mineru_token, baidu_api_key, elevenlabs_api_key,
        ...otherData
      } = formData;
      const payload: Parameters<typeof api.updateSettings>[0] = {
        ...otherData,
        ai_provider_format: 'gemini',
        text_model_source: '',
        image_model_source: '',
        image_caption_model_source: '',
      };

      // Only send sensitive fields if user entered a new value
      if (api_key) payload.api_key = api_key;
      if (mineru_token) payload.mineru_token = mineru_token;
      if (baidu_api_key) payload.baidu_api_key = baidu_api_key;
      if (elevenlabs_api_key) payload.elevenlabs_api_key = elevenlabs_api_key;

      if (storageMode === 'client') {
        const cachedClient = getCachedClientConfig();
        const effectiveApiKey = api_key || (cachedClient?.api_key ?? '');
        const effectiveMineru = mineru_token || cachedClient?.mineru_token;
        const effectiveBaidu = baidu_api_key || cachedClient?.baidu_api_key;
        const effectiveElevenLabs = elevenlabs_api_key || cachedClient?.elevenlabs_api_key;

        await saveClientKeys({
          ai_provider_format: 'gemini',
          api_key: effectiveApiKey,
          api_base_url: otherData.api_base_url,
          lazyllm_api_keys: {},
          text_model: otherData.text_model,
          image_model: otherData.image_model,
          mineru_token: effectiveMineru,
          baidu_api_key: effectiveBaidu,
          elevenlabs_api_key: effectiveElevenLabs,
        });

        // Save settings (including entered keys) to backend so both client headers and backend tasks work seamlessly
        if (effectiveApiKey) payload.api_key = effectiveApiKey;
        const response = await api.updateSettings(payload);
        if (response.data) {
          setSettings(response.data);
          useApiKeyReminderStore.getState().updateSettings(response.data);
        }

        show({
          message: !i18n.language?.startsWith('en')
            ? 'Đã lưu API Key!'
            : 'API Key saved!',
          type: 'success',
        });

        // Keep entered keys visible in the inputs!
        setFormData(prev => ({
          ...prev,
          ai_provider_format: 'gemini',
          api_base_url: otherData.api_base_url ?? '',
          api_key: effectiveApiKey,
          mineru_token: effectiveMineru || prev.mineru_token,
          baidu_api_key: effectiveBaidu || prev.baidu_api_key,
          elevenlabs_api_key: effectiveElevenLabs || prev.elevenlabs_api_key,
        }));
      } else {
        const response = await api.updateSettings(payload);
        if (response.data) {
          setSettings(response.data);
          useApiKeyReminderStore.getState().updateSettings(response.data);
          show({
            message: !i18n.language?.startsWith('en')
              ? 'Đã lưu API Key!'
              : 'API Key saved!',
            type: 'success',
          });

          // Save keys into session storage so page reload still displays them
          try {
            sessionStorage.setItem('banana_saved_keys', JSON.stringify({
              ai_provider_format: 'gemini',
              api_key: api_key || '',
              api_base_url: otherData.api_base_url ?? '',
              mineru_token: mineru_token || '',
              baidu_api_key: baidu_api_key || '',
              elevenlabs_api_key: elevenlabs_api_key || '',
            }));
          } catch (_) {}

          // Keep entered keys visible in the inputs!
          setFormData(prev => ({
            ...prev,
            ai_provider_format: 'gemini',
            api_base_url: otherData.api_base_url ?? '',
            api_key: api_key || prev.api_key,
            mineru_token: mineru_token || prev.mineru_token,
            baidu_api_key: baidu_api_key || prev.baidu_api_key,
            elevenlabs_api_key: elevenlabs_api_key || prev.elevenlabs_api_key,
          }));
        }
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

  const handleFieldChange = (key: string, value: any) => {
    setFormData(prev => ({ ...prev, [key]: value }));
  };

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
      // Prepare settings for test (Google Gemini only)
      const testSettings: any = {
        ai_provider_format: 'gemini',
        text_model_source: '',
        image_model_source: '',
        image_caption_model_source: '',
      };

      // Only pass non-empty filled values
      if (formData.api_key) testSettings.api_key = formData.api_key;
      if (formData.api_base_url) testSettings.api_base_url = formData.api_base_url;
      if (formData.text_model) testSettings.text_model = formData.text_model;
      if (formData.image_model) testSettings.image_model = formData.image_model;
      if (formData.image_caption_model) testSettings.image_caption_model = formData.image_caption_model;
      if (formData.mineru_api_base) testSettings.mineru_api_base = formData.mineru_api_base;
      if (formData.mineru_token) testSettings.mineru_token = formData.mineru_token;
      if (formData.baidu_api_key) testSettings.baidu_api_key = formData.baidu_api_key;
      if (formData.image_resolution) testSettings.image_resolution = formData.image_resolution;

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
      <div className="space-y-8">
        <div data-testid="global-api-config-section" className="space-y-4">
          {/* Form cấu hình Google Gemini */}
          <SettingsActiveProviderForm
            formData={formData}
            setFormData={setFormData}
            settings={settings}
            handleFieldChange={handleFieldChange}
            t={t}
            isVi={isVi}
            serviceTestStates={serviceTestStates}
            triggerTest={triggerTest}
            dismissTest={dismissTest}
            onSave={handleSave}
            isSaving={isSaving}
          />
        </div>

        {/* General & Output Config */}
        <div className="space-y-6">
          {settingsSections.filter((section) =>
            section.title === t('settings.sections.imageConfig') ||
            section.title === t('settings.sections.outputLanguage')
          ).map((section) => (
            <div key={section.title}>
              <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-foreground-primary mb-2.5 sm:mb-3 flex items-center">
                {section.icon}
                <span className="ml-2">{section.title}</span>
              </h2>
              <div className="space-y-4">
                {section.fields.map((field) => renderField(field))}
              </div>
            </div>
          ))}
        </div>

        {/* Advanced settings (collapsible) */}
        <SettingsAdvanced open={advancedOpen} onToggle={() => setAdvancedOpen(!advancedOpen)} label={t('settings.sections.advancedSettings')}>
              {isDesktop && <DataStorageSettings />}

              {/* Performance + reasoning mode */}
              {settingsSections.filter((section) =>
                section.title === t('settings.sections.performanceConfig') ||
                section.title === t('settings.sections.textReasoning') ||
                section.title === t('settings.sections.imageReasoning')
              ).map((section) => (
                <div key={section.title}>
                  <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-foreground-primary mb-3 sm:mb-4 flex items-center">
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
            className="w-full sm:w-auto justify-center"
          >
            {t('settings.actions.resetToDefault')}
          </Button>
          <Button
            variant="primary"
            icon={<Save size={18} />}
            onClick={handleSave}
            loading={isSaving}
            className="w-full sm:w-auto justify-center"
          >
            {isSaving ? t('settings.actions.saving') : t('settings.actions.save')}
          </Button>
        </SettingsActions>
      </div>
    </>
  );
};

// SettingsPage component - full page wrapper
export const SettingsPage: React.FC = () => <SettingsPageFrame><Settings /></SettingsPageFrame>;