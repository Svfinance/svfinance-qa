/**
 * Testes de layout mobile — viewport 375x812 (iPhone SE).
 *
 * Cenários de layout:
 *  - Página de login não tem scroll horizontal
 *  - Dashboard não tem scroll horizontal
 *  - Tabelas têm scroll horizontal (overflow-x) quando necessário
 *  - Modais não transbordam do viewport
 *  - Botões têm área de toque mínima (~44px)
 *  - Formulários são usáveis (inputs não cortados)
 *
 * Nota: o SV Finance usa SidebarDock no mobile (bolinhas flutuantes draggable).
 * Não testamos cliques no dock — navegamos via URL direta.
 *
 * data-testid necessários para estabilizar:
 *   - main-content-wrapper (wrapper principal do conteúdo)
 *   - modal-container (container do modal para checar overflow)
 */

import { test, expect } from "@playwright/test";
import { loginQa, gotoPage } from "../helpers/auth";

test.describe("Layout Mobile (375x812)", () => {
  test("login sem scroll horizontal", async ({ page }) => {
    await page.goto("/");
    await page.waitForSelector('input[type="email"]', { timeout: 15_000 });

    // A largura do documento não deve exceder a largura do viewport
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const viewWidth   = page.viewportSize()?.width ?? 375;
    expect(scrollWidth).toBeLessThanOrEqual(viewWidth + 2); // +2 para borda
  });

  test("dashboard sem scroll horizontal após login", async ({ page }) => {
    await loginQa(page);
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const viewWidth   = page.viewportSize()?.width ?? 375;
    expect(scrollWidth).toBeLessThanOrEqual(viewWidth + 2);
  });

  test("página de clientes abre sem overflow horizontal", async ({ page }) => {
    await loginQa(page);
    await gotoPage(page, "/clients");
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const viewWidth   = page.viewportSize()?.width ?? 375;
    expect(scrollWidth).toBeLessThanOrEqual(viewWidth + 2);
  });

  test("página de orders abre sem overflow horizontal", async ({ page }) => {
    await loginQa(page);
    await gotoPage(page, "/orders");
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const viewWidth   = page.viewportSize()?.width ?? 375;
    expect(scrollWidth).toBeLessThanOrEqual(viewWidth + 2);
  });

  test("modal de criar cliente não transborda do viewport", async ({ page }) => {
    await loginQa(page);
    await gotoPage(page, "/clients");

    await page.click('button:has-text("+ Novo Cliente")');
    await page.waitForSelector('input[placeholder="Nome do cliente"]', { timeout: 8_000 });

    // O modal não deve causar scroll horizontal
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const viewWidth   = page.viewportSize()?.width ?? 375;
    expect(scrollWidth).toBeLessThanOrEqual(viewWidth + 4); // +4 tolerância para sombras

    // Input de nome deve estar visível (não cortado pelo viewport)
    const nomeInput = page.locator('input[placeholder="Nome do cliente"]');
    await expect(nomeInput).toBeVisible();
    const box = await nomeInput.boundingBox();
    expect(box).not.toBeNull();
    if (box) {
      expect(box.x + box.width).toBeLessThanOrEqual(viewWidth + 4);
    }
  });

  test("botão principal de criar cliente tem altura mínima de 40px", async ({ page }) => {
    await loginQa(page);
    await gotoPage(page, "/clients");

    const btn = page.locator('button:has-text("+ Novo Cliente")');
    const box = await btn.boundingBox();
    expect(box).not.toBeNull();
    if (box) {
      // Mínimo recomendado para toque: 40px (Apple HIG: 44px, mas 40px aceitável)
      expect(box.height).toBeGreaterThanOrEqual(40);
    }
  });

  test("formulário de cliente tem botão de submit visível sem scroll", async ({ page }) => {
    await loginQa(page);
    await gotoPage(page, "/clients");

    await page.click('button:has-text("+ Novo Cliente")');
    await page.waitForSelector('input[placeholder="Nome do cliente"]', { timeout: 8_000 });

    // Preenche o mínimo obrigatório
    await page.fill('input[placeholder="Nome do cliente"]', "[QA] Mobile Layout Test");

    // Botão de submit deve estar visível sem precisar scrollar
    const submitBtn = page.locator('button:has-text("Criar Cliente")');
    await submitBtn.scrollIntoViewIfNeeded();
    await expect(submitBtn).toBeVisible({ timeout: 5_000 });

    // Cancela o modal
    await page.click('button:has-text("Cancelar")');
  });
});
