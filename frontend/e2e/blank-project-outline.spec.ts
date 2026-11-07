import { test, expect, type Page, type APIRequestContext } from '@playwright/test';

/**
 * "" UI
 * idea ""
 */

const STREAM_URL = '**/generate/outline/stream';

async function createProject(request: APIRequestContext, body: object): Promise<string> {
  const res = await request.post('/api/projects', { data: body });
  expect(res.ok()).toBeTruthy();
  const json = await res.json();
  return json.data.project_id;
}

/**  idea  AI */
async function blockOutlineStream(page: Page): Promise<() => number> {
  let calls = 0;
  await page.route(STREAM_URL, async route => {
    calls += 1;
    await route.fulfill({ status: 200, contentType: 'text/event-stream', body: '' });
  });
  return () => calls;
}

async function openOutline(page: Page, projectId: string) {
  await page.addInitScript(() => localStorage.setItem('hasSeenHelpModal', 'true'));
  await page.goto(`/project/${projectId}/outline`);
  await page.waitForLoadState('domcontentloaded');
  // Test verification logic
  await expect(page.getByRole('button', { name: /|Add Page/ }).first()).toBeVisible({
    timeout: 15000,
  });
}

const genOutlineBtn = (page: Page) =>
  page.getByRole('button', { name: /||Auto Generate Outline|Parse Outline/ });

/**
 *  CSS class 
 *  DOM  —— ""
 */
const sourceBoxes = (page: Page) => page.locator('[contenteditable="true"]:visible');

test.describe('', () => {
  test('', async ({ page, request }) => {
    const calls = await blockOutlineStream(page);
    const id = await createProject(request, { creation_type: 'blank' });
    await openOutline(page, id);

    await expect(genOutlineBtn(page)).toHaveCount(0);
    await expect(sourceBoxes(page)).toHaveCount(0);

    // Test verification logic
    await page.waitForTimeout(2500);
    expect(calls()).toBe(0);
  });

  test('idea ', async ({ page, request }) => {
    await blockOutlineStream(page);
    const id = await createProject(request, {
      creation_type: 'idea',
      idea_prompt: 'AI ',
    });
    await openOutline(page, id);

    await expect(genOutlineBtn(page).first()).toBeVisible();
    await expect(sourceBoxes(page).first()).toBeVisible();
  });

  test('', async ({ page, request }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await blockOutlineStream(page);
    const id = await createProject(request, { creation_type: 'blank' });
    await openOutline(page, id);

    await expect(sourceBoxes(page)).toHaveCount(0);
    await expect(genOutlineBtn(page)).toHaveCount(0);
  });

  test(' idea ', async ({ page, request }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await blockOutlineStream(page);
    const id = await createProject(request, {
      creation_type: 'idea',
      idea_prompt: 'AI ',
    });
    await openOutline(page, id);

    await expect(sourceBoxes(page).first()).toBeVisible();
  });

  test('', async ({ page, request }) => {
    await blockOutlineStream(page);
    const id = await createProject(request, { creation_type: 'blank' });
    await openOutline(page, id);

    await page.getByRole('button', { name: /|Add Page/ }).first().click();

    // Test verification logic
    await expect(page.getByText(/\s*1\s*|Page\s*1/).first()).toBeVisible({ timeout: 10000 });
    // Test verification logic
    await expect(sourceBoxes(page)).toHaveCount(0);
  });
});

test.describe(' + ', () => {
  test(' multi', async ({ page }) => {
    await page.addInitScript(() => localStorage.setItem('hasSeenHelpModal', 'true'));
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(800);

    let modeBody: any = null;
    await page.route('**/template-mode', async route => {
      modeBody = route.request().postDataJSON();
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, message: 'Success', data: {} }),
      });
    });

    await page.getByText(/|Per-page templates/).first().click();
    await page
      .getByRole('button', { name: /|Or start from a blank project/ })
      .first()
      .click();

    await expect.poll(() => modeBody, { timeout: 20000 }).not.toBeNull();
    expect(modeBody.mode).toBe('multi');
  });
});