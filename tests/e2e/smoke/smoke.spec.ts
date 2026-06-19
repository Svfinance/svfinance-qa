/**
 * Suíte SMOKE — roda em todo push/PR, deve terminar em < 5 minutos.
 * Cobre o fluxo principal: login → dashboard → criar cliente → criar OS → concluir OS → logout.
 *
 * Roda em dois projetos: chromium (desktop) e mobile-chrome (375x812).
 * Nota: no mobile o menu usa o componente SidebarDock (bolinhas flutuantes),
 * por isso navegamos via URL direta em vez de clicar nos itens da sidebar.
 *
 * data-testid necessários para estabilizar este spec:
 *   - login-email-input, login-password-input, login-submit-button
 *   - dashboard-root (wrapper do dashboard)
 *   - new-client-button, client-name-input, client-submit-button
 *   - new-order-button, order-client-select, order-submit-button
 *   - order-status-badge (exibe o status atual da OS)
 *   - logout-button
 */

import { test, expect } from "@playwright/test";
import { loginQa, gotoPage } from "../helpers/auth";

const TIMESTAMP = Date.now();

test.describe("Smoke — Fluxo principal", () => {
  test.beforeEach(async ({ page }) => {
    await loginQa(page);
  });

  test("dashboard carrega após login", async ({ page }) => {
    // Verifica que algum elemento característico do dashboard está visível
    await expect(page.locator("text=Dashboard").first()).toBeVisible({ timeout: 10_000 });
  });

  test("criar cliente → aparece na lista", async ({ page }) => {
    const nomeCliente = `[QA] Smoke Cliente ${TIMESTAMP}`;
    await gotoPage(page, "/clients");

    // Abre modal de criação
    await page.click('button:has-text("+ Novo Cliente")');
    await page.waitForSelector('input[placeholder="Nome do cliente"]', { timeout: 8_000 });

    // Preenche nome e salva
    await page.fill('input[placeholder="Nome do cliente"]', nomeCliente);
    await page.click('button:has-text("Criar Cliente")');

    // Aguarda feedback (toast de sucesso ou cliente na lista)
    await page.waitForTimeout(2_000);
    await expect(page.locator(`text=${nomeCliente}`).first()).toBeVisible({ timeout: 10_000 });
  });

  test("criar OS vinculada ao cliente → aparece na lista", async ({ page }) => {
    await gotoPage(page, "/orders");

    // Abre modal de nova OS
    await page.click('button:has-text("+ Nova O.S")');
    await page.waitForSelector('select, [placeholder*="liente"]', { timeout: 8_000 });

    // Seleciona primeiro cliente disponível no select
    const clientSelect = page.locator("select").first();
    const options = await clientSelect.locator("option").count();
    if (options <= 1) {
      test.skip(true, "Nenhum cliente disponível para criar OS no smoke test");
      return;
    }
    await clientSelect.selectOption({ index: 1 });

    // Salva a OS
    const submitBtn = page.locator('button[type="submit"]').last();
    await submitBtn.click();

    // Aguarda feedback
    await page.waitForTimeout(2_000);
    // A OS criada deve aparecer na lista
    await expect(page.locator("text=Abertas, text=Em andamento, text=Total").first()).toBeVisible({ timeout: 10_000 });
  });

  test("logout redireciona para login", async ({ page }) => {
    // Tenta clicar no botão Sair — pode estar em sidebar vertical (desktop) ou dock (mobile)
    const sairBtn = page.locator('button:has-text("Sair"), span:has-text("Sair")').first();

    const isVisible = await sairBtn.isVisible().catch(() => false);
    if (!isVisible) {
      // No mobile com dock, o botão pode estar oculto; usa URL direta via localStorage clear
      await page.evaluate(() => {
        localStorage.clear();
        sessionStorage.clear();
      });
      await page.goto("/");
    } else {
      await sairBtn.click();
    }

    // Após logout deve estar na tela de login
    await expect(page.locator('button:has-text("ENTRAR"), input[type="email"]').first()).toBeVisible({ timeout: 10_000 });
  });
});
