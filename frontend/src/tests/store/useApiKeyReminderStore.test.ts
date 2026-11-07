import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useApiKeyReminderStore, isAiKeyConfigured } from '@/store/useApiKeyReminderStore';
import * as api from '@/api/endpoints';
import type { Settings } from '@/types';

vi.mock('@/api/endpoints', () => ({
  getSettings: vi.fn(),
}));

describe('isAiKeyConfigured', () => {
  it('returns false for null or undefined settings', () => {
    expect(isAiKeyConfigured(null)).toBe(false);
    expect(isAiKeyConfigured(undefined)).toBe(false);
  });

  it('detects configured key for direct provider Gemini', () => {
    const s1 = { ai_provider_format: 'gemini', api_key_length: 39 } as Settings;
    const s2 = { ai_provider_format: 'gemini', api_key_length: 0 } as Settings;
    expect(isAiKeyConfigured(s1)).toBe(true);
    expect(isAiKeyConfigured(s2)).toBe(false);
  });

  it('detects configured key or OAuth for OpenAI and Codex', () => {
    const sKey = { ai_provider_format: 'openai', api_key_length: 45, openai_oauth_connected: false } as Settings;
    const sOAuth = { ai_provider_format: 'openai', api_key_length: 0, openai_oauth_connected: true } as Settings;
    const sCodex = { ai_provider_format: 'codex', openai_oauth_connected: true } as Settings;
    const sNone = { ai_provider_format: 'openai', api_key_length: 0, openai_oauth_connected: false } as Settings;

    expect(isAiKeyConfigured(sKey)).toBe(true);
    expect(isAiKeyConfigured(sOAuth)).toBe(true);
    expect(isAiKeyConfigured(sCodex)).toBe(true);
    expect(isAiKeyConfigured(sNone)).toBe(false);
  });

  it('detects LazyLLM vendor key configuration', () => {
    const sVendor = {
      ai_provider_format: 'deepseek',
      api_key_length: 0,
      lazyllm_api_keys_info: { deepseek: 32, siliconflow: 0 },
    } as unknown as Settings;

    const sUnconfigured = {
      ai_provider_format: 'siliconflow',
      api_key_length: 0,
      lazyllm_api_keys_info: { deepseek: 32, siliconflow: 0 },
    } as unknown as Settings;

    expect(isAiKeyConfigured(sVendor)).toBe(true);
    expect(isAiKeyConfigured(sUnconfigured)).toBe(false);
  });

  it('recognizes text model override credentials even if provider key is 0', () => {
    const sOverride = {
      ai_provider_format: 'gemini',
      api_key_length: 0,
      text_api_key_length: 35,
    } as unknown as Settings;

    expect(isAiKeyConfigured(sOverride)).toBe(true);
  });
});

describe('useApiKeyReminderStore', () => {
  beforeEach(() => {
    sessionStorage.clear();
    useApiKeyReminderStore.setState({
      isConfigured: null,
      isChecking: false,
      isModalOpen: false,
      isFloatingDismissed: false,
      settings: null,
    });
    vi.clearAllMocks();
  });

  it('checkSettings sets isConfigured=false and isModalOpen=true when key is missing', async () => {
    vi.mocked(api.getSettings).mockResolvedValueOnce({
      success: true,
      data: {
        ai_provider_format: 'gemini',
        api_key_length: 0,
      } as Settings,
      message: 'Success',
    });

    const configured = await useApiKeyReminderStore.getState().checkSettings();
    expect(configured).toBe(false);
    expect(useApiKeyReminderStore.getState().isConfigured).toBe(false);
    expect(useApiKeyReminderStore.getState().isModalOpen).toBe(true);
  });

  it('checkSettings sets isConfigured=true and isModalOpen=false when key is present', async () => {
    vi.mocked(api.getSettings).mockResolvedValueOnce({
      success: true,
      data: {
        ai_provider_format: 'gemini',
        api_key_length: 39,
      } as Settings,
      message: 'Success',
    });

    const configured = await useApiKeyReminderStore.getState().checkSettings();
    expect(configured).toBe(true);
    expect(useApiKeyReminderStore.getState().isConfigured).toBe(true);
    expect(useApiKeyReminderStore.getState().isModalOpen).toBe(false);
  });

  it('closeModal hides modal and snoozes popup', () => {
    useApiKeyReminderStore.setState({ isModalOpen: true });
    useApiKeyReminderStore.getState().closeModal();

    expect(useApiKeyReminderStore.getState().isModalOpen).toBe(false);
    expect(sessionStorage.getItem('banana_key_reminder_snoozed')).toBe('true');
  });

  it('updateSettings instantly clears reminders when key becomes configured', () => {
    useApiKeyReminderStore.setState({ isConfigured: false, isModalOpen: true });

    useApiKeyReminderStore.getState().updateSettings({
      ai_provider_format: 'gemini',
      api_key_length: 40,
    } as Settings);

    expect(useApiKeyReminderStore.getState().isConfigured).toBe(true);
    expect(useApiKeyReminderStore.getState().isModalOpen).toBe(false);
    expect(useApiKeyReminderStore.getState().isFloatingDismissed).toBe(false);
  });
});
