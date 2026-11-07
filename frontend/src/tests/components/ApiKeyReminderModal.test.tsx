import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ApiKeyReminderModal } from '@/components/shared/ApiKeyReminderModal';
import { useApiKeyReminderStore } from '@/store/useApiKeyReminderStore';

const mockedNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockedNavigate,
  };
});

describe('ApiKeyReminderModal', () => {
  beforeEach(() => {
    mockedNavigate.mockReset();
    sessionStorage.clear();
    useApiKeyReminderStore.setState({
      isConfigured: false,
      isChecking: false,
      isModalOpen: true,
      isFloatingDismissed: false,
      settings: null,
    });
  });

  it('renders modal with reminder information when key is not configured', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <ApiKeyReminderModal />
      </MemoryRouter>
    );

    expect(screen.getByText('Chưa cấu hình API Key')).toBeInTheDocument();
    expect(screen.getByText('Đi tới Cài đặt cấu hình')).toBeInTheDocument();
    expect(screen.getByText('Nhắc tôi sau')).toBeInTheDocument();
  });

  it('navigates to /settings when clicking primary action button', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <ApiKeyReminderModal />
      </MemoryRouter>
    );

    const goButton = screen.getByText('Đi tới Cài đặt cấu hình');
    fireEvent.click(goButton);

    expect(mockedNavigate).toHaveBeenCalledWith('/settings');
    expect(useApiKeyReminderStore.getState().isModalOpen).toBe(false);
  });

  it('dismisses modal and shows floating reminder pill when clicking remind later', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <ApiKeyReminderModal />
      </MemoryRouter>
    );

    const remindLaterBtn = screen.getByText('Nhắc tôi sau');
    fireEvent.click(remindLaterBtn);

    expect(useApiKeyReminderStore.getState().isModalOpen).toBe(false);
  });

  it('does not render anything on /settings path', () => {
    render(
      <MemoryRouter initialEntries={['/settings']}>
        <ApiKeyReminderModal />
      </MemoryRouter>
    );

    expect(screen.queryByText('Chưa cấu hình API Key')).not.toBeInTheDocument();
  });
});
