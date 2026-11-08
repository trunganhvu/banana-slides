import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { TextStyleSelector } from '@/components/shared/TextStyleSelector';
import * as endpoints from '@/api/endpoints';

vi.mock('@/api/endpoints', () => ({
  extractStyleFromImage: vi.fn(),
  generateStyleFromContent: vi.fn(),
  listUserStyleTemplates: vi.fn().mockResolvedValue({ data: { templates: [] } }),
  createUserStyleTemplate: vi.fn(),
  deleteUserStyleTemplate: vi.fn(),
}));

describe('TextStyleSelector Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders correctly with default props', () => {
    render(<TextStyleSelector value="" onChange={vi.fn()} />);
    expect(screen.getByRole('button', { name: /Generate from content|Tự động tạo theo nội dung/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Extract from image|Trích xuất từ hình ảnh/i })).toBeInTheDocument();
  });

  it('shows error toast when sourceContent is empty and generate button clicked', () => {
    const handleToast = vi.fn();
    render(<TextStyleSelector value="" onChange={vi.fn()} onToast={handleToast} sourceContent="" />);

    const generateBtn = screen.getByRole('button', { name: /Generate from content|Tự động tạo theo nội dung/i });
    fireEvent.click(generateBtn);

    expect(handleToast).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'error',
      })
    );
    expect(endpoints.generateStyleFromContent).not.toHaveBeenCalled();
  });

  it('calls generateStyleFromContent and updates value when sourceContent is provided', async () => {
    const handleChange = vi.fn();
    const handleToast = vi.fn();
    (endpoints.generateStyleFromContent as any).mockResolvedValueOnce({
      data: { style_description: '\n#0B0F19' },
    });

    render(
      <TextStyleSelector
        value=""
        onChange={handleChange}
        onToast={handleToast}
        sourceContent="AI Presentation"
      />
    );

    const generateBtn = screen.getByRole('button', { name: /Generate from content|Tự động tạo theo nội dung/i });
    fireEvent.click(generateBtn);

    await waitFor(() => {
      expect(endpoints.generateStyleFromContent).toHaveBeenCalledWith('AI Presentation', expect.any(String));
      expect(handleChange).toHaveBeenCalledWith('\n#0B0F19');
      expect(handleToast).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'success',
        })
      );
    });
  });

  it('handles error gracefully when generateStyleFromContent fails', async () => {
    const handleChange = vi.fn();
    const handleToast = vi.fn();
    (endpoints.generateStyleFromContent as any).mockRejectedValueOnce(
      new Error('Network error')
    );

    render(
      <TextStyleSelector
        value=""
        onChange={handleChange}
        onToast={handleToast}
        sourceContent="AI Presentation"
      />
    );

    const generateBtn = screen.getByRole('button', { name: /Generate from content|Tự động tạo theo nội dung/i });
    fireEvent.click(generateBtn);

    await waitFor(() => {
      expect(handleToast).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'error',
        })
      );
      expect(handleChange).not.toHaveBeenCalled();
    });
  });
});
