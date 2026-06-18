#!/bin/bash
# scripts/save-session.sh — svfinance-qa
# Executar AO ENCERRAR toda sessão Claude Code neste repo.
# Uso: ./scripts/save-session.sh
#
# ATENÇÃO: usa git commit -S (assinatura GPG).
# GPG exige TTY interativo — NÃO funciona dentro do Claude Code.
# Se detectar ambiente Claude Code, este script aborta com aviso.

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_ROOT"

# Detecção de ambiente Claude Code.
# Claude Code define CLAUDE_CODE ou CLAUDECODE no ambiente do processo.
# Fallback adicional: verificar se stdout não é TTY (ex: pipe ou sub-processo).
DENTRO_CLAUDE_CODE=false
if [ -n "${CLAUDE_CODE:-}" ] || [ -n "${CLAUDECODE:-}" ]; then
  DENTRO_CLAUDE_CODE=true
fi
if [ ! -t 1 ]; then
  # stdout não é TTY — GPG não conseguirá solicitar a senha
  DENTRO_CLAUDE_CODE=true
fi

if [ "$DENTRO_CLAUDE_CODE" = true ]; then
  echo ""
  echo "⚠️  AVISO: ambiente sem TTY interativo detectado (Claude Code ou pipe)."
  echo "   git commit -S requer GPG com TTY para solicitar a senha da chave."
  echo "   Rode este script em um terminal normal, fora do Claude Code:"
  echo ""
  echo "   cd $PROJECT_ROOT"
  echo "   ./scripts/save-session.sh"
  echo ""
  exit 1
fi

echo "=================================================="
echo "  svfinance-qa — Salvando sessão (sv-protocol v1.0)"
echo "=================================================="
echo ""

# Verificar se há mudanças para commitar
STATUS=$(git status --short)
if [ -z "$STATUS" ]; then
  echo "ℹ️  Nenhuma mudança pendente. Nada a salvar."
  exit 0
fi

echo "📋 Mudanças desta sessão:"
git status --short
echo ""

# Commitar org-ia/ (estado-qa.md e afins)
ORGDIFF=$(git diff --name-only org-ia/ 2>/dev/null || true)
if [ -n "$ORGDIFF" ]; then
  git add org-ia/
  git commit -S -m "docs(org-ia): atualiza estado-qa da sessão $(date '+%Y-%m-%d')"
  echo "✅ org-ia/ salvo."
fi

# Avisar sobre arquivos fora de org-ia/ ainda não commitados
UNTRACKED=$(git status --short | grep "^??" | grep -v "org-ia/" | head -5 || true)
if [ -n "$UNTRACKED" ]; then
  echo ""
  echo "⚠️  Código não commitado detectado:"
  echo "$UNTRACKED"
  echo "   Commite o código antes de encerrar:"
  echo "   git add <arquivo> && git commit -S -m 'feat(escopo): descrição'"
fi

# Push
git push origin main
echo ""
echo "✅ Sessão salva e sincronizada com GitHub."
echo ""
echo "Na próxima sessão:"
echo "  cd $PROJECT_ROOT"
echo "  ./scripts/health-check.sh"
echo "  Ler org-ia/estado-qa.md"
echo "  claude"
echo "=================================================="
