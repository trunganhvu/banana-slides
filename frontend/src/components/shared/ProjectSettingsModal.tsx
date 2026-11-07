import React, { useState } from 'react';
import { X, FileText, Settings as SettingsIcon, Download, Sparkles, AlertTriangle, HelpCircle, Lightbulb } from 'lucide-react';
import { Button, Textarea, TextStyleSelector } from '@/components/shared';
import { useT } from '@/hooks/useT';
import { Settings } from '@/pages/Settings';
import type { ExportExtractorMethod, ExportInpaintMethod } from '@/types';
import { ASPECT_RATIO_OPTIONS } from '@/config/aspectRatio';

// Component logic
const projectSettingsI18n = {
  zh: {
    projectSettings: {
      title: "Cài đặt", projectConfig: "Cài đặt dự án", exportConfig: "Cài đặt xuất", globalConfig: "Cài đặt chung",
      projectConfigTitle: "Cấu hình cấp dự án", projectConfigDesc: "Các cài đặt này chỉ áp dụng cho dự án hiện tại",
      globalConfigTitle: "Cài đặt chung", globalConfigDesc: "Các cài đặt này áp dụng cho tất cả các dự án",
      aspectRatio: "Tỷ lệ khung hình", aspectRatioDesc: "Đặt tỷ lệ khung hình cho các hình ảnh trang trình chiếu được tạo",
      aspectRatioLocked: "Không thể thay đổi tỷ lệ khung hình sau khi hình ảnh đã được tạo",
      aspectRatioHelp: "Một số mô hình chỉ hỗ trợ các tỷ lệ khung hình cụ thể (ví dụ: 16:9, 4:3, 1:1). Nếu tạo ảnh thất bại, hãy thử chuyển sang tỷ lệ khung hình khác.",
      extraRequirements: "Yêu cầu bổ sung", extraRequirementsDesc: "AI sẽ tham khảo các yêu cầu bổ sung này khi tạo từng trang",
      extraRequirementsPlaceholder: "Ví dụ: Sử dụng bố cục gọn gàng, hiển thị tiêu đề dàn ý cấp 1 ở trên cùng, thêm hình minh họa PPT phong phú hơn...",
      saveExtraRequirements: "Lưu yêu cầu bổ sung",
      styleDescription: "Mô tả phong cách", styleDescriptionDesc: "Mô tả phong cách tổng thể PPT bạn mong muốn, AI sẽ tạo các trang theo phong cách đó",
      styleDescriptionPlaceholder: "Ví dụ: Phong cách kinh doanh đơn giản, sử dụng màu xanh navy và trắng, phông chữ rõ ràng, bố cục gọn gàng...",
      saveStyleDescription: "Lưu mô tả phong cách",
      styleTip: "Mô tả phong cách sẽ tự động được thêm vào prompt khi tạo hình ảnh. Nếu ảnh mẫu cũng được tải lên, mô tả phong cách sẽ đóng vai trò như ghi chú bổ sung.",
      editablePptxExport: "Cài đặt xuất PPTX có thể chỉnh sửa", editablePptxExportDesc: "Cấu hình cách hoạt động của tính năng 'Xuất PPTX có thể chỉnh sửa'. Các cài đặt này ảnh hưởng đến chất lượng xuất và chi phí gọi API.",
      extractorMethod: "Phương pháp trích xuất thành phần", extractorMethodDesc: "Chọn cách trích xuất các thành phần có thể chỉnh sửa như văn bản và bảng từ hình ảnh PPT",
      extractorHybrid: "Trích xuất kết hợp (Khuyên dùng)", extractorHybridDesc: "Phân tích bố cục MinerU + OCR độ chính xác cao Baidu để nhận dạng văn bản chính xác hơn",
      extractorMineru: "Trích xuất MinerU", extractorMineruDesc: "Chỉ sử dụng MinerU để phân tích bố cục và nhận dạng văn bản",
      backgroundMethod: "Phương pháp ảnh nền", backgroundMethodDesc: "Chọn cách tạo ảnh nền sạch (xóa văn bản khỏi ảnh gốc làm nền PPT)",
      backgroundHybrid: "Phương pháp kết hợp (Khuyên dùng)", backgroundHybridDesc: "Xóa chữ chính xác Baidu + nâng cao chất lượng bằng mô hình tạo ảnh",
      backgroundGenerative: "Phương pháp tạo ảnh AI", backgroundGenerativeDesc: "Sử dụng mô hình tạo ảnh (như Gemini) để tạo trực tiếp hình nền, chất lượng cao nhưng có thể còn chi tiết thừa",
      backgroundBaidu: "Phục hồi Baidu", backgroundBaiduDesc: "Sử dụng API phục hồi ảnh của Baidu, nhanh nhưng chất lượng trung bình",
      usesAiModel: "Sử dụng mô hình ảnh AI",
      costTip: "Các tùy chọn có đánh dấu 'Sử dụng mô hình ảnh AI' sẽ gọi API tạo ảnh AI (như Gemini), phát sinh thêm chi phí API theo từng trang. Để tối ưu chi phí, hãy chọn 'Phục hồi Baidu'.",
      iconSubjectExtraction: "Nền trong suốt cho biểu tượng",
      iconSubjectExtractionDesc: "Khi bật, các hình ảnh được phát hiện là biểu tượng trong quá trình xuất sẽ được xử lý qua mô hình RMBG-2.0 cục bộ để tạo PNG nền trong suốt trước khi đưa vào PPT, tránh việc nền gốc của biểu tượng xung đột với nền trang chiếu mới. Chỉ áp dụng cho các phần tử phân loại là biểu tượng; ảnh chụp và hình minh họa vẫn giữ nguyên cắt hình chữ nhật gốc.",
      iconSubjectExtractionTip: "Được hỗ trợ bởi suy luận RMBG-2.0 ONNX cục bộ. Mô hình ~512MB được tải xuống tự động trong lần sử dụng đầu tiên. Nếu trích xuất thất bại đối với một biểu tượng riêng lẻ, hệ thống sẽ tự động dùng lại ảnh chữ nhật gốc mà không ảnh hưởng đến việc xuất.",
      errorHandling: "Chiến lược xử lý lỗi", errorHandlingDesc: "Cấu hình cách xử lý các lỗi xảy ra trong quá trình xuất",
      allowPartialResult: "Cho phép kết quả một phần", allowPartialResultDesc: "Khi bật, quá trình xuất sẽ bỏ qua các lỗi (như trích xuất kiểu hoặc kết xuất văn bản thất bại) và tiếp tục, có thể tạo ra kết quả chưa hoàn chỉnh. Khi tắt, mọi lỗi sẽ dừng quá trình xuất ngay lập tức kèm theo lý do cụ thể.",
      allowPartialResultWarning: "Bật tùy chọn này có thể khiến tệp PPTX bị thiếu kiểu văn bản, định vị sai phần tử hoặc thiếu nội dung. Chỉ nên bật khi bạn cần kết quả nhanh và chấp nhận suy giảm chất lượng.",
      saveExportSettings: "Lưu cài đặt xuất",
      tip: "Mẹo"
    },
    shared: { saving: "Đang lưu..." }
  },
  en: {
    projectSettings: {
      title: "Settings", projectConfig: "Project Settings", exportConfig: "Export Settings", globalConfig: "Global Settings",
      projectConfigTitle: "Project-level Configuration", projectConfigDesc: "These settings only apply to the current project",
      globalConfigTitle: "Global Settings", globalConfigDesc: "These settings apply to all projects",
      aspectRatio: "Aspect Ratio", aspectRatioDesc: "Set the aspect ratio for generated slide images",
      aspectRatioLocked: "Cannot change aspect ratio after images have been generated",
      aspectRatioHelp: "Some models only support specific aspect ratios (e.g. 16:9, 4:3, 1:1). If image generation fails, try switching to a different aspect ratio.",
      extraRequirements: "Extra Requirements", extraRequirementsDesc: "AI will reference these extra requirements when generating each page",
      extraRequirementsPlaceholder: "e.g., Use compact layout, show first-level outline title at top, add richer PPT illustrations...",
      saveExtraRequirements: "Save Extra Requirements",
      styleDescription: "Style Description", styleDescriptionDesc: "Describe your expected PPT overall style, AI will generate pages in that style",
      styleDescriptionPlaceholder: "e.g., Simple business style, use navy blue and white colors, clear fonts, clean layout...",
      saveStyleDescription: "Save Style Description",
      styleTip: "Style description will be automatically added to the prompt when generating images. If a template image is also uploaded, the style description will serve as supplementary notes.",
      editablePptxExport: "Editable PPTX Export Settings", editablePptxExportDesc: "Configure how 'Export Editable PPTX' works. These settings affect export quality and API call costs.",
      extractorMethod: "Component Extraction Method", extractorMethodDesc: "Choose how to extract editable components like text and tables from PPT images",
      extractorHybrid: "Hybrid Extraction (Recommended)", extractorHybridDesc: "MinerU layout analysis + Baidu high-precision OCR for more accurate text recognition",
      extractorMineru: "MinerU Extraction", extractorMineruDesc: "Use only MinerU for layout analysis and text recognition",
      backgroundMethod: "Background Image Method", backgroundMethodDesc: "Choose how to generate clean background images (remove text from original for PPT background)",
      backgroundHybrid: "Hybrid Method (Recommended)", backgroundHybridDesc: "Baidu precise text removal + generative model quality enhancement",
      backgroundGenerative: "Generative Method", backgroundGenerativeDesc: "Use generative model (like Gemini) to directly generate background, high quality but may have residual elements",
      backgroundBaidu: "Baidu Inpainting", backgroundBaiduDesc: "Use Baidu image repair API, fast but average quality",
      usesAiModel: "Uses AI Image Model",
      costTip: "Options marked 'Uses AI Image Model' will call AI image generation API (like Gemini), incurring extra API costs per page. To control costs, choose 'Baidu Inpainting'.",
      iconSubjectExtraction: "Icon Transparent Background",
      iconSubjectExtractionDesc: "When enabled, images detected as icons during export are processed via the local RMBG-2.0 model to produce transparent-background PNGs before being placed in the PPT, avoiding the icon's original background clashing with the new slide background. Only applies to elements classified as icons; photos and illustrations keep the original rectangular crop.",
      iconSubjectExtractionTip: "Powered by local RMBG-2.0 ONNX inference. The ~512MB model is downloaded automatically on first use. If extraction fails for an individual icon, it falls back silently to the original rectangular crop without affecting export.",
      errorHandling: "Error Handling Strategy", errorHandlingDesc: "Configure how to handle errors during export",
      allowPartialResult: "Allow Partial Results", allowPartialResultDesc: "When enabled, export will skip errors (like style extraction or text rendering failures) and continue, potentially resulting in incomplete output. When disabled, any error will stop export immediately with a specific reason.",
      allowPartialResultWarning: "Enabling this option may result in PPTX files with missing text styles, mispositioned elements, or missing content. Only enable when you need quick results and can accept quality loss.",
      saveExportSettings: "Save Export Settings",
      tip: "Tip"
    },
    shared: { saving: "Saving..." }
  }
};

interface ProjectSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  extraRequirements: string;
  templateStyle: string;
  onExtraRequirementsChange: (value: string) => void;
  onTemplateStyleChange: (value: string) => void;
  onSaveExtraRequirements: () => void;
  onSaveTemplateStyle: () => void;
  isSavingRequirements: boolean;
  isSavingTemplateStyle: boolean;
  sourceContent?: string;
  exportExtractorMethod?: ExportExtractorMethod;
  exportInpaintMethod?: ExportInpaintMethod;
  exportAllowPartial?: boolean;
  enableIconSubjectExtraction?: boolean;
  onExportExtractorMethodChange?: (value: ExportExtractorMethod) => void;
  onExportInpaintMethodChange?: (value: ExportInpaintMethod) => void;
  onExportAllowPartialChange?: (value: boolean) => void;
  onEnableIconSubjectExtractionChange?: (value: boolean) => void;
  onSaveExportSettings?: () => void;
  isSavingExportSettings?: boolean;
  aspectRatio?: string;
  onAspectRatioChange?: (value: string) => void;
  onSaveAspectRatio?: () => void;
  isSavingAspectRatio?: boolean;
  hasImages?: boolean;
}

type SettingsTab = 'project' | 'global' | 'export';

export const ProjectSettingsModal: React.FC<ProjectSettingsModalProps> = ({
  isOpen,
  onClose,
  extraRequirements,
  templateStyle,
  onExtraRequirementsChange,
  onTemplateStyleChange,
  onSaveExtraRequirements,
  onSaveTemplateStyle,
  isSavingRequirements,
  isSavingTemplateStyle,
  sourceContent,
  exportExtractorMethod = 'hybrid',
  exportInpaintMethod = 'hybrid',
  exportAllowPartial = false,
  enableIconSubjectExtraction = true,
  onExportExtractorMethodChange,
  onExportInpaintMethodChange,
  onExportAllowPartialChange,
  onEnableIconSubjectExtractionChange,
  onSaveExportSettings,
  isSavingExportSettings = false,
  aspectRatio = '16:9',
  onAspectRatioChange,
  onSaveAspectRatio,
  isSavingAspectRatio = false,
  hasImages = false,
}) => {
  const t = useT(projectSettingsI18n);
  const [activeTab, setActiveTab] = useState<SettingsTab>('project');

  const EXTRACTOR_METHOD_OPTIONS: { value: ExportExtractorMethod; labelKey: string; descKey: string }[] = [
    { value: 'hybrid', labelKey: 'projectSettings.extractorHybrid', descKey: 'projectSettings.extractorHybridDesc' },
    { value: 'mineru', labelKey: 'projectSettings.extractorMineru', descKey: 'projectSettings.extractorMineruDesc' },
  ];

  const INPAINT_METHOD_OPTIONS: { value: ExportInpaintMethod; labelKey: string; descKey: string; usesAI: boolean }[] = [
    { value: 'hybrid', labelKey: 'projectSettings.backgroundHybrid', descKey: 'projectSettings.backgroundHybridDesc', usesAI: true },
    { value: 'generative', labelKey: 'projectSettings.backgroundGenerative', descKey: 'projectSettings.backgroundGenerativeDesc', usesAI: true },
    { value: 'baidu', labelKey: 'projectSettings.backgroundBaidu', descKey: 'projectSettings.backgroundBaiduDesc', usesAI: false },
  ];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-background-secondary rounded-xl shadow-2xl w-full max-w-5xl h-[90vh] flex flex-col overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-border-primary flex-shrink-0">
          <h2 className="text-xl font-bold text-gray-900 dark:text-foreground-primary">{t('projectSettings.title')}</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-background-hover rounded-lg transition-colors"
            aria-label={t('common.close')}
          >
            <X size={20} />
          </button>
        </div>

        <div className="flex-1 flex flex-col md:flex-row overflow-hidden min-h-0">
          <aside className="w-full md:w-64 bg-gray-50 dark:bg-background-primary border-b md:border-b-0 md:border-r border-gray-200 dark:border-border-primary flex-shrink-0">
            <nav className="grid grid-cols-3 gap-2 p-2 md:block md:p-4 md:space-y-2">
              <button
                onClick={() => setActiveTab('project')}
                className={`w-full flex items-center justify-center md:justify-start gap-2 md:gap-3 px-2 md:px-4 py-3 rounded-lg transition-all ${
                  activeTab === 'project'
                    ? 'bg-banana-500 text-white shadow-md'
                    : 'bg-white dark:bg-background-secondary text-gray-700 dark:text-foreground-secondary hover:bg-gray-100 dark:hover:bg-background-hover'
                }`}
              >
                <FileText size={20} />
                <span className="font-medium">{t('projectSettings.projectConfig')}</span>
              </button>
              <button
                onClick={() => setActiveTab('export')}
                className={`w-full flex items-center justify-center md:justify-start gap-2 md:gap-3 px-2 md:px-4 py-3 rounded-lg transition-all ${
                  activeTab === 'export'
                    ? 'bg-banana-500 text-white shadow-md'
                    : 'bg-white dark:bg-background-secondary text-gray-700 dark:text-foreground-secondary hover:bg-gray-100 dark:hover:bg-background-hover'
                }`}
              >
                <Download size={20} />
                <span className="font-medium">{t('projectSettings.exportConfig')}</span>
              </button>
              <button
                onClick={() => setActiveTab('global')}
                className={`w-full flex items-center justify-center md:justify-start gap-2 md:gap-3 px-2 md:px-4 py-3 rounded-lg transition-all ${
                  activeTab === 'global'
                    ? 'bg-banana-500 text-white shadow-md'
                    : 'bg-white dark:bg-background-secondary text-gray-700 dark:text-foreground-secondary hover:bg-gray-100 dark:hover:bg-background-hover'
                }`}
              >
                <SettingsIcon size={20} />
                <span className="font-medium">{t('projectSettings.globalConfig')}</span>
              </button>
            </nav>
          </aside>

          <div className="flex-1 min-w-0 min-h-0 overflow-y-auto p-4 md:p-6">
            {activeTab === 'project' ? (
              <div className="max-w-3xl space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-foreground-primary mb-4">{t('projectSettings.projectConfigTitle')}</h3>
                  <p className="text-sm text-gray-600 dark:text-foreground-tertiary mb-6">
                    {t('projectSettings.projectConfigDesc')}
                  </p>
                </div>

                {/* UI element */}
                <div className="pb-6 border-b border-gray-200 dark:border-border-primary space-y-4">
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <h4 className="text-base font-semibold text-gray-900 dark:text-foreground-primary">{t('projectSettings.aspectRatio')}</h4>
                      <div className="relative group">
                        <button type="button" className="p-1 -m-1 rounded-full focus:outline-none focus:ring-2 focus:ring-banana-500">
                          <HelpCircle size={16} className="text-gray-400 dark:text-foreground-tertiary cursor-help" />
                        </button>
                        <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 w-64 p-2 bg-gray-900 dark:bg-gray-700 text-white text-xs rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible group-focus-within:opacity-100 group-focus-within:visible transition-all z-10 pointer-events-none">
                          {t('projectSettings.aspectRatioHelp')}
                        </div>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-foreground-tertiary">
                      {hasImages ? t('projectSettings.aspectRatioLocked') : t('projectSettings.aspectRatioDesc')}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {ASPECT_RATIO_OPTIONS.map((opt) => (
                      <button
                        key={opt.value}
                        type="button"
                        disabled={hasImages}
                        onClick={() => onAspectRatioChange?.(opt.value)}
                        className={`px-4 py-2 text-sm font-medium rounded-lg border-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed ${
                          aspectRatio === opt.value
                            ? 'border-banana-500 bg-banana-50 dark:bg-background-secondary text-banana-700 dark:text-banana'
                            : 'border-gray-200 dark:border-border-primary text-gray-700 dark:text-foreground-secondary hover:border-gray-300 dark:hover:border-gray-500 bg-white dark:bg-background-secondary'
                        }`}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                  {onSaveAspectRatio && !hasImages && (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={onSaveAspectRatio}
                      disabled={isSavingAspectRatio}
                      className="w-full sm:w-auto"
                    >
                      {isSavingAspectRatio ? t('shared.saving') : t('common.save')}
                    </Button>
                  )}
                </div>

                <div className="pb-6 border-b border-gray-200 dark:border-border-primary space-y-4">
                  <div>
                    <h4 className="text-base font-semibold text-gray-900 dark:text-foreground-primary mb-2">{t('projectSettings.extraRequirements')}</h4>
                    <p className="text-sm text-gray-600 dark:text-foreground-tertiary">
                      {t('projectSettings.extraRequirementsDesc')}
                    </p>
                  </div>
                  <Textarea
                    value={extraRequirements}
                    onChange={(e) => onExtraRequirementsChange(e.target.value)}
                    placeholder={t('projectSettings.extraRequirementsPlaceholder')}
                    rows={4}
                    className="text-sm"
                  />
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={onSaveExtraRequirements}
                    disabled={isSavingRequirements}
                    className="w-full sm:w-auto"
                  >
                    {isSavingRequirements ? t('shared.saving') : t('projectSettings.saveExtraRequirements')}
                  </Button>
                </div>

                <div className="space-y-4">
                  <div>
                    <h4 className="text-base font-semibold text-gray-900 dark:text-foreground-primary mb-2">{t('projectSettings.styleDescription')}</h4>
                    <p className="text-sm text-gray-600 dark:text-foreground-tertiary">
                      {t('projectSettings.styleDescriptionDesc')}
                    </p>
                  </div>
                  <TextStyleSelector
                    value={templateStyle}
                    onChange={onTemplateStyleChange}
                    sourceContent={sourceContent}
                  />
                  <div className="flex flex-col sm:flex-row gap-3">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={onSaveTemplateStyle}
                      disabled={isSavingTemplateStyle}
                      className="w-full sm:w-auto"
                    >
                      {isSavingTemplateStyle ? t('shared.saving') : t('projectSettings.saveStyleDescription')}
                    </Button>
                  </div>
                  <div className="pl-4 border-l-4 border-blue-300 dark:border-blue-600">
                    <p className="text-xs text-gray-700 dark:text-foreground-secondary flex items-start gap-1.5">
                      <Lightbulb size={14} className="flex-shrink-0 mt-0.5" />
                      <span><strong>{t('projectSettings.tip')}: </strong>{t('projectSettings.styleTip')}</span>
                    </p>
                  </div>
                </div>
              </div>
            ) : activeTab === 'export' ? (
              <div className="max-w-3xl space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-foreground-primary mb-4">{t('projectSettings.editablePptxExport')}</h3>
                  <p className="text-sm text-gray-600 dark:text-foreground-tertiary mb-6">
                    {t('projectSettings.editablePptxExportDesc')}
                  </p>
                </div>

                <div className="pb-6 border-b border-gray-200 dark:border-border-primary space-y-4">
                  <div>
                    <h4 className="text-base font-semibold text-gray-900 dark:text-foreground-primary mb-2">{t('projectSettings.extractorMethod')}</h4>
                    <p className="text-sm text-gray-600 dark:text-foreground-tertiary">
                      {t('projectSettings.extractorMethodDesc')}
                    </p>
                  </div>
                  <div className="space-y-3">
                    {EXTRACTOR_METHOD_OPTIONS.map((option) => (
                      <label
                        key={option.value}
                        className={`flex items-start gap-3 p-4 rounded-lg border-2 cursor-pointer transition-all ${
                          exportExtractorMethod === option.value
                            ? 'border-banana-500 bg-banana-50 dark:bg-background-secondary'
                            : 'border-gray-200 dark:border-border-primary hover:border-gray-300 dark:hover:border-gray-500 bg-white dark:bg-background-secondary'
                        }`}
                      >
                        <input
                          type="radio"
                          name="extractorMethod"
                          value={option.value}
                          checked={exportExtractorMethod === option.value}
                          onChange={(e) => onExportExtractorMethodChange?.(e.target.value as ExportExtractorMethod)}
                          className="mt-1 w-4 h-4 text-banana-500 focus:ring-banana-500"
                        />
                        <div className="flex-1">
                          <div className="font-medium text-gray-900 dark:text-foreground-primary">{t(option.labelKey)}</div>
                          <div className="text-sm text-gray-600 dark:text-foreground-tertiary mt-1">{t(option.descKey)}</div>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                <div className="pb-6 border-b border-gray-200 dark:border-border-primary space-y-4">
                  <div>
                    <h4 className="text-base font-semibold text-gray-900 dark:text-foreground-primary mb-2">{t('projectSettings.backgroundMethod')}</h4>
                    <p className="text-sm text-gray-600 dark:text-foreground-tertiary">
                      {t('projectSettings.backgroundMethodDesc')}
                    </p>
                  </div>
                  <div className="space-y-3">
                    {INPAINT_METHOD_OPTIONS.map((option) => (
                      <label
                        key={option.value}
                        className={`flex items-start gap-3 p-4 rounded-lg border-2 cursor-pointer transition-all ${
                          exportInpaintMethod === option.value
                            ? 'border-banana-500 bg-banana-50 dark:bg-background-secondary'
                            : 'border-gray-200 dark:border-border-primary hover:border-gray-300 dark:hover:border-gray-500 bg-white dark:bg-background-secondary'
                        }`}
                      >
                        <input
                          type="radio"
                          name="inpaintMethod"
                          value={option.value}
                          checked={exportInpaintMethod === option.value}
                          onChange={(e) => onExportInpaintMethodChange?.(e.target.value as ExportInpaintMethod)}
                          className="mt-1 w-4 h-4 text-banana-500 focus:ring-banana-500"
                        />
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-gray-900 dark:text-foreground-primary">{t(option.labelKey)}</span>
                            {option.usesAI && (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-300">
                                <Sparkles size={12} />
                                {t('projectSettings.usesAiModel')}
                              </span>
                            )}
                          </div>
                          <div className="text-sm text-gray-600 dark:text-foreground-tertiary mt-1">{t(option.descKey)}</div>
                        </div>
                      </label>
                    ))}
                  </div>
                  <div className="pl-4 border-l-4 border-yellow-300 dark:border-yellow-600 flex items-start gap-2">
                    <AlertTriangle size={16} className="text-yellow-600 dark:text-yellow-500 flex-shrink-0 mt-0.5" />
                    <p className="text-xs text-gray-700 dark:text-foreground-secondary">
                      <strong>{t('projectSettings.tip')}: </strong>{t('projectSettings.costTip')}
                    </p>
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <h4 className="text-base font-semibold text-gray-900 dark:text-foreground-primary mb-2">{t('projectSettings.iconSubjectExtraction')}</h4>
                  </div>
                  <label className="flex items-start gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={enableIconSubjectExtraction}
                      onChange={(e) => onEnableIconSubjectExtractionChange?.(e.target.checked)}
                      className="mt-1 w-4 h-4 text-banana-500 focus:ring-banana-500 rounded"
                    />
                    <div className="flex-1">
                      <div className="font-medium text-gray-900 dark:text-foreground-primary">{t('projectSettings.iconSubjectExtraction')}</div>
                      <div className="text-sm text-gray-600 dark:text-foreground-tertiary mt-1">
                        {t('projectSettings.iconSubjectExtractionDesc')}
                      </div>
                    </div>
                  </label>
                  <div className="pl-4 border-l-4 border-yellow-300 dark:border-yellow-600 flex items-start gap-2">
                    <AlertTriangle size={16} className="text-yellow-600 dark:text-yellow-500 flex-shrink-0 mt-0.5" />
                    <p className="text-xs text-gray-700 dark:text-foreground-secondary">
                      <strong>{t('projectSettings.tip')}: </strong>{t('projectSettings.iconSubjectExtractionTip')}
                    </p>
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <h4 className="text-base font-semibold text-gray-900 dark:text-foreground-primary mb-2">{t('projectSettings.errorHandling')}</h4>
                    <p className="text-sm text-gray-600 dark:text-foreground-tertiary">
                      {t('projectSettings.errorHandlingDesc')}
                    </p>
                  </div>
                  <label className="flex items-start gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={exportAllowPartial}
                      onChange={(e) => onExportAllowPartialChange?.(e.target.checked)}
                      className="mt-1 w-4 h-4 text-red-500 focus:ring-red-500 rounded"
                    />
                    <div className="flex-1">
                      <div className="font-medium text-gray-900 dark:text-foreground-primary">{t('projectSettings.allowPartialResult')}</div>
                      <div className="text-sm text-gray-600 dark:text-foreground-tertiary mt-1">
                        {t('projectSettings.allowPartialResultDesc')}
                      </div>
                    </div>
                  </label>
                  <div className="pl-4 border-l-4 border-red-300 dark:border-red-600 flex items-start gap-2">
                    <AlertTriangle size={16} className="text-red-700 dark:text-red-400 flex-shrink-0 mt-0.5" />
                    <p className="text-xs text-gray-700 dark:text-foreground-secondary">
                      <strong>{t('common.warning')}: </strong>{t('projectSettings.allowPartialResultWarning')}
                    </p>
                  </div>
                </div>

                {onSaveExportSettings && (
                  <div className="flex justify-end pt-4">
                    <Button
                      variant="primary"
                      onClick={onSaveExportSettings}
                      disabled={isSavingExportSettings}
                    >
                      {isSavingExportSettings ? t('shared.saving') : t('projectSettings.saveExportSettings')}
                    </Button>
                  </div>
                )}
              </div>
            ) : (
              <div className="max-w-4xl">
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-foreground-primary mb-2">{t('projectSettings.globalConfigTitle')}</h3>
                  <p className="text-sm text-gray-600 dark:text-foreground-tertiary">
                    {t('projectSettings.globalConfigDesc')}
                  </p>
                </div>
                <Settings />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};