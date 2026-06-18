"""
Fixtures compartilhadas pelos testes de API.

A fixture `qa_company` roda o seed uma vez por sessão pytest, faz login via
POST /login e disponibiliza credenciais + cliente HTTP autenticado para todos
os testes que dependam dela.
"""

import os
import sys

import pytest
import requests
from dotenv import load_dotenv

# Carrega .env da raiz do svfinance-qa
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

# Adiciona o svfinance-api ao path para que o seed possa importar create_app
_api_path = os.environ.get("SVFINANCE_API_PATH", "")
if _api_path and os.path.isdir(_api_path) and _api_path not in sys.path:
    sys.path.insert(0, _api_path)


# URL base da API — sobrescrita via variável de ambiente para facilitar
# apontar para localhost em dev
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.svfinance.com.br/api").rstrip("/")


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
    from app.extensions import db

    # Importa a função de seed — evita duplicar a lógica de criação aqui
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from seed.seed_qa_company import criar_empresa_qa

    flask_app = create_app()
    with flask_app.app_context():
        credenciais = criar_empresa_qa()

    # Login via API para obter o JWT — valida que a empresa criada consegue
    # autenticar de fato (smoke test implícito do seed)
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

    # Session com Authorization pré-configurada para todos os testes
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
