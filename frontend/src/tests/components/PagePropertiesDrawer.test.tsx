import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PagePropertiesDrawer, getExtraFields, normKey, LEGACY_MAP } from '@/components/preview/PagePropertiesDrawer';

describe('PagePropertiesDrawer normKey and extraFields', () => {
  it('exports normKey function and maps legacy fields correctly', () => {
    expect(typeof normKey).toBe('function');
    expect(normKey('\u914d\u56fe\u4e0e\u7d20\u6750')).toBe('Hình ảnh & Tư liệu');
    expect(normKey('\u7248\u5f0f\u4e0e\u91cd\u70b9')).toBe('Bố cục & Trọng tâm');
    expect(normKey('\u6f14\u8bb2\u8005\u5907\u6ce8')).toBe('Ghi chú thuyết trình');
    expect(normKey('Custom Field')).toBe('Custom Field');
  });

  it('normalizes legacy keys in getExtraFields', () => {
    const descContent = {
      text: 'Test description',
      extra_fields: {
        '\u914d\u56fe\u4e0e\u7d20\u6750': 'Legacy image requirements',
        'Custom': 'Custom notes',
      },
    };
    const fields = getExtraFields(descContent);
    expect(fields['Hình ảnh & Tư liệu']).toBe('Legacy image requirements');
    expect(fields['Custom']).toBe('Custom notes');
  });

  it('renders correctly when open with page data without crashing', () => {
    const dummyPage: any = {
      id: 'p-1',
      order_index: 0,
      status: 'DRAFT',
      outline_content: { title: 'Slide Title', points: ['Point 1', 'Point 2'] },
      description_content: { text: 'Slide description' },
      template_style_text: 'Minimal modern',
    };

    render(
      <PagePropertiesDrawer
        page={dummyPage}
        projectId="proj-1"
        pageIndex={0}
        pageCount={1}
        isOpen={true}
        onToggle={vi.fn()}
        onUpdate={vi.fn()}
        onUpdatePageTemplate={vi.fn().mockResolvedValue(undefined)}
        onOpenTemplateSetup={vi.fn()}
        showToast={vi.fn()}
      />
    );

    expect(screen.getByTestId('page-properties-drawer')).toBeInTheDocument();
  });
});
