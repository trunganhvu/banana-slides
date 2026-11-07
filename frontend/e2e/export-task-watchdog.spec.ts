/**
 *  + ""
 *
 *  PPTX  "88%  17/24 "
 *  88%
 * 
 */
import { expect, test } from '@playwright/test'
import { execFileSync } from 'child_process'
import crypto from 'crypto'
import path from 'path'

const FRONTEND_DIR = process.cwd().endsWith('frontend')
  ? process.cwd()
  : path.join(process.cwd(), 'frontend')
const PROJECT_ROOT = path.resolve(FRONTEND_DIR, '..')
const DB_PATH = process.env.DATABASE_PATH || path.join(PROJECT_ROOT, 'backend', 'instance', 'database.db')

function sqlText(value: string): string {
  return `CAST(X'${Buffer.from(value, 'utf8').toString('hex')}' AS TEXT)`
}

async function createProject(request: any, idea: string): Promise<string> {
  const response = await request.post('/api/projects', {
    data: { creation_type: 'idea', idea_prompt: idea, template_style: 'default' },
  })
  expect(response.ok()).toBeTruthy()
  return (await response.json()).data.project_id as string
}

function insertExportTask(options: {
  taskId: string
  projectId: string
  status: string
  progress: Record<string, unknown>
}) {
  const progress = JSON.stringify(options.progress)
  execFileSync('sqlite3', [
    '-cmd',
    '.timeout 5000',
    DB_PATH,
    `INSERT INTO tasks (id, project_id, task_type, status, progress, created_at)
     VALUES ('${options.taskId}', '${options.projectId}', 'EXPORT_EDITABLE_PPTX',
       '${options.status}', ${sqlText(progress)}, CURRENT_TIMESTAMP);`,
  ])
}

async function seedStoredTask(page: any, payload: Record<string, unknown>) {
  await page.addInitScript((task: Record<string, unknown>) => {
    localStorage.setItem('hasSeenHelpModal', 'true')
    localStorage.setItem('export-tasks-storage', JSON.stringify({
      state: { tasks: [task] },
      version: 0,
    }))
  }, payload)
}

test('a task left over from a previous run stops showing 88% and reports interrupted', async ({ page, request }) => {
  const projectId = await createProject(request, ' E2E')
  const taskId = crypto.randomUUID()
  const localTaskId = `e2e-watchdog-${Date.now()}`
  const staleHeartbeat = new Date(Date.now() - 3.5 * 3600 * 1000).toISOString()

  insertExportTask({
    taskId,
    projectId,
    status: 'PROCESSING',
    progress: {
      total: 100,
      completed: 88,
      failed: 0,
      current_step: ' 17/24 ...',
      percent: 88,
      heartbeat_at: staleHeartbeat,
      messages: [
        '[PPTX]  16/24 ...',
        '[PPTX]  17/24 ...',
      ],
    },
  })

  await seedStoredTask(page, {
    id: localTaskId,
    taskId,
    projectId,
    type: 'editable-pptx',
    status: 'PROCESSING',
    progress: { total: 100, completed: 88, percent: 88, current_step: ' 17/24 ...' },
    createdAt: new Date().toISOString(),
  })

  try {
    await page.goto(`/project/${projectId}/preview`)
    await page.waitForFunction(() => document.body.innerText.length > 50, { timeout: 15000 })
    await page.getByLabel('').click()

    const panel = page.getByTestId('export-tasks-list')
    // Test verification logic
    await expect(panel.getByText(/^$/)).toBeVisible({ timeout: 20000 })
    // Test verification logic
    await expect(panel.getByText(/.*3\.5 /)).toBeVisible({ timeout: 20000 })
    await expect(panel.getByText('TASK_INTERRUPTED')).toBeVisible()
    await expect(panel.getByText('')).toBeVisible()
    await expect(panel.getByText(' × ')).toBeVisible()

    // Test verification logic
    await expect(panel.getByText('88%')).toHaveCount(0)
    await expect(page.getByText(/^\d+ $/)).toHaveCount(0)

    const taskResponse = await request.get(`/api/projects/${projectId}/tasks/${taskId}`)
    expect(taskResponse.ok()).toBeTruthy()
    const backendTask = (await taskResponse.json()).data
    expect(backendTask.status).toBe('FAILED')
    expect(backendTask.progress.error_code).toBe('TASK_INTERRUPTED')
    expect(backendTask.progress.percent).toBe(88)
  } finally {
    await request.delete(`/api/projects/${projectId}`)
  }
})

test('a task with a fresh heartbeat keeps running instead of being failed', async ({ page, request }) => {
  const projectId = await createProject(request, ' E2E')
  const taskId = crypto.randomUUID()
  const localTaskId = `e2e-watchdog-fresh-${Date.now()}`

  insertExportTask({
    taskId,
    projectId,
    status: 'PROCESSING',
    progress: {
      total: 100,
      completed: 88,
      failed: 0,
      current_step: ' 17/24 ...',
      percent: 88,
      heartbeat_at: new Date().toISOString(),
      messages: ['[PPTX]  17/24 ...'],
    },
  })

  await seedStoredTask(page, {
    id: localTaskId,
    taskId,
    projectId,
    type: 'editable-pptx',
    status: 'PROCESSING',
    progress: { total: 100, completed: 88, percent: 88, current_step: ' 17/24 ...' },
    createdAt: new Date().toISOString(),
  })

  const statusRequests: string[] = []
  page.on('request', (req) => {
    if (req.url().includes(`/tasks/${taskId}`)) statusRequests.push(req.url())
  })

  try {
    await page.goto(`/project/${projectId}/preview`)
    await page.waitForFunction(() => document.body.innerText.length > 50, { timeout: 15000 })
    await page.getByLabel('').click()

    const panel = page.getByTestId('export-tasks-list')
    await expect(panel.getByText('88%')).toBeVisible({ timeout: 10000 })

    // Test verification logic
    await expect.poll(() => statusRequests.length, { timeout: 15000 }).toBeGreaterThanOrEqual(3)

    await expect(panel.getByText('88%')).toBeVisible()
    await expect(panel.getByText(/|/)).toHaveCount(0)
    // Test verification logic
    await expect(panel.getByText('')).toHaveCount(0)

    const taskResponse = await request.get(`/api/projects/${projectId}/tasks/${taskId}`)
    const backendTask = (await taskResponse.json()).data
    expect(backendTask.status).toBe('PROCESSING')
  } finally {
    await request.delete(`/api/projects/${projectId}`)
  }
})

test('a stalled task renders the localized stuck message', async ({ page, request }) => {
  const projectId = await createProject(request, ' E2E')
  const taskId = crypto.randomUUID()
  const localTaskId = `e2e-watchdog-stalled-${Date.now()}`

  insertExportTask({
    taskId,
    projectId,
    status: 'FAILED',
    progress: {
      total: 100,
      completed: 88,
      failed: 1,
      current_step: ' 17/24 ...',
      percent: 88,
      backend_status: 'FAILED',
      error_code: 'TASK_STALLED',
      error_stage: 'task_watchdog',
      error_details: { reason: 'stalled', idle_seconds: 1260, last_step: 'PPTX' },
      messages: ['[PPTX]  17/24 ...'],
    },
  })

  await seedStoredTask(page, {
    id: localTaskId,
    taskId,
    projectId,
    type: 'editable-pptx',
    // Test verification logic
    status: 'PROCESSING',
    progress: { total: 100, completed: 88, percent: 88 },
    createdAt: new Date().toISOString(),
  })

  try {
    await page.goto(`/project/${projectId}/preview`)
    await page.waitForFunction(() => document.body.innerText.length > 50, { timeout: 15000 })
    await page.getByLabel('').click()

    const panel = page.getByTestId('export-tasks-list')
    await expect(panel.getByText(/^$/)).toBeVisible({ timeout: 15000 })
    await expect(panel.getByText(/ 21  PPTX/)).toBeVisible()
    await expect(panel.getByText('TASK_STALLED')).toBeVisible()
    await expect(panel.getByText('')).toBeVisible()
  } finally {
    await request.delete(`/api/projects/${projectId}`)
  }
})