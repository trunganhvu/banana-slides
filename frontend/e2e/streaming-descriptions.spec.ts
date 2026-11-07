import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://localhost:3240';

/**
 * Helper: create a project with outline pages via API and navigate to detail editor
 */
async function createProjectWithOutline(page: import('@playwright/test').Page, ideaPrompt: string) {
  // Create project
  const resp = await page.request.post(`${BASE_URL}/api/projects`, {
    data: {
      creation_type: 'idea',
      idea_prompt: ideaPrompt,
    },
  });
  const body = await resp.json();
  const projectId = body.data?.project_id;
  expect(projectId).toBeTruthy();

  // Create some pages with outlines
  const pageTitles = ['Introduction', 'Main Content', 'Conclusion'];
  for (let i = 0; i < pageTitles.length; i++) {
    await page.request.post(`${BASE_URL}/api/projects/${projectId}/pages`, {
      data: {
        order_index: i,
        outline_content: { title: pageTitles[i], points: [`Point ${i + 1}A`, `Point ${i + 1}B`] },
        status: 'DRAFT',
      },
    });
  }

  // Update project status
  await page.request.put(`${BASE_URL}/api/projects/${projectId}`, {
    data: { status: 'OUTLINE_GENERATED' },
  });

  await page.goto(`${BASE_URL}/project/${projectId}/detail`);
  await page.waitForLoadState('networkidle');
  return projectId;
}

// ===== Mock Tests =====

test.describe('Streaming Descriptions - Mock Tests', () => {
  test('should render descriptions incrementally via SSE', async ({ page }) => {
    const projectId = await createProjectWithOutline(page, 'Test streaming descriptions');

    // Get page IDs
    const projectResp = await page.request.get(`${BASE_URL}/api/projects/${projectId}`);
    const projectData = await projectResp.json();
    const pages = projectData.data?.pages || [];
    expect(pages.length).toBe(3);

    // Mock SSE streaming endpoint
    let mockCalled = false;
    await page.route(`**/api/projects/*/generate/descriptions/stream`, async (route) => {
      mockCalled = true;

      const sseEvents = pages.map((p: any, i: number) => {
        const descEvent = `event: description\ndata: ${JSON.stringify({
          page_index: i,
          page_id: p.page_id,
          text: `Page ${i + 1}\n\n\n- Content for page ${i + 1}`,
          extra_fields: i === 0 ? { 'Bố cục & Trọng tâm': '' } : { 'Bố cục & Trọng tâm': '' },
        })}\n\n`;
        return descEvent;
      });

      const doneEvent = `event: done\ndata: ${JSON.stringify({
        total: pages.length,
        pages: pages.map((p: any, i: number) => ({
          ...p,
          status: 'DESCRIPTION_GENERATED',
          description_content: {
            text: `Page ${i + 1}\n\n\n- Content for page ${i + 1}`,
            extra_fields: i === 0 ? { 'Bố cục & Trọng tâm': '' } : { 'Bố cục & Trọng tâm': '' },
          },
        })),
      })}\n\n`;

      const body = sseEvents.join('') + doneEvent;

      await route.fulfill({
        status: 200,
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
        },
        body,
      });
    });

    // Also mock the settings to return streaming mode (cached in sessionStorage)
    await page.evaluate(() => {
      sessionStorage.setItem('banana-settings', JSON.stringify({
        description_generation_mode: 'streaming',
      }));
    });

    // Click the generate descriptions button
    const generateBtn = page.locator('button').filter({ hasText: /|Generate/ });
    await generateBtn.first().click();

    // Wait for descriptions to appear
    await expect(page.locator('text=Content for page 1')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=Content for page 2')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=Content for page 3')).toBeVisible({ timeout: 10000 });

    expect(mockCalled).toBe(true);
  });

  test('should display extra fields when present', async ({ page }) => {
    const projectId = await createProjectWithOutline(page, 'Test extra fields display');

    // Get page IDs
    const projectResp = await page.request.get(`${BASE_URL}/api/projects/${projectId}`);
    const projectData = await projectResp.json();
    const pages = projectData.data?.pages || [];

    // Update a page with description_content that includes extra_fields
    await page.request.put(
      `${BASE_URL}/api/projects/${projectId}/pages/${pages[0].page_id}/description`,
      {
        data: {
          description_content: {
            text: 'Test Page\n\n\n- Test content',
            extra_fields: { 'Bố cục & Trọng tâm': '+' },
          },
        },
      }
    );

    // Navigate to detail editor
    await page.goto(`${BASE_URL}/project/${projectId}/detail`);
    await page.waitForLoadState('networkidle');

    // Check extra field is displayed
    await expect(page.locator('text=Bố cục & Trọng tâm')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=+')).toBeVisible({ timeout: 5000 });
  });

  test('should display extra fields from old layout_suggestion format (backward compat)', async ({ page }) => {
    const projectId = await createProjectWithOutline(page, 'Test backward compat');

    const projectResp = await page.request.get(`${BASE_URL}/api/projects/${projectId}`);
    const projectData = await projectResp.json();
    const pages = projectData.data?.pages || [];

    // Old format with layout_suggestion
    await page.request.put(
      `${BASE_URL}/api/projects/${projectId}/pages/${pages[0].page_id}/description`,
      {
        data: {
          description_content: {
            text: '',
            layout_suggestion: '',
          },
        },
      }
    );

    await page.goto(`${BASE_URL}/project/${projectId}/detail`);
    await page.waitForLoadState('networkidle');

    // Old layout_suggestion should be mapped to "Gợi ý bố cục" field (legacy name)
    await expect(page.locator('text=Gợi ý bố cục')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=')).toBeVisible({ timeout: 5000 });
  });

  test('should fall back to parallel mode when setting is parallel', async ({ page }) => {
    const projectId = await createProjectWithOutline(page, 'Test parallel mode');

    // Get page IDs
    const projectResp = await page.request.get(`${BASE_URL}/api/projects/${projectId}`);
    const projectData = await projectResp.json();
    const pages = projectData.data?.pages || [];

    // Set parallel mode in sessionStorage
    await page.evaluate(() => {
      sessionStorage.setItem('banana-settings', JSON.stringify({
        description_generation_mode: 'parallel',
      }));
    });

    // Mock the parallel endpoint (not streaming)
    let parallelCalled = false;
    await page.route(`**/api/projects/*/generate/descriptions`, async (route) => {
      // Only intercept POST (not the stream endpoint which has /stream suffix)
      if (route.request().url().includes('/stream')) {
        return route.continue();
      }
      parallelCalled = true;
      await route.fulfill({
        status: 202,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: { task_id: 'mock-task-123', status: 'GENERATING_DESCRIPTIONS', total_pages: pages.length },
        }),
      });
    });

    // Mock task polling
    await page.route(`**/api/tasks/mock-task-123`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: { status: 'COMPLETED', progress: { total: pages.length, completed: pages.length } },
        }),
      });
    });

    // Click generate
    const generateBtn = page.locator('button').filter({ hasText: /|Generate/ });
    await generateBtn.first().click();

    // Wait a bit for the mode dispatch
    await page.waitForTimeout(2000);
    expect(parallelCalled).toBe(true);
  });
});

// ===== Integration Tests =====

test.describe('Streaming Descriptions - Integration Tests', () => {
  test('DetailEditor settings panel should show generation mode and extra fields', async ({ page }) => {
    const projectId = await createProjectWithOutline(page, 'Test settings panel');
    await page.goto(`${BASE_URL}/project/${projectId}/detail`);
    await page.waitForLoadState('networkidle');

    // Find the Settings2 button by its title attribute
    const gearBtn = page.locator('button[title=""], button[title="Description Settings"]');
    await expect(gearBtn).toBeVisible({ timeout: 5000 });
    await gearBtn.click();

    // Check generation mode buttons
    await expect(page.locator('text=').or(page.locator('text=Streaming'))).toBeVisible({ timeout: 3000 });
    await expect(page.locator('text=').or(page.locator('text=Parallel'))).toBeVisible({ timeout: 3000 });

    // Check detail level buttons
    await expect(page.locator('text=').or(page.locator('text=Concise'))).toBeVisible();
    await expect(page.locator('text=').or(page.locator('text=Default'))).toBeVisible();
    await expect(page.getByRole('button', { name: /|Detailed/ })).toBeVisible();

    // Check extra fields section
    await expect(page.locator('text=').or(page.locator('text=Extra Fields'))).toBeVisible();
    // Default field "Bố cục & Trọng tâm" should be shown
    await expect(page.locator('text=Bố cục & Trọng tâm')).toBeVisible();
  });

  test('should persist generation mode via settings API', async ({ page }) => {
    const projectId = await createProjectWithOutline(page, 'Test mode persist');
    await page.goto(`${BASE_URL}/project/${projectId}/detail`);
    await page.waitForLoadState('networkidle');

    // Open settings panel
    const gearBtn = page.locator('button[title=""], button[title="Description Settings"]');
    await gearBtn.click();

    // Click parallel button
    const parallelBtn = page.locator('button').filter({ hasText: /|Parallel/ });
    await parallelBtn.first().click();

    // Wait for debounced save
    await page.waitForTimeout(1500);

    // Verify via API
    const settingsResp = await page.request.get(`${BASE_URL}/api/settings`);
    const settingsData = await settingsResp.json();
    expect(settingsData.data?.description_generation_mode).toBe('parallel');

    // Reset back to streaming
    await page.request.put(`${BASE_URL}/api/settings`, {
      data: { description_generation_mode: 'streaming' },
    });
  });

  test('should add and remove extra fields', async ({ page }) => {
    const projectId = await createProjectWithOutline(page, 'Test extra fields config');
    await page.goto(`${BASE_URL}/project/${projectId}/detail`);
    await page.waitForLoadState('networkidle');

    // Open settings panel
    const gearBtn = page.locator('button[title=""], button[title="Description Settings"]');
    await gearBtn.click();

    // Add a new field via input
    const fieldInput = page.locator('input[placeholder=""], input[placeholder="Add Field"]');
    await fieldInput.fill('');
    await fieldInput.press('Enter');

    // New field should appear as an active pill button
    const newPill = page.locator('button').filter({ hasText: '' });
    await expect(newPill).toBeVisible({ timeout: 3000 });

    // Wait for debounced save
    await page.waitForTimeout(1500);

    // Verify via API — both fields should be active
    const settingsResp = await page.request.get(`${BASE_URL}/api/settings`);
    const settingsData = await settingsResp.json();
    expect(settingsData.data?.description_extra_fields).toContain('');
    expect(settingsData.data?.description_extra_fields).toContain('Bố cục & Trọng tâm');

    // Test verification logic
    await newPill.click();
    await page.waitForTimeout(1500);

    // Verify it's removed from active fields but still visible in pool
    const settingsResp2 = await page.request.get(`${BASE_URL}/api/settings`);
    const settingsData2 = await settingsResp2.json();
    expect(settingsData2.data?.description_extra_fields).not.toContain('');
    await expect(newPill).toBeVisible(); // Still in pool, just inactive

    // Clean up: reset extra fields
    await page.request.put(`${BASE_URL}/api/settings`, {
      data: { description_extra_fields: ['Hình ảnh & Tư liệu', 'Bố cục & Trọng tâm', 'Ghi chú thuyết trình'] },
    });
    // Clean up localStorage pool
    await page.evaluate(() => localStorage.removeItem('banana-available-extra-fields'));
  });

  test('edit dialog should preserve extra fields on save', async ({ page }) => {
    const projectId = await createProjectWithOutline(page, 'Test edit extra fields');

    const projectResp = await page.request.get(`${BASE_URL}/api/projects/${projectId}`);
    const projectData = await projectResp.json();
    const pages = projectData.data?.pages || [];

    // Set a page with extra_fields
    await page.request.put(
      `${BASE_URL}/api/projects/${projectId}/pages/${pages[0].page_id}/description`,
      {
        data: {
          description_content: {
            text: '',
            extra_fields: { 'Bố cục & Trọng tâm': '' },
          },
        },
      }
    );

    await page.goto(`${BASE_URL}/project/${projectId}/detail`);
    await page.waitForLoadState('networkidle');

    // Click edit on first card
    const editBtn = page.locator('button').filter({ hasText: /|Edit/ }).first();
    await editBtn.click();

    // Modal should be visible with extra field input
    await expect(page.locator('label').filter({ hasText: 'Bố cục & Trọng tâm' })).toBeVisible({ timeout: 5000 });
    const fieldTextarea = page.locator('textarea').filter({ hasText: '' });
    await expect(fieldTextarea).toBeVisible();

    // Edit the extra field value
    await fieldTextarea.fill('');

    // Save
    const saveBtn = page.locator('button').filter({ hasText: /|Save/ });
    await saveBtn.click();

    // Verify the card shows updated value (use paragraph to avoid matching textarea)
    await expect(page.getByRole('paragraph').filter({ hasText: '' })).toBeVisible({ timeout: 5000 });
  });

  test('single page regeneration should still work', async ({ page }) => {
    const projectId = await createProjectWithOutline(page, 'Test single page regen');

    await page.goto(`${BASE_URL}/project/${projectId}/detail`);
    await page.waitForLoadState('networkidle');

    // Click regenerate on the first page card
    const regenBtn = page.locator('button').filter({ hasText: /|Regenerate/ });
    await expect(regenBtn.first()).toBeVisible({ timeout: 5000 });
  });
});