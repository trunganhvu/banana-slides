import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { act } from 'react';
import { SettingsAbout } from '@/pages/Settings';

vi.mock('@/utils/appVersion', () => ({
  appVersion: {
    display: 'v9.9.9',
    detail: 'v9.9.9 (abcdef1234567890)',
  },
}));

const checkForUpdates = vi.fn();

vi.mock('@/api/endpoints', () => ({
  checkForUpdates: () => checkForUpdates(),
}));

const labels: Record<string, string> = {
  'settings.sections.about': '',
  'settings.about.version': '',
  'settings.about.source': 'GitHub ',
  'settings.about.checkUpdate': '',
  'settings.about.checking': '...',
  'settings.about.upToDate': '',
  'settings.about.updateAvailable': '{{version}}',
  'settings.about.unknown': '',
  'settings.about.resultTitle': '',
  'settings.about.download': '',
  'settings.about.close': '',
};

const t = (key: string, vars?: Record<string, string>) => {
  let value = labels[key] || key;
  Object.entries(vars || {}).forEach(([varKey, varValue]) => {
    value = value.replace(`{{${varKey}}}`, varValue);
  });
  return value;
};

describe('SettingsAbout', () => {
  it('shows the current app version in settings', () => {
    render(<SettingsAbout t={t} />);

    expect(screen.getByText('')).toBeInTheDocument();
    expect(screen.getByText(': v9.9.9')).toBeInTheDocument();
    expect(screen.getByLabelText(' v9.9.9 (abcdef1234567890)')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'GitHub ' })).toHaveAttribute('href', 'https://github.com/Anionex/banana-slides');
  });

  it('shows a user-friendly message when an update is available', async () => {
    checkForUpdates.mockResolvedValueOnce({
      data: {
        status: 'update_available',
        update_available: true,
        message: 'A newer Docker image is available.',
        repository: 'anoinex/banana-slides',
        current: { short_sha: '1111111', is_docker: true },
        latest: {
          tag: 'latest',
          sha: '2222222333333333344444444444555555555555',
          image: 'anoinex/banana-slides:latest',
          last_updated: '2026-06-01T08:11:22Z',
        },
      },
    });

    render(<SettingsAbout t={t} />);
    await act(async () => {
      await userEvent.click(screen.getByRole('button', { name: // }));
    });

    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).getByText('2222222')).toBeInTheDocument();
    expect(within(dialog).getByTestId('update-available-icon')).toBeInTheDocument();
    expect(within(dialog).getByText('')).toBeInTheDocument();
    expect(within(dialog).queryByText(/Docker Hub/)).not.toBeInTheDocument();
    expect(within(dialog).queryByText(//)).not.toBeInTheDocument();
    expect(within(dialog).queryByText(/SHA/i)).not.toBeInTheDocument();
  });

  it('shows a green check when the app is up to date', async () => {
    render(<SettingsAbout t={t} />);

    checkForUpdates.mockResolvedValueOnce({
      data: {
        status: 'up_to_date',
        update_available: false,
        message: 'Current image is up to date.',
        repository: 'anoinex/banana-slides',
        current: { short_sha: '2222222', is_docker: true },
        latest: {
          tag: 'latest',
          sha: '2222222',
          image: 'anoinex/banana-slides:latest',
          last_updated: '2026-06-01T08:11:22Z',
        },
      },
    });

    await act(async () => {
      await userEvent.click(screen.getByRole('button', { name: // }));
    });

    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).getByText('')).toBeInTheDocument();
    expect(within(dialog).getByTestId('update-success-icon')).toBeInTheDocument();
    expect(within(dialog).queryByText(/Docker Hub/)).not.toBeInTheDocument();
  });
});