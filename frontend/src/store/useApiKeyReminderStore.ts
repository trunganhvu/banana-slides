import { create } from 'zustand';
import type { Settings } from '@/types';
import * as api from '@/api/endpoints';
import { hasClientKeyConfigured } from '@/utils/clientKeyStorage';

/**
 * Checks whether the current application settings have a valid AI API key configured.
 * Checks active provider first, plus per-model overrides and LazyLLM credentials.
 */
export function isAiKeyConfigured(settings: Settings | null | undefined): boolean {
  // 0. Check client-side encrypted key storage first
  if (hasClientKeyConfigured()) {
    return true;
  }

  if (!settings) return false;

  // Google Gemini only
  return (settings.api_key_length ?? 0) > 0 || (settings.text_api_key_length ?? 0) > 0;
}

const STORAGE_KEY_SNOOZE = 'banana_key_reminder_snoozed';

interface ApiKeyReminderState {
  isConfigured: boolean | null; // null = checking / unknown, false = missing, true = configured
  isChecking: boolean;
  isModalOpen: boolean;
  isFloatingDismissed: boolean;
  settings: Settings | null;

  checkSettings: () => Promise<boolean>;
  openModal: () => void;
  closeModal: () => void;
  dismissFloating: () => void;
  updateSettings: (newSettings: Settings) => void;
}

export const useApiKeyReminderStore = create<ApiKeyReminderState>((set, get) => ({
  isConfigured: null,
  isChecking: false,
  isModalOpen: false,
  isFloatingDismissed: sessionStorage.getItem(STORAGE_KEY_SNOOZE) === 'true',
  settings: null,

  checkSettings: async () => {
    // Avoid duplicate in-flight checks
    if (get().isChecking) {
      return get().isConfigured ?? false;
    }

    set({ isChecking: true });
    try {
      const response = await api.getSettings();
      const settingsData = response?.data;
      if (settingsData) {
        const configured = isAiKeyConfigured(settingsData);
        const snoozed = sessionStorage.getItem(STORAGE_KEY_SNOOZE) === 'true';

        set({
          isConfigured: configured,
          settings: settingsData,
          isChecking: false,
          // Automatically open modal on initial load if key is missing and not already dismissed
          isModalOpen: !configured && !snoozed,
        });
        return configured;
      }
      set({ isChecking: false });
      return false;
    } catch (error) {
      console.warn('Failed to verify API key configuration:', error);
      set({ isChecking: false });
      return false;
    }
  },

  openModal: () => {
    set({ isModalOpen: true });
  },

  closeModal: () => {
    // Closing the modal snoozes popup but keeps floating pill active
    sessionStorage.setItem(STORAGE_KEY_SNOOZE, 'true');
    set({ isModalOpen: false });
  },

  dismissFloating: () => {
    sessionStorage.setItem(STORAGE_KEY_SNOOZE, 'true');
    set({ isFloatingDismissed: true, isModalOpen: false });
  },

  updateSettings: (newSettings: Settings) => {
    const configured = isAiKeyConfigured(newSettings);
    if (configured) {
      sessionStorage.removeItem(STORAGE_KEY_SNOOZE);
      set({
        isConfigured: true,
        settings: newSettings,
        isModalOpen: false,
        isFloatingDismissed: false,
      });
    } else {
      set({
        isConfigured: false,
        settings: newSettings,
      });
    }
  },
}));
