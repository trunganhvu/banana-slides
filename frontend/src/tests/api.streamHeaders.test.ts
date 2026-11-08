import { describe, it, expect, beforeEach, vi } from 'vitest';
import { generateOutlineStream, generateDescriptionsStream } from '@/api/endpoints';
import { saveClientKeys, clearClientKeys } from '@/utils/clientKeyStorage';

describe('stream endpoints client headers', () => {
  beforeEach(() => {
    localStorage.clear();
    clearClientKeys();
    vi.restoreAllMocks();
  });

  it('attaches client storage headers to generateOutlineStream fetch request', async () => {
    await saveClientKeys({
      ai_provider_format: 'gemini',
      api_key: 'AIzaSyTestClientStreamKey',
    });

    let capturedHeaders: Record<string, string> = {};
    const mockFetch = vi.fn().mockImplementation((_url, init) => {
      capturedHeaders = init?.headers || {};
      return Promise.resolve({
        ok: true,
        body: {
          getReader() {
            return {
              read: vi.fn().mockResolvedValue({ done: true, value: undefined }),
            };
          },
        },
      });
    });
    vi.stubGlobal('fetch', mockFetch);

    const callbacks = {
      onPage: vi.fn(),
      onDone: vi.fn(),
      onError: vi.fn(),
    };

    await generateOutlineStream('proj-123', callbacks, 'vi');

    expect(mockFetch).toHaveBeenCalled();
    expect(capturedHeaders['X-Client-Storage-Mode']).toBe('client');
    expect(capturedHeaders['X-Client-Provider']).toBe('gemini');
    expect(capturedHeaders['X-Client-Api-Key']).toBe('AIzaSyTestClientStreamKey');
  });

  it('attaches client storage headers to generateDescriptionsStream fetch request', async () => {
    await saveClientKeys({
      ai_provider_format: 'gemini',
      api_key: 'AIzaSyTestClientStreamKey',
    });

    let capturedHeaders: Record<string, string> = {};
    const mockFetch = vi.fn().mockImplementation((_url, init) => {
      capturedHeaders = init?.headers || {};
      return Promise.resolve({
        ok: true,
        body: {
          getReader() {
            return {
              read: vi.fn().mockResolvedValue({ done: true, value: undefined }),
            };
          },
        },
      });
    });
    vi.stubGlobal('fetch', mockFetch);

    const callbacks = {
      onDescription: vi.fn(),
      onDone: vi.fn(),
      onError: vi.fn(),
    };

    await generateDescriptionsStream('proj-123', callbacks, 'vi');

    expect(mockFetch).toHaveBeenCalled();
    expect(capturedHeaders['X-Client-Storage-Mode']).toBe('client');
    expect(capturedHeaders['X-Client-Provider']).toBe('gemini');
    expect(capturedHeaders['X-Client-Api-Key']).toBe('AIzaSyTestClientStreamKey');
  });
});
