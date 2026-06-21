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

    // domcontentloaded + 1500ms de espera evita race condition de hidratação React
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(1_500);
    await page.click('text=Fazer login');
    await page.waitForSelector('input[type="email"]', { timeout: 10_000 });

    await page.fill('input[type="email"]',    email);
    await page.fill('input[type="password"]', password);
    await page.click('button:has-text("ENTRAR")');

    await page.waitForURL("**/dashboard", { timeout: 20_000 });
    expect(page.url()).toContain("/dashboard");
  });

  test("login com senha errada exibe mensagem de erro", async ({ page }) => {
    const { email } = getQaSession();

    await page.goto("/", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(1_500);
    await page.click('text=Fazer login');
    await page.waitForSelector('input[type="email"]', { timeout: 10_000 });

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
    expect(page.url()).not.toContain("/dashboard");
  });

  test("logout retorna para landing page", async ({ page }) => {
    // Usa loginQa (já corrigido com domcontentloaded + wait)
    await import("../helpers/auth").then(({ loginQa }) => loginQa(page));

    // "Sair" é um <div> com onclick na sidebar (não um <button>)
    const sair = page.locator('text=Sair').first();
    await sair.waitFor({ state: "visible", timeout: 10_000 });
    await sair.click();

    // Após logout: retorna à landing page
    await page.waitForURL("**/", { timeout: 10_000 });
    await expect(page.locator('text=Fazer login').first()).toBeVisible({ timeout: 8_000 });
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
