import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { Settings as SettingsType } from '@/types';

const mockApiGet = vi.fn();
const mockGetSettings = vi.fn();
const mockUpdateSettings = vi.fn();
const mockResetSettings = vi.fn();

const mockAuthState: {
  user: {
    id: string;
    email: string;
    name: string;
    role: 'user' | 'admin';
    login_count: number;
    generation_count: number;
    tokens_in: number;
    tokens_out: number;
  } | null;
  token: string | null;
  isLoading: boolean;
  isAuthConfigLoading: boolean;
  isSyncingSession: boolean;
  isBackendReady: boolean;
  googleClientId: string;
  loginWithGoogleCredential: () => Promise<boolean>;
  devLogin: () => Promise<boolean>;
  logout: () => void;
  openLoginModal: () => void;
  closeLoginModal: () => void;
  isLoginModalOpen: boolean;
  renderGoogleButton: () => void;
} = {
  user: null,
  token: 'test-jwt',
  isLoading: false,
  isAuthConfigLoading: false,
  isSyncingSession: false,
  isBackendReady: true,
  googleClientId: '',
  loginWithGoogleCredential: async () => true,
  devLogin: async () => true,
  logout: () => {},
  openLoginModal: () => {},
  closeLoginModal: () => {},
  isLoginModalOpen: false,
  renderGoogleButton: () => {},
};

vi.mock('@/context/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useAuth: () => mockAuthState,
}));

vi.mock('@/api/client', () => ({
  apiClient: {
    get: (...args: unknown[]) => mockApiGet(...args),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
  getBaseURL: () => '',
  getImageUrl: (p?: string) => p || '',
  triggerDownload: vi.fn(),
}));

vi.mock('@/api/endpoints', () => ({
  OUTPUT_LANGUAGE_OPTIONS: [
    { value: 'vi', label: 'Tiếng Việt' },
    { value: 'en', label: 'English' },
  ],
  checkAccessCode: vi.fn().mockResolvedValue({ data: { enabled: false } }),
  verifyAccessCode: vi.fn().mockResolvedValue({ data: { valid: true } }),
  getSettings: () => mockGetSettings(),
  updateSettings: (payload: Record<string, unknown>) => mockUpdateSettings(payload),
  resetSettings: () => mockResetSettings(),
  checkForUpdates: vi.fn(),
  getOpenAIOAuthUrl: vi.fn(),
  disconnectOpenAIOAuth: vi.fn(),
  submitOAuthManualCallback: vi.fn(),
  getOpenAIOAuthStatus: vi.fn(),
  runSettingsTest: vi.fn(),
  getSettingsTestStatus: vi.fn(),
  testBaiduOcr: vi.fn(),
  testTextModel: vi.fn(),
  testCaptionModel: vi.fn(),
  testBaiduInpaint: vi.fn(),
  testImageModel: vi.fn(),
  testMineruPdf: vi.fn(),
}));

vi.mock('@/pages/Home', () => ({
  Home: () => <div data-testid="home-page">Home</div>,
}));

vi.mock('@/pages/Landing', () => ({
  Landing: () => <div data-testid="landing-page">Landing</div>,
}));

vi.mock('@/components/shared/UpdateChecker', () => ({
  UpdateChecker: () => null,
  getDesktopTopInset: () => 0,
}));

vi.mock('@/components/shared/ApiKeyReminderModal', () => ({
  ApiKeyReminderModal: () => null,
}));

vi.mock('@/components/shared/LoginModal', () => ({
  LoginModal: () => null,
}));

import App from '@/App';
import { Settings } from '@/pages/Settings';

const baseSettings: SettingsType = {
  id: 1,
  ai_provider_format: 'gemini',
  api_base_url: '',
  api_key_length: 10,
  image_resolution: '4K',
  image_quality: 'auto',
  image_aspect_ratio: '16:9',
  max_description_workers: 5,
  max_image_workers: 8,
  text_model: 'gemini-3.5-flash-lite',
  image_model: 'gemini-2.5-flash-image',
  mineru_api_base: '',
  mineru_token_length: 0,
  image_caption_model: 'gemini-3.5-flash-lite',
  output_language: 'vi',
  description_generation_mode: 'streaming',
  description_extra_fields: ['Hình ảnh & Tư liệu', 'Bố cục & Trọng tâm'],
  image_prompt_extra_fields: ['Hình ảnh & Tư liệu', 'Bố cục & Trọng tâm'],
  enable_text_reasoning: false,
  text_max_output_tokens: 32768,
  text_thinking_budget: 1024,
  enable_image_reasoning: false,
  image_thinking_budget: 1024,
  enable_image_quality_control: false,
  baidu_api_key_length: 0,
  text_model_source: '',
  image_model_source: '',
  image_caption_model_source: '',
  lazyllm_api_keys_info: {},
  text_api_key_length: 0,
  text_api_base_url: '',
  image_api_key_length: 0,
  image_api_base_url: '',
  image_caption_api_key_length: 0,
  image_caption_api_base_url: '',
  openai_image_api_protocol: 'auto',
  openai_oauth_connected: false,
  elevenlabs_enabled: false,
  elevenlabs_api_key_length: 0,
  elevenlabs_voice_id: '',
};

describe('Admin route access and Settings model/resolution defaults', () => {
  beforeEach(() => {
    mockApiGet.mockReset();
    mockGetSettings.mockReset();
    mockUpdateSettings.mockReset();
    mockResetSettings.mockReset();
    mockAuthState.isLoading = false;
    mockAuthState.isSyncingSession = false;
    mockAuthState.user = null;
  });

  it('renders AdminDashboard at /admin for users with role === "admin"', async () => {
    mockAuthState.user = {
      id: 'admin-1',
      email: 'admin@example.com',
      name: 'Admin User',
      role: 'admin',
      login_count: 5,
      generation_count: 3,
      tokens_in: 1000,
      tokens_out: 2000,
    };

    mockApiGet.mockImplementation((url: string) => {
      if (url === '/api/admin/stats') {
        return Promise.resolve({
          data: {
            code: 0,
            data: {
              total_users: 2,
              total_visits: 10,
              total_generations: 7,
              total_tokens_in: 1200,
              total_tokens_out: 3400,
              total_projects: 4,
            },
          },
        });
      }
      if (url === '/api/admin/users') {
        return Promise.resolve({
          data: {
            code: 0,
            data: {
              users: [
                {
                  id: 'admin-1',
                  email: 'admin@example.com',
                  name: 'Admin User',
                  role: 'admin',
                  login_count: 5,
                  generation_count: 3,
                  tokens_in: 1000,
                  tokens_out: 2000,
                  project_count: 2,
                },
              ],
            },
          },
        });
      }
      return Promise.resolve({ data: {} });
    });

    window.history.pushState({}, '', '/admin');
    render(<App />);

    expect(await screen.findByText('Quản trị hệ thống')).toBeInTheDocument();
    await waitFor(() => {
      expect(mockApiGet).toHaveBeenCalledWith('/api/admin/stats');
      expect(mockApiGet).toHaveBeenCalledWith('/api/admin/users');
    });
    expect(await screen.findByText('admin@example.com')).toBeInTheDocument();
  });

  it('redirects non-admin users away from /admin', async () => {
    mockAuthState.user = {
      id: 'user-1',
      email: 'member@example.com',
      name: 'Member User',
      role: 'user',
      login_count: 1,
      generation_count: 0,
      tokens_in: 0,
      tokens_out: 0,
    };

    window.history.pushState({}, '', '/admin');
    render(<App />);

    expect(await screen.findByTestId('home-page')).toBeInTheDocument();
    expect(screen.queryByText('Quản trị hệ thống')).toBeNull();
  });

  it('normalizes image model to gemini-3.1-flash-lite-image and offers only 1K and 2K resolutions', async () => {
    mockGetSettings.mockResolvedValue({ data: baseSettings });

    render(
      <MemoryRouter>
        <Settings />
      </MemoryRouter>
    );

    expect(await screen.findByDisplayValue('gemini-3.1-flash-lite-image')).toBeInTheDocument();

    const resolutionContainer = screen.getByTestId('setting-image_resolution');
    const select = resolutionContainer.querySelector('select') as HTMLSelectElement;
    expect(select).toBeTruthy();

    const optionValues = Array.from(select.options).map((opt) => opt.value);
    expect(optionValues).toEqual(['1K', '2K']);
    expect(select.value).toBe('2K');
  });
});
