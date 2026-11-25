import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 90_000,
  retries: 0,
  reporter: "line",
  use: { baseURL: process.env.SRC_E2E_URL ?? "http://localhost:3000" },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        launchOptions: { executablePath: process.env.SRC_E2E_CHROMIUM },
      },
    },
    { name: "firefox", use: { ...devices["Desktop Firefox"] } },
  ],
});
