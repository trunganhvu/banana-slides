import axios from 'axios';
import { isDesktop } from '@/utils';
import i18n from '@/i18n';

const DESKTOP_BACKEND_PORT_STORAGE_KEY = '__desktop_backend_port__';

function isValidPort(port: number): boolean {
  return Number.isInteger(port) && port > 0 && port <= 65535;
}

function parsePort(value: unknown): number {
  return Number.parseInt(String(value ?? ''), 10);
}

function resolveDesktopBackendPort(): number {
  const rawPort = (window as any).electronAPI?.getBackendPort?.();
  const port = parsePort(rawPort);
  if (isValidPort(port)) {
    sessionStorage.setItem(DESKTOP_BACKEND_PORT_STORAGE_KEY, String(port));
    return port;
  }

  const cachedPort = parsePort(sessionStorage.getItem(DESKTOP_BACKEND_PORT_STORAGE_KEY));
  if (isValidPort(cachedPort)) {
    return cachedPort;
  }

  console.warn('Desktop backend port is unavailable');
  return 0;
}

const isClientSideUrl = (url: string) => /^\/?(data|blob):/i.test(url);
const normalizeClientSideUrl = (url: string) => url.replace(/^\/(?=(data|blob):)/i, '');

// API client endpoint
if (isDesktop) {
  (window as any).__BACKEND_PORT__ = resolveDesktopBackendPort();
}

export function getBaseURL(): string {
  if (!isDesktop) return '';
  const port = (window as any).__BACKEND_PORT__;
  if (!isValidPort(port)) {
    console.warn('Desktop backend port is unavailable');
    return 'http://127.0.0.1:0';
  }
  return `http://127.0.0.1:${port}`;
}

// API client endpoint
export function triggerDownload(relativeOrAbsoluteUrl: string, filename?: string): void {
  if (!relativeOrAbsoluteUrl || typeof relativeOrAbsoluteUrl !== 'string') {
    console.warn('Invalid download URL:', relativeOrAbsoluteUrl);
    return;
  }

  if (isDesktop) {
    if (isClientSideUrl(relativeOrAbsoluteUrl)) {
      const url = normalizeClientSideUrl(relativeOrAbsoluteUrl);
      (window as any).electronAPI.downloadFile(url, filename || 'download');
      return;
    }

    const normalizedPath = relativeOrAbsoluteUrl.startsWith('/')
      ? relativeOrAbsoluteUrl
      : `/${relativeOrAbsoluteUrl}`;
    const url = /^https?:\/\//i.test(relativeOrAbsoluteUrl)
      ? relativeOrAbsoluteUrl
      : `${getBaseURL()}${normalizedPath}`;
    let fallbackFilename = 'download';
    try {
      fallbackFilename = new URL(url).pathname.split('/').pop() || 'download';
    } catch {
      fallbackFilename = relativeOrAbsoluteUrl.split('?')[0].split('/').filter(Boolean).pop() || 'download';
    }
    (window as any).electronAPI.downloadFile(url, filename || fallbackFilename);
  } else {
    // Downloads may start after a long export request, when popup activation has expired.
    const link = document.createElement('a');
    link.href = relativeOrAbsoluteUrl;
    link.rel = 'noopener';
    link.download = filename || relativeOrAbsoluteUrl.split(/[?#]/)[0].split('/').pop() || '';
    link.hidden = true;
    document.body.appendChild(link);
    try {
      link.click();
    } finally {
      link.remove();
    }
  }
}

// API client endpoint
export const apiClient = axios.create({
  timeout: 300000, // API client endpoint
});

// API client endpoint
apiClient.interceptors.request.use(
  (config) => {
    const hasAbsoluteBaseURL = typeof config.baseURL === 'string' && /^https?:\/\//i.test(config.baseURL);
    const hasAbsoluteRequestURL = typeof config.url === 'string' && /^https?:\/\//i.test(config.url);
    if (!hasAbsoluteBaseURL && !hasAbsoluteRequestURL) {
      config.baseURL = getBaseURL();
    }

    // Attach access code header for backend enforcement
    const accessCode = localStorage.getItem('banana-access-code');
    if (accessCode && config.headers) {
      config.headers['X-Access-Code'] = accessCode;
    }

    // API client endpoint
    if (config.headers && !config.headers['Accept-Language']) {
      config.headers['Accept-Language'] = i18n.language || 'zh';
    }

    // API client endpoint
    // API client endpoint
    if (config.data instanceof FormData) {
      // API client endpoint
      if (config.headers) {
        delete config.headers['Content-Type'];
      }
    } else if (config.headers && !config.headers['Content-Type']) {
      // API client endpoint
      config.headers['Content-Type'] = 'application/json';
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// API client endpoint
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // API client endpoint
    if (error.response) {
      // API client endpoint
      console.error('API Error:', error.response.data);
    } else if (error.request) {
      // API client endpoint
      console.error('Network Error:', error.request);
    } else {
      // API client endpoint
      console.error('Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// API client endpoint
// API client endpoint
export const getImageUrl = (path?: string, timestamp?: string | number): string => {
  if (!path) return '';
  if (isClientSideUrl(path)) {
    return normalizeClientSideUrl(path);
  }

  // API client endpoint
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  // API client endpoint
  let url = path.startsWith('/') ? path : '/' + path;

  if (isDesktop) {
    url = `${getBaseURL()}${url}`;
  }
  
  // API client endpoint
  if (timestamp) {
    const ts = typeof timestamp === 'string' 
      ? new Date(timestamp).getTime() 
      : timestamp;
    url += `?v=${ts}`;
  }
  
  return url;
};

export default apiClient;