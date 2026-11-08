/**
 * Client-side encrypted API Key storage using native Web Crypto API (AES-GCM 256-bit).
 *
 * Ensures individual browser clients keep their own private API keys without
 * exposing them in plaintext inside localStorage or persisting them into the server database.
 */

export interface ClientKeysConfig {
  storageMode: 'client' | 'server';
  ai_provider_format: string;
  api_key: string;
  api_base_url?: string;
  lazyllm_api_keys: Record<string, string>;
  text_model?: string;
  image_model?: string;
  mineru_token?: string;
  baidu_api_key?: string;
  elevenlabs_api_key?: string;
  updatedAt?: number;
}

const STORAGE_KEY_ENC = 'banana_client_keys_enc';
const STORAGE_KEY_SALT = 'banana_client_salt';
const STORAGE_KEY_MODE = 'banana_storage_mode';

// In-memory decrypted cache for fast synchronous HTTP request interceptor access
let inMemoryConfig: ClientKeysConfig | null = null;
let cachedHeaders: Record<string, string> | null = null;
let isInitialized = false;

// Convert Uint8Array to Base64
function bufferToBase64(buffer: ArrayBuffer | Uint8Array): string {
  const bytes = buffer instanceof Uint8Array ? buffer : new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return window.btoa(binary);
}

// Convert Base64 to Uint8Array
function base64ToBuffer(base64: string): Uint8Array {
  const binary = window.atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

// Get or generate a persistent device-bound salt
function getOrCreateDeviceSalt(): Uint8Array {
  try {
    const existing = localStorage.getItem(STORAGE_KEY_SALT);
    if (existing) {
      return base64ToBuffer(existing);
    }
    const newSalt = window.crypto.getRandomValues(new Uint8Array(16));
    localStorage.setItem(STORAGE_KEY_SALT, bufferToBase64(newSalt));
    return newSalt;
  } catch {
    return new Uint8Array([11, 22, 33, 44, 55, 66, 77, 88, 99, 10, 21, 32, 43, 54, 65, 76]);
  }
}

// Derive a 256-bit AES-GCM CryptoKey using PBKDF2
async function deriveAesKey(salt: Uint8Array): Promise<CryptoKey | null> {
  if (!window.crypto?.subtle) {
    return null;
  }
  try {
    const encoder = new TextEncoder();
    // Unique device entropy seed
    const rawSeed = `banana-client-key-vault-${window.location.host || 'local'}`;
    const baseKey = await window.crypto.subtle.importKey(
      'raw',
      encoder.encode(rawSeed),
      'PBKDF2',
      false,
      ['deriveKey']
    );

    return await window.crypto.subtle.deriveKey(
      {
        name: 'PBKDF2',
        salt: new Uint8Array(salt),
        iterations: 100000,
        hash: 'SHA-256',
      },
      baseKey,
      { name: 'AES-GCM', length: 256 },
      false,
      ['encrypt', 'decrypt']
    );
  } catch (error) {
    console.warn('Web Crypto key derivation failed, using fallback:', error);
    return null;
  }
}

// Encrypt plaintext JSON string with AES-GCM
async function encryptData(plainText: string): Promise<string> {
  const salt = getOrCreateDeviceSalt();
  const aesKey = await deriveAesKey(salt);

  if (!aesKey || !window.crypto?.subtle) {
    // Fallback obfuscation for non-crypto environments
    return `obf:${window.btoa(encodeURIComponent(plainText))}`;
  }

  const iv = window.crypto.getRandomValues(new Uint8Array(12));
  const encoder = new TextEncoder();
  const cipherBuffer = await window.crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    aesKey,
    encoder.encode(plainText)
  );

  const payload = {
    v: 1,
    iv: bufferToBase64(iv),
    data: bufferToBase64(cipherBuffer),
  };

  return `enc:${JSON.stringify(payload)}`;
}

// Decrypt AES-GCM ciphertext to plaintext JSON string
async function decryptData(cipherString: string): Promise<string | null> {
  if (!cipherString) return null;

  if (cipherString.startsWith('obf:')) {
    try {
      return decodeURIComponent(window.atob(cipherString.slice(4)));
    } catch {
      return null;
    }
  }

  if (!cipherString.startsWith('enc:')) {
    return null;
  }

  try {
    const payload = JSON.parse(cipherString.slice(4));
    const salt = getOrCreateDeviceSalt();
    const aesKey = await deriveAesKey(salt);
    if (!aesKey || !window.crypto?.subtle) return null;

    const iv = base64ToBuffer(payload.iv);
    const dataBuffer = base64ToBuffer(payload.data);

    const decrypted = await window.crypto.subtle.decrypt(
      { name: 'AES-GCM', iv },
      aesKey,
      dataBuffer
    );

    const decoder = new TextDecoder();
    return decoder.decode(decrypted);
  } catch (error) {
    console.warn('Failed to decrypt client keys:', error);
    return null;
  }
}

function updateCachedHeaders(config: ClientKeysConfig | null) {
  inMemoryConfig = config;
  if (!config || config.storageMode !== 'client') {
    cachedHeaders = null;
    return;
  }

  const headers: Record<string, string> = {
    'X-Client-Storage-Mode': 'client',
  };

  if (config.ai_provider_format) {
    headers['X-Client-Provider'] = config.ai_provider_format;
  }
  if (config.api_key) {
    headers['X-Client-Api-Key'] = config.api_key;
  }
  if (config.api_base_url) {
    headers['X-Client-Api-Base'] = config.api_base_url;
  }
  if (config.lazyllm_api_keys && Object.keys(config.lazyllm_api_keys).length > 0) {
    headers['X-Client-Lazyllm-Keys'] = JSON.stringify(config.lazyllm_api_keys);
  }
  if (config.text_model) {
    headers['X-Client-Text-Model'] = config.text_model;
  }
  if (config.image_model) {
    headers['X-Client-Image-Model'] = config.image_model;
  }
  if (config.mineru_token) {
    headers['X-Client-Mineru-Token'] = config.mineru_token;
  }
  if (config.baidu_api_key) {
    headers['X-Client-Baidu-Key'] = config.baidu_api_key;
  }
  if (config.elevenlabs_api_key) {
    headers['X-Client-Elevenlabs-Key'] = config.elevenlabs_api_key;
  }

  cachedHeaders = headers;
}

/**
 * Initialize and load client keys into memory cache.
 */
export async function initClientKeyStorage(): Promise<ClientKeysConfig | null> {
  if (isInitialized && inMemoryConfig) {
    return inMemoryConfig;
  }

  try {
    const rawEnc = localStorage.getItem(STORAGE_KEY_ENC);
    if (!rawEnc) {
      updateCachedHeaders(null);
      isInitialized = true;
      return null;
    }

    const plain = await decryptData(rawEnc);
    if (!plain) {
      updateCachedHeaders(null);
      isInitialized = true;
      return null;
    }

    const parsed: ClientKeysConfig = JSON.parse(plain);
    updateCachedHeaders(parsed);
    isInitialized = true;
    return parsed;
  } catch (error) {
    console.warn('Error initializing client key storage:', error);
    updateCachedHeaders(null);
    isInitialized = true;
    return null;
  }
}

/**
 * Save encrypted client keys to localStorage and update memory cache.
 */
export async function saveClientKeys(config: Partial<ClientKeysConfig>): Promise<void> {
  const current = inMemoryConfig || {
    storageMode: 'client',
    ai_provider_format: 'gemini',
    api_key: '',
    lazyllm_api_keys: {},
  };

  const updated: ClientKeysConfig = {
    ...current,
    ...config,
    storageMode: 'client',
    updatedAt: Date.now(),
  };

  const plainJson = JSON.stringify(updated);
  const encString = await encryptData(plainJson);
  localStorage.setItem(STORAGE_KEY_ENC, encString);
  localStorage.setItem(STORAGE_KEY_MODE, 'client');
  updateCachedHeaders(updated);
}

/**
 * Load and return decrypted client keys.
 */
export async function loadClientKeys(): Promise<ClientKeysConfig | null> {
  return initClientKeyStorage();
}

/**
 * Clear client-side keys from localStorage and memory cache.
 */
export function clearClientKeys(): void {
  localStorage.removeItem(STORAGE_KEY_ENC);
  updateCachedHeaders(null);
}

/**
 * Get the current storage mode selection ('client' or 'server').
 */
export function getClientStorageMode(): 'client' | 'server' {
  const stored = localStorage.getItem(STORAGE_KEY_MODE);
  return stored === 'server' ? 'server' : 'client';
}

/**
 * Set the current storage mode selection.
 */
export function setClientStorageMode(mode: 'client' | 'server'): void {
  localStorage.setItem(STORAGE_KEY_MODE, mode);
  if (inMemoryConfig) {
    inMemoryConfig.storageMode = mode;
    updateCachedHeaders(inMemoryConfig);
  }
}

/**
 * Synchronous check whether a valid key is configured on the client.
 */
export function hasClientKeyConfigured(): boolean {
  if (!inMemoryConfig || inMemoryConfig.storageMode !== 'client') {
    // If not in memory yet, check if encrypted record exists in storage
    const hasRecord = Boolean(localStorage.getItem(STORAGE_KEY_ENC));
    const mode = localStorage.getItem(STORAGE_KEY_MODE);
    return hasRecord && mode !== 'server';
  }

  const provider = (inMemoryConfig.ai_provider_format || 'gemini').toLowerCase();
  if (inMemoryConfig.api_key && inMemoryConfig.api_key.trim().length > 0) {
    return true;
  }

  const lazyKey = inMemoryConfig.lazyllm_api_keys?.[provider];
  if (lazyKey && lazyKey.trim().length > 0) {
    return true;
  }

  return false;
}

/**
 * Synchronous accessor for apiClient request interceptor.
 */
export function getCachedClientHeaders(): Record<string, string> | null {
  return cachedHeaders;
}

/**
 * Synchronous accessor for in-memory decrypted client config.
 */
export function getCachedClientConfig(): ClientKeysConfig | null {
  return inMemoryConfig;
}

// Automatically initiate decryption on module load so cache is primed
if (typeof window !== 'undefined') {
  initClientKeyStorage().catch(() => {});
}
