import { defineConfig, devices } from "@playwright/test";

const WEB_PORT = Number(process.env.QA_WEB_PORT ?? 3000);
const API_PORT = Number(process.env.QA_API_PORT ?? 8000);

export default defineConfig({
  testDir: ".",
  globalSetup: require.resolve("./global-setup"),
  timeout: 120_000,
  expect: { timeout: 30_000 },
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: [["list"], ["html", { open: "never", outputFolder: "../playwright-report" }]],
  use: {
    baseURL: `http://127.0.0.1:${WEB_PORT}`,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: undefined,
  metadata: {
    apiBase: `http://127.0.0.1:${API_PORT}`,
  },
});
