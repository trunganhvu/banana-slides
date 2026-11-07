/**
 * E2E tests for the SlidePreview page-properties drawer.
 *
 * 1. Mock UI tests: open/close, width persistence, drag + keyboard resize,
 *    mobile overlay, request payload shape per field.
 * 2. Integration tests: every editable field round-trips through the real
 *    backend and survives a reload, including the two debounce races that the
 *    accumulating save queue fixes.
 */

import { test, expect, type Page } from '@playwright/test'
import { seedProjectWithImages } from './helpers/seed-project'

const MOCK_PROJECT_ID = 'drawer-mock-project'

/** Minimal project payload so SlidePreview renders without a backend. */
function mockProject(overrides: Record<string, unknown> = {}) {
  return {
    id: MOCK_PROJECT_ID,
    project_id: MOCK_PROJECT_ID,
    project_title: '',
    status: 'DRAFT',
    template_mode: 'single',
    image_aspect_ratio: '16:9',
    created_at: '2026-07-01T10:00:00.000Z',
    updated_at: '2026-07-01T10:00:00.000Z',
    pages: [
      {
        id: 'page-1',
        page_id: 'page-1',
        order_index: 0,
        status: 'COMPLETED',
        part: '',
        outline_content: { title: '', points: [''] },
        description_content: { text: '' },
        narration_text: '',
        created_at: '2026-07-01T10:00:00.000Z',
        updated_at: '2026-07-01T10:00:00.000Z',
      },
      {
        id: 'page-2',
        page_id: 'page-2',
        order_index: 1,
        status: 'DRAFT',
        outline_content: { title: '', points: [] },
        created_at: '2026-07-01T10:00:00.000Z',
        updated_at: '2026-07-01T10:00:00.000Z',
      },
    ],
    ...overrides,
  }
}

async function mockPreview(page: Page, project = mockProject()) {
  await page.route('**/api/access-code/check', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ success: true, data: { enabled: false } }),
    })
  )
  await page.route('**/api/settings', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ success: true, data: {} }),
    })
  )
  await page.route(`**/api/projects/${MOCK_PROJECT_ID}`, (route) => {
    if (route.request().method() !== 'GET') return route.continue()
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ success: true, data: project }),
    })
  })
  await page.route('**/image-versions', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ success: true, data: { versions: [] } }),
    })
  )
}

/** Force the drawer open regardless of the viewport-based first-run default. */
async function openDrawerByDefault(page: Page, width?: number) {
  await page.addInitScript(
    ([w]) => {
      // Init scripts re-run on every navigation, so only seed the first load —
      // otherwise a reload would clobber whatever the test just changed.
      if (localStorage.getItem('previewDrawer.open') === null) {
        localStorage.setItem('previewDrawer.open', 'true')
      }
      if (w && localStorage.getItem('previewDrawer.width') === null) {
        localStorage.setItem('previewDrawer.width', String(w))
      }
    },
    [width]
  )
}

const drawer = (page: Page) => page.getByTestId('page-properties-drawer')
/** The description/extra fields are MarkdownTextarea (contentEditable), not <textarea>. */
const descriptionBox = (page: Page) =>
  page.getByTestId('drawer-description-field').locator('[contenteditable="true"]')
const extraFieldBox = (page: Page, name: string) =>
  page.getByTestId(`drawer-extra-field-${name}`).locator('[contenteditable="true"]')
async function clearAndType(editor: ReturnType<typeof descriptionBox>, text: string) {
  await editor.focus()
  await editor.press('ControlOrMeta+a')
  if (text) await editor.page().keyboard.insertText(text)
  else await editor.press('Backspace')
}
const drawerWidth = (page: Page) =>
  drawer(page).evaluate((el) => Math.round(el.getBoundingClientRect().width))

test.describe('Page properties drawer - UI (mock)', () => {
  test('opens by default on desktop and unmounts its inputs when collapsed', async ({ page }) => {
    await mockPreview(page)
    await page.goto(`/project/${MOCK_PROJECT_ID}/preview`)

    // Desktop first visit: the drawer is open by default so page properties
    // are immediately editable.
    expect(await drawerWidth(page)).toBeGreaterThan(0)
    await expect(page.getByTestId('drawer-title-input')).toBeVisible()

    // Collapse it — the aside stays mounted at zero width, and its fields leave
    // the DOM entirely so they cannot collide with other selectors.
    await page.getByRole('button', { name: '' }).click()
    await expect.poll(() => drawerWidth(page)).toBe(0)
    await expect(page.getByTestId('drawer-title-input')).toHaveCount(0)
    await expect(page.getByTestId('drawer-resize-handle')).toHaveCount(0)

    // And re-opening from the edge grip brings the fields back.
    await page.getByTestId('toggle-page-properties').click()
    await expect(page.getByTestId('drawer-title-input')).toBeVisible()
  })

  test('stays closed by default on tablet widths where the preview has no room', async ({ page }) => {
    await mockPreview(page)
    await page.setViewportSize({ width: 800, height: 900 })
    await page.goto(`/project/${MOCK_PROJECT_ID}/preview`)

    // Test verification logic
    expect(await drawerWidth(page)).toBe(0)
    await expect(page.getByTestId('toggle-page-properties')).toBeVisible()
    await expect(page.getByTestId('drawer-title-input')).toHaveCount(0)
  })

  test('clamps the initially opened drawer width at the lg breakpoint', async ({ page }) => {
    await mockPreview(page)
    await page.setViewportSize({ width: 1024, height: 900 })
    await page.goto(`/project/${MOCK_PROJECT_ID}/preview`)

    // Test verification logic
    await expect(page.getByTestId('drawer-title-input')).toBeVisible()
    expect(await drawerWidth(page)).toBe(300)
  })

  test('clamps the double-click reset to the viewport at the lg breakpoint', async ({ page }) => {
    await mockPreview(page)
    await openDrawerByDefault(page, 400)
    await page.setViewportSize({ width: 1024, height: 900 })
    await page.goto(`/project/${MOCK_PROJECT_ID}/preview`)

    // Test verification logic
    await expect(page.getByTestId('drawer-title-input')).toBeVisible()
    expect(await drawerWidth(page)).toBe(300)
    await page.getByTestId('drawer-resize-handle').dblclick()
    await expect.poll(() => drawerWidth(page)).toBe(300)
  })

  test('re-clamps the drawer width when the window shrinks and restores the preference when enlarged', async ({ page }) => {
    await mockPreview(page)
    await openDrawerByDefault(page, 640)
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto(`/project/${MOCK_PROJECT_ID}/preview`)
    await expect.poll(() => drawerWidth(page)).toBe(640)

    // Test verification logic
    await page.setViewportSize({ width: 1024, height: 900 })
    await expect.poll(() => drawerWidth(page)).toBe(300)
    expect(await page.evaluate(() => localStorage.getItem('previewDrawer.width'))).toBe('640')

    // Test verification logic
    await page.setViewportSize({ width: 1440, height: 900 })
    await expect.poll(() => drawerWidth(page)).toBe(640)
  })

  test('reapplies the first-visit default when resizing across the lg breakpoint', async ({ page }) => {
    await mockPreview(page)
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto(`/project/${MOCK_PROJECT_ID}/preview`)
    await expect(page.getByTestId('drawer-title-input')).toBeVisible()

    // Test verification logic
    await page.setViewportSize({ width: 800, height: 900 })
    await expect.poll(() => drawerWidth(page)).toBe(0)
    await expect(page.getByTestId('drawer-title-input')).toHaveCount(0)

    await page.setViewportSize({ width: 1440, height: 900 })
    await expect(page.getByTestId('drawer-title-input')).toBeVisible()
  })

  test('keeps the user explicit drawer choice when resizing across the lg breakpoint', async ({ page }) => {
    await mockPreview(page)
    await openDrawerByDefault(page, 380)
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto(`/project/${MOCK_PROJECT_ID}/preview`)
    await expect(page.getByTestId('drawer-title-input')).toBeVisible()

    // Test verification logic
    await page.setViewportSize({ width: 800, height: 900 })
    await expect.poll(() => drawerWidth(page)).toBe(300)
    await expect(page.getByTestId('drawer-title-input')).toBeVisible()

    await page.setViewportSize({ width: 1440, height: 900 })
    await expect.poll(() => drawerWidth(page)).toBe(380)
  })

  test('keeps the user explicit close when resizing across the lg breakpoint', async ({ page }) => {
    await mockPreview(page)
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto(`/project/${MOCK_PROJECT_ID}/preview`)
    await expect(page.getByTestId('drawer-title-input')).toBeVisible()

    // Test verification logic
    await page.getByRole('button', { name: '' }).click()
    await expect.poll(() => drawerWidth(page)).toBe(0)
    expect(await page.evaluate(() => localStorage.getItem('previewDrawer.open'))).toBe('false')

    await page.setViewportSize({ width: 800, height: 900 })
    await expect.poll(() => drawerWidth(page)).toBe(0)
    await expect(page.getByTestId('drawer-title-input')).toHaveCount(0)

    await page.setViewportSize({ width: 1440, height: 900 })
    await expect.poll(() => drawerWidth(page)).toBe(0)
    await expect(page.getByTestId('drawer-title-input')).toHaveCount(0)
  })

  test('toggles open/closed and remembers the choice across reloads', async ({ page }) => {
    await mockPreview(page)
    await openDrawerByDefault(page)
    await page.goto(`/project/${MOCK_PROJECT_ID}/preview`)

    await expect(drawer(page)).toBeVisible()
    await expect(page.getByTestId('drawer-title-input')).toHaveValue('')

    // Collapse it from the panel header — the aside stays mounted at zero width.
    await page.getByRole('button', { name: '' }).click()
    await expect.poll(() => drawerWidth(page)).toBe(0)
    expect(await page.evaluate(() => localStorage.getItem('previewDrawer.open'))).toBe('false')

    await page.reload()
    await expect.poll(() => drawerWidth(page)).toBe(0)

    // And re-opening from the edge grip sticks too.
    await page.getByTestId('toggle-page-properties').click()
    await expect.poll(() => drawerWidth(page)).toBeGreaterThan(0)
    await page.reload()
    await expect.poll(() => drawerWidth(page)).toBeGreaterThan(0)
  })

  test('shows the selected page and follows page switches', async ({ page }) => {
    await mockPreview(page)
    await openDrawerByDefault(page)
    await page.goto(`/project/${MOCK_PROJECT_ID}/preview`)

    await expect(page.getByTestId('drawer-title-input')).toHaveValue('')
    await expect(page.getByTestId('drawer-part-input')).toHaveValue('')
    await expect(descriptionBox(page)).toHaveText('')
    // Key points belong to the outline stage — the drawer must not surface them.
    await expect(drawer(page)).not.toContainText('')

    // Narration is collapsed by default, with a dot hinting it has content.
    await expect(page.getByTestId('drawer-narration-input')).toHaveCount(0)
    await expect(page.getByTestId('drawer-narration-dot')).toBeVisible()
    await page.getByTestId('drawer-narration-toggle').click()
    await expect(page.getByTestId('drawer-narration-input')).toHaveValue('')

    await page.getByRole('button', { name: '' }).click()

    await expect(page.getByTestId('drawer-title-input')).toHaveValue('')
    await expect(page.getByTestId('drawer-part-input')).toHaveValue('')
    await expect(descriptionBox(page)).toHaveText('')
  })

  test('keeps outline points intact when the title is edited', async ({ page }) => {
    await mockPreview(page)
    await openDrawerByDefault(page)
    await page.goto(`/project/${MOCK_PROJECT_ID}/preview`)

    let outlinePayload: any = null
    await page.route('**/pages/page-1/outline', async (route) => {
      outlinePayload = route.request().postDataJSON()
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, data: {} }),
      })
    })

    await page.getByTestId('drawer-title-input').fill('')
    await expect.poll(() => outlinePayload, { timeout: 8000 }).not.toBeNull()
    expect(outlinePayload.outline_content).toEqual({
      title: '',
      points: [''],
    })
  })

  test('picks up edits made outside the drawer without clobbering typing', async ({ page }) => {
    // Anything that writes these fields through the store — a syncProject after
    // AI regeneration, another tab, the outline editor — has to show up in an
    // open drawer rather than leaving stale text behind. Drive it through a
    // Test verification logic
    // outline/description fields of its own.
    const project = mockProject()
    let served = project
    await mockPreview(page, project)
    await page.route(`**/api/projects/${MOCK_PROJECT_ID}`, (route) => {
      if (route.request().method() !== 'GET') return route.continue()
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, data: served }),
      })
    })
    await openDrawerByDefault(page)
    await page.goto(`/project/${MOCK_PROJECT_ID}/preview`)
    await expect(page.getByTestId('drawer-title-input')).toHaveValue('')

    const updated = mockProject()
    updated.pages[0].outline_content = { title: '', points: [''] }
    served = updated

    await page.getByRole('button', { name: '' }).click()

    await expect(page.getByTestId('drawer-title-input')).toHaveValue('')
  })

  test('does not let a background sync overwrite in-progress typing', async ({ page }) => {
    await mockPreview(page)
    await openDrawerByDefault(page)
    await page.goto(`/project/${MOCK_PROJECT_ID}/preview`)

    // Every project GET keeps returning the ORIGINAL title, mimicking a
    // syncProject() landing before the debounced save has flushed.
    await page.getByTestId('drawer-title-input').click()
    await page.getByTestId('drawer-title-input').fill('')

    // Stays put while focused and while the save is still queued.
    await page.waitForTimeout(2500)
    await expect(page.getByTestId('drawer-title-input')).toHaveValue('')
  })

  test('resizes by dragging the handle and persists the width', async ({ page }) => {
    await mockPreview(page)
    await openDrawerByDefault(page, 380)
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto(`/project/${MOCK_PROJECT_ID}/preview`)

    expect(await drawerWidth(page)).toBe(380)

    const handle = page.getByTestId('drawer-resize-handle')
    const box = (await handle.boundingBox())!
    await page.mouse.move(box.x + box.width / 2, box.y + 200)
    await page.mouse.down()
    await page.mouse.move(box.x - 120, box.y + 200, { steps: 10 })
    await page.mouse.up()

    // ~500 rather than exactly 500: the handle centre lands on a half pixel.
    await expect.poll(() => drawerWidth(page)).toBeGreaterThan(495)
    const dragged = await drawerWidth(page)
    expect(dragged).toBeLessThan(505)
    expect(await page.evaluate(() => localStorage.getItem('previewDrawer.width'))).toBe(
      String(dragged)
    )

    await page.reload()
    await expect.poll(() => drawerWidth(page)).toBe(dragged)
  })

  test('clamps the width to the allowed range while dragging', async ({ page }) => {
    await mockPreview(page)
    await openDrawerByDefault(page, 380)
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto(`/project/${MOCK_PROJECT_ID}/preview`)

    const handle = page.getByTestId('drawer-resize-handle')
    const box = (await handle.boundingBox())!

    // Drag far past the maximum — 1440 viewport allows at most 640.
    await page.mouse.move(box.x + box.width / 2, box.y + 200)
    await page.mouse.down()
    await page.mouse.move(100, box.y + 200, { steps: 10 })
    await page.mouse.up()
    await expect.poll(() => drawerWidth(page)).toBe(640)

    // Drag far past the minimum.
    const box2 = (await handle.boundingBox())!
    await page.mouse.move(box2.x + box2.width / 2, box2.y + 200)
    await page.mouse.down()
    await page.mouse.move(1430, box2.y + 200, { steps: 10 })
    await page.mouse.up()
    await expect.poll(() => drawerWidth(page)).toBe(300)
  })

  test('resizes with the keyboard and resets on double click', async ({ page }) => {
    await mockPreview(page)
    await openDrawerByDefault(page, 400)
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto(`/project/${MOCK_PROJECT_ID}/preview`)

    const handle = page.getByTestId('drawer-resize-handle')
    await handle.focus()

    await handle.press('ArrowLeft')
    await expect.poll(() => drawerWidth(page)).toBe(416)
    await handle.press('ArrowRight')
    await expect.poll(() => drawerWidth(page)).toBe(400)
    await handle.press('Shift+ArrowLeft')
    await expect.poll(() => drawerWidth(page)).toBe(448)
    await handle.press('End')
    await expect.poll(() => drawerWidth(page)).toBe(300)
    await handle.press('Home')
    await expect.poll(() => drawerWidth(page)).toBe(640)

    await handle.dblclick()
    await expect.poll(() => drawerWidth(page)).toBe(380)
  })

  test('sends each field to its own endpoint with the right payload', async ({ page }) => {
    await mockPreview(page)
    await openDrawerByDefault(page)
    await page.goto(`/project/${MOCK_PROJECT_ID}/preview`)

    const calls: { url: string; body: any }[] = []
    for (const suffix of ['outline', 'description', 'narration']) {
      await page.route(`**/pages/page-1/${suffix}`, async (route) => {
        calls.push({ url: route.request().url(), body: route.request().postDataJSON() })
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true, data: {} }),
        })
      })
    }
    await page.route('**/pages/page-1', async (route) => {
      calls.push({ url: route.request().url(), body: route.request().postDataJSON() })
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, data: {} }),
      })
    })

    await page.getByTestId('drawer-title-input').fill('')
    await page.getByTestId('drawer-part-input').fill('')
    await clearAndType(descriptionBox(page), '')
    await page.getByTestId('drawer-narration-toggle').click()
    await page.getByTestId('drawer-narration-input').fill('')

    await expect.poll(() => calls.length, { timeout: 8000 }).toBeGreaterThanOrEqual(4)

    const outline = calls.find((c) => c.url.endsWith('/outline'))!
    expect(outline.body.outline_content.title).toBe('')
    expect(calls.find((c) => c.url.endsWith('/description'))!.body.description_content.text).toBe(
      ''
    )
    expect(calls.find((c) => c.url.endsWith('/narration'))!.body).toEqual({
      narration_text: '',
    })
    expect(calls.find((c) => c.url.endsWith('/pages/page-1'))!.body).toEqual({ part: '' })
  })

  test('survives legacy rows whose extra fields are not strings', async ({ page }) => {
    // description_content is a JSON blob and the legacy layout_suggestion
    // fallback has no writer left in the backend, so old rows can hold values
    // that were never strings. Editing used to throw `value.trim is not a
    // function` out of buildDescriptionContent and blank the drawer.
    const legacy = mockProject()
    legacy.pages[0].description_content = {
      text: '',
      extra_fields: { Hình ảnh & Tư liệu: 42 as unknown as string, Bố cục & Trọng tâm: null as unknown as string },
    }
    await mockPreview(page, legacy)
    await openDrawerByDefault(page)

    let body: any = null
    await page.route('**/pages/page-1/description', async (route) => {
      body = route.request().postDataJSON()
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, data: {} }),
      })
    })

    await page.goto(`/project/${MOCK_PROJECT_ID}/preview`)
    await clearAndType(descriptionBox(page), '')

    await expect.poll(() => body, { timeout: 8000 }).not.toBeNull()
    expect(body.description_content.text).toBe('')
    // Coerced, not crashed: the number survives as text, the null is dropped.
    expect(body.description_content.extra_fields).toEqual({ Hình ảnh & Tư liệu: '42' })
    await expect(drawer(page)).toBeVisible()
  })

  test('shows the saving indicator then settles on saved', async ({ page }) => {
    await mockPreview(page)
    await openDrawerByDefault(page)
    await page.goto(`/project/${MOCK_PROJECT_ID}/preview`)

    await page.route('**/pages/page-1/outline', async (route) => {
      await new Promise((r) => setTimeout(r, 600))
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, data: {} }),
      })
    })

    const indicator = page.getByTestId('drawer-save-state')
    await page.getByTestId('drawer-title-input').fill('')

    await expect(indicator).toContainText('')
    await expect(indicator).toContainText('', { timeout: 8000 })
  })

  test('renders as an overlay with a dismissing scrim on mobile', async ({ page }) => {
    await mockPreview(page)
    await openDrawerByDefault(page)
    await page.setViewportSize({ width: 375, height: 812 })
    await page.goto(`/project/${MOCK_PROJECT_ID}/preview`)

    // Floats above the preview instead of taking layout space.
    expect(await drawer(page).evaluate((el) => getComputedStyle(el).position)).toBe('fixed')
    // The resize handle is desktop-only.
    await expect(page.getByTestId('drawer-resize-handle')).toBeHidden()

    await page.mouse.click(20, 400) // tap the scrim
    await expect.poll(() => drawerWidth(page)).toBe(0)
  })

  test('does not let the drawer occlude the export tasks popover on desktop', async ({ page }) => {
    await mockPreview(page)
    await openDrawerByDefault(page, 640)
    await page.route(`**/api/projects/${MOCK_PROJECT_ID}/exports`, (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            files: [{
              filename: 'demo.pdf',
              type: 'pdf',
              size: 1024,
              modified_at: new Date().toISOString(),
              download_url: '/files/demo.pdf',
            }],
          },
        }),
      })
    )

    await page.goto(`/project/${MOCK_PROJECT_ID}/preview`)
    await page.getByLabel('').click()

    const popover = page.getByTestId('export-tasks-popover')
    await expect(popover).toBeVisible()
    await expect(popover).toContainText('demo.pdf')

    // Test verification logic
    expect(await drawer(page).evaluate((el) => getComputedStyle(el).zIndex)).toBe('auto')

    const drawerBox = await drawer(page).boundingBox()
    const popoverBox = await popover.boundingBox()
    expect(drawerBox).not.toBeNull()
    expect(popoverBox).not.toBeNull()
    // Test verification logic
    expect(popoverBox!.x + popoverBox!.width).toBeGreaterThan(drawerBox!.x)

    // Test verification logic
    const topIsPopover = await page.evaluate(({ x, y }) => {
      const el = document.elementFromPoint(x, y)
      const popoverEl = document.querySelector('[data-testid="export-tasks-popover"]')
      return !!popoverEl && (popoverEl === el || popoverEl.contains(el))
    }, {
      x: popoverBox!.x + popoverBox!.width - 8,
      y: popoverBox!.y + 16,
    })
    expect(topIsPopover).toBe(true)
  })

  test('shows the per-page template section only in multi-template mode', async ({ page }) => {
    await mockPreview(page)
    await openDrawerByDefault(page)
    await page.goto(`/project/${MOCK_PROJECT_ID}/preview`)
    await expect(page.getByTestId('drawer-change-template')).toHaveCount(0)
    await expect(page.getByTestId('drawer-template-style-input')).toHaveCount(0)

    await page.unrouteAll({ behavior: 'ignoreErrors' })
    await mockPreview(page, mockProject({ template_mode: 'multi' }))
    await page.goto(`/project/${MOCK_PROJECT_ID}/preview`)
    await expect(drawer(page)).toContainText('')
    await expect(page.getByTestId('drawer-change-template')).toBeVisible()
    await expect(page.getByTestId('drawer-template-style-input')).toBeVisible()
  })

  test('picks a template for the page straight from the drawer', async ({ page }) => {
    await mockPreview(page, mockProject({ template_mode: 'multi' }))
    await openDrawerByDefault(page)

    await page.route('**/template-assets', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            assets: [
              {
                id: 'asset-1',
                image_url: '/files/a.jpg',
                thumb_url: null,
                analysis_status: 'COMPLETED',
                analysis_json: null,
                analysis_notes: null,
                analysis_error: null,
                user_label: '',
                user_edited_analysis: false,
                source: 'upload',
                sort_order: 0,
              },
            ],
          },
        }),
      })
    )

    let patch: any = null
    await page.route('**/pages/page-1/template', async (route) => {
      patch = route.request().postDataJSON()
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: { page: { page_id: 'page-1', template_asset_id: 'asset-1' } },
        }),
      })
    })

    await page.goto(`/project/${MOCK_PROJECT_ID}/preview`)
    await page.getByTestId('drawer-change-template').click()
    await page.getByRole('dialog').getByText('').click()

    await expect.poll(() => patch, { timeout: 8000 }).not.toBeNull()
    expect(patch).toEqual({ template_asset_id: 'asset-1', selection_source: 'manual' })
  })

  test('saves the per-page template prompt as you type', async ({ page }) => {
    await mockPreview(page, mockProject({ template_mode: 'multi' }))
    await openDrawerByDefault(page)

    let patch: any = null
    await page.route('**/pages/page-1/template', async (route) => {
      patch = route.request().postDataJSON()
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, data: { page: { page_id: 'page-1' } } }),
      })
    })

    await page.goto(`/project/${MOCK_PROJECT_ID}/preview`)
    await page.getByTestId('drawer-template-style-input').fill('')

    await expect.poll(() => patch, { timeout: 8000 }).not.toBeNull()
    expect(patch).toEqual({ template_style_text: '', selection_source: 'manual' })
  })

  test('flushes a template prompt typed just before switching pages', async ({ page }) => {
    await mockPreview(page, mockProject({ template_mode: 'multi' }))
    await openDrawerByDefault(page)

    const patches: { pageId: string; body: any }[] = []
    await page.route('**/pages/*/template', async (route) => {
      const pageId = route.request().url().match(/pages\/([^/]+)\/template/)![1]
      patches.push({ pageId, body: route.request().postDataJSON() })
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, data: { page: { page_id: pageId } } }),
      })
    })

    await page.goto(`/project/${MOCK_PROJECT_ID}/preview`)
    // Type, then switch pages well inside the 800ms debounce window. The prompt
    // used to be dropped by the clearTimeout on unmount/page switch.
    await page.getByTestId('drawer-template-style-input').fill('')
    await page.getByRole('button', { name: '' }).click()

    await expect.poll(() => patches.length, { timeout: 8000 }).toBeGreaterThan(0)
    // It must land on page-1 — the page it was typed on — not on page-2.
    expect(patches[0].pageId).toBe('page-1')
    expect(patches[0].body.template_style_text).toBe('')
  })

  test('still debounces while typing instead of firing per keystroke', async ({ page }) => {
    await mockPreview(page, mockProject({ template_mode: 'multi' }))
    await openDrawerByDefault(page)

    let calls = 0
    await page.route('**/pages/page-1/template', async (route) => {
      calls += 1
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, data: { page: { page_id: 'page-1' } } }),
      })
    })

    await page.goto(`/project/${MOCK_PROJECT_ID}/preview`)
    const input = page.getByTestId('drawer-template-style-input')
    await input.click()
    // Six keystrokes inside one debounce window must collapse into one request.
    // Guards the flush-on-page-switch fix above: reaching the flush callback
    // through an effect dependency would re-arm it every render and turn the
    // debounce into per-keystroke saves.
    await page.keyboard.type('', { delay: 40 })
    await page.keyboard.type('', { delay: 40 })

    await expect.poll(() => calls, { timeout: 8000 }).toBe(1)
  })
})

test.describe('Page properties drawer - integration', () => {
  test('every field round-trips through the backend and survives a reload', async ({
    page,
    request,
    baseURL,
  }) => {
    // Test verification logic
    // Test verification logic
    const defaultExtraFields = ['Hình ảnh & Tư liệu', 'Bố cục & Trọng tâm', 'Ghi chú thuyết trình']
    await request.put('/api/settings', { data: { description_extra_fields: ['Hình ảnh & Tư liệu'] } })
    try {
      const { projectId } = await seedProjectWithImages(baseURL!, 2)
      await openDrawerByDefault(page)
      await page.goto(`/project/${projectId}/preview`)

      await expect(drawer(page)).toBeVisible()

      await page.getByTestId('drawer-title-input').fill('')
      await page.getByTestId('drawer-part-input').fill('')
      await clearAndType(descriptionBox(page), '')
      await clearAndType(extraFieldBox(page, 'Hình ảnh & Tư liệu'), '')
      await page.getByTestId('drawer-narration-toggle').click()
      await page.getByTestId('drawer-narration-input').fill('')

      await expect(page.getByTestId('drawer-save-state')).toContainText('', { timeout: 10000 })

      // Persisted server-side, not just optimistically in the store.
      const resp = await request.get(`/api/projects/${projectId}`)
      const firstPage = (await resp.json()).data.pages[0]
      expect(firstPage.outline_content.title).toBe('')
      expect(firstPage.part).toBe('')
      expect(firstPage.description_content.text).toBe('')
      expect(firstPage.description_content.extra_fields).toEqual({ Hình ảnh & Tư liệu: '' })
      expect(firstPage.narration_text).toBe('')

      // And the drawer rehydrates from the server after a reload.
      await page.reload()
      await expect(page.getByTestId('drawer-title-input')).toHaveValue('')
      await expect(page.getByTestId('drawer-part-input')).toHaveValue('')
      await expect(descriptionBox(page)).toHaveText('')
      await expect(extraFieldBox(page, 'Hình ảnh & Tư liệu')).toHaveText('')
      await page.getByTestId('drawer-narration-toggle').click()
      await expect(page.getByTestId('drawer-narration-input')).toHaveValue('')
    } finally {
      await request.put('/api/settings', { data: { description_extra_fields: defaultExtraFields } })
    }
  })

  test('keeps every field when several are edited inside one debounce window', async ({
    page,
    request,
    baseURL,
  }) => {
    const { projectId } = await seedProjectWithImages(baseURL!, 1)
    await openDrawerByDefault(page)
    await page.goto(`/project/${projectId}/preview`)
    await expect(drawer(page)).toBeVisible()

    // No awaits in between: all four land inside the same 1s debounce window,
    // which used to keep only the last one.
    await page.getByTestId('drawer-narration-toggle').click()
    await page.getByTestId('drawer-title-input').fill('')
    await page.getByTestId('drawer-part-input').fill('')
    await clearAndType(descriptionBox(page), '')
    await page.getByTestId('drawer-narration-input').fill('')

    await expect(page.getByTestId('drawer-save-state')).toContainText('', { timeout: 10000 })

    const firstPage = (await (await request.get(`/api/projects/${projectId}`)).json()).data.pages[0]
    expect(firstPage.outline_content.title).toBe('')
    expect(firstPage.part).toBe('')
    expect(firstPage.description_content.text).toBe('')
    expect(firstPage.narration_text).toBe('')
  })

  test('keeps an edit made just before switching pages', async ({ page, request, baseURL }) => {
    const { projectId } = await seedProjectWithImages(baseURL!, 2)
    await openDrawerByDefault(page)
    await page.goto(`/project/${projectId}/preview`)
    await expect(drawer(page)).toBeVisible()

    // Edit page 1, then jump to page 2 and edit it before the debounce fires.
    await page.getByTestId('drawer-title-input').fill('')
    await page.getByRole('button', { name: '' }).click()
    await page.getByTestId('drawer-title-input').fill('')

    await expect(page.getByTestId('drawer-save-state')).toContainText('', { timeout: 10000 })

    const pages = (await (await request.get(`/api/projects/${projectId}`)).json()).data.pages
    expect(pages[0].outline_content.title).toBe('')
    expect(pages[1].outline_content.title).toBe('')
  })
})