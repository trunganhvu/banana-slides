import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright E2E -  UI 
 * 
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  // Logic
  testDir: './e2e',
  
  // Logic
  testMatch: '**/*.spec.ts',
  
  // Logic
  fullyParallel: true,
  
  // Logic
  forbidOnly: !!process.env.CI,
  
  // Logic
  retries: 0,
  
  // Logic
  workers: process.env.CI ? 1 : undefined,
  
  // Logic
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list'],
    ...(process.env.CI ? [['github'] as const] : []),
  ],
  
  // Logic
  use: {
    // Logic
    baseURL: process.env.BASE_URL || 'http://localhost:3011',
    
    // Logic
    screenshot: 'only-on-failure',
    
    // Logic
    video: 'retain-on-failure',
    
    // Logic
    trace: 'retain-on-failure',
    
    // Logic
    locale: 'zh-CN',

    // Logic
    actionTimeout: 15000,
    navigationTimeout: 30000,
  },
  
  // Logic
  timeout: 60000,
  
  // Logic
  expect: {
    timeout: 10000,
  },
  
  // Logic
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  
  // Logic
  webServer: process.env.CI ? undefined : {
    command: 'cd .. && docker compose up -d && sleep 10',
    url: 'http://localhost:3011',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
})