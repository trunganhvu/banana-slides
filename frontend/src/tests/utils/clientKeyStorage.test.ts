import { describe, it, expect, beforeEach } from 'vitest';
import {
  saveClientKeys,
  loadClientKeys,
  clearClientKeys,
  hasClientKeyConfigured,
  getClientStorageMode,
  setClientStorageMode,
  getCachedClientHeaders,
} from '@/utils/clientKeyStorage';

describe('clientKeyStorage', () => {
  beforeEach(() => {
    localStorage.clear();
    clearClientKeys();
  });

  it('defaults to client storage mode', () => {
    expect(getClientStorageMode()).toBe('client');
  });

  it('can switch storage mode', () => {
    setClientStorageMode('server');
    expect(getClientStorageMode()).toBe('server');

    setClientStorageMode('client');
    expect(getClientStorageMode()).toBe('client');
  });

  it('encrypts and saves client keys and retrieves them intact', async () => {
    await saveClientKeys({
      ai_provider_format: 'gemini',
      api_key: 'AIzaSyTestClientKey123',
      api_base_url: 'https://generativelanguage.googleapis.com',
      lazyllm_api_keys: {
        deepseek: 'sk-deepseek-test-key',
      },
      mineru_token: 'mineru-client-token',
    });

    // Verify plaintext is NOT stored in localStorage directly
    const rawStored = localStorage.getItem('banana_client_keys_enc');
    expect(rawStored).toBeTruthy();
    expect(rawStored).not.toContain('AIzaSyTestClientKey123');
    expect(rawStored).not.toContain('sk-deepseek-test-key');

    // Decrypt and verify contents
    const loaded = await loadClientKeys();
    expect(loaded).toBeTruthy();
    expect(loaded?.ai_provider_format).toBe('gemini');
    expect(loaded?.api_key).toBe('AIzaSyTestClientKey123');
    expect(loaded?.lazyllm_api_keys.deepseek).toBe('sk-deepseek-test-key');
    expect(loaded?.mineru_token).toBe('mineru-client-token');

    // Check header generation
    const headers = getCachedClientHeaders();
    expect(headers).toBeTruthy();
    expect(headers?.['X-Client-Storage-Mode']).toBe('client');
    expect(headers?.['X-Client-Provider']).toBe('gemini');
    expect(headers?.['X-Client-Api-Key']).toBe('AIzaSyTestClientKey123');

    // Check configured flag
    expect(hasClientKeyConfigured()).toBe(true);
  });

  it('clears client keys properly', async () => {
    await saveClientKeys({
      ai_provider_format: 'openai',
      api_key: 'sk-proj-test123',
    });

    expect(hasClientKeyConfigured()).toBe(true);

    clearClientKeys();
    expect(localStorage.getItem('banana_client_keys_enc')).toBeNull();
    expect(hasClientKeyConfigured()).toBe(false);
    expect(getCachedClientHeaders()).toBeNull();
  });
});
