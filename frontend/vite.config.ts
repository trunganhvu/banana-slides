/// <reference types="vitest" />
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'node:path'
import crypto from 'node:crypto'
import { execSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

/**
 * Compute a deterministic port from the worktree directory name.
 * Must match the algorithm in backend/app.py `_compute_worktree_port`.
 */
function computeWorktreePort(basePort: number): number {
  const basename = path.basename(path.resolve(__dirname, '..'))
  const hashHex = crypto.createHash('md5').update(basename).digest('hex').substring(0, 8)
  const offset = parseInt(hashHex, 16) % 500
  return basePort + offset
}

function gitValue(command: string): string {
  try {
    return execSync(command, {
      cwd: path.resolve(__dirname, '..'),
      stdio: ['ignore', 'pipe', 'ignore'],
      encoding: 'utf8',
    }).trim()
  } catch {
    return ''
  }
}

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Logic
  const envDir = path.resolve(__dirname, '..')

  // Logic
  const env = loadEnv(mode, envDir, '')

  // Logic
  const backendPort = env.BACKEND_PORT || String(computeWorktreePort(5011))
  const frontendPort = Number(env.FRONTEND_PORT) || computeWorktreePort(3011)
  const backendUrl = `http://localhost:${backendPort}`
  const gitTag = env.VITE_APP_VERSION_TAG || gitValue('git describe --tags --exact-match HEAD')
  const gitSha = env.VITE_APP_COMMIT_SHA || gitValue('git rev-parse HEAD')
  const gitShortSha = env.VITE_APP_COMMIT_SHORT_SHA || gitSha.slice(0, 7)
  
  return {
    base: './',
    envDir,
    plugins: [react()],
    define: {
      'import.meta.env.VITE_APP_VERSION_TAG': JSON.stringify(gitTag),
      'import.meta.env.VITE_APP_COMMIT_SHA': JSON.stringify(gitSha),
      'import.meta.env.VITE_APP_COMMIT_SHORT_SHA': JSON.stringify(gitShortSha),
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port: frontendPort,
      host: true, // 
      watch: {
        usePolling: true, // WSL 
      },
      hmr: {
        overlay: true, // 
      },
      proxy: {
        // Logic
        '/api': {
          target: backendUrl,
          changeOrigin: true,
        },
        // Logic
        '/files': {
          target: backendUrl,
          changeOrigin: true,
        },
        // Logic
        '/health': {
          target: backendUrl,
          changeOrigin: true,
        },
      },
    },
    // Logic
    test: {
      globals: true,
      environment: 'jsdom',
      setupFiles: './src/tests/setup.ts',
      include: ['src/**/*.{test,spec}.{js,ts,jsx,tsx}'],
      exclude: ['node_modules', 'dist'],
      coverage: {
        provider: 'v8',
        reporter: ['text', 'json', 'html'],
        exclude: [
          'node_modules/',
          'src/tests/',
          '**/*.d.ts',
          '**/*.config.*',
        ],
      },
    },
  }
})