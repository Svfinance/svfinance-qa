/**
 * Testes de fluxos mobile — viewport 375x812.
 *
 * Cenários de funcionalidade em tela pequena:
 *  - Login em mobile → dashboard carrega sem layout quebrado
 *  - Dashboard financeiro em mobile → cards visíveis e não transbordam
 *  - Criar cliente em mobile → formulário usável e funcional
 *  - Página de OS em mobile → lista carrega sem erro
 *  - Página de transações em mobile → lista carrega sem erro
 *
 * Navegação: sempre via URL direta (o dock mobile é draggable e difícil de clicar).
 */

import { test, expect } from "@playwright/test";
import { loginQa, gotoPage } from "../helpers/auth";

const TS = Date.now();

test.describe("Fluxos Mobile (375x812)", () => {
  test("login em mobile dashboard carrega sem layout quebrado", async ({ page }) => {
    await loginQa(page);

    // Dashboard deve carregar (algum elemento com texto Dashboard ou widget)
    await expect(page.locator("text=Dashboard").first()).toBeVisible({ timeout: 15_000 });

    // Sem scroll horizontal
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    expect(scrollWidth).toBeLessThanOrEqual((page.viewportSize()?.width ?? 375) + 2);
  });

  test("dashboard financeiro em mobile cards não transbordam", async ({ page }) => {
    await loginQa(page);
    await gotoPage(page, "/transactions");

    // Aguarda carregamento
    await page.waitForLoadState("networkidle");
    const viewWidth = page.viewportSize()?.width ?? 375;

    // Verifica overflow horizontal
    const overflow = await page.evaluate(() => {
      const body = document.body;
      return body.scrollWidth > window.innerWidth;
    });
    expect(overflow).toBe(false);

    // Verifica que algum card/elemento de saldo está visível
    await expect(page.locator("text=Saldo, text=Receitas, text=Despesas, text=Transações").first()).toBeVisible({ timeout: 10_000 });
    const _ = viewWidth; // usa variável
  });

  test("criar cliente em mobile formulário funcional", async ({ page }) => {
    await loginQa(page);
    await gotoPage(page, "/clients");

    // Abre formulário
    await page.click('button:has-text("+ Novo Cliente")');
    await page.waitForSelector('input[placeholder="Nome do cliente"]', { timeout: 8_000 });

    // Input deve estar visível e focável
    const nomeInput = page.locator('input[placeholder="Nome do cliente"]');
    await expect(nomeInput).toBeVisible();

    // Preenche e submete
    await nomeInput.fill(`[QA] Mobile Criar ${TS}`);
    await page.click('button:has-text("Criar Cliente")');
    await page.waitForTimeout(2_000);

    // Verifica que o cliente foi criado (aparece na lista ou toast de sucesso)
    const criado = await page.locator(`text=[QA] Mobile Criar ${TS}`).first().isVisible({ timeout: 8_000 }).catch(() => false);
    const toast  = await page.locator("text=sucesso, text=criado, text=Cliente").first().isVisible({ timeout: 3_000 }).catch(() => false);
    expect(criado || toast).toBe(true);
  });

  test("página de OS em mobile lista carrega sem erro", async ({ page }) => {
    await loginQa(page);
    await gotoPage(page, "/orders");

    await expect(page.locator("text=Pedidos / O.S, text=Ordens, text=Total").first()).toBeVisible({ timeout: 10_000 });

    // Sem erro crítico de JS (página não em branco)
    const bodyText = await page.locator("body").innerText();
    expect(bodyText.length).toBeGreaterThan(20);
  });

  test("página de transações em mobile lista carrega sem erro", async ({ page }) => {
    await loginQa(page);
    await gotoPage(page, "/transactions");

    await expect(page.locator("text=Transações, text=Receitas, text=Despesas").first()).toBeVisible({ timeout: 10_000 });

    const bodyText = await page.locator("body").innerText();
    expect(bodyText.length).toBeGreaterThan(20);
  });

  test("página de contas em mobile carrega sem erro", async ({ page }) => {
    await loginQa(page);
    await gotoPage(page, "/bills");

    await expect(page.locator("text=Contas, text=Pagar, text=Receber, text=Vencimento").first()).toBeVisible({ timeout: 10_000 });

    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    expect(scrollWidth).toBeLessThanOrEqual((page.viewportSize()?.width ?? 375) + 2);
  });
});
