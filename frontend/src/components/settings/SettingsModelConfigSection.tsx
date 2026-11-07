import React, { useState } from 'react';
import { FileText, ChevronDown, ChevronUp, Sparkles, SlidersHorizontal, Image, Eye } from 'lucide-react';
import { Button } from '@/components/shared';
import type { useT } from '@/hooks/useT';

interface ModelConfigItem {
  modelKey: string;
  sourceKey: string;
  apiKeyKey: string;
  apiBaseKey: string;
  apiKeyLengthKey: string;
  label: string;
  placeholder: string;
  description: string;
  sourceLabel: string;
}

interface Props {
  modelConfigItems: ModelConfigItem[];
  renderModelConfigGroup: (item: any) => React.ReactNode;
  formData: {
    ai_provider_format: string;
    text_model: string;
    image_model: string;
    image_caption_model: string;
    text_model_source: string;
    image_model_source: string;
    image_caption_model_source: string;
    [key: string]: any;
  };
  isVi: boolean;
  t: ReturnType<typeof useT>;
}

export const SettingsModelConfigSection: React.FC<Props> = ({
  modelConfigItems,
  renderModelConfigGroup,
  formData,
  isVi,
  t,
}) => {
  const hasCustomModels = Boolean(
    formData.text_model ||
    formData.image_model ||
    formData.image_caption_model ||
    formData.text_model_source ||
    formData.image_model_source ||
    formData.image_caption_model_source
  );

  // Default to open if user has configured custom models, otherwise start collapsed
  const [isExpanded, setIsExpanded] = useState(hasCustomModels);
  const [activeTab, setActiveTab] = useState<'all' | 'text' | 'image' | 'caption'>('all');

  const visibleItems = activeTab === 'all'
    ? modelConfigItems
    : modelConfigItems.filter(item => {
        if (activeTab === 'text') return item.modelKey === 'text_model';
        if (activeTab === 'image') return item.modelKey === 'image_model';
        if (activeTab === 'caption') return item.modelKey === 'image_caption_model';
        return true;
      });

  return (
    <div className="rounded-xl border border-gray-200 bg-white shadow-sm dark:border-border-primary dark:bg-background-secondary overflow-hidden transition-all">
      {/* Header & Summary */}
      <div className="p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-banana-100 text-banana-800 dark:bg-banana-950/60 dark:text-banana-300 flex items-center justify-center shrink-0">
              <FileText size={18} />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="text-base font-semibold text-gray-900 dark:text-foreground-primary">
                  {isVi ? 'Cấu hình mô hình chi tiết' : 'Detailed Model Configuration'}
                </h3>
                {hasCustomModels ? (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200 dark:bg-blue-950/40 dark:text-blue-300 dark:border-blue-800">
                    <SlidersHorizontal size={11} />
                    {isVi ? 'Đang tùy biến mô hình' : 'Custom Models Active'}
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600 border border-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-700">
                    <Sparkles size={11} className="text-banana-500" />
                    {isVi ? 'Tự động theo nhà cung cấp' : 'Auto via Provider'}
                  </span>
                )}
              </div>
              <p className="text-xs text-gray-500 dark:text-foreground-tertiary mt-0.5">
                {isVi
                  ? 'Mặc định hệ thống tự động sử dụng mô hình phù hợp theo Nhà cung cấp AI đã chọn. Chỉ mở rộng nếu muốn chỉ định mô hình riêng.'
                  : 'By default, the system uses optimal models for the AI provider selected above. Only expand to customize individual models.'}
              </p>
            </div>
          </div>

          <Button
            variant="secondary"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
            icon={isExpanded ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
          >
            {isExpanded
              ? isVi ? 'Thu gọn' : 'Collapse'
              : isVi ? 'Tùy biến mô hình chi tiết' : 'Customize Models'}
          </Button>
        </div>

        {/* Compact Summary Row (always visible to give clear status) */}
        <div className="mt-4 pt-3 border-t border-gray-100 dark:border-border-primary/60 grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
          <div className="p-2.5 rounded-lg bg-gray-50 dark:bg-background-tertiary border border-gray-100 dark:border-border-primary/40 flex items-center justify-between">
            <span className="text-gray-500 dark:text-foreground-tertiary flex items-center gap-1.5">
              <FileText size={13} className="text-blue-500" />
              {isVi ? 'Văn bản:' : 'Text:'}
            </span>
            <span className="font-mono font-medium text-gray-800 dark:text-foreground-secondary truncate max-w-[160px]" title={formData.text_model || 'Tự động'}>
              {formData.text_model || (isVi ? 'Tự động' : 'Default')}
            </span>
          </div>

          <div className="p-2.5 rounded-lg bg-gray-50 dark:bg-background-tertiary border border-gray-100 dark:border-border-primary/40 flex items-center justify-between">
            <span className="text-gray-500 dark:text-foreground-tertiary flex items-center gap-1.5">
              <Image size={13} className="text-emerald-500" />
              {isVi ? 'Tạo ảnh:' : 'Image:'}
            </span>
            <span className="font-mono font-medium text-gray-800 dark:text-foreground-secondary truncate max-w-[160px]" title={formData.image_model || 'Tự động'}>
              {formData.image_model || (isVi ? 'Tự động' : 'Default')}
            </span>
          </div>

          <div className="p-2.5 rounded-lg bg-gray-50 dark:bg-background-tertiary border border-gray-100 dark:border-border-primary/40 flex items-center justify-between">
            <span className="text-gray-500 dark:text-foreground-tertiary flex items-center gap-1.5">
              <Eye size={13} className="text-purple-500" />
              {isVi ? 'Nhận diện:' : 'Vision:'}
            </span>
            <span className="font-mono font-medium text-gray-800 dark:text-foreground-secondary truncate max-w-[160px]" title={formData.image_caption_model || 'Tự động'}>
              {formData.image_caption_model || (isVi ? 'Tự động' : 'Default')}
            </span>
          </div>
        </div>
      </div>

      {/* Expanded Tabbed Content */}
      {isExpanded && (
        <div className="border-t border-gray-200 dark:border-border-primary bg-gray-50/40 dark:bg-background-tertiary/40 p-5 space-y-4">
          {/* Sub-tabs for Models */}
          <div className="flex flex-wrap items-center gap-1.5 p-1 bg-gray-100 dark:bg-background-secondary rounded-lg w-fit">
            <button
              type="button"
              onClick={() => setActiveTab('all')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                activeTab === 'all'
                  ? 'bg-white text-gray-950 shadow-sm dark:bg-background-tertiary dark:text-foreground-primary'
                  : 'text-gray-600 hover:text-gray-900 dark:text-foreground-tertiary dark:hover:text-foreground-primary'
              }`}
            >
              {isVi ? 'Tất cả (3 mô hình)' : 'All (3 Models)'}
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('text')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                activeTab === 'text'
                  ? 'bg-white text-gray-950 shadow-sm dark:bg-background-tertiary dark:text-foreground-primary'
                  : 'text-gray-600 hover:text-gray-900 dark:text-foreground-tertiary dark:hover:text-foreground-primary'
              }`}
            >
              📝 {isVi ? 'Mô hình văn bản' : 'Text Model'}
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('image')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                activeTab === 'image'
                  ? 'bg-white text-gray-950 shadow-sm dark:bg-background-tertiary dark:text-foreground-primary'
                  : 'text-gray-600 hover:text-gray-900 dark:text-foreground-tertiary dark:hover:text-foreground-primary'
              }`}
            >
              🎨 {isVi ? 'Mô hình tạo ảnh' : 'Image Model'}
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('caption')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                activeTab === 'caption'
                  ? 'bg-white text-gray-950 shadow-sm dark:bg-background-tertiary dark:text-foreground-primary'
                  : 'text-gray-600 hover:text-gray-900 dark:text-foreground-tertiary dark:hover:text-foreground-primary'
              }`}
            >
              👁️ {isVi ? 'Mô hình nhận diện ảnh' : 'Vision Model'}
            </button>
          </div>

          {/* Model Form Items */}
          <div className="bg-white dark:bg-background-secondary p-4 rounded-xl border border-gray-200/80 dark:border-border-primary/80 space-y-4">
            {visibleItems.map(renderModelConfigGroup)}
          </div>
        </div>
      )}
    </div>
  );
};
