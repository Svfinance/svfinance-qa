"""
Cria uma empresa de QA no banco de produção, isolada por company_id.

O usuário admin nasce com email_verified=True para bypass da confirmação de
e-mail — a rota /dev/verify não funciona em produção (DEV_MODE=False no Render).

Uso:
    python seed/seed_qa_company.py
"""

import json
import os
import sys
from datetime import datetime

from dotenv import load_dotenv

# Carrega .env antes de qualquer import do Flask, pois create_app() lê as
# variáveis de ambiente no momento da inicialização.
# Nota: app/__init__.py também chama load_dotenv() bare no import, mas por
# padrão não sobrescreve variáveis já setadas — este load_dotenv() prevalece.
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

_api_path = os.environ.get("SVFINANCE_API_PATH", "")
if not _api_path or not os.path.isdir(_api_path):
    print(
        "ERRO: SVFINANCE_API_PATH não definido ou inválido.\n"
        f"  Valor atual: {_api_path!r}\n"
        "  Defina no .env o caminho absoluto para o diretório raiz do svfinance-api."
    )
    sys.exit(1)

sys.path.insert(0, _api_path)

from app import create_app            # noqa: E402 — import após ajuste de sys.path
from app.extensions import db         # noqa: E402
from app.models import Company, User  # noqa: E402

_REPO_ROOT    = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_SESSION_FILE = os.path.join(_REPO_ROOT, ".qa_session.json")


def _obter_senha() -> str:
    """Falha explicitamente se QA_PASSWORD não estiver configurado."""
    senha = os.environ.get("QA_PASSWORD", "")
    if not senha:
        print(
            "ERRO: QA_PASSWORD não definido.\n"
            "  Adicione QA_PASSWORD=<senha> ao arquivo .env do svfinance-qa."
        )
        sys.exit(1)
    return senha


def criar_empresa_qa(senha: str | None = None) -> dict:
    """
    Cria Company + User QA e retorna as credenciais geradas.

    Não usa CompanyService porque ele não existe ainda. Se vier a existir,
    substituir a criação manual abaixo pela chamada ao service.
    """
    agora = datetime.now()
    hoje  = agora.strftime("%Y-%m-%d")
    hora  = agora.strftime("%H:%M:%S")
    ts    = agora.strftime("%Y%m%d%H%M%S")

    senha = senha or _obter_senha()
    email = f"qa+{ts}@svfinance.com.br"

    nova_empresa = Company(
        name       = f"[QA] {hoje} {hora}",   # ex: "[QA] 2026-06-17 14:32:07"
        plan       = "free",
        nicho      = "generic",
        created_at = hoje,                     # String(20) — não é DateTime
        active     = True,
    )
    db.session.add(nova_empresa)
    db.session.flush()  # garante nova_empresa.id antes do commit

    novo_usuario = User(
        email        = email,
        name         = "QA Bot",
        role         = "admin",
        account_type = "business",
        company_id   = nova_empresa.id,
        active       = True,
        # Bypass da confirmação de e-mail: a rota /dev/verify retorna 403
        # em produção (DEV_MODE=False), então setamos diretamente no banco
        email_verified           = True,
        email_verification_token = None,
    )
    novo_usuario.set_password(senha)
    db.session.add(novo_usuario)
    db.session.commit()

    return {
        "company_id":   nova_empresa.id,
        "company_name": nova_empresa.name,
        "email":        email,
        "password":     senha,
        "user_id":      novo_usuario.id,
    }


def main():
    app = create_app()
    with app.app_context():
        credenciais = criar_empresa_qa()

    with open(_SESSION_FILE, "w") as f:
        json.dump(credenciais, f, indent=2)

    print(f"\nEmpresa QA criada. Credenciais salvas em: {_SESSION_FILE}")
    print(f"  company_id : {credenciais['company_id']}")
    print(f"  company    : {credenciais['company_name']}")
    print(f"  email      : {credenciais['email']}")

    return credenciais


if __name__ == "__main__":
    main()
