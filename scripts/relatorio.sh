#!/usr/bin/env bash
set -euo pipefail
DATA=$(date +%Y-%m-%d)
python reports/gerar_relatorio_bugs.py --data "$DATA"
echo ""
cat "reports/$DATA/RELATORIO-BUGS-PRONTOS.md"
