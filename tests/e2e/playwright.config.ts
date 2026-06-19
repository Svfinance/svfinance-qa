import { defineConfig, devices } from "@playwright/test";
import * as dotenv from "dotenv";
import * as path from "path";

// Carrega .env da raiz do svfinance-qa
dotenv.config({ path: path.resolve(__dirname, "../../.env") });

const BASE_URL = process.env.E2E_BASE_URL ?? "https://app.svfinance.com.br";

export default defineConfig({
  testDir: "./",
  testMatch: "**/*.spec.ts",
  timeout: 30_000,
  retries: process.env.CI ? 2 : 0,
  workers: 1, // sequencial — testes E2E compartilham estado da empresa QA

  // Screenshots, traces e vídeos vão para test-results/ na raiz do repo.
  // O workflow do GitHub Actions sobe essa pasta como artifact.
  outputDir: path.resolve(__dirname, "../../test-results"),

  reporter: [
    ["list"],
    [
      "html",
      {
        outputFolder: path.resolve(
          __dirname,
          "../../reports",
          new Date().toISOString().slice(0, 10),
          "playwright"
        ),
        open: "never",
      },
    ],
  ],

  use: {
    baseURL:      BASE_URL,
    headless:     true,
    screenshot:   "only-on-failure",
    video:        "retain-on-failure",
    trace:        "on-first-retry",   // grava trace apenas na primeira retry (CI usa retries: 2)
    locale:       "pt-BR",
    timezoneId:   "America/Sao_Paulo",
    // Flags necessárias para rodar no WSL2 sem sandbox de usuário
    launchOptions: {
      args: [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-software-rasterizer",
        "--single-process",
      ],
    },
  },

  projects: [
    {
      name: "chromium",
      use:  { ...devices["Desktop Chrome"] },
      testMatch: ["**/smoke/**/*.spec.ts", "**/desktop/**/*.spec.ts"],
    },
    {
      name: "mobile-chrome",
      use:  { ...devices["Pixel 5"], viewport: { width: 375, height: 812 } },
      testMatch: ["**/smoke/**/*.spec.ts", "**/mobile/**/*.spec.ts"],
    },
    {
      name: "tablet-chrome",
      use:  { ...devices["iPad (gen 7)"], viewport: { width: 768, height: 1024 } },
      testMatch: ["**/tablet/**/*.spec.ts"],
    },
  ],
});
