# org-ia/estado-qa.md — Memória Operacional do QA

Este arquivo é a fonte de verdade entre sessões de teste. Sempre que um teste
falhar, o estado deve ser registrado aqui de forma estruturada — seja por um
script automatizado, seja manualmente por Guilherme ou pelo agente ativo.

Ao iniciar qualquer sessão neste repositório, leia este arquivo primeiro.
Ele responde: o que está pendente, o que já foi tentado, e o que falta investigar.

---

## Formato de entrada de bug

```
## BUG-00X — <módulo>
- Data/hora:
- Cenário testado:
- Resultado esperado:
- Resultado obtido:
- Evidência: reports/<data>/<arquivo>
- Status: NÃO INVESTIGADO | EM INVESTIGAÇÃO | CORRIGIDO | IGNORADO (falso positivo)
- Hipótese de causa (se houver):
```

**Status possíveis:**
- `NÃO INVESTIGADO` — falha detectada, ainda não analisada
- `EM INVESTIGAÇÃO` — sendo investigada (registrar hipótese abaixo)
- `CORRIGIDO` — fix aplicado no svfinance-api (registrar commit)
- `IGNORADO (falso positivo)` — falha de ambiente ou dado de teste, não é bug real

---

## Última execução

**Data:** 2026-06-22  
**Resultado:** 78 falha(s) total — 78 falha(s) em teste(s) — 0 BUG(s) novo(s), 78 duplicata(s)  
**Arquivo:** reports/2026-06-22/falhas.jsonl


## Bugs ativos

### BUG-001 — Locator CSS com vírgula (`text=X, text=Y`) não funciona no Playwright
- **Data:** 2026-06-20
- **Cenários afetados:** smoke de Produtos, dashboard Financeiro
- **Resultado esperado:** locator com OR entre seletores de texto
- **Resultado obtido:** nenhum elemento encontrado (timeout) mesmo com os textos visíveis na página
- **Causa:** `text=X, text=Y` é interpretado como CSS onde `text=` não é pseudo-classe válida. A sintaxe correta é `:text("X"), :text("Y")` ou `page.locator('text=X').or(...)`.
- **Status:** CORRIGIDO — resolvido pelo commit 0113a27 do svfinance-app (ambos os testes passam agora)

### BUG-002 — criarCliente falha silenciosamente em testes sequenciais
- **Data:** 2026-06-20
- **Cenário:** teste "buscar cliente pelo nome" (segundo teste de clients.spec.ts)
- **Resultado esperado:** `[QA] E2E Busca {TS}` criado e visível após reload
- **Resultado obtido:** "Total de Clientes" permanece em 22 (sem incremento), cliente não encontrado
- **Status:** CORRIGIDO — resolvido pelo commit 0113a27 do svfinance-app (fetchClients atualiza lista corretamente após criação)

### BUG-003 — Edit de cliente não persiste (nome original permanece no DB)
- **Data:** 2026-06-20
- **Cenário:** teste "editar cliente mudança reflete na lista"
- **Resultado esperado:** nome editado visível após reload
- **Resultado obtido:** nome original permanece, screenshot confirma `[QA] E2E Editar {TS}` (não `[QA] E2E Editado`)
- **Evidência:** screenshot `test-results/desktop-clients-Clientes-—-eb91f-*/test-failed-1.png`
- **Causa confirmada:** linha 121 usa `fill()` mas o form de edição usa input controlado pelo React com valor pré-existente — `fill()` substitui o DOM mas NÃO dispara `onChange` do React. O `criarCliente()` usa corretamente `setReactInputValue()` (linha 51), mas o fluxo de edição não. O `waitForResponse` intercepta o PUT (que de fato retorna < 400), mas o payload vai com o nome original porque o React state nunca foi atualizado.
- **Status:** CAUSA CONFIRMADA — aguardando aprovação para aplicar fix (substituir `fill()` por `setReactInputValue()` na linha 121)

### BUG-004 — Delete executa mas cliente ainda visível após reload
- **Data:** 2026-06-20 / atualizado 2026-06-21
- **Cenário:** teste "deletar cliente sem vínculo some da lista"
- **Resultado esperado:** cliente removido após confirmar no modal
- **Resultado obtido:** `aindaVisivel = true` após reload + busca pelo TS
- **Evidência:** screenshot `test-results/desktop-clients-Clientes-—-0821f-*/test-failed-1.png`
- **O que se sabe:** o `waitForResponse` para DELETE `/clients/\d+` COMPLETOU sem timeout e com status < 400 (o teste não falha na linha 168). Ou seja: um DELETE foi executado com sucesso. Mas o cliente `[QA] E2E Deletar {TS}` ainda aparece na lista.
- **Hipótese (não confirmada):** o DELETE pode ter deletado outro cliente com o mesmo TS (Criar, Busca ou Editar). O modal pode estar mapeando o ID errado via estado React.
- **O que falta para confirmar:** logar `delResp.url()` para ver qual client_id foi deletado.
- **Status:** EM INVESTIGAÇÃO — diagnóstico incompleto, aguardando instrução para adicionar log diagnóstico

## BUG-005 — desktop/clients.spec.ts > Clientes — Desktop
- Data/hora: 2026-06-22 17:15:21
- Cenário testado: editar cliente mudança reflete na lista (company_id: 70)
- Resultado esperado: —
- Resultado obtido: Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('tr.cl-row:has-text("[QA] E2E Editado 1782148445443")').first()
Expected: visible
Timeout: 8000ms
Error: element(s) not found

Call log:
[2m  - Expect "toBeVisible" with timeout 8000ms[22m
[2m  - waiting for locator('tr.cl-row:has-text("[QA] E2E Editado 1782148445443")').first()[22m

- Evidência: reports/2026-06-22/falhas.jsonl
- Status: NÃO INVESTIGADO
- Hipótese de causa (se houver): —
<!-- falha-id: 720bb1a8 -->

## BUG-006 — desktop/clients.spec.ts > Clientes — Desktop
- Data/hora: 2026-06-22 17:16:56
- Cenário testado: deletar cliente sem vínculo some da lista (company_id: 70)
- Resultado esperado: —
- Resultado obtido: TimeoutError: page.waitForFunction: Timeout 10000ms exceeded.
- Evidência: reports/2026-06-22/falhas.jsonl
- Status: NÃO INVESTIGADO
- Hipótese de causa (se houver): —
<!-- falha-id: c08a67ca -->

## BUG-007 — desktop/products.spec.ts > Produtos — Desktop
- Data/hora: 2026-06-22 17:20:13
- Cenário testado: criar produto aparece na lista (company_id: 70)
- Resultado esperado: —
- Resultado obtido: TimeoutError: page.waitForResponse: Timeout 15000ms exceeded while waiting for event "response"
- Evidência: reports/2026-06-22/falhas.jsonl
- Status: NÃO INVESTIGADO
- Hipótese de causa (se houver): —
<!-- falha-id: 203eac5d -->

## BUG-008 — desktop/products.spec.ts > Produtos — Desktop
- Data/hora: 2026-06-22 17:21:37
- Cenário testado: campo de busca filtra produto por nome (company_id: 70)
- Resultado esperado: —
- Resultado obtido: TimeoutError: page.waitForResponse: Timeout 15000ms exceeded while waiting for event "response"
- Evidência: reports/2026-06-22/falhas.jsonl
- Status: NÃO INVESTIGADO
- Hipótese de causa (se houver): —
<!-- falha-id: 182b5a57 -->

## BUG-009 — desktop/products.spec.ts > Produtos — Desktop
- Data/hora: 2026-06-22 17:22:59
- Cenário testado: excluir produto some da lista (company_id: 70)
- Resultado esperado: —
- Resultado obtido: TimeoutError: page.waitForResponse: Timeout 15000ms exceeded while waiting for event "response"
- Evidência: reports/2026-06-22/falhas.jsonl
- Status: NÃO INVESTIGADO
- Hipótese de causa (se houver): —
<!-- falha-id: ff15e213 -->

## BUG-010 — smoke/smoke.spec.ts > Smoke — Fluxo principal
- Data/hora: 2026-06-22 17:24:19
- Cenário testado: criar cliente → aparece na lista (company_id: 70)
- Resultado esperado: —
- Resultado obtido: Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=[QA] Smoke Cliente 1782149035134').first()
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
[2m  - Expect "toBeVisible" with timeout 10000ms[22m
[2m  - waiting for locator('text=[QA] Smoke Cliente 1782149035134').first()[22m

- Evidência: reports/2026-06-22/falhas.jsonl
- Status: NÃO INVESTIGADO
- Hipótese de causa (se houver): —
<!-- falha-id: 2d5b20ae -->

## BUG-011 — smoke/smoke.spec.ts > Smoke — Fluxo principal
- Data/hora: 2026-06-22 17:25:27
- Cenário testado: criar OS vinculada ao cliente → aparece na lista (company_id: 70)
- Resultado esperado: —
- Resultado obtido: Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Abertas, text=Em andamento, text=Total').first()
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
[2m  - Expect "toBeVisible" with timeout 10000ms[22m
[2m  - waiting for locator('text=Abertas, text=Em andamento, text=Total').first()[22m

- Evidência: reports/2026-06-22/falhas.jsonl
- Status: NÃO INVESTIGADO
- Hipótese de causa (se houver): —
<!-- falha-id: f9072f57 -->

## BUG-012 — smoke/smoke.spec.ts > Smoke — Fluxo principal
- Data/hora: 2026-06-22 17:26:31
- Cenário testado: logout redireciona para login (company_id: 70)
- Resultado esperado: —
- Resultado obtido: Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('button:has-text("ENTRAR"), input[type="email"]').first()
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
[2m  - Expect "toBeVisible" with timeout 10000ms[22m
[2m  - waiting for locator('button:has-text("ENTRAR"), input[type="email"]').first()[22m

- Evidência: reports/2026-06-22/falhas.jsonl
- Status: NÃO INVESTIGADO
- Hipótese de causa (se houver): —
<!-- falha-id: 334365a9 -->

## BUG-013 — mobile/mobile-flows.spec.ts > Fluxos Mobile (375x812)
- Data/hora: 2026-06-22 17:27:24
- Cenário testado: login em mobile dashboard carrega sem layout quebrado (company_id: 70)
- Resultado esperado: —
- Resultado obtido: Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Dashboard').first()
Expected: visible
Timeout: 15000ms
Error: element(s) not found

Call log:
[2m  - Expect "toBeVisible" with timeout 15000ms[22m
[2m  - waiting for locator('text=Dashboard').first()[22m

- Evidência: reports/2026-06-22/falhas.jsonl
- Status: NÃO INVESTIGADO
- Hipótese de causa (se houver): —
<!-- falha-id: 6eb8f035 -->

## BUG-014 — mobile/mobile-flows.spec.ts > Fluxos Mobile (375x812)
- Data/hora: 2026-06-22 17:28:26
- Cenário testado: dashboard financeiro em mobile cards não transbordam (company_id: 70)
- Resultado esperado: —
- Resultado obtido: Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Saldo, text=Receitas, text=Despesas, text=Transações').first()
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
[2m  - Expect "toBeVisible" with timeout 10000ms[22m
[2m  - waiting for locator('text=Saldo, text=Receitas, text=Despesas, text=Transações').first()[22m

- Evidência: reports/2026-06-22/falhas.jsonl
- Status: NÃO INVESTIGADO
- Hipótese de causa (se houver): —
<!-- falha-id: 8cb70402 -->

## BUG-015 — mobile/mobile-flows.spec.ts > Fluxos Mobile (375x812)
- Data/hora: 2026-06-22 17:29:23
- Cenário testado: criar cliente em mobile formulário funcional (company_id: 70)
- Resultado esperado: —
- Resultado obtido: Error: [2mexpect([22m[31mreceived[39m[2m).[22mtoBe[2m([22m[32mexpected[39m[2m) // Object.is equality[22m

Expected: [32mtrue[39m
Received: [31mfalse[39m
- Evidência: reports/2026-06-22/falhas.jsonl
- Status: NÃO INVESTIGADO
- Hipótese de causa (se houver): —
<!-- falha-id: 28386f96 -->

## BUG-016 — mobile/mobile-flows.spec.ts > Fluxos Mobile (375x812)
- Data/hora: 2026-06-22 17:30:12
- Cenário testado: página de OS em mobile lista carrega sem erro (company_id: 70)
- Resultado esperado: —
- Resultado obtido: Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Pedidos / O.S, text=Ordens, text=Total').first()
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
[2m  - Expect "toBeVisible" with timeout 10000ms[22m
[2m  - waiting for locator('text=Pedidos / O.S, text=Ordens, text=Total').first()[22m

- Evidência: reports/2026-06-22/falhas.jsonl
- Status: NÃO INVESTIGADO
- Hipótese de causa (se houver): —
<!-- falha-id: b30e3089 -->

## BUG-017 — mobile/mobile-flows.spec.ts > Fluxos Mobile (375x812)
- Data/hora: 2026-06-22 17:31:21
- Cenário testado: página de transações em mobile lista carrega sem erro (company_id: 70)
- Resultado esperado: —
- Resultado obtido: Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Transações, text=Receitas, text=Despesas').first()
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
[2m  - Expect "toBeVisible" with timeout 10000ms[22m
[2m  - waiting for locator('text=Transações, text=Receitas, text=Despesas').first()[22m

- Evidência: reports/2026-06-22/falhas.jsonl
- Status: NÃO INVESTIGADO
- Hipótese de causa (se houver): —
<!-- falha-id: 26e05a59 -->

## BUG-018 — mobile/mobile-flows.spec.ts > Fluxos Mobile (375x812)
- Data/hora: 2026-06-22 17:32:25
- Cenário testado: página de contas em mobile carrega sem erro (company_id: 70)
- Resultado esperado: —
- Resultado obtido: Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Contas, text=Pagar, text=Receber, text=Vencimento').first()
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
[2m  - Expect "toBeVisible" with timeout 10000ms[22m
[2m  - waiting for locator('text=Contas, text=Pagar, text=Receber, text=Vencimento').first()[22m

- Evidência: reports/2026-06-22/falhas.jsonl
- Status: NÃO INVESTIGADO
- Hipótese de causa (se houver): —
<!-- falha-id: c9253b98 -->

## BUG-019 — mobile/mobile-layout.spec.ts > Layout Mobile (375x812)
- Data/hora: 2026-06-22 17:33:25
- Cenário testado: login sem scroll horizontal (company_id: 70)
- Resultado esperado: —
- Resultado obtido: TimeoutError: page.waitForSelector: Timeout 15000ms exceeded.
Call log:
[2m  - waiting for locator('input[type="email"]') to be visible[22m

- Evidência: reports/2026-06-22/falhas.jsonl
- Status: NÃO INVESTIGADO
- Hipótese de causa (se houver): —
<!-- falha-id: d0c6015a -->

## BUG-020 — smoke/smoke.spec.ts > Smoke — Fluxo principal
- Data/hora: 2026-06-22 17:35:11
- Cenário testado: dashboard carrega após login (company_id: 70)
- Resultado esperado: —
- Resultado obtido: Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Dashboard').first()
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
[2m  - Expect "toBeVisible" with timeout 10000ms[22m
[2m  - waiting for locator('text=Dashboard').first()[22m

- Evidência: reports/2026-06-22/falhas.jsonl
- Status: NÃO INVESTIGADO
- Hipótese de causa (se houver): —
<!-- falha-id: e3eb7996 -->

## BUG-021 — tablet/tablet-layout.spec.ts > Layout Tablet (768x1024)
- Data/hora: 2026-06-22 17:38:56
- Cenário testado: login sem overflow horizontal (company_id: 70)
- Resultado esperado: —
- Resultado obtido: Error: browserType.launch: Executable doesn't exist at /home/runner/.cache/ms-playwright/webkit-2311/pw_run.sh
╔════════════════════════════════════════════════════════════╗
║ Looks like Playwright was just installed or updated.       ║
║ Please run the following command to download new browsers: ║
║                                                            ║
║     npx playwright install                                 ║
║                                                            ║
║ <3 Playwright Team                                         ║
╚════════════════════════════════════════════════════════════╝
- Evidência: reports/2026-06-22/falhas.jsonl
- Status: NÃO INVESTIGADO
- Hipótese de causa (se houver): —
<!-- falha-id: b411dd5f -->

## BUG-022 — tablet/tablet-layout.spec.ts > Layout Tablet (768x1024)
- Data/hora: 2026-06-22 17:38:58
- Cenário testado: dashboard carrega sem overflow horizontal (company_id: 70)
- Resultado esperado: —
- Resultado obtido: Error: browserType.launch: Executable doesn't exist at /home/runner/.cache/ms-playwright/webkit-2311/pw_run.sh
╔════════════════════════════════════════════════════════════╗
║ Looks like Playwright was just installed or updated.       ║
║ Please run the following command to download new browsers: ║
║                                                            ║
║     npx playwright install                                 ║
║                                                            ║
║ <3 Playwright Team                                         ║
╚════════════════════════════════════════════════════════════╝
- Evidência: reports/2026-06-22/falhas.jsonl
- Status: NÃO INVESTIGADO
- Hipótese de causa (se houver): —
<!-- falha-id: fd6059c7 -->

## BUG-023 — tablet/tablet-layout.spec.ts > Layout Tablet (768x1024)
- Data/hora: 2026-06-22 17:39:00
- Cenário testado: página de clientes sem overflow horizontal (company_id: 70)
- Resultado esperado: —
- Resultado obtido: Error: browserType.launch: Executable doesn't exist at /home/runner/.cache/ms-playwright/webkit-2311/pw_run.sh
╔════════════════════════════════════════════════════════════╗
║ Looks like Playwright was just installed or updated.       ║
║ Please run the following command to download new browsers: ║
║                                                            ║
║     npx playwright install                                 ║
║                                                            ║
║ <3 Playwright Team                                         ║
╚════════════════════════════════════════════════════════════╝
- Evidência: reports/2026-06-22/falhas.jsonl
- Status: NÃO INVESTIGADO
- Hipótese de causa (se houver): —
<!-- falha-id: 851f0cb7 -->

## BUG-024 — tablet/tablet-layout.spec.ts > Layout Tablet (768x1024)
- Data/hora: 2026-06-22 17:39:02
- Cenário testado: página de OS sem overflow horizontal (company_id: 70)
- Resultado esperado: —
- Resultado obtido: Error: browserType.launch: Executable doesn't exist at /home/runner/.cache/ms-playwright/webkit-2311/pw_run.sh
╔════════════════════════════════════════════════════════════╗
║ Looks like Playwright was just installed or updated.       ║
║ Please run the following command to download new browsers: ║
║                                                            ║
║     npx playwright install                                 ║
║                                                            ║
║ <3 Playwright Team                                         ║
╚════════════════════════════════════════════════════════════╝
- Evidência: reports/2026-06-22/falhas.jsonl
- Status: NÃO INVESTIGADO
- Hipótese de causa (se houver): —
<!-- falha-id: f90214ce -->

## BUG-025 — tablet/tablet-layout.spec.ts > Layout Tablet (768x1024)
- Data/hora: 2026-06-22 17:39:03
- Cenário testado: formulário de cliente usa largura adequada para tablet (company_id: 70)
- Resultado esperado: —
- Resultado obtido: Error: browserType.launch: Executable doesn't exist at /home/runner/.cache/ms-playwright/webkit-2311/pw_run.sh
╔════════════════════════════════════════════════════════════╗
║ Looks like Playwright was just installed or updated.       ║
║ Please run the following command to download new browsers: ║
║                                                            ║
║     npx playwright install                                 ║
║                                                            ║
║ <3 Playwright Team                                         ║
╚════════════════════════════════════════════════════════════╝
- Evidência: reports/2026-06-22/falhas.jsonl
- Status: NÃO INVESTIGADO
- Hipótese de causa (se houver): —
<!-- falha-id: 8b691ecb -->

## BUG-026 — tablet/tablet-layout.spec.ts > Layout Tablet (768x1024)
- Data/hora: 2026-06-22 17:39:05
- Cenário testado: sidebar visível ou navegação acessível no tablet (company_id: 70)
- Resultado esperado: —
- Resultado obtido: Error: browserType.launch: Executable doesn't exist at /home/runner/.cache/ms-playwright/webkit-2311/pw_run.sh
╔════════════════════════════════════════════════════════════╗
║ Looks like Playwright was just installed or updated.       ║
║ Please run the following command to download new browsers: ║
║                                                            ║
║     npx playwright install                                 ║
║                                                            ║
║ <3 Playwright Team                                         ║
╚════════════════════════════════════════════════════════════╝
- Evidência: reports/2026-06-22/falhas.jsonl
- Status: NÃO INVESTIGADO
- Hipótese de causa (se houver): —
<!-- falha-id: 37da8e6f -->

## BUG-027 — tablet/tablet-layout.spec.ts > Layout Tablet (768x1024)
- Data/hora: 2026-06-22 17:39:07
- Cenário testado: página de transações no tablet sem overflow (company_id: 70)
- Resultado esperado: —
- Resultado obtido: Error: browserType.launch: Executable doesn't exist at /home/runner/.cache/ms-playwright/webkit-2311/pw_run.sh
╔════════════════════════════════════════════════════════════╗
║ Looks like Playwright was just installed or updated.       ║
║ Please run the following command to download new browsers: ║
║                                                            ║
║     npx playwright install                                 ║
║                                                            ║
║ <3 Playwright Team                                         ║
╚════════════════════════════════════════════════════════════╝
- Evidência: reports/2026-06-22/falhas.jsonl
- Status: NÃO INVESTIGADO
- Hipótese de causa (se houver): —
<!-- falha-id: 29e08881 -->

---

## Histórico de execuções

| Data | Resultado | Empresa QA usada | Observação |
|---|---|---|---|
| 2026-06-22 | 78 falha(s) total — 78 falha(s) em teste(s) — 23 BUG(s) novo(s), 55 duplicata(s) | — | — |
| 2026-06-20 | 9✅ 9❌ 7⏭️ | seed QA existente | Primeira execução real contra produção |

---

## Hipóteses em aberto

1. **BUG-002**: o form de criação de cliente fecha silenciosamente (sem criar) quando chamado no segundo teste da mesma suíte — investigar se há validação de duplicidade por nome ou race condition com React state
2. **BUG-003**: `fill()` em input controlado pelo React com valor pré-existente não dispara onChange — testar com `click({clickCount:3}) + fill()` ou `pressSequentially()`
3. **UX-001/002**: confirmar com Guilherme se ausência de auto-refresh nas listas é design intencional ou bug a corrigir no frontend
