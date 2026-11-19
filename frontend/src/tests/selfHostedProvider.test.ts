import { describe, it, expect, beforeEach } from 'vitest';
import {
  saveClientKeys,
  clearClientKeys,
  getCachedClientHeaders,
  hasClientKeyConfigured,
  normalizeProviderFormat,
} from '@/utils/clientKeyStorage';
import { isAiKeyConfigured } from '@/store/useApiKeyReminderStore';
import type { Settings } from '@/types';

describe('self-hosted LLM client storage and reminder helpers', () => {
  beforeEach(() => {
    localStorage.clear();
    clearClientKeys();
  });

  it('normalizes provider aliases consistently', () => {
    expect(normalizeProviderFormat('gemini')).toBe('gemini');
    expect(normalizeProviderFormat('openai')).toBe('openai');
    expect(normalizeProviderFormat('local')).toBe('openai');
    expect(normalizeProviderFormat('self_hosted')).toBe('openai');
    expect(normalizeProviderFormat('openai-compatible')).toBe('openai');
  });

  it('supports keyless local LLM in client storage headers and readiness check', async () => {
    await saveClientKeys({
      ai_provider_format: 'openai',
      api_base_url: 'http://localhost:11434/v1',
      api_key: '',
      text_model: 'qwen2.5:14b',
    });

    const headers = getCachedClientHeaders();
    expect(headers).not.toBeNull();
    expect(headers?.['X-Client-Provider']).toBe('openai');
    expect(headers?.['X-Client-Api-Base']).toBe('http://localhost:11434/v1');
    expect(headers?.['X-Client-Api-Key']).toBeUndefined();
    expect(headers?.['X-Client-Text-Model']).toBe('qwen2.5:14b');
    expect(hasClientKeyConfigured()).toBe(true);
  });

  it('treats keyless openai settings with endpoint URL as configured in reminder store', () => {
    const localSettings: Settings = {
      id: 1,
      ai_provider_format: 'openai',
      api_base_url: 'http://localhost:1234/v1',
      api_key_length: 0,
      text_model: 'llama3.3',
      image_model: '',
      image_resolution: '2K',
      image_aspect_ratio: '16:9',
      max_description_workers: 5,
      max_image_workers: 8,
    };

    const unconfiguredLocalSettings: Settings = {
      ...localSettings,
      api_base_url: '',
      api_key_length: 0,
    };

    expect(isAiKeyConfigured(localSettings)).toBe(true);
    expect(isAiKeyConfigured(unconfiguredLocalSettings)).toBe(false);
  });
});
