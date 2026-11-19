import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { HtmlSlidePreview } from '@/components/preview/HtmlSlidePreview';
import { DescriptionCard } from '@/components/preview/DescriptionCard';
import type { Page } from '@/types';

vi.mock('@/hooks/useT', () => ({
  useT: () => (key: string) => key,
}));

vi.mock('@/api/client', () => ({
  getImageUrl: (path: string) => `http://localhost:5011${path}`,
}));

vi.mock('@/api/endpoints', () => ({
  updatePage: vi.fn().mockResolvedValue({}),
  uploadDescriptionImage: vi.fn(),
  getMaterials: vi.fn().mockResolvedValue({ data: { materials: [] } }),
  extractFileContent: vi.fn(),
}));

vi.mock('@/hooks/useGeneratingState', () => ({
  useDescriptionGeneratingState: () => false,
}));

vi.mock('@/components/shared/MarkdownTextarea', () => ({
  MarkdownTextarea: ({ value, onChange, placeholder }: { value: string; onChange: (v: string) => void; placeholder?: string }) => (
    <textarea value={value} placeholder={placeholder} onChange={(e) => onChange(e.target.value)} />
  ),
}));

describe('HtmlSlidePreview & DescriptionCard HTML preview', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders null when neither htmlUrl nor htmlContent is provided', () => {
    const { container } = render(<HtmlSlidePreview />);
    expect(container.firstChild).toBeNull();
  });

  it('renders sandboxed iframe for htmlUrl with resolved URL and scaled viewport', () => {
    render(
      <HtmlSlidePreview
        htmlUrl="/files/proj-1/pages/page-1.html"
        title="Slide 1 Title"
        aspectRatio="4:3"
        allowFullscreen
      />
    );

    const wrapper = screen.getByTestId('html-slide-preview');
    expect(wrapper).toBeInTheDocument();

    const iframe = screen.getByTitle('Slide 1 Title') as HTMLIFrameElement;
    expect(iframe).toBeInTheDocument();
    expect(iframe.getAttribute('src')).toBe('http://localhost:5011/files/proj-1/pages/page-1.html');
    expect(iframe.getAttribute('sandbox')).toBe('allow-scripts allow-same-origin');
    expect(iframe.style.width).toBe('1024px');
    expect(iframe.style.height).toBe('768px');

    const zoomBtn = screen.getByRole('button', { name: 'Fullscreen: Slide 1 Title' });
    fireEvent.click(zoomBtn);
    expect(screen.getAllByTitle('Slide 1 Title').length).toBe(2);
  });

  it('supports inline srcDoc rendering via htmlContent', () => {
    render(
      <HtmlSlidePreview
        htmlContent="<html><body><h1>Hello Slide</h1></body></html>"
        title="Inline HTML Slide"
        interactive
      />
    );

    const iframe = screen.getByTitle('Inline HTML Slide') as HTMLIFrameElement;
    expect(iframe.getAttribute('srcdoc')).toContain('Hello Slide');
    expect(iframe.style.pointerEvents).toBe('auto');
  });

  it('renders HtmlSlidePreview and synthesized description inside DescriptionCard when html_slide_url exists', () => {
    const htmlPage: Page = {
      id: 'page-html-1',
      order_index: 0,
      part: 'Overview',
      outline_content: {
        title: 'Revenue Growth Deck',
        points: ['Point 1', 'Point 2'],
      },
      description_content: {
        text: 'Synthesized reverse description from HTML slide.',
        extra_fields: {
          'Hình ảnh & Tư liệu': 'Dark gradient bar chart.',
        },
      },
      html_slide_url: '/files/proj-1/pages/page-html-1.html',
      status: 'DESCRIPTION_GENERATED',
    };

    render(
      <DescriptionCard
        page={htmlPage}
        index={0}
        projectId="proj-1"
        aspectRatio="16:9"
        extraFieldNames={['Hình ảnh & Tư liệu']}
        showToast={vi.fn()}
        onUpdate={vi.fn()}
        onRegenerate={vi.fn()}
      />
    );

    expect(screen.getByText('HTML Slide')).toBeInTheDocument();
    expect(screen.getByTestId('html-slide-preview')).toBeInTheDocument();
    const iframe = screen.getByTitle('Revenue Growth Deck') as HTMLIFrameElement;
    expect(iframe.getAttribute('src')).toBe('http://localhost:5011/files/proj-1/pages/page-html-1.html');
    expect(screen.getByText('Revenue Growth Deck')).toBeInTheDocument();
    expect(screen.getByText('Synthesized reverse description from HTML slide.')).toBeInTheDocument();
  });
});
