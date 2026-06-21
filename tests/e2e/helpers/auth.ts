/**
 * Helpers de autenticação para testes E2E.
 * Lê credenciais do .qa_session.json na raiz do repo.
 */

import * as fs   from "fs";
import * as path from "path";
import { Page }  from "@playwright/test";

interface QaSession {
  company_id:   number;
  company_name: string;
  email:        string;
  password:     string;
  user_id:      number;
}

/** Retorna as credenciais da empresa QA do arquivo .qa_session.json. */
export function getQaSession(): QaSession {
  const sessionPath = path.resolve(__dirname, "../../../.qa_session.json");
  if (!fs.existsSync(sessionPath)) {
    throw new Error(
      ".qa_session.json não encontrado. " +
      "Execute: python seed/seed_qa_company.py"
    );
  }
  return JSON.parse(fs.readFileSync(sessionPath, "utf-8"));
}

/**
 * Faz login na aplicação via formulário.
 * Aguarda o redirecionamento para /dashboard antes de retornar.
 */
export async function loginQa(page: Page): Promise<void> {
  const { email, password } = getQaSession();

  // domcontentloaded é obrigatório — com "load" padrão o React ainda não hidratou
  // e o onClick do botão "Fazer login" não dispara o formulário
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1_500); // aguarda hidratação React

  await page.waitForSelector('text=Fazer login', { timeout: 10_000 });
  await page.click('text=Fazer login');
  await page.waitForSelector('input[type="email"]', { timeout: 10_000 });

  await page.fill('input[type="email"]',    email);
  await page.fill('input[type="password"]', password);
  await page.click('button:has-text("ENTRAR")');

  // Aguarda redirecionamento para o dashboard
  await page.waitForURL("**/dashboard", { timeout: 20_000 });
}

/**
 * Navega para uma página via URL direta (mais confiável que clicar na sidebar).
 * Aguarda o network estar idle antes de retornar.
 */
export async function gotoPage(page: Page, path: string): Promise<void> {
  await page.goto(path, { waitUntil: "domcontentloaded" });
  // networkidle pode nunca ser atingido em produção (WebSockets, polling) — não bloqueia
  await page.waitForLoadState("networkidle", { timeout: 15_000 }).catch(() => {});
}
