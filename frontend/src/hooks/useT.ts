import { useCallback } from 'react';
import { useTranslation } from 'react-i18next';

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
 * Component-colocated translation hook
 *
 * Usage:
 * ```ts
 * const i18n = {
 *   vi: { title: 'Chào {{name}}', sub: { a: '1' } },
 *   en: { title: 'Hello {{name}}', sub: { a: '1' } },
 * };
 * const t = useT(i18n);
 * t('title', { name: 'World' }); // Supports interpolation
 * t('sub.a');                     // Supports nested keys
 * t('common.save');               // Automatically falls back to global common/nav/theme
 * ```
 *
 * When no parameter is passed, equivalent to react-i18next's useTranslation().t
 */
export function useT<T extends NestedRecord>(translations?: Translations<T>) {
  const { t: globalT, i18n } = useTranslation();
  const isEn = i18n.language?.startsWith('en');

  const t = useCallback(
    (key: string, params?: Record<string, unknown>): string => {
      if (translations) {
        const dict = isEn ? translations.en : (translations.vi ?? translations.zh ?? translations.en);
        const val = getByPath(dict, key);
        if (typeof val === 'string') {
          return interpolate(val, params);
        }
        // Fallback to English when key is missing in Vietnamese
        if (!isEn) {
          const fallback = getByPath(translations.en, key);
          if (typeof fallback === 'string') {
            return interpolate(fallback, params);
          }
        }
      }
      // Fallback to global (common.*, nav.*, theme.*)
      return globalT(key, params) as string;
    },
    [translations, isEn, globalT]
  );

  return t;
}
