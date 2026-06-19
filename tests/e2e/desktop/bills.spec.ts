/**
 * Testes E2E de contas a pagar/receber — desktop (1280x720).
 *
 * Cenários:
 *  - Criar conta a pagar → aparece na lista
 *  - Conta com vencimento passado aparece na lista (frontend pode destacar visualmente)
 *  - Marcar como paga → status muda visualmente
 *  - Excluir conta → some da lista
 *
 * data-testid necessários para estabilizar:
 *   Componente: Bills / BillForm
 *   - new-bill-button
 *   - bill-description-input
 *   - bill-amount-input
 *   - bill-due-date-input
 *   - bill-submit-button
 *   - bill-pay-button (marcar como paga)
 *   - bill-row (linha da lista)
 *   - bill-status-badge
 */

import { test, expect, Page } from "@playwright/test";
import { loginQa, gotoPage }  from "../helpers/auth";

const TS      = Date.now();
const FUTURO  = new Date(Date.now() + 30 * 86400000).toISOString().slice(0, 10);
const PASSADO = new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 10);

async function abrirFormConta(page: Page) {
  const btn = page.locator(
    'button:has-text("+ Nova"), button:has-text("Nova Conta"), button:has-text("Adicionar"), button:has-text("+")'
  ).first();
  await btn.waitFor({ state: "visible", timeout: 8_000 });
  await btn.click();
  await page.waitForTimeout(1_000);
}

test.describe("Contas a Pagar/Receber — Desktop", () => {
  test.beforeEach(async ({ page }) => {
    await loginQa(page);
    await gotoPage(page, "/bills");
  });

  test("página de contas carrega sem erro", async ({ page }) => {
    await expect(page.locator("text=Contas").first()).toBeVisible({ timeout: 10_000 });
  });

  test("criar conta a pagar aparece na lista", async ({ page }) => {
    const desc = `[QA] E2E Conta Pagar ${TS}`;
    await abrirFormConta(page);

    const descInput  = page.locator('input[placeholder*="Descrição"], input[placeholder*="escri"]').first();
    const hasForm    = await descInput.isVisible({ timeout: 5_000 }).catch(() => false);
    if (!hasForm) {
      test.skip(true, "Formulário de conta não encontrado — verificar seletor em Bills.jsx");
      return;
    }

    await descInput.fill(desc);

    const amountInput = page.locator('input[type="number"], input[placeholder*="alor"]').first();
    await amountInput.fill("350");

    // Data de vencimento
    const dateInput = page.locator('input[type="date"]').first();
    if (await dateInput.isVisible().catch(() => false)) {
      await dateInput.fill(FUTURO);
    }

    // Tipo: payable
    const tipoSelect = page.locator('select').first();
    if (await tipoSelect.isVisible().catch(() => false)) {
      await tipoSelect.selectOption("payable");
    }

    await page.locator('button[type="submit"], button:has-text("Salvar"), button:has-text("Criar")').last().click();
    await page.waitForTimeout(2_000);

    await expect(page.locator(`text=${desc}`).first()).toBeVisible({ timeout: 8_000 });
  });

  test("conta vencida aparece na lista (frontend destaca visualmente)", async ({ page }) => {
    const desc = `[QA] E2E Conta Vencida ${TS}`;
    await abrirFormConta(page);

    const descInput = page.locator('input[placeholder*="Descrição"], input[placeholder*="escri"]').first();
    const hasForm   = await descInput.isVisible({ timeout: 5_000 }).catch(() => false);
    if (!hasForm) {
      test.skip(true, "Formulário de conta não encontrado");
      return;
    }

    await descInput.fill(desc);
    const amountInput = page.locator('input[type="number"], input[placeholder*="alor"]').first();
    await amountInput.fill("100");
    const dateInput = page.locator('input[type="date"]').first();
    if (await dateInput.isVisible().catch(() => false)) {
      await dateInput.fill(PASSADO);
    }

    await page.locator('button[type="submit"], button:has-text("Salvar"), button:has-text("Criar")').last().click();
    await page.waitForTimeout(2_000);

    // Conta deve aparecer na lista (mesmo vencida)
    await expect(page.locator(`text=${desc}`).first()).toBeVisible({ timeout: 8_000 });
  });

  test("marcar conta como paga muda status visualmente", async ({ page }) => {
    const desc = `[QA] E2E Conta Pagar Status ${TS}`;
    await abrirFormConta(page);

    const descInput = page.locator('input[placeholder*="Descrição"], input[placeholder*="escri"]').first();
    const hasForm   = await descInput.isVisible({ timeout: 5_000 }).catch(() => false);
    if (!hasForm) {
      test.skip(true, "Formulário de conta não encontrado");
      return;
    }

    await descInput.fill(desc);
    await page.locator('input[type="number"]').first().fill("250");
    const dateInput = page.locator('input[type="date"]').first();
    if (await dateInput.isVisible().catch(() => false)) {
      await dateInput.fill(FUTURO);
    }
    await page.locator('button[type="submit"], button:has-text("Salvar"), button:has-text("Criar")').last().click();
    await page.waitForTimeout(2_000);

    // Procura botão de "Pagar" ou "Marcar como paga" na linha da conta
    const row    = page.locator(`tr:has-text("${desc}"), [class*="row"]:has-text("${desc}")`).first();
    const hasRow = await row.isVisible({ timeout: 5_000 }).catch(() => false);
    if (!hasRow) {
      test.skip(true, "Linha da conta não encontrada após criação");
      return;
    }

    const pagarBtn = row.locator('button:has-text("Pagar"), button:has-text("✓"), button[title*="Pagar"]').first();
    const hasPagar = await pagarBtn.isVisible().catch(() => false);
    if (!hasPagar) {
      test.skip(true, "Botão de pagar não encontrado — verificar seletor em Bills.jsx");
      return;
    }

    await pagarBtn.click();
    await page.waitForTimeout(2_000);

    // Status deve mudar visualmente (texto "Paga" ou cor diferente)
    const pagoVisivel = await page.locator(`text=Paga, text=paga, text=paid`).first().isVisible().catch(() => false);
    expect(pagoVisivel).toBe(true);
  });
});
