"""
Lê reports/<data>/falhas.jsonl e atualiza org-ia/estado-qa.md.

Idempotente: usa hash SHA-256 (8 chars) de modulo+cenario+erro[:100] para
não duplicar entradas BUG já registradas. A seção "Histórico de execuções"
recebe no máximo uma linha por data, mesmo que o script rode várias vezes.

Uso:
    python reports/consolidar_relatorio.py
    python reports/consolidar_relatorio.py --data 2026-06-17
"""

import hashlib
import json
import os
import re
import sys
from datetime import date, datetime

REPO_ROOT   = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ESTADO_PATH = os.path.join(REPO_ROOT, "org-ia", "estado-qa.md")
REPORTS_DIR = os.path.join(REPO_ROOT, "reports")


def _hash_falha(falha: dict) -> str:
    """Hash estável por falha — não muda se o JSONL for relido."""
    chave = f"{falha.get('modulo', '')}|{falha.get('cenario', '')}|{falha.get('erro', '')[:100]}"
    return hashlib.sha256(chave.encode()).hexdigest()[:8]


def _ler_falhas(data: str) -> list[dict]:
    arquivo = os.path.join(REPORTS_DIR, data, "falhas.jsonl")
    if not os.path.isfile(arquivo):
        return []
    falhas = []
    with open(arquivo, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if linha:
                try:
                    falhas.append(json.loads(linha))
                except json.JSONDecodeError:
                    continue
    return falhas


def _ids_existentes(conteudo: str) -> set[str]:
    """Extrai hashes já presentes no estado-qa.md para evitar duplicatas."""
    return set(re.findall(r"<!-- falha-id: ([a-f0-9]{8}) -->", conteudo))


def _proximo_bug(conteudo: str) -> int:
    nums = re.findall(r"## BUG-(\d+)", conteudo)
    return max((int(n) for n in nums), default=0) + 1


def _formatar_bug(n: int, falha: dict, fid: str, data: str) -> str:
    ts      = falha.get("timestamp", datetime.now().isoformat(timespec="seconds"))
    modulo  = falha.get("modulo", "?")
    cenario = falha.get("cenario", "?")
    erro    = falha.get("erro", "?")
    esperado = falha.get("resultado_esperado")
    cid     = falha.get("company_id_usado")

    linha_cenario  = f"- Cenário testado: {cenario}" + (f" (company_id: {cid})" if cid else "")
    linha_esperado = f"- Resultado esperado: {esperado}" if esperado else "- Resultado esperado: —"

    return (
        f"\n## BUG-{n:03d} — {modulo}\n"
        f"- Data/hora: {ts}\n"
        f"{linha_cenario}\n"
        f"{linha_esperado}\n"
        f"- Resultado obtido: {erro}\n"
        f"- Evidência: reports/{data}/falhas.jsonl\n"
        f"- Status: NÃO INVESTIGADO\n"
        f"- Hipótese de causa (se houver): —\n"
        f"<!-- falha-id: {fid} -->\n"
    )


def _hash_infra(falhas_setup: list[dict]) -> str:
    """Hash do bloco de infraestrutura — baseado no erro da primeira falha de setup."""
    erro = falhas_setup[0].get("erro", "") if falhas_setup else ""
    chave = f"infraestrutura|{erro[:100]}"
    return hashlib.sha256(chave.encode()).hexdigest()[:8]


def _formatar_bug_infra(n: int, falhas_setup: list[dict], fid: str, data: str) -> str:
    """Colapsa N falhas de setup numa única entrada de infraestrutura."""
    primeira = falhas_setup[0]
    ts    = primeira.get("timestamp", datetime.now().isoformat(timespec="seconds"))
    erro  = primeira.get("erro", "?")
    nomes = ", ".join(f.get("cenario", "?") for f in falhas_setup)
    n_af  = len(falhas_setup)

    return (
        f"\n## BUG-{n:03d} — infraestrutura/fixture\n"
        f"- Data/hora: {ts}\n"
        f"- Cenário testado: Falha de setup em {n_af} teste(s): {nomes}\n"
        f"- Resultado esperado: Fixture de sessão inicializa sem erros\n"
        f"- Resultado obtido: {erro}\n"
        f"- Evidência: reports/{data}/falhas.jsonl\n"
        f"- Status: INFRAESTRUTURA\n"
        f"- Hipótese de causa (se houver): —\n"
        f"<!-- falha-id: {fid} -->\n"
    )


def _atualizar_ultima_execucao(conteudo: str, data: str, resumo: str) -> str:
    """Substitui o conteúdo inteiro da seção 'Última execução'."""
    novo = (
        f"**Data:** {data}  \n"
        f"**Resultado:** {resumo}  \n"
        f"**Arquivo:** reports/{data}/falhas.jsonl"
    )
    return re.sub(
        r"(## Última execução\n).*?(\n---)",
        lambda m: m.group(1) + "\n" + novo + "\n",
        conteudo, count=1, flags=re.DOTALL,
    )


def _inserir_bugs(conteudo: str, novos: list[str]) -> str:
    """Insere novos BUGs na seção 'Bugs ativos'."""
    bloco = "".join(novos)
    if "**(nenhum ainda)**" in conteudo:
        return conteudo.replace("\n**(nenhum ainda)**\n", bloco, 1)
    # Sem placeholder: insere antes do '---' que fecha a seção
    return re.sub(
        r"(## Bugs ativos\n.*?)(\n---)",
        lambda m: m.group(1) + bloco + m.group(2),
        conteudo, count=1, flags=re.DOTALL,
    )


def _adicionar_historico(conteudo: str, data: str, resumo: str) -> str:
    """Adiciona linha ao histórico. Idempotente: ignora se a data já consta."""
    if f"| {data} |" in conteudo:
        return conteudo
    nova_linha = f"| {data} | {resumo} | — | — |"
    # Substitui o placeholder inicial
    if "| — | — | — | — |" in conteudo:
        return conteudo.replace("| — | — | — | — |", nova_linha, 1)
    # Fallback: adiciona após o cabeçalho da tabela
    return re.sub(
        r"(\| Data \|.*?\n\|[-| ]+\|\n)",
        lambda m: m.group(0) + nova_linha + "\n",
        conteudo, count=1,
    )


def main(data: str | None = None) -> None:
    data = data or date.today().isoformat()
    falhas = _ler_falhas(data)

    if not falhas:
        print(f"Nenhuma falha em reports/{data}/falhas.jsonl — estado-qa.md não alterado.")
        return

    # Entradas sem campo "fase" (legado antes da v2 do hook) tratadas como execucao
    falhas_setup = [f for f in falhas if f.get("fase") == "setup"]
    falhas_exec  = [f for f in falhas if f.get("fase") != "setup"]

    with open(ESTADO_PATH, encoding="utf-8") as f:
        conteudo = f.read()

    existentes = _ids_existentes(conteudo)
    proximo    = _proximo_bug(conteudo)
    novos_bugs = []
    n_duplas   = 0

    # Falhas de setup → 1 único BUG de infraestrutura, independente de quantos testes afetou
    if falhas_setup:
        fid = _hash_infra(falhas_setup)
        if fid in existentes:
            n_duplas += 1
        else:
            novos_bugs.append(_formatar_bug_infra(proximo, falhas_setup, fid, data))
            existentes.add(fid)
            proximo += 1

    # Falhas de execução → BUG individual por teste
    for falha in falhas_exec:
        fid = _hash_falha(falha)
        if fid in existentes:
            n_duplas += 1
            continue
        novos_bugs.append(_formatar_bug(proximo, falha, fid, data))
        existentes.add(fid)
        proximo += 1

    n_novas = len(novos_bugs)

    # Resumo com alerta explícito quando infra está quebrada
    partes = []
    if falhas_setup:
        partes.append(f"⚠️ {len(falhas_setup)} falha(s) de infraestrutura/fixture")
    if falhas_exec:
        partes.append(f"{len(falhas_exec)} falha(s) em teste(s)")
    detalhe = " + ".join(partes) if partes else "0 falhas"
    resumo  = f"{len(falhas)} falha(s) total — {detalhe} — {n_novas} BUG(s) novo(s), {n_duplas} duplicata(s)"

    if novos_bugs:
        conteudo = _inserir_bugs(conteudo, novos_bugs)

    conteudo = _atualizar_ultima_execucao(conteudo, data, resumo)
    conteudo = _adicionar_historico(conteudo, data, resumo)

    with open(ESTADO_PATH, "w", encoding="utf-8") as f:
        f.write(conteudo)

    print(f"estado-qa.md atualizado — {n_novas} BUG(s) novo(s), {n_duplas} duplicata(s) ignorada(s).")
    if falhas_setup:
        print(f"  ⚠️  {len(falhas_setup)} falha(s) de setup colapsadas em 1 BUG de infraestrutura.")


if __name__ == "__main__":
    data_arg = None
    args = sys.argv[1:]
    if "--data" in args:
        idx = args.index("--data")
        if idx + 1 < len(args):
            data_arg = args[idx + 1]
    main(data=data_arg)
