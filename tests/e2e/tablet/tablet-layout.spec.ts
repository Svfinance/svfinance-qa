/**
 * Testes de layout tablet — viewport 768x1024.
 *
 * Cenários:
 *  - Login carrega sem overflow horizontal
 *  - Dashboard carrega sem overflow horizontal
 *  - Tabelas de clientes/OS sem scroll horizontal desnecessário
 *  - Formulários usam largura adequada (não coluna estreita de mobile)
 *  - Sidebar visível (tablet usa sidebar vertical ou horizontal)
 *
 * Nota: 768px é o breakpoint comum entre mobile e desktop.
 * O app pode usar layout de sidebar vertical colapsada neste viewport.
 */

import { test, expect } from "@playwright/test";
import { loginQa, gotoPage } from "../helpers/auth";

test.describe("Layout Tablet (768x1024)", () => {
  test("login sem overflow horizontal", async ({ page }) => {
    await page.goto("/");
    await page.waitForSelector('input[type="email"]', { timeout: 15_000 });

    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const viewWidth   = page.viewportSize()?.width ?? 768;
    expect(scrollWidth).toBeLessThanOrEqual(viewWidth + 2);
  });

  test("dashboard carrega sem overflow horizontal", async ({ page }) => {
    await loginQa(page);
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const viewWidth   = page.viewportSize()?.width ?? 768;
    expect(scrollWidth).toBeLessThanOrEqual(viewWidth + 2);
  });

  test("página de clientes sem overflow horizontal", async ({ page }) => {
    await loginQa(page);
    await gotoPage(page, "/clients");

    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const viewWidth   = page.viewportSize()?.width ?? 768;
    expect(scrollWidth).toBeLessThanOrEqual(viewWidth + 2);
  });

  test("página de OS sem overflow horizontal", async ({ page }) => {
    await loginQa(page);
    await gotoPage(page, "/orders");

    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const viewWidth   = page.viewportSize()?.width ?? 768;
    expect(scrollWidth).toBeLessThanOrEqual(viewWidth + 2);
  });

  test("formulário de cliente usa largura adequada para tablet", async ({ page }) => {
    await loginQa(page);
    await gotoPage(page, "/clients");

    await page.click('button:has-text("+ Novo Cliente")');
    await page.waitForSelector('input[placeholder="Nome do cliente"]', { timeout: 8_000 });

    const nomeInput = page.locator('input[placeholder="Nome do cliente"]');
    const box       = await nomeInput.boundingBox();
    expect(box).not.toBeNull();
    if (box) {
      // No tablet o input não deve ser nem muito estreito (mobile) nem ultra-largo (desktop wide)
      // Aceita qualquer largura >= 200px (formulário usável)
      expect(box.width).toBeGreaterThanOrEqual(200);
      // Não deve transbordar o viewport
      expect(box.x + box.width).toBeLessThanOrEqual((page.viewportSize()?.width ?? 768) + 4);
    }

    await page.click('button:has-text("Cancelar")');
  });

  test("sidebar visível ou navegação acessível no tablet", async ({ page }) => {
    await loginQa(page);

    // No tablet, deve existir alguma forma de navegação visível
    // Pode ser sidebar, top bar, ou dock
    const hasNav =
      (await page.locator('nav, [class*="sidebar"], [class*="Sidebar"]').first().isVisible().catch(() => false)) ||
      (await page.locator('button:has-text("Sair")').first().isVisible().catch(() => false)) ||
      (await page.locator('a[href="/clients"], a[href="/orders"]').first().isVisible().catch(() => false));

    expect(hasNav).toBe(true);
  });

  test("página de transações no tablet sem overflow", async ({ page }) => {
    await loginQa(page);
    await gotoPage(page, "/transactions");

    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const viewWidth   = page.viewportSize()?.width ?? 768;
    expect(scrollWidth).toBeLessThanOrEqual(viewWidth + 2);

    await expect(page.locator("text=Transações").first()).toBeVisible({ timeout: 10_000 });
  });
});
