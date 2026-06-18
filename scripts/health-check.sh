#!/bin/bash
# scripts/health-check.sh — svfinance-qa
# Executar no início de TODA sessão Claude Code neste repo.
# Uso: ./scripts/health-check.sh

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_ROOT"

echo "=================================================="
echo "  svfinance-qa — Health Check (sv-protocol v1.0)"
echo "=================================================="
echo ""

# 1. Branch atual
BRANCH=$(git branch --show-current)
echo "📌 Branch: $BRANCH"
if [ "$BRANCH" != "main" ]; then
  echo "⚠️  ATENÇÃO: não está na main!"
fi
echo ""

# 2. Status do repositório
echo "📋 Git status:"
git status --short
echo ""

# 3. Últimos 5 commits
echo "📜 Últimos 5 commits:"
git log --oneline -5
echo ""

# 4. Diff pendente
DIFF=$(git diff --stat)
if [ -n "$DIFF" ]; then
  echo "📝 Diff pendente:"
  echo "$DIFF"
  echo ""
fi

# 5. Última empresa QA criada localmente
# Substitui o "flask db heads" do svfinance-api — não aplicável aqui
echo "🏢 Última empresa QA (local):"
if [ -f ".qa_session.json" ]; then
  company_id=$(python3 -c "import json; d=json.load(open('.qa_session.json')); print(d.get('company_id','?'))" 2>/dev/null || echo "?")
  company_name=$(python3 -c "import json; d=json.load(open('.qa_session.json')); print(d.get('company_name','?'))" 2>/dev/null || echo "?")
  echo "  company_id  : $company_id"
  echo "  company_name: $company_name"
else
  echo "  Nenhuma empresa QA local ainda — rode python seed/seed_qa_company.py antes de testar manualmente"
fi
echo ""

# 6. Arquivos org-ia disponíveis
echo "📁 org-ia/ disponível:"
if [ -d "org-ia" ]; then
  ls org-ia/
else
  echo "  (org-ia/ não encontrada)"
fi
echo ""

# 7. Bugs ativos — prévia rápida sem abrir o arquivo inteiro
echo "🐛 Bugs ativos (estado-qa.md):"
if [ -f "org-ia/estado-qa.md" ]; then
  TOTAL=$(grep -c "^## BUG-" org-ia/estado-qa.md 2>/dev/null || echo "0")
  if [ "$TOTAL" -eq 0 ]; then
    echo "  (nenhum bug registrado)"
  else
    echo "  Total registrado: $TOTAL bug(s)"
    # Mostra os títulos dos últimos 5 bugs (mais recentes)
    grep "^## BUG-" org-ia/estado-qa.md | tail -5 | while read -r linha; do
      echo "  $linha"
    done
    if [ "$TOTAL" -gt 5 ]; then
      echo "  ... (ver org-ia/estado-qa.md para lista completa)"
    fi
  fi
else
  echo "  (org-ia/estado-qa.md não encontrado)"
fi
echo ""

echo "=================================================="
echo "  Próximos passos:"
echo "  1. Ler org-ia/estado-qa.md (estado atual e bugs pendentes)"
echo "  2. Criar .env se não existir: cp .env.example .env"
echo "  3. Rodar python seed/seed_qa_company.py antes de testar manualmente"
echo "=================================================="
