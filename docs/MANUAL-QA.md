# Manual de QA — svfinance-qa

> Referência operacional para rodar, interpretar e corrigir testes do SV Finance.
> Última atualização: 2026-06-21 | Estado atual: 12 ✅ 5 ❌ 8 ⏭️

---

## 1. Visão geral

O svfinance-qa automatiza dois tipos de verificação rodando contra **produção** (`api.svfinance.com.br` + `app.svfinance.com.br`) usando uma empresa isolada criada pelo seed (nome sempre começa com `[QA] `).

| Tipo | Ferramenta | O que verifica |
|---|---|---|
| **Testes de API** | pytest + requests (Python) | Endpoints HTTP: status codes, payloads, regras de negócio |
| **Testes E2E** | Playwright (TypeScript) | Fluxos reais no navegador: login, CRUD de clientes, produtos, financeiro, OS |

**O que roda sozinho:** o workflow `qa-scheduled.yml` dispara a cada 6 horas via cron do GitHub Actions. Atualmente executa apenas os testes de API; os testes E2E ainda não estão no cron (item no backlog).

**O que é manual:** testes E2E, seed/cleanup de empresa QA, investigação de bugs.

---

## 2. Listar todos os testes existentes

```bash
# Testes de API (Python)
find tests/api/ -name "test_*.py" | sort

# Testes E2E (TypeScript)
find tests/e2e/ -name "*.spec.ts" | sort
```

Arquivos atuais:

```
tests/api/
  test_auth.py        test_bills.py       test_clients.py
  test_financial.py   test_orders.py      test_products.py
  test_team.py

tests/e2e/desktop/
  auth.spec.ts        bills.spec.ts       clients.spec.ts
  financial.spec.ts   orders.spec.ts      products.spec.ts

tests/e2e/smoke/
  smoke.spec.ts

tests/e2e/mobile/
  mobile-flows.spec.ts    mobile-layout.spec.ts   (não rodados em produção ainda)

tests/e2e/tablet/
  tablet-layout.spec.ts   (não rodado em produção ainda)
```

---

## 3. Rodar testes de API localmente

**Pré-requisito:** `.env` configurado com `DATABASE_URL`, `JWT_SECRET_KEY`, `SECRET_KEY` e `SVFINANCE_API_PATH` apontando para o diretório local do `svfinance-api`.

O pytest precisa rodar com o **venv do svfinance-api** (ele tem Flask + SQLAlchemy). O venv local do svfinance-qa não tem Flask.

```bash
# Rodar todos os testes de API
$SVFINANCE_API_PATH/venv/bin/python -m pytest tests/api/ -v

# Rodar apenas um módulo
$SVFINANCE_API_PATH/venv/bin/python -m pytest tests/api/test_clients.py -v

# Rodar um teste específico
$SVFINANCE_API_PATH/venv/bin/python -m pytest tests/api/test_clients.py::test_criar_cliente_dados_validos -v
```

Falhas são gravadas automaticamente em `reports/YYYY-MM-DD/falhas.jsonl` pelo hook do `conftest.py`.

---

## 4. Rodar testes E2E localmente

**Pré-requisito:** `.env` com `QA_EMAIL`, `QA_PASSWORD` e `E2E_BASE_URL` (padrão: `https://app.svfinance.com.br`).

```bash
# Suíte desktop completa (o mais comum)
npx playwright test --config=tests/e2e/playwright.config.ts tests/e2e/desktop/ --reporter=list

# Um spec específico
npx playwright test --config=tests/e2e/playwright.config.ts tests/e2e/desktop/clients.spec.ts --reporter=list

# Um teste específico por nome
npx playwright test --config=tests/e2e/playwright.config.ts --grep "editar cliente" --reporter=list

# Com UI do Playwright (abre browser visível — útil para debug)
npx playwright test --config=tests/e2e/playwright.config.ts tests/e2e/desktop/clients.spec.ts --headed
```

Artefatos de falha (screenshot, vídeo) ficam em `test-results/` na raiz do repo.

---

## 5. Execuções automáticas no GitHub Actions

Link direto: **https://github.com/Svfinance/svfinance-qa/actions**

O workflow `QA Agendado — svfinance` roda a cada 6 horas (00h, 06h, 12h, 18h UTC) e pode ser disparado manualmente via "Run workflow".

Cada execução sobe como artefato os arquivos `reports/` e `test-results/` (retidos por 7 dias). Para baixar: clique na execução → seção "Artifacts" → `qa-results-N-N`.

---

## 6. Como ler `org-ia/estado-qa.md`

Este arquivo é a fonte de verdade entre sessões. Sempre leia primeiro ao retomar o QA.

**Seção "Última execução":** data, resultado resumido (X ✅ Y ❌ Z ⏭️), tabela com causa raiz de cada falha.

**Seção "Achados de UX":** comportamentos da aplicação que podem ser bug ou design — registrados para decisão posterior com o time.

**Seção "Bugs ativos":** cada BUG-NNN tem: data, cenário, resultado esperado, resultado obtido, evidência (screenshot/log), status e hipótese de causa.

**Status de bug:**

| Status | Significado |
|---|---|
| `NÃO INVESTIGADO` | Falha detectada, ainda não analisada |
| `EM INVESTIGAÇÃO` | Em análise (hipótese registrada) |
| `CORRIGIDO` | Fix aplicado — citar commit do repo correto |
| `IGNORADO (falso positivo)` | Falha de ambiente ou dado de teste, não é bug real |

---

## 7. Fluxo de correção de bug

### 7.1 Decidir onde o bug está

| Sintoma | Repo a abrir |
|---|---|
| API retorna status errado, payload incorreto, regra de negócio violada | `svfinance-api` |
| UI não atualiza após ação, botão não funciona, modal não abre, seletor errado | `svfinance-app` |
| Teste usa seletor errado, aguarda tempo insuficiente, lógica de assertion errada | `svfinance-qa` |

### 7.2 Abrir o repo correto e aplicar o fix

```bash
# Backend
cd ~/projetos/svfinance/svfinance-api
claude

# Frontend
cd ~/projetos/svfinance/svfinance-app
claude

# Testes
cd ~/projetos/svfinance/svfinance-qa
claude
```

### 7.3 Antes de commitar — regras que nunca quebram

1. **SEMPRE revisar o diff** antes de aprovar qualquer `Edit` ou `Write` sugerido pelo Claude Code. Leia o que mudou, linha por linha.
2. **NUNCA commitar dentro do Claude Code.** O GPG falha por falta de TTY no terminal do agente. Use um terminal externo:

```bash
# Terminal externo (fora do Claude Code):
git diff                          # revisar o que mudou
git add -p                        # adicionar seletivamente
git commit -S -m "fix(clientes): descrição do fix"
```

3. **Depois do commit**, volte ao svfinance-qa e rode o teste que estava falhando para confirmar:

```bash
npx playwright test --config=tests/e2e/playwright.config.ts --grep "nome do teste" --reporter=list
```

### 7.4 Atualizar o estado após o fix

Abra `org-ia/estado-qa.md` e altere o status do BUG:

```markdown
- **Status:** CORRIGIDO — commit abc1234 no svfinance-app (descrição do que mudou)
```

---

## 8. Cobertura atual por módulo

Estado em 2026-06-21 (após commit `0113a27` no svfinance-app).

### API (pytest)

| Módulo | Arquivo | Estado |
|---|---|---|
| Auth | `test_auth.py` | Não rodado localmente recentemente (setup requer venv do svfinance-api) |
| Clientes | `test_clients.py` | Não rodado recentemente |
| Financeiro | `test_financial.py` | Não rodado recentemente |
| Ordens de Serviço | `test_orders.py` | Não rodado recentemente |
| Produtos | `test_products.py` | Não rodado recentemente |
| Contas | `test_bills.py` | Não rodado recentemente |
| Equipe | `test_team.py` | Não rodado recentemente |

> Os testes de API rodaram em 2026-06-18 e falharam por `ModuleNotFoundError` no setup (SVFINANCE_API_PATH não apontava para o repo). Após corrigir o `.env`, não foram rerodados.

### E2E Desktop (Playwright — run de 2026-06-21)

| Módulo | Cenário | Status |
|---|---|---|
| Auth | login válido | ✅ |
| Auth | senha errada exibe erro | ✅ |
| Auth | logout | ✅ |
| Auth | sem token redireciona | ✅ |
| Clientes | criar via formulário | ✅ |
| Clientes | buscar por nome | ✅ |
| Clientes | validação nome obrigatório | ✅ |
| Clientes | editar — mudança reflete na lista | ❌ BUG-003 (fix aplicado em 2026-06-21, requer rerun) |
| Clientes | deletar sem vínculo | ❌ BUG-004 (UI mostra cache stale após DELETE bem-sucedido) |
| Clientes | deletar COM OS vinculada | ⏭️ skipped |
| Financeiro | transações carrega | ✅ |
| Financeiro | cards de saldo | ✅ |
| Financeiro | criar receita | ⏭️ skipped |
| Financeiro | criar despesa | ⏭️ skipped |
| Contas | página carrega | ✅ |
| Contas | criar conta a pagar | ⏭️ skipped |
| Contas | conta vencida | ⏭️ skipped |
| Contas | marcar como paga | ⏭️ skipped |
| Produtos | página carrega | ✅ |
| Produtos | criar produto | ❌ URL do endpoint POST não identificada (timeout no waitForResponse) |
| Produtos | buscar produto | ❌ depende de criar |
| Produtos | excluir produto | ❌ depende de criar |
| OS | listar sem erro | ✅ |
| OS | criar OS | ⏭️ skipped |
| OS | filtrar por status | ⏭️ skipped |

### E2E Mobile / Tablet

Não rodados em produção. Os specs existem (`mobile-flows.spec.ts`, `mobile-layout.spec.ts`, `tablet-layout.spec.ts`) mas nunca foram executados contra produção.

---

## 9. Backlog de QA

| Item | Prioridade | Observação |
|---|---|---|
| Adicionar E2E ao cron (`qa-scheduled.yml`) | Alta | Atualmente só API roda no CI; E2E é manual |
| Descobrir URL real do endpoint POST de produtos | Alta | `waitForResponse` timeout — `/products`, `/items`, `/catalog` não batem |
| Resolver BUG-004 (delete UI stale) | Alta | Causa confirmada: cache frontend; decidir fix (polling ou verificação via API) |
| Rodar testes E2E mobile/tablet de verdade | Média | Specs existem mas nunca foram executados |
| NF-e | Baixa | Não iniciado — módulo ainda não tem spec |
| Restaura Glass (tenant separado) | Baixa | Deve ter spec próprio (`restauraglass.spec.ts`) com `isRG` detection |
| Testes de API — rerodar após fix do SVFINANCE_API_PATH | Média | Última tentativa falhou no setup, não nos testes em si |
| data-testid nos componentes React | Média | Lista em cada spec (ver comentário no topo de `clients.spec.ts`) — estabilizaria seletores frágeis |
