import React, { useState, useRef, useCallback } from 'react';
import { Edit2, FileText, RefreshCw, Tag, Layout, Image, Focus, MessageSquare, ImageOff } from 'lucide-react';
import { useT } from '@/hooks/useT';
import { useImagePaste, buildMaterialsMarkdown } from '@/hooks/useImagePaste';
import { Card, ContextualStatusBadge, Button, Modal, Skeleton, Markdown, MaterialSelector } from '@/components/shared';
import { MarkdownTextarea, type MarkdownTextareaRef } from '@/components/shared/MarkdownTextarea';
import { useDescriptionGeneratingState } from '@/hooks/useGeneratingState';
import type { Page, DescriptionContent, Material } from '@/types';

// Component logic
const descriptionCardI18n = {
  zh: {
    descriptionCard: {
      page: "Trang {{num}}", regenerate: "Tạo lại",
      descriptionTitle: "Chỉnh sửa mô tả trang", description: "Văn bản trang",
      noDescription: "Chưa có mô tả nào được tạo",
      uploadingImage: "Đang tải ảnh lên...",
      descriptionPlaceholder: "Chỉ nhập văn bản hiển thị trên trang (tiêu đề, ý chính, số liệu); yêu cầu hình ảnh và bố cục vui lòng điền vào các trường bên dưới.",
      coverPage: "Bìa",
      coverPageTooltip: "Trang đầu tiên là trang bìa, mặc định giữ phong cách tối giản",
      notInImagePrompt: "Không dùng khi tạo ảnh"
    }
  },
  en: {
    descriptionCard: {
      page: "Page {{num}}", regenerate: "Regenerate",
      descriptionTitle: "Edit Descriptions", description: "Page Text",
      noDescription: "No description generated yet",
      uploadingImage: "Uploading image...",
      descriptionPlaceholder: "Only the text to be rendered on the slide (title, points, data); put visuals and layout requirements in the fields below. Supports pasting images",
      coverPage: "Cover",
      coverPageTooltip: "This is the cover page, default to keep simple style",
      notInImagePrompt: "Not used in image generation"
    }
  }
};

export interface DescriptionCardProps {
  page: Page;
  index: number;
  projectId?: string;
  extraFieldNames?: string[];
  imagePromptFields?: string[];
  showToast: (props: { message: string; type: 'success' | 'error' | 'info' | 'warning' }) => void;
  onUpdate: (data: Partial<Page>) => void;
  onRegenerate: () => void;
  isAiRefining?: boolean;
}

// Component logic
const getDescriptionText = (descContent: DescriptionContent | undefined): string => {
  if (!descContent) return '';
  if ('text' in descContent) {
    return descContent.text;
  } else if ('text_content' in descContent && Array.isArray(descContent.text_content)) {
    return descContent.text_content.join('\n');
  }
  return '';
};

// Component logic
const getExtraFields = (descContent: DescriptionContent | undefined): Record<string, string> => {
  if (!descContent) return {};
  if (descContent.extra_fields) return descContent.extra_fields;
  // Component logic
  if (descContent.layout_suggestion) return { 'Gợi ý bố cục': descContent.layout_suggestion };
  return {};
};

// Component logic
const getExtraFieldsKey = (descContent: DescriptionContent | undefined): string => {
  const fields = getExtraFields(descContent);
  return JSON.stringify(fields);
};

export const DescriptionCard: React.FC<DescriptionCardProps> = React.memo(({
  page,
  index,
  projectId,
  extraFieldNames = [],
  imagePromptFields,
  showToast,
  onUpdate,
  onRegenerate,
  isAiRefining = false,
}) => {
  const t = useT(descriptionCardI18n);

  const text = getDescriptionText(page.description_content);
  const extraFields = getExtraFields(page.description_content);

  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState('');
  const [isMaterialSelectorOpen, setIsMaterialSelectorOpen] = useState(false);
  const [editExtraFields, setEditExtraFields] = useState<Record<string, string>>({});
  const textareaRef = useRef<MarkdownTextareaRef>(null);
  const extraFieldRefs = useRef<Record<string, MarkdownTextareaRef | null>>({});

  // Active field target for image paste — switched via onFocus
  const activeSetContent = useRef<(updater: (prev: string) => string) => void>(setEditContent);
  const activeInsertAtCursor = useRef<((markdown: string) => void) | undefined>(
    () => textareaRef.current?.insertAtCursor('')
  );

  const { handlePaste, handleFiles, isUploading } = useImagePaste({
    projectId,
    setContent: (updater) => activeSetContent.current(updater),
    showToast: showToast,
    insertAtCursor: (md) => activeInsertAtCursor.current?.(md),
  });

  const handleMaterialSelect = useCallback((materials: Material[]) => {
    const setContent = (updater: (prev: string) => string) => activeSetContent.current(updater);
    const markdown = buildMaterialsMarkdown(materials, setContent);
    activeInsertAtCursor.current?.(markdown + '\n');
  }, []);

  // Focus handlers to switch paste target
  const focusMainDesc = useCallback(() => {
    activeSetContent.current = setEditContent;
    activeInsertAtCursor.current = (md: string) => textareaRef.current?.insertAtCursor(md);
  }, []);

  const focusExtraField = useCallback((fieldName: string) => {
    activeSetContent.current = (updater) =>
      setEditExtraFields(prev => ({ ...prev, [fieldName]: updater(prev[fieldName] || '') }));
    activeInsertAtCursor.current = (md: string) => extraFieldRefs.current[fieldName]?.insertAtCursor(md);
  }, []);

  // Component logic
  const generating = useDescriptionGeneratingState(page, isAiRefining);

  const handleEdit = () => {
    // Component logic
    const currentText = getDescriptionText(page.description_content);
    const currentExtraFields = getExtraFields(page.description_content);
    setEditContent(currentText);
    setEditExtraFields({ ...currentExtraFields });
    setIsEditing(true);
  };

  const handleSave = () => {
    // Component logic
    const filteredFields: Record<string, string> = {};
    for (const [key, value] of Object.entries(editExtraFields)) {
      if (value.trim()) {
        filteredFields[key] = value;
      }
    }
    onUpdate({
      description_content: {
        text: editContent,
        ...(Object.keys(filteredFields).length > 0 ? { extra_fields: filteredFields } : {}),
      } as DescriptionContent,
    });
    setIsEditing(false);
  };

  const LEGACY_MAP: Record<string, string> = {
    '\u914d\u56fe\u4e0e\u7d20\u6750': 'Hình ảnh & Tư liệu',
    '\u7248\u5f0f\u4e0e\u91cd\u70b9': 'Bố cục & Trọng tâm',
    '\u6f14\u8bb2\u8005\u5907\u6ce8': 'Ghi chú thuyết trình',
    '\u89c6\u89c9\u5143\u7d20': 'Yếu tố thị giác',
    '\u89c6\u89c9\u7126\u70b9': 'Điểm nhấn thị giác',
    '\u6392\u7248\u5e03\u5c40': 'Bố cục trình bày',
    '\u6392\u7248\u5efa\u8bae': 'Gợi ý bố cục',
  };
  const normKey = (k: string) => LEGACY_MAP[k] || k;
  // Component logic
  const allFieldNames = [...new Set([...extraFieldNames.map(normKey), ...Object.keys(extraFields).map(normKey)])];

  return (
    <>
      <Card className="p-0 overflow-hidden flex flex-col">
        {/* UI element */}
        <div className="bg-banana-50 dark:bg-background-hover px-4 py-3 border-b border-gray-100 dark:border-border-primary flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-gray-900 dark:text-foreground-primary">{t('descriptionCard.page', { num: index + 1 })}</span>
              {index === 0 && (
                <span
                  className="text-xs px-1.5 py-0.5 bg-banana-100 dark:bg-banana-900/30 text-banana-700 dark:text-banana-400 rounded"
                  title={t('descriptionCard.coverPageTooltip')}
                >
                  {t('descriptionCard.coverPage')}
                </span>
              )}
              {page.part && (
                <span className="text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded">
                  {page.part}
                </span>
              )}
            </div>
            <ContextualStatusBadge page={page} context="description" />
          </div>
        </div>

        {/* UI element */}
        <div className="p-4 flex-1 max-h-96 overflow-y-auto desc-card-scroll" data-testid="description-card-content">
          {generating ? (
            <div className="space-y-2">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
              <div className="text-center py-4 text-gray-500 dark:text-foreground-tertiary text-sm">
                {t('common.generating')}
              </div>
            </div>
          ) : text ? (
            <div className="text-sm text-gray-700 dark:text-foreground-secondary">
              <Markdown>{text}</Markdown>
              {allFieldNames.map(name => {
                const value = extraFields[name] || extraFields[Object.keys(LEGACY_MAP).find(k => LEGACY_MAP[k] === name) || ''];
                if (!value) return null;
                // Component logic
                const FIELD_ICONS: Record<string, typeof Tag> = {
                  'Hình ảnh & Tư liệu': Image,
                  'Bố cục & Trọng tâm': Layout,
                  'Ghi chú thuyết trình': MessageSquare,
                  'Yếu tố thị giác': Image,
                  'Điểm nhấn thị giác': Focus,
                  'Bố cục trình bày': Layout,
                  'Gợi ý bố cục': Layout,
                };
                const FieldIcon = FIELD_ICONS[name] || Tag;
                const notInImagePrompt = imagePromptFields && !imagePromptFields.includes(name);
                return (
                  <div key={name} className="mt-3 pt-3 border-t border-gray-100 dark:border-border-primary">
                    <div className="flex items-center gap-1.5 text-xs text-gray-500 dark:text-foreground-tertiary mb-1">
                      <FieldIcon size={12} />
                      <span className="font-medium">{name}</span>
                      {notInImagePrompt && (
                        <span className="relative group/nip">
                          <ImageOff size={11} className="opacity-50" />
                          <span className="absolute left-1/2 -translate-x-1/2 bottom-full mb-1.5 w-max max-w-40 px-2 py-1 text-[10px] leading-snug text-gray-600 dark:text-foreground-secondary bg-white dark:bg-background-primary border border-gray-200 dark:border-border-primary rounded-md shadow-md opacity-0 pointer-events-none group-hover/nip:opacity-100 transition-opacity z-50">
                            {t('descriptionCard.notInImagePrompt')}
                          </span>
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-foreground-tertiary"><Markdown>{value}</Markdown></div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-400 dark:text-foreground-tertiary">
              <div className="flex text-3xl mb-2 justify-center"><FileText className="text-gray-400 dark:text-foreground-tertiary" size={48} /></div>
              <p className="text-sm">{t('descriptionCard.noDescription')}</p>
            </div>
          )}
        </div>

        {/* UI element */}
        <div className="border-t border-gray-100 dark:border-border-primary px-4 py-3 flex justify-end gap-2 mt-auto flex-shrink-0">
          <Button
            variant="ghost"
            size="sm"
            icon={<Edit2 size={16} />}
            onClick={handleEdit}
            disabled={generating}
            className="no-min-touch-target"
          >
            {t('common.edit')}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            icon={<RefreshCw size={16} className={generating ? 'animate-spin' : ''} />}
            onClick={onRegenerate}
            disabled={generating}
            className="no-min-touch-target"
          >
            {generating ? t('common.generating') : t('descriptionCard.regenerate')}
          </Button>
        </div>
      </Card>

      {/* UI element */}
      <Modal
        isOpen={isEditing}
        onClose={() => setIsEditing(false)}
        title={t('descriptionCard.descriptionTitle')}
        size="lg"
      >
        <div className="space-y-4">
          <MarkdownTextarea
            ref={textareaRef}
            label={t('descriptionCard.description')}
            value={editContent}
            onChange={setEditContent}
            onPaste={handlePaste}
            onFiles={handleFiles}
            onSelectFromLibrary={() => setIsMaterialSelectorOpen(true)}
            onFocus={focusMainDesc}
            rows={6}
            placeholder={t('descriptionCard.descriptionPlaceholder')}
          />
          {/* UI element */}
          {allFieldNames.map(name => (
            <MarkdownTextarea
              key={name}
              ref={el => { extraFieldRefs.current[name] = el; }}
              label={name}
              value={editExtraFields[name] || ''}
              onChange={v => setEditExtraFields(prev => ({ ...prev, [name]: v }))}
              onPaste={handlePaste}
              onFiles={handleFiles}
              onFocus={() => focusExtraField(name)}
              showUploadButton={false}
              rows={2}
              placeholder={name}
            />
          ))}
          <div className="flex justify-end gap-3 pt-4">
            <Button variant="ghost" onClick={() => setIsEditing(false)}>
              {t('common.cancel')}
            </Button>
            <Button variant="primary" onClick={handleSave} disabled={isUploading}>
              {t('common.save')}
            </Button>
          </div>
        </div>
      </Modal>

      <MaterialSelector
        projectId={projectId}
        isOpen={isMaterialSelectorOpen}
        onClose={() => setIsMaterialSelectorOpen(false)}
        onSelect={handleMaterialSelect}
        multiple
      />
    </>
  );
}, (prev, next) =>
  prev.index === next.index &&
  prev.isAiRefining === next.isAiRefining &&
  prev.projectId === next.projectId &&
  prev.page.id === next.page.id &&
  prev.page.status === next.page.status &&
  prev.page.part === next.page.part &&
  getDescriptionText(prev.page.description_content) === getDescriptionText(next.page.description_content) &&
  getExtraFieldsKey(prev.page.description_content) === getExtraFieldsKey(next.page.description_content) &&
  JSON.stringify(prev.extraFieldNames) === JSON.stringify(next.extraFieldNames) &&
  JSON.stringify(prev.imagePromptFields) === JSON.stringify(next.imagePromptFields)
);