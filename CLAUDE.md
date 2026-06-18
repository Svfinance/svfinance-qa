# CLAUDE.md — svfinance-qa
> Schema operacional sv-protocol v1.0. Regras transversais vivem em `~/.claude/CLAUDE.md` global.
> Este arquivo cobre APENAS o que é específico do repositório de QA automatizado.

---

## Projeto

- **Nome:** svfinance-qa
- **Descrição:** Suite de testes automatizados do SV Finance — testes de API (pytest + requests)
  e testes E2E (Playwright). Roda contra produção (`api.svfinance.com.br`) usando
  uma empresa fake isolada por `company_id`, criada e destruída pelo script de seed.
- **sv-protocol:** v1.0
- **Repo:** github.com/Svfinance/svfinance-qa
- **Branch principal:** `main`

---

## Atores

| Ator | Papel | Alias |
|---|---|---|
| Guilherme (Operador) | Owner · único commiter atual | `salvatiniguilherme@gmail.com` |
| Opus | Arquitetura, decisões, org-ia/ | `opus@svfinance.com.br` |
| Son Coder SV | Código, scripts (Fase 2) | `son-coder@svfinance.com.br` |

---

## Stack

- **Testes de API:** Python 3.13 · pytest · requests
- **Testes E2E:** Playwright (TypeScript)
- **Seed:** SQLAlchemy direto (importa `create_app` do svfinance-api via `sys.path`)
- **CI:** GitHub Actions (a definir)
- **Ambiente alvo:** Produção (`https://api.svfinance.com.br/api`)

**Decisões arquiteturais — não reabrir:**
- Testes rodam contra produção (não há staging)
- Empresa de QA isolada por `company_id` — nome sempre começa com `[QA] `
- Seed bypassa confirmação de e-mail setando `email_verified=True` direto no banco
- `/dev/verify/<email>` não funciona em produção (DEV_MODE=False no Render) — não tentar usar
- Cleanup automático: empresas QA com mais de 7 dias são deletadas pelo `cleanup_qa_companies.py`

---

## Topologia operacional

| Ambiente | URL | Observação |
|---|---|---|
| API alvo | `https://api.svfinance.com.br/api` | Configurável via `API_BASE_URL` no `.env` |
| Dev local | `http://localhost:5000/api` | Para testes locais contra o backend local |

---

## Estrutura do repositório

```
seed/
  seed_qa_company.py        # cria empresa QA no banco de produção
  cleanup_qa_companies.py   # remove empresas QA com mais de 7 dias
tests/
  api/
    conftest.py             # fixture qa_company (scope=session)
    test_*.py               # testes de API por módulo
  e2e/
    playwright.config.ts    # configuração do Playwright
    *.spec.ts               # specs E2E por fluxo
org-ia/
  estado-qa.md              # memória operacional entre sessões (BUGs, execuções)
reports/                    # gerado automaticamente (conteúdo no .gitignore)
```

---

## Como usar

### 1. Configurar ambiente

```bash
cp .env.example .env
# Editar .env com DATABASE_URL, JWT_SECRET_KEY, SECRET_KEY, RESEND_API_KEY
# e apontar SVFINANCE_API_PATH para o diretório local do svfinance-api
```

### 2. Criar empresa QA

```bash
# Adiciona o svfinance-api ao PYTHONPATH e roda o seed
python seed/seed_qa_company.py
# Saída: company_id, email e senha prontos para copiar
```

### 3. Rodar testes de API

```bash
pytest tests/api/ -v
```

### 4. Limpar empresas antigas

```bash
# Dry-run (padrão — não deleta nada)
python seed/cleanup_qa_companies.py

# Deletar de fato (exige flag explícita)
python seed/cleanup_qa_companies.py --confirm
```

---

## Ordem de leitura na retomada de sessão

1. `org-ia/estado-qa.md` — última execução e bugs pendentes
2. `git log --oneline -5` + `git diff --stat`
3. `CLAUDE.md` (este arquivo) — contexto operacional

---

## Padrões que nunca quebram (herdados do sv-protocol)

```python
# Seed sempre filtra pelo prefixo [QA] para nunca tocar em dados reais
companies = Company.query.filter(Company.name.like("[QA] %")).all()

# Cascade de delete — ordem obrigatória (ver cleanup_qa_companies.py)
# Nunca deletar Company sem antes deletar todos os dependentes

# Comentários de código em português claro e conciso
# Arquivos com no máximo 500-1500 linhas
```
