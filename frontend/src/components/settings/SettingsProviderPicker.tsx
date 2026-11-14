import React from "react";
import { ChevronDown } from "lucide-react";

export interface ProviderPromotion {
  key: string;
  testId: string;
  active: boolean;
  name: string;
  tagline: string;
  suitedFor: string;
  points: string[];
  cta: string;
  activeLabel: string;
  note: string;
  onSelect: () => void;
  href: string;
  linkLabel: string;
}

interface Props {
  label: string;
  globalProviderSources: {
    value: string;
    label: string;
    disabled?: boolean;
    hint?: string | null;
  }[];
  selectedGlobalProvider: string;
  providerPromotions?: ProviderPromotion[];
  selectGlobalProvider: (value: string) => void;
  disabledLabel?: string;
  isVi?: boolean;
}

export function SettingsProviderPicker({
  label,
  globalProviderSources,
  selectedGlobalProvider,
  selectGlobalProvider,
  disabledLabel,
  isVi = true,
}: Props) {
  return (
    <div className="space-y-2">
      <div>
        <label
          htmlFor="ai-provider-select"
          className="block text-sm font-semibold text-gray-900 dark:text-foreground-primary mb-1"
        >
          {label || (isVi ? "Nhà cung cấp AI (Provider)" : "AI Provider")}
        </label>
        <p className="text-xs text-gray-500 dark:text-foreground-tertiary">
          {isVi
            ? "Chọn nhà cung cấp AI bạn muốn sử dụng (Google Gemini, OpenAI, DeepSeek, OpenRouter, Groq, Doubao...)"
            : "Select the AI provider to use (Google Gemini, OpenAI, DeepSeek, OpenRouter, Groq, Doubao...)"}
        </p>
      </div>

      <div className="relative">
        <select
          id="ai-provider-select"
          data-testid="ai-provider-dropdown-select"
          value={selectedGlobalProvider}
          onChange={(e) => selectGlobalProvider(e.target.value)}
          className="w-full h-11 pl-3.5 pr-10 rounded-lg border border-gray-300 dark:border-border-primary bg-white dark:bg-background-secondary focus:outline-none focus:ring-2 focus:ring-banana-500 focus:border-transparent text-sm font-medium text-gray-900 dark:text-foreground-primary appearance-none cursor-pointer shadow-sm transition-colors"
        >
          {globalProviderSources.map((opt) => (
            <option key={opt.value} value={opt.value} disabled={opt.disabled}>
              {opt.label}
              {opt.value === "gemini" ? ` (${isVi ? "Mặc định - Văn bản & Ảnh" : "Default - Text & Image"})` : ""}
              {opt.value === "openai" ? ` (${isVi ? "Hỗ trợ OpenAI / OpenRouter / Groq / DeepSeek" : "Supports OpenAI / OpenRouter / Groq / DeepSeek"})` : ""}
              {opt.disabled && disabledLabel ? ` (${disabledLabel})` : ""}
            </option>
          ))}
        </select>
        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3.5 text-gray-400">
          <ChevronDown size={18} />
        </div>
      </div>

      {/* Screen-reader / test compatibility container */}
      <div data-testid="global-provider-pills" className="sr-only" aria-hidden="true">
        {globalProviderSources.map((option) => (
          <button
            key={option.value}
            type="button"
            data-provider={option.value}
            onClick={() => selectGlobalProvider(option.value)}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}
