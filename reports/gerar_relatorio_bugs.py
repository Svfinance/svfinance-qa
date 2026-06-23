"""
Lê org-ia/estado-qa.md e gera reports/<data>/RELATORIO-BUGS-PRONTOS.md
com uma ficha por bug ativo (NÃO INVESTIGADO ou EM INVESTIGAÇÃO).

Uso:
    python reports/gerar_relatorio_bugs.py
    python reports/gerar_relatorio_bugs.py --data 2026-06-22
"""

import os
import re
import sys
from datetime import date

REPO_ROOT   = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ESTADO_PATH = os.path.join(REPO_ROOT, "org-ia", "estado-qa.md")
REPORTS_DIR = os.path.join(REPO_ROOT, "reports")

STATUS_ATIVOS = {"NÃO INVESTIGADO", "EM INVESTIGAÇÃO"}


def _campo(bloco: str, *labels: str) -> str:
    """Extrai o valor de qualquer uma das labels (bold ou plain)."""
    for label in labels:
        m = re.search(
            rf"^- (?:\*\*)?{re.escape(label)}(?:\*\*)?:(?:\*\*)?\s*(.+)$",
            bloco, re.MULTILINE,
        )
        if m:
            return m.group(1).strip()
    return "—"


def _extrair_status(bloco: str) -> str:
    valor = _campo(bloco, "Status")
    # Normaliza: "CORRIGIDO — ..." → "CORRIGIDO", "EM INVESTIGAÇÃO — ..." → "EM INVESTIGAÇÃO"
    for s in STATUS_ATIVOS | {"CORRIGIDO", "IGNORADO (falso positivo)", "INFRAESTRUTURA"}:
        if valor.startswith(s):
            return s
    return valor


def _extrair_bugs(conteudo: str) -> list[dict]:
    """Extrai blocos BUG do estado-qa.md e filtra pelos status ativos."""
    bugs = []
    # Captura cada bloco ### BUG-NNN até o próximo ### BUG ou ---
    padrao = re.compile(
        r"^(### BUG-\d+[^\n]*\n(?:(?!^### BUG-\d+|^---).*\n)*)",
        re.MULTILINE,
    )
    for m in padrao.finditer(conteudo):
        bloco = m.group(1)
        titulo = re.match(r"### (.+)", bloco)
        status = _extrair_status(bloco)
        if status not in STATUS_ATIVOS:
            continue
        bugs.append({
            "titulo":   titulo.group(1).strip() if titulo else "BUG desconhecido",
            "data":     _campo(bloco, "Data/hora", "Data"),
            "cenario":  _campo(bloco, "Cenário testado", "Cenário", "Cenários afetados"),
            "esperado": _campo(bloco, "Resultado esperado"),
            "obtido":   _campo(bloco, "Resultado obtido"),
            "evidencia":_campo(bloco, "Evidência"),
            "status":   status,
            "hipotese": _campo(bloco,
                               "Hipótese de causa (se houver)",
                               "Hipótese (não confirmada)",
                               "Hipótese"),
        })
    return bugs


def _formatar_ficha(bug: dict) -> str:
    return (
        f"## {bug['titulo']}\n\n"
        f"- **Status:** {bug['status']}\n"
        f"- **Data:** {bug['data']}\n"
        f"- **Cenário:** {bug['cenario']}\n"
        f"- **Resultado esperado:** {bug['esperado']}\n"
        f"- **Resultado obtido:** {bug['obtido']}\n"
        f"- **Evidência:** {bug['evidencia']}\n"
        f"- **Hipótese:** {bug['hipotese']}\n"
    )


def main(data: str | None = None) -> None:
    data = data or date.today().isoformat()

    with open(ESTADO_PATH, encoding="utf-8") as f:
        conteudo = f.read()

    bugs_ativos = _extrair_bugs(conteudo)

    saida_dir = os.path.join(REPORTS_DIR, data)
    os.makedirs(saida_dir, exist_ok=True)
    saida_path = os.path.join(saida_dir, "RELATORIO-BUGS-PRONTOS.md")

    with open(saida_path, "w", encoding="utf-8") as f:
        f.write(f"# Relatório de Bugs Ativos — {data}\n\n")
        if not bugs_ativos:
            f.write("_Nenhum bug ativo no momento._\n")
        else:
            f.write(f"**Total:** {len(bugs_ativos)} bug(s) ativo(s)\n\n---\n\n")
            for bug in bugs_ativos:
                f.write(_formatar_ficha(bug))
                f.write("\n---\n\n")

    print(f"Relatório gerado: {saida_path} ({len(bugs_ativos)} bug(s) ativo(s))")


if __name__ == "__main__":
    data_arg = None
    args = sys.argv[1:]
    if "--data" in args:
        idx = args.index("--data")
        if idx + 1 < len(args):
            data_arg = args[idx + 1]
    main(data=data_arg)
