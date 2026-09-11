import { defineConfig } from '@playwright/test'
export default defineConfig({
  testDir: './tests', timeout: 30_000, use: { baseURL: 'http://127.0.0.1:8765' },
  webServer: { command: '..\\.venv\\Scripts\\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8765', cwd: '../backend', url: 'http://127.0.0.1:8765/api/health', reuseExistingServer: true }
})

