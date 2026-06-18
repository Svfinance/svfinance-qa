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

  reporter: [
    ["list"],
    [
      "html",
      {
        outputFolder: path.resolve(
          __dirname,
          "../../reports",
          new Date().toISOString().slice(0, 10), // "2026-06-17"
          "playwright"
        ),
        open: "never",
      },
    ],
  ],

  use: {
    baseURL:           BASE_URL,
    headless:          true,
    screenshot:        "only-on-failure",
    video:             "retain-on-failure",
    trace:             "retain-on-failure",
    locale:            "pt-BR",
    timezoneId:        "America/Sao_Paulo",
  },

  projects: [
    {
      name:  "chromium",
      use:   { ...devices["Desktop Chrome"] },
    },
  ],
});
