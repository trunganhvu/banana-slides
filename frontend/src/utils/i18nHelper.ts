import i18n from '@/i18n';

type NestedRecord = { [key: string]: string | NestedRecord };
type Translations<T extends NestedRecord> = { vi?: T; zh?: T; en: T };

function getByPath(obj: unknown, path: string): unknown {
  return path.split('.').reduce((acc: unknown, key) => {
    if (acc && typeof acc === 'object' && key in (acc as Record<string, unknown>)) {
      return (acc as Record<string, unknown>)[key];
    }
    return undefined;
  }, obj);
}

function interpolate(str: string, params?: Record<string, unknown>): string {
  if (!params) return str;
  return str.replace(/\{\{(\w+)\}\}/g, (_, k) =>
    params[k] !== undefined ? String(params[k]) : `{{${k}}}`
  );
}

/**
 * Non-React translation helper (for stores, utils, api, etc.)
 *
 * Usage:
 * ```ts
 * const storeI18n = {
 *   vi: { loadError: 'Tải thất bại' },
 *   en: { loadError: 'Failed to load' },
 * };
 * const t = getT(storeI18n);
 * t('loadError');
 * ```
 */
export function getT<T extends NestedRecord>(translations: Translations<T>) {
  return (key: string, params?: Record<string, unknown>): string => {
    const isEn = i18n.language?.startsWith('en');
    const dict = isEn ? translations.en : (translations.vi ?? translations.zh ?? translations.en);
    const val = getByPath(dict, key);
    if (typeof val === 'string') {
      return interpolate(val, params);
    }
    if (!isEn) {
      const fallback = getByPath(translations.en, key);
      if (typeof fallback === 'string') {
        return interpolate(fallback, params);
      }
    }
    return i18n.t(key, params) as string;
  };
}
