import { defineConfig, devices } from '@playwright/test';

// Dev-only E2E harness. Serves the built ./public over http:// (dialog,
// module scripts, and Pagefind fetch all require a real origin, not file://).
// Nothing here ships — see CLAUDE.md "No npm" note.

const PORT = 8080;

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['github'], ['list']] : 'list',
  timeout: 15_000,
  use: {
    baseURL: `http://localhost:${PORT}`,
    trace: 'on-first-retry',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: `python3 -m http.server ${PORT} --directory public --bind 127.0.0.1`,
    url: `http://localhost:${PORT}/`,
    reuseExistingServer: !process.env.CI,
    timeout: 30_000,
  },
});
