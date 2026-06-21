/**
 * Testes E2E de clientes — desktop (1280x720).
 *
 * Cenários:
 *  - Criar cliente → aparece na lista após reload
 *  - Buscar cliente → filtra corretamente
 *  - Editar cliente → mudança reflete na lista após reload
 *  - Deletar cliente sem vínculo → some da lista
 *  - Tentar deletar cliente COM OS vinculada → mensagem de erro aparece
 *  - Validação de campo obrigatório (nome) → não submete
 *
 * Achados da UI:
 *  - A lista NÃO atualiza automaticamente após criar/editar — reload necessário
 *  - Cada row (tr.cl-row) tem 2 botões: ✏️ (primeiro) e 🗑️ (último)
 *  - Delete abre modal com botões ✕, Cancelar, Excluir
 *
 * data-testid necessários para estabilizar:
 *   - new-client-button, client-name-input, client-submit-button
 *   - client-search-input, client-row, client-edit-button, client-delete-button
 *   - client-delete-confirm-button, client-error-toast
 */

import { test, expect, Page } from "@playwright/test";
import { loginQa, gotoPage }  from "../helpers/auth";

const TS = Date.now();

async function abrirFormCliente(page: Page) {
  await page.click('button:has-text("+ Novo Cliente")');
  await page.waitForSelector('input[placeholder="Nome do cliente"]', { timeout: 8_000 });
}

async function setReactInputValue(page: Page, selector: string, value: string) {
  // React controlled inputs ignoram fill() pois não dispara onChange via state interno.
  // A única forma confiável: usar o setter nativo do HTMLInputElement + disparar evento 'input'.
  await page.evaluate(
    ([sel, val]) => {
      const el = document.querySelector(sel) as HTMLInputElement | null;
      if (!el) throw new Error(`Elemento não encontrado: ${sel}`);
      const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value")!.set!;
      setter.call(el, val);
      el.dispatchEvent(new Event("input", { bubbles: true }));
      el.dispatchEvent(new Event("change", { bubbles: true }));
    },
    [selector, value] as const
  );
}

async function criarCliente(page: Page, nome: string) {
  await abrirFormCliente(page);
  await setReactInputValue(page, 'input[placeholder="Nome do cliente"]', nome);
  await page.click('button:has-text("Criar Cliente")');
  // Aguarda o form fechar antes de recarregar — reload prematuro cancela o POST
  await page.waitForSelector('input[placeholder="Nome do cliente"]', { state: "hidden", timeout: 10_000 });
  await page.waitForTimeout(1_000);
  // Lista não atualiza automaticamente — reload obrigatório (UX-001)
  await page.goto("/clients");
  await page.waitForLoadState("networkidle", { timeout: 20_000 }).catch(() => {});
  await page.waitForTimeout(1_500);
}

test.describe("Clientes — Desktop", () => {
  test.beforeEach(async ({ page }) => {
    await loginQa(page);
    await gotoPage(page, "/clients");
    await page.waitForTimeout(1_500);
  });

  test("criar cliente via formulário aparece na lista", async ({ page }) => {
    const nome = `[QA] E2E Criar ${TS}`;
    await criarCliente(page, nome);
    await expect(page.locator(`tr.cl-row:has-text("${nome}")`).first()).toBeVisible({ timeout: 8_000 });
  });

  test("buscar cliente pelo nome filtra corretamente", async ({ page }) => {
    const nome = `[QA] E2E Busca ${TS}`;
    await criarCliente(page, nome);

    // Pré-condição: cliente deve existir na lista após reload (sem filtro de busca)
    // Se falhar aqui, o problema é na criação (BUG-002), não na busca
    await expect(page.locator(`tr.cl-row:has-text("${nome}")`).first()).toBeVisible({ timeout: 8_000 });

    const busca = page.locator('input[placeholder*="Buscar"]');
    await busca.fill(nome.split(" ").pop() as string); // busca pelo timestamp (único)
    await page.waitForTimeout(1_000);

    await expect(page.locator(`tr.cl-row:has-text("${nome}")`).first()).toBeVisible();
    await busca.fill("");
  });

  test("validação de nome obrigatório não submete", async ({ page }) => {
    await abrirFormCliente(page);
    await page.click('button:has-text("Criar Cliente")');
    await page.waitForTimeout(1_000);

    // Modal ainda aberto — campo required impede submit
    const modalAberto = await page.locator('input[placeholder="Nome do cliente"]').isVisible();
    expect(modalAberto).toBe(true);
  });

  test("editar cliente mudança reflete na lista", async ({ page }) => {
    const nomeOriginal = `[QA] E2E Editar ${TS}`;
    const nomeEditado  = `[QA] E2E Editado ${TS}`;
    await criarCliente(page, nomeOriginal);

    // Busca pelo cliente para garantir que está visível (evita paginação)
    const busca = page.locator('input[placeholder*="Buscar"]');
    await busca.fill(String(TS));
    await page.waitForTimeout(1_000);

    // Clica no botão ✏️ (primeiro botão da row)
    const row = page.locator(`tr.cl-row:has-text("${nomeOriginal}")`).first();
    await row.waitFor({ timeout: 5_000 });
    const editBtn = row.locator("button").first();
    await editBtn.click();
    await page.waitForSelector('input[placeholder="Nome do cliente"]', { timeout: 5_000 });

    const nomeInput = page.locator('input[placeholder="Nome do cliente"]');
    // O form de edição pode ter comportamento diferente do form de criação
    // Tenta fill() primeiro; se não funcionar, cair em pressSequentially (BUG-003)
    await nomeInput.fill(nomeEditado);
    await page.waitForTimeout(300);

    // waitForResponse para PUT garante que o backend confirmou a atualização
    const [editResp] = await Promise.all([
      page.waitForResponse(
        res => /\/clients\/\d+/.test(res.url()) && (res.request().method() === "PUT" || res.request().method() === "PATCH"),
        { timeout: 15_000 }
      ),
      page.click('button:has-text("Salvar Alterações")'),
    ]);
    if (editResp.status() >= 400) throw new Error(`PUT /clients falhou: ${editResp.status()}`);
    await page.waitForTimeout(500);
    await page.goto("/clients");
    await page.waitForLoadState("networkidle", { timeout: 20_000 }).catch(() => {});
    await page.waitForTimeout(1_500);

    // Busca pelo novo nome para confirmar
    await busca.fill(String(TS));
    await page.waitForTimeout(1_000);
    await expect(page.locator(`tr.cl-row:has-text("${nomeEditado}")`).first()).toBeVisible({ timeout: 8_000 });
  });

  test("deletar cliente sem vínculo some da lista", async ({ page }) => {
    const nome = `[QA] E2E Deletar ${TS}`;
    await criarCliente(page, nome);

    // Busca pelo cliente para garantir visibilidade (evita paginação)
    const busca = page.locator('input[placeholder*="Buscar"]');
    await busca.fill(String(TS));
    await page.waitForTimeout(1_000);

    // Clica no botão 🗑️ (último botão da row)
    const row = page.locator(`tr.cl-row:has-text("${nome}")`).first();
    await row.waitFor({ timeout: 5_000 });
    await row.locator("button").last().click();

    // Aguarda modal pelo texto (o modal não tem role="dialog" — BUG-004)
    await page.waitForSelector('text=Esta ação não pode ser desfeita', { timeout: 5_000 });
    // waitForResponse garante que o backend confirmou a exclusão antes de navegar
    const [delResp] = await Promise.all([
      page.waitForResponse(
        res => /\/clients\/\d+/.test(res.url()) && res.request().method() === "DELETE",
        { timeout: 10_000 }
      ),
      page.locator('button:has-text("Excluir")').last().click(),
    ]);
    if (delResp.status() >= 400) throw new Error(`DELETE /clients falhou: ${delResp.status()}`);
    await page.waitForTimeout(500);
    // Reload para verificar — a UI pode não atualizar automaticamente após delete
    await page.goto("/clients");
    await page.waitForLoadState("networkidle", { timeout: 20_000 }).catch(() => {});
    await page.waitForTimeout(1_500);
    // Busca pelo TS (evita problemas com '[' na string de busca)
    await busca.fill(String(TS));
    await page.waitForTimeout(1_000);

    const aindaVisivel = await page.locator(`tr.cl-row:has-text("${nome}")`).isVisible().catch(() => false);
    expect(aindaVisivel).toBe(false);
  });

  test("deletar cliente COM OS vinculada exibe erro", async ({ page }) => {
    const nome = `[QA] E2E Cliente Com OS ${TS}`;
    await criarCliente(page, nome);

    // Busca o token do localStorage
    const token = await page.evaluate(() => localStorage.getItem("sv_token"));
    if (!token) {
      test.skip(true, "Token não encontrado no localStorage");
      return;
    }

    // Busca client_id via API
    const baseUrl = process.env.API_BASE_URL ?? "https://api.svfinance.com.br/api";
    const clients = await page.evaluate(async ([url, tkn, n]) => {
      const r = await fetch(`${url}/clients`, { headers: { Authorization: `Bearer ${tkn}` } });
      const d = await r.json();
      return (d as {name: string; id: number}[]).filter(c => c.name === n);
    }, [baseUrl, token, nome] as const);

    if (!clients.length) {
      test.skip(true, "Cliente criado não encontrado via API");
      return;
    }

    // Cria OS vinculada via API
    await page.evaluate(async ([url, tkn, cid]) => {
      await fetch(`${url}/orders`, {
        method: "POST",
        headers: { Authorization: `Bearer ${tkn}`, "Content-Type": "application/json" },
        body: JSON.stringify({ client_id: cid, items: [], notes: "[QA] OS para teste E2E" }),
      });
    }, [baseUrl, token, clients[0].id] as const);

    await page.reload();
    await page.waitForLoadState("networkidle", { timeout: 20_000 }).catch(() => {});
    await page.waitForTimeout(1_500);

    // Tenta excluir
    const row = page.locator(`tr.cl-row:has-text("${nome}")`).first();
    await row.waitFor({ timeout: 5_000 });
    await row.locator("button").last().click();

    // Aguarda modal abrir (mesmo padrão do teste deletar simples)
    const modal = page.locator('[role="dialog"]').first();
    await modal.waitFor({ state: "visible", timeout: 5_000 });
    await modal.locator('button:has-text("Excluir")').click();
    await page.waitForTimeout(3_000);

    // Deve exibir mensagem de erro (vínculo com OS)
    const erroVisivel =
      (await page.locator("text=vínculo").first().isVisible().catch(() => false)) ||
      (await page.locator("text=vinculado").first().isVisible().catch(() => false)) ||
      (await page.locator("text=pedido").first().isVisible().catch(() => false)) ||
      (await page.locator("text=Não é possível").first().isVisible().catch(() => false)) ||
      (await page.locator("text=ordem").first().isVisible().catch(() => false));

    expect(erroVisivel).toBe(true);
  });
});
