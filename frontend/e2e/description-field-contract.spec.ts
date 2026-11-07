import { test, expect } from '@playwright/test';

/**
 *  v2 
 *
 * Mock  UI  AI
 * 
 */

const BASE_URL = process.env.BASE_URL || 'http://localhost:3223';

const NEW_FIELDS = ['Hình ảnh & Tư liệu', 'Bố cục & Trọng tâm', 'Ghi chú thuyết trình'];
const LEGACY_FIELDS = ['Hình ảnh & Tư liệu', 'Bố cục & Trọng tâm', 'Bố cục & Trọng tâm'];

async function createProjectWithPages(page: import('@playwright/test').Page, prompt: string, titles: string[]) {
  const resp = await page.request.post(`${BASE_URL}/api/projects`, {
    data: { creation_type: 'idea', idea_prompt: prompt },
  });
  const projectId = (await resp.json()).data?.project_id;
  expect(projectId).toBeTruthy();

  for (let i = 0; i < titles.length; i++) {
    await page.request.post(`${BASE_URL}/api/projects/${projectId}/pages`, {
      data: {
        order_index: i,
        outline_content: { title: titles[i], points: [` ${i + 1}`] },
        status: 'DRAFT',
      },
    });
  }
  await page.request.put(`${BASE_URL}/api/projects/${projectId}`, {
    data: { status: 'OUTLINE_GENERATED' },
  });
  return projectId;
}

async function setPageDescription(
  page: import('@playwright/test').Page,
  projectId: string,
  pageId: string,
  description_content: Record<string, unknown>,
) {
  const resp = await page.request.put(
    `${BASE_URL}/api/projects/${projectId}/pages/${pageId}/description`,
    { data: { description_content } },
  );
  expect(resp.ok()).toBeTruthy();
}

async function getPages(page: import('@playwright/test').Page, projectId: string) {
  const resp = await page.request.get(`${BASE_URL}/api/projects/${projectId}`);
  return (await resp.json()).data?.pages || [];
}

// Test verification logic

test.describe(' - Mock', () => {
  test('', async ({ page }) => {
    await page.route('**/api/settings', async (route) => {
      if (route.request().method() !== 'GET') return route.continue();
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            description_generation_mode: 'streaming',
            description_extra_fields: NEW_FIELDS,
            image_prompt_extra_fields: ['Hình ảnh & Tư liệu', 'Bố cục & Trọng tâm'],
          },
        }),
      });
    });

    const projectId = await createProjectWithPages(page, '', ['']);
    await page.goto(`${BASE_URL}/project/${projectId}/detail`);
    await page.waitForLoadState('networkidle');

    const gearBtn = page.locator('button[title=""], button[title="Description Settings"]');
    await gearBtn.click();

    for (const field of NEW_FIELDS) {
      await expect(page.locator('button').filter({ hasText: field }).first()).toBeVisible({ timeout: 5000 });
    }
    // Test verification logic
    for (const legacy of LEGACY_FIELDS) {
      await expect(page.locator('button').filter({ hasText: new RegExp(`^${legacy}$`) })).toHaveCount(0);
    }
  });

  test('', async ({ page }) => {
    const projectId = await createProjectWithPages(page, '', ['']);
    const pages = await getPages(page, projectId);

    await setPageDescription(page, projectId, pages[0].page_id, {
      text: '',
      extra_fields: { 'Hình ảnh & Tư liệu': '', 'Bố cục & Trọng tâm': '' },
    });

    await page.goto(`${BASE_URL}/project/${projectId}/detail`);
    await page.waitForLoadState('networkidle');

    await expect(page.locator('text=Hình ảnh & Tư liệu')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=')).toBeVisible();
    await expect(page.locator('text=Bố cục & Trọng tâm')).toBeVisible();
    await expect(page.locator('text=')).toBeVisible();
  });
});

// Test verification logic

test.describe(' - ', () => {
  test('', async ({ page }) => {
    const projectId = await createProjectWithPages(page, '', ['']);
    const pages = await getPages(page, projectId);
    const pageId = pages[0].page_id;

    await setPageDescription(page, projectId, pageId, {
      text: '',
      extra_fields: { 'Hình ảnh & Tư liệu': '', 'Bố cục & Trọng tâm': '' },
    });

    await page.goto(`${BASE_URL}/project/${projectId}/detail`);
    await page.waitForLoadState('networkidle');
    await expect(page.locator('text=')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=')).toBeVisible();

    // Test verification logic
    await page.locator('button').filter({ hasText: /|Edit/ }).first().click();
    const dialog = page.getByRole('dialog');
    // Test verification logic
    await expect(dialog.getByText('', { exact: true })).toBeVisible({ timeout: 5000 });
    await expect(dialog.getByText('Hình ảnh & Tư liệu', { exact: true })).toBeVisible();
    await expect(dialog.getByText('Bố cục & Trọng tâm', { exact: true })).toBeVisible();

    // Test verification logic
    const layoutBox = dialog.getByRole('textbox').nth(2);
    await expect(layoutBox).toHaveText('', { timeout: 5000 });
    // Test verification logic
    await layoutBox.click();
    await page.keyboard.press('ControlOrMeta+a');
    await page.keyboard.insertText('');
    // Test verification logic
    const savePromise = page.waitForResponse(
      (r) => r.url().includes('/description') && r.request().method() === 'PUT' && r.ok(),
    );
    await page.locator('button').filter({ hasText: /^$|^Save$/ }).click();
    await savePromise;

    await page.reload();
    await page.waitForLoadState('networkidle');
    await expect(page.locator('text=')).toBeVisible({ timeout: 5000 });

    // Test verification logic
    const after = await getPages(page, projectId);
    expect(after[0].description_content.extra_fields['Bố cục & Trọng tâm']).toBe('');

    // Test verification logic
    await setPageDescription(page, projectId, pageId, { text: '' });
    await page.reload();
    await page.waitForLoadState('networkidle');
    await expect(page.locator('text=')).toHaveCount(0);
  });

  test(' AI', async ({ page }) => {
    test.setTimeout(240000);

    const resp = await page.request.post(`${BASE_URL}/api/projects`, {
      data: { creation_type: 'idea', idea_prompt: '6 ' },
    });
    const projectId = (await resp.json()).data?.project_id;

    const genResp = await page.request.post(
      `${BASE_URL}/api/projects/${projectId}/generate/outline`,
      { data: {}, timeout: 180000 },
    );
    expect(genResp.ok()).toBeTruthy();

    // Test verification logic
    let pages: any[] = [];
    for (let i = 0; i < 60; i++) {
      pages = await getPages(page, projectId);
      if (pages.length > 1 && pages.every((p) => p.outline_content?.points?.length)) break;
      await page.waitForTimeout(3000);
    }
    expect(pages.length).toBeGreaterThan(1);

    // Test verification logic
    const contentPages = pages.slice(1);
    const firstPoints = contentPages.map((p) => p.outline_content.points[0] as string);
    console.log('\n' + firstPoints.map((s, i) => `  ${i + 2}. ${s}`).join('\n'));

    const assertionLike = firstPoints.filter((s) => s && s.length >= 12);
    expect(assertionLike.length).toBeGreaterThanOrEqual(Math.ceil(contentPages.length * 0.7));
  });

  test(' AI', async ({ page }) => {
    test.setTimeout(300000);

    const projectId = await createProjectWithPages(page, 'SaaS ', ['', '']);

    const genResp = await page.request.post(
      `${BASE_URL}/api/projects/${projectId}/generate/descriptions`,
      { data: {}, timeout: 240000 },
    );
    expect(genResp.ok()).toBeTruthy();

    let pages: any[] = [];
    for (let i = 0; i < 80; i++) {
      pages = await getPages(page, projectId);
      if (pages.every((p) => p.description_content?.text)) break;
      await page.waitForTimeout(3000);
    }

    const withFields = pages.filter((p) => p.description_content?.extra_fields);
    console.log('', JSON.stringify(pages.map((p) => Object.keys(p.description_content?.extra_fields || {}))));
    expect(withFields.length).toBeGreaterThan(0);

    for (const p of pages) {
      // Test verification logic
      expect(p.description_content.text).not.toContain('');
      expect(p.description_content.text).not.toContain('Hình ảnh & Tư liệu');
      expect(p.description_content.text).not.toContain('Bố cục & Trọng tâm');
    }

    const allFieldNames = new Set(pages.flatMap((p) => Object.keys(p.description_content?.extra_fields || {})));
    console.log('', [...allFieldNames].join(', '));
    expect([...allFieldNames].some((n) => NEW_FIELDS.includes(n))).toBeTruthy();

    await page.goto(`${BASE_URL}/project/${projectId}/detail`);
    await page.waitForLoadState('networkidle');
    await expect(page.locator('text=Hình ảnh & Tư liệu').or(page.locator('text=Bố cục & Trọng tâm')).first()).toBeVisible({ timeout: 10000 });
  });

  test(' AI', async ({ page }) => {
    test.setTimeout(240000);

    const projectId = await createProjectWithPages(page, '', ['']);
    const pages = await getPages(page, projectId);
    await setPageDescription(page, projectId, pages[0].page_id, {
      text: '\n- ',
      extra_fields: { 'Hình ảnh & Tư liệu': '', 'Bố cục & Trọng tâm': '' },
    });

    const refineResp = await page.request.post(
      `${BASE_URL}/api/projects/${projectId}/refine/descriptions`,
      { data: { user_requirement: '' }, timeout: 180000 },
    );
    expect(refineResp.ok()).toBeTruthy();

    const after = await getPages(page, projectId);
    const content = after[0].description_content;
    console.log('', JSON.stringify(content));

    // Test verification logic
    expect(content.extra_fields).toBeTruthy();
    expect(Object.keys(content.extra_fields).length).toBeGreaterThan(0);
    expect(content.text).not.toContain('Hình ảnh & Tư liệu');
    expect(content.text).not.toContain('Bố cục & Trọng tâm');
  });

  test('', async ({ page }) => {
    test.setTimeout(420000);

    const projectId = await createProjectWithPages(page, '', ['']);
    const pages = await getPages(page, projectId);

    // Test verification logic
    const uploadResp = await page.request.post(`${BASE_URL}/api/projects/${projectId}/materials/upload`, {
      multipart: {
        file: {
          name: 'material.png',
          mimeType: 'image/png',
          buffer: Buffer.from(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==',
            'base64',
          ),
        },
      },
    });
    expect(uploadResp.ok()).toBeTruthy();
    const materialUrl = (await uploadResp.json()).data?.url || (await uploadResp.json()).data?.file_path;
    console.log(' URL', materialUrl);

    // Test verification logic
    await setPageDescription(page, projectId, pages[0].page_id, {
      text: '\n- ',
      extra_fields: { 'Hình ảnh & Tư liệu': `![](${materialUrl})` },
    });

    // Test verification logic
    await page.request.put(`${BASE_URL}/api/projects/${projectId}`, {
      data: { template_style: '' },
    });

    const genResp = await page.request.post(
      `${BASE_URL}/api/projects/${projectId}/generate/images`,
      { data: {}, timeout: 360000 },
    );
    expect(genResp.ok(), await genResp.text()).toBeTruthy();

    let imaged: any[] = [];
    for (let i = 0; i < 60; i++) {
      imaged = await getPages(page, projectId);
      if (imaged.every((p) => p.generated_image_url)) break;
      await page.waitForTimeout(4000);
    }
    console.log('', imaged.map((p) => p.generated_image_url).join(', '));
    // Test verification logic
    expect(imaged[0].generated_image_url).toBeTruthy();

    // Test verification logic
    const imageResp = await page.request.get(imaged[0].generated_image_url.startsWith('http')
      ? imaged[0].generated_image_url
      : `${BASE_URL}${imaged[0].generated_image_url}`);
    expect(imageResp.ok()).toBeTruthy();
    expect(Number(imageResp.headers()['content-length'] || '0')).toBeGreaterThan(1000);
  });
});