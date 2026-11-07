import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://localhost:3011';

test.describe('Generate Style from Content E2E', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => localStorage.setItem('hasSeenHelpModal', 'true'));
  });

  test('generates style from home content input and applies to text area', async ({ page }) => {
    // Mock the backend generate-style-from-content API
    await page.route((url) => url.pathname.startsWith('/api/generate-style-from-content'), async (route) => {
      const json = {
        success: true,
        message: 'Success',
        data: {
          style_description: '\n#FFFFFF#0284C7\n\n',
        },
      };
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(json),
      });
    });

    await page.goto(BASE_URL);

    // Test verification logic
    const toggle = page.getByText(/|Use text description for style/);
    await toggle.scrollIntoViewIfNeeded();
    await toggle.click();

    // Test verification logic
    const generateStyleBtn = page.getByRole('button', { name: /|Generate from content/i });
    await expect(generateStyleBtn).toBeVisible();
    await generateStyleBtn.click();

    // Verify error toast for empty content
    await expect(page.locator('text= PPT ').or(page.locator('text=Please enter PPT topic or content first'))).toBeVisible();

    // Now type some content in the main idea/outline input (the first textbox on page)
    const contentInput = page.getByRole('textbox').first();
    await contentInput.fill('AI');

    // Test verification logic
    await generateStyleBtn.click();

    // Verify success toast
    await expect(page.locator('text=').or(page.locator('text=Style generated successfully'))).toBeVisible();

    // Verify that the style textarea now has the generated style description
    const styleTextarea = page.locator('textarea[placeholder*=""], textarea[placeholder*="Describe your desired PPT style"]');
    await expect(styleTextarea).toHaveValue(//);
  });
});


