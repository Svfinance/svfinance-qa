/**
 * Testes E2E de autenticação — desktop (1280x720).
 *
 * Cenários:
 *  - Login com credenciais válidas → redireciona para /dashboard
 *  - Login com senha errada → mensagem de erro visível
 *  - Logout → volta para tela de login
 *  - Tentar acessar /dashboard sem login → redireciona para login
 *
 * data-testid necessários para estabilizar:
 *   - login-email-input, login-password-input, login-submit-button
 *   - login-error-message (div de erro)
 *   - logout-button
 */

import { test, expect } from "@playwright/test";
import { getQaSession }  from "../helpers/auth";

test.describe("Auth — Desktop", () => {
  test("login válido redireciona para dashboard", async ({ page }) => {
    const { email, password } = getQaSession();

    await page.goto("/");
    await page.waitForSelector('input[type="email"]', { timeout: 15_000 });

    await page.fill('input[type="email"]',    email);
    await page.fill('input[type="password"]', password);
    await page.click('button:has-text("ENTRAR")');

    await page.waitForURL("**/dashboard", { timeout: 20_000 });
    expect(page.url()).toContain("/dashboard");
  });

  test("login com senha errada exibe mensagem de erro", async ({ page }) => {
    const { email } = getQaSession();

    await page.goto("/");
    await page.waitForSelector('input[type="email"]', { timeout: 15_000 });

    await page.fill('input[type="email"]',    email);
    await page.fill('input[type="password"]', "senhaerrada_qa_teste");
    await page.click('button:has-text("ENTRAR")');

    // Aguarda mensagem de erro aparecer (sem redirecionar)
    await page.waitForTimeout(3_000);
    const erroVisible =
      (await page.locator("text=Email ou senha inválidos").isVisible()) ||
      (await page.locator("text=inválido").first().isVisible().catch(() => false)) ||
      (await page.locator("text=erro").first().isVisible().catch(() => false));

    expect(erroVisible).toBe(true);
    // Não deve ter redirecionado
    expect(page.url()).not.toContain("/dashboard");
  });

  test("logout redireciona para tela de login", async ({ page }) => {
    const { email, password } = getQaSession();

    // Faz login
    await page.goto("/");
    await page.waitForSelector('input[type="email"]');
    await page.fill('input[type="email"]',    email);
    await page.fill('input[type="password"]', password);
    await page.click('button:has-text("ENTRAR")');
    await page.waitForURL("**/dashboard", { timeout: 20_000 });

    // Clica em Sair
    const sairBtn = page.locator('button:has-text("Sair")').first();
    await sairBtn.waitFor({ state: "visible", timeout: 10_000 });
    await sairBtn.click();

    // Aguarda voltar para login
    await expect(page.locator('button:has-text("ENTRAR")').first()).toBeVisible({ timeout: 10_000 });
  });

  test("acessar /dashboard sem token redireciona para login", async ({ page }) => {
    // Navega direto sem login — o app deve redirecionar
    await page.goto("/dashboard");
    await page.waitForTimeout(3_000);

    // Deve estar na tela de login (formulário visível) ou URL não deve ser /dashboard
    const loginVisible = await page.locator('input[type="email"]').isVisible().catch(() => false);
    const urlOk        = !page.url().includes("/dashboard");

    expect(loginVisible || urlOk).toBe(true);
  });
});
