import { test, expect } from '@playwright/test'

const getBackendUrl = () => {
  if (process.env.BACKEND_URL) return process.env.BACKEND_URL
  const frontendUrl = process.env.BASE_URL || 'http://localhost:3011'
  const parsedFrontendUrl = new URL(frontendUrl)
  const frontendPort = parseInt(parsedFrontendUrl.port || '3011', 10)
  return `${parsedFrontendUrl.protocol}//${parsedFrontendUrl.hostname}:${frontendPort + 2000}`
}

test.describe('Markdown import preview', () => {
  test('integration: preview shows appended page count before importing outline markdown', async ({ page }) => {
    const backendUrl = getBackendUrl()
    const createResponse = await fetch(`${backendUrl}/api/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        creation_type: 'idea',
        idea_prompt: 'Markdown import preview test',
      }),
    })
    const created = await createResponse.json()
    const projectId = created.data?.project_id as string
    expect(projectId).toBeTruthy()

    try {
      await fetch(`${backendUrl}/api/projects/${projectId}/pages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          order_index: 0,
          outline_content: { title: '', points: [''] },
        }),
      })

      await page.addInitScript(() => localStorage.setItem('hasSeenHelpModal', 'true'))
      await page.goto(`/project/${projectId}/outline`)
      await expect(page.getByText('')).toBeVisible()

      await page.getByRole('button', { name: /\/|Import\/Export/ }).click()
      await page.getByRole('button', { name: /^$|^Import$/ }).click()

      const markdown = [
        '# Test logic
        '',
        '',
        '',
        '---',
        '',
        '# Test logic
        '',
        '',
      ].join('\n')
      await page.getByPlaceholder(/|Paste outline/).fill(markdown)

      await expect(page.getByText(/ 2 |2 page\(s\) will be appended/)).toBeVisible()
      await page.getByRole('button', { name: /|Import into Project/ }).click()

      await expect(page.getByText('')).toBeVisible()
      await expect(page.getByText('')).toBeVisible()

      const projectResponse = await fetch(`${backendUrl}/api/projects/${projectId}`)
      const project = await projectResponse.json()
      const titles = project.data.pages.map((item: { outline_content?: { title?: string } }) => item.outline_content?.title)
      expect(titles).toEqual(expect.arrayContaining(['', '', '']))
      expect(project.data.pages).toHaveLength(3)
    } finally {
      await fetch(`${backendUrl}/api/projects/${projectId}`, { method: 'DELETE' })
    }
  })
})