"""
Fixtures compartilhadas pelos testes de API.

A fixture `qa_company` roda o seed uma vez por sessão pytest, faz login via
POST /login e disponibiliza credenciais + cliente HTTP autenticado para todos
os testes que dependam dela.

O hook pytest_runtest_makereport grava falhas em JSONL para consolidação
posterior via reports/consolidar_relatorio.py.
"""

import json
import os
import sys
from datetime import date, datetime

import pytest
import requests
from dotenv import load_dotenv

# Carrega .env da raiz do svfinance-qa
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

# Adiciona o svfinance-api ao path para que o seed possa importar create_app
_api_path = os.environ.get("SVFINANCE_API_PATH", "")
if _api_path and os.path.isdir(_api_path) and _api_path not in sys.path:
    sys.path.insert(0, _api_path)


API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.svfinance.com.br/api").rstrip("/")

_REPO_ROOT   = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_REPORTS_DIR = os.path.join(_REPO_ROOT, "reports")


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def qa_company():
    """
    Cria empresa QA uma única vez por sessão de testes e retorna:

      - company_id  (int)
      - email       (str)
      - password    (str)
      - user_id     (int)
      - token       (str)  — JWT de 30 dias
      - client      (requests.Session) — pré-autenticado com o token JWT

    O seed não é desfeito ao final da sessão; a limpeza é responsabilidade
    do script cleanup_qa_companies.py (empresas >7 dias são removidas).
    """
    from app import create_app

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from seed.seed_qa_company import criar_empresa_qa

    flask_app = create_app()
    with flask_app.app_context():
        credenciais = criar_empresa_qa()

    # Login via API — smoke test implícito do seed
    resp = requests.post(
        f"{API_BASE_URL}/login",
        json={
            "email":    credenciais["email"],
            "password": credenciais["password"],
        },
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"Login da empresa QA falhou após o seed.\n"
        f"  Status: {resp.status_code}\n"
        f"  Body:   {resp.text}"
    )

    token = resp.json()["token"]

    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {token}"})
    session.base_url = API_BASE_URL  # tipo: ignore[attr-defined]

    return {
        "company_id": credenciais["company_id"],
        "email":      credenciais["email"],
        "password":   credenciais["password"],
        "user_id":    credenciais["user_id"],
        "token":      token,
        "client":     session,
    }


@pytest.fixture(scope="session")
def api(qa_company):
    """Atalho para o cliente HTTP autenticado."""
    return qa_company["client"]


@pytest.fixture(scope="session")
def base_url():
    """URL base da API para uso em testes que precisam montar URLs manualmente."""
    return API_BASE_URL


# ── Hook de captura de falhas ─────────────────────────────────────────────────

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Grava falhas em reports/<data>/falhas.jsonl para consolidação posterior."""
    outcome = yield
    rep = outcome.get_result()

    # Captura falhas de call (bug real) e de setup (fixture/infraestrutura)
    if rep.when not in ("call", "setup") or not rep.failed:
        return

    hoje = date.today().isoformat()
    pasta = os.path.join(_REPORTS_DIR, hoje)
    os.makedirs(pasta, exist_ok=True)

    # "test_clients.py" → "clients"
    nome_arquivo = os.path.basename(str(item.fspath))
    modulo = nome_arquivo.removeprefix("test_").removesuffix(".py")

    # Primeira linha da docstring como resultado esperado (convenção nos testes)
    resultado_esperado = None
    fn = getattr(item, "function", None)
    if fn and fn.__doc__:
        primeira = fn.__doc__.strip().splitlines()[0]
        if primeira:
            resultado_esperado = primeira

    # company_id da fixture se disponível no contexto do teste
    company_id_usado = None
    try:
        qa = item.funcargs.get("qa_company")
        if qa:
            company_id_usado = qa.get("company_id")
    except Exception:
        pass

    # Última linha não-vazia do traceback como mensagem de erro resumida
    erro_str = str(rep.longrepr)
    linhas = [l.strip() for l in erro_str.splitlines() if l.strip()]
    erro = linhas[-1][:300] if linhas else erro_str[:300]

    entrada: dict = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "modulo":    modulo,
        "cenario":   item.name,
        "erro":      erro,
        # "setup" → falha na fixture (infraestrutura); "execucao" → falha no corpo do teste
        "fase":      "setup" if rep.when == "setup" else "execucao",
    }
    if resultado_esperado:
        entrada["resultado_esperado"] = resultado_esperado
    if company_id_usado is not None:
        entrada["company_id_usado"] = company_id_usado

    arquivo = os.path.join(pasta, "falhas.jsonl")
    with open(arquivo, "a", encoding="utf-8") as f:
        f.write(json.dumps(entrada, ensure_ascii=False) + "\n")
