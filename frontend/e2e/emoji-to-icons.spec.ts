import { test, expect, type Page } from '@playwright/test';

/**  emoji  lucide  /  */

async function openHome(page: Page) {
  await page.addInitScript(() => localStorage.setItem('hasSeenHelpModal', 'true'));
  await page.goto('/');
  await page.waitForLoadState('domcontentloaded');
  await page.waitForTimeout(800);
}

/**  pptx */
async function attachFakePptx(page: Page) {
  await page.locator('input[accept=".pdf,.pptx,.ppt"]').setInputFiles({
    name: 'demo.pptx',
    mimeType: 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    buffer: Buffer.from('fake pptx for e2e'),
  });
}

test('tagline  🍌', async ({ page }) => {
  await openHome(page);
  const tagline = page.getByText(/nano banana pro/).first();
  await expect(tagline).toBeVisible();
  expect(await tagline.textContent()).not.toContain('🍌');
});

test(' pptx  toast  💡 ', async ({ page }) => {
  await openHome(page);
  await page.getByRole('button', { name: /PPT |PPT Renovation/ }).first().click();
  await page.waitForTimeout(400);

  await attachFakePptx(page);

  const toast = page.getByText(/ PPTX  PDF|recommend converting/i).first();
  await expect(toast).toBeVisible({ timeout: 10000 });
  expect(await toast.textContent()).not.toContain('💡');
});

test(' lucide  ✕ ', async ({ page }) => {
  await openHome(page);
  await page.getByRole('button', { name: /PPT |PPT Renovation/ }).first().click();
  await page.waitForTimeout(400);

  await attachFakePptx(page);

  const chip = page.getByText('demo.pptx').first();
  await expect(chip).toBeVisible({ timeout: 10000 });

  // Test verification logic
  const removeBtn = page
    .locator('button')
    .filter({ has: page.locator('svg.lucide-x') })
    .first();
  await expect(removeBtn).toBeVisible();
  expect(await removeBtn.textContent()).not.toContain('✕');

  // Test verification logic
  await removeBtn.click();
  await expect(page.getByText('demo.pptx')).toHaveCount(0);
});