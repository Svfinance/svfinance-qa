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

**2026-06-21 — suíte E2E desktop contra produção (após commit 0113a27)**
- Resultado: 12 passaram | 5 falharam | 8 pulados
- Config: `--config=tests/e2e/playwright.config.ts`, `workers: 1`, sem retries
- Log completo: `~/.local/share/rtk/tee/1782059976_playwright.log`

| Teste | Status | Causa raiz |
|---|---|---|
| Auth — todos (4) | ✅ | — |
| Contas — carrega | ✅ | — |
| Financeiro — transações carrega | ✅ | — |
| Financeiro — cards de saldo | ✅ | BUG-001 resolvido pelo commit 0113a27 |
| OS — lista sem erros | ✅ | — |
| Clientes — criar | ✅ | — |
| Clientes — validação | ✅ | — |
| Clientes — buscar | ✅ | BUG-002 resolvido pelo commit 0113a27 |
| Produtos — smoke | ✅ | resolvido (locator h1:has-text) |
| Clientes — editar | ❌ | BUG-003: `fill()` não dispara React onChange — usa nome original no PUT |
| Clientes — deletar | ❌ | BUG-004: DELETE executa mas cliente errado pode ter sido removido |
| Produtos — criar | ❌ | `waitForResponse` timeout: URL `/products`/`/items`/`/catalog` não bate com endpoint real |
| Produtos — buscar | ❌ | idem — depende de criarProduto que falha |
| Produtos — excluir | ❌ | idem — depende de criarProduto que falha |
| Contas — criar/vencida/pagar (3) | ⏭️ | skipped intencionalmente (seletores pendentes) |
| Financeiro — receita/despesa (2) | ⏭️ | skipped intencionalmente |
| OS — criar/filtrar (2) | ⏭️ | skipped intencionalmente |
| Clientes — COM OS (1) | ⏭️ | skipped intencionalmente |

### Execução anterior (2026-06-20)
- Resultado: 9 passaram | 9 falharam | 7 pulados
- Log: `~/.local/share/rtk/tee/1781914334_playwright.log`

---

## Achados de UX (comportamento da aplicação)

### UX-001 — Lista de clientes não atualiza automaticamente após criar/editar
- **Módulos afetados:** Clientes
- **Comportamento observado:** após criar ou editar um cliente e o modal fechar, a lista exibe dados antigos. Um reload completo da página é necessário para ver o novo estado.
- **É bug ou design?** A ser confirmado com Guilherme. O teste foi ajustado para fazer `page.goto("/clients")` + networkidle após cada operação de escrita.
- **Impacto de UX:** o usuário precisa pressionar F5 manualmente para ver o cliente recém-criado. Pode causar duplicatas se re-submeter o formulário.

### UX-002 — Lista de produtos não atualiza automaticamente após criar/editar
- **Módulos afetados:** Produtos & Serviços (`/products`)
- **Comportamento observado:** idêntico ao UX-001 — após criar um produto via formulário, a lista permanece com o estado anterior. O produto criado não aparece sem reload.
- **É bug ou design?** Mesma pergunta em aberto. O teste foi ajustado com reload após submit (mesmo padrão de clientes).
- **Impacto de UX:** usuário vê "Nenhum item encontrado" mesmo tendo acabado de criar um produto — risco alto de re-submissão acidental.

---

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

---

## Histórico de execuções

| Data | Resultado | Empresa QA usada | Observação |
|---|---|---|---|
| 2026-06-20 | 9✅ 9❌ 7⏭️ | seed QA existente | Primeira execução real contra produção |

---

## Hipóteses em aberto

1. **BUG-002**: o form de criação de cliente fecha silenciosamente (sem criar) quando chamado no segundo teste da mesma suíte — investigar se há validação de duplicidade por nome ou race condition com React state
2. **BUG-003**: `fill()` em input controlado pelo React com valor pré-existente não dispara onChange — testar com `click({clickCount:3}) + fill()` ou `pressSequentially()`
3. **UX-001/002**: confirmar com Guilherme se ausência de auto-refresh nas listas é design intencional ou bug a corrigir no frontend
