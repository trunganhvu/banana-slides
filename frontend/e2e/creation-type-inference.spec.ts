import { test, expect, type Page } from '@playwright/test';

/**
 * createProject  creation_type
 * 
 */

const CREATE_URL = '**/api/projects';

/**  payload mock  AI  */
async function capturePayload(page: Page, act: () => Promise<void>): Promise<any> {
  let body: any = null;
  await page.route(CREATE_URL, async route => {
    if (route.request().method() !== 'POST') return route.fallback();
    body = route.request().postDataJSON();
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        message: 'Success',
        data: { project_id: 'e2e-fake-id', status: 'DRAFT', pages: [] },
      }),
    });
  });
  await act();
  await expect.poll(() => body, { timeout: 15000 }).not.toBeNull();
  await page.unroute(CREATE_URL);
  return body;
}

async function openHome(page: Page) {
  // Test verification logic
  await page.addInitScript(() => {
    localStorage.setItem('hasSeenHelpModal', 'true');
  });
  await page.goto('/');
  await page.waitForLoadState('domcontentloaded');
  await page.waitForTimeout(800);
}

async function selectTab(page: Page, names: RegExp) {
  await page.getByRole('button', { name: names }).first().click();
  await page.waitForTimeout(300);
}

async function fillContent(page: Page, text: string) {
  // Test verification logic
  const box = page.locator('[contenteditable="true"]').first();
  await box.waitFor({ state: 'visible', timeout: 10000 });
  await box.click();
  await page.keyboard.insertText(text);
  // Test verification logic
  await expect(
    page.getByRole('button', { name: /^(|Next)$/ }).first()
  ).toBeEnabled({ timeout: 10000 });
}

async function clickCreate(page: Page) {
  // Test verification logic
  await page
    .getByRole('button', { name: /^(|Next)$/ })
    .first()
    .click();
}

test.describe('creation_type ', () => {
  test(' -> idea', async ({ page }) => {
    await openHome(page);
    await selectTab(page, /|From Idea/);
    await fillContent(page, 'AI ');
    const body = await capturePayload(page, () => clickCreate(page));

    expect(body.creation_type).toBe('idea');
    expect(body.idea_prompt).toBe('AI ');
    expect(body.outline_text).toBeUndefined();
    expect(body.description_text).toBeUndefined();
  });

  test(' -> outline', async ({ page }) => {
    await openHome(page);
    await selectTab(page, /|From Outline/);
    await fillContent(page, '');
    const body = await capturePayload(page, () => clickCreate(page));

    expect(body.creation_type).toBe('outline');
    expect(body.outline_text).toBe('');
    expect(body.idea_prompt).toBeUndefined();
  });

  test(' -> descriptions', async ({ page }) => {
    await openHome(page);
    await selectTab(page, /|From Description/);
    await fillContent(page, '');
    const body = await capturePayload(page, () => clickCreate(page));

    // Test verification logic
    expect(body.creation_type).toBe('descriptions');
    expect(body.description_text).toBe('');
    expect(body.idea_prompt).toBeUndefined();
  });

  test(' -> blank', async ({ page }) => {
    await openHome(page);
    const body = await capturePayload(page, async () => {
      await page
        .getByRole('button', { name: /|Or start from a blank project/ })
        .first()
        .click();
    });

    expect(body.creation_type).toBe('blank');
    expect(body.idea_prompt).toBeUndefined();
    expect(body.outline_text).toBeUndefined();
    expect(body.description_text).toBeUndefined();
  });
});