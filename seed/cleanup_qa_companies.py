"""
Remove empresas de QA com mais de 7 dias do banco de produção.

Identifica empresas QA pelo prefixo "[QA] " no nome. A data é extraída do
próprio nome ("[QA] YYYY-MM-DD"), com fallback para o campo created_at.

Rodado sem flags: apenas lista o que seria deletado (dry-run seguro).
Para deletar de fato: passar --confirm.

Uso:
    python seed/cleanup_qa_companies.py             # dry-run
    python seed/cleanup_qa_companies.py --confirm   # deleta de fato
"""

import os
import sys
from datetime import date, datetime, timedelta

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

_api_path = os.environ.get("SVFINANCE_API_PATH", "")
if not _api_path or not os.path.isdir(_api_path):
    print(
        "ERRO: SVFINANCE_API_PATH não definido ou inválido.\n"
        f"  Valor atual: {_api_path!r}"
    )
    sys.exit(1)

sys.path.insert(0, _api_path)

from app import create_app                          # noqa: E402
from app.extensions import db                      # noqa: E402
from app.models import (                           # noqa: E402
    BrandAsset, BrandProject, Bill, CheckinPin,
    Client, CommissionRule, Company, Goal,
    ImportLog, LimpezaOccurrence, LimpezaServiceCard,
    Order, Product, Quote, ServiceCheckin,
    ServiceRecord, StockMovement, Subscription,
    Transaction, User,
)

LIMITE_DIAS = 7
PREFIXO_QA  = "[QA] "


def _data_da_empresa(company: Company) -> date | None:
    """
    Extrai a data de criação da empresa QA.

    Suporta dois formatos de nome:
      "[QA] YYYY-MM-DD HH:MM:SS"  (formato atual, desde 2026-06-17)
      "[QA] YYYY-MM-DD"           (formato antigo, caso existam empresas legadas)

    Os primeiros 10 chars após o prefixo são sempre "YYYY-MM-DD" em ambos os
    formatos, então basta fatiar [:10] para parsear.
    Fallback: campo created_at da Company.
    Retorna None se não conseguir parsear nenhum dos dois.
    """
    nome_sem_prefixo = company.name[len(PREFIXO_QA):]  # "2026-06-17 14:32:07" ou "2026-06-17"
    try:
        return datetime.strptime(nome_sem_prefixo[:10], "%Y-%m-%d").date()
    except ValueError:
        pass

    if company.created_at:
        try:
            return datetime.strptime(company.created_at[:10], "%Y-%m-%d").date()
        except ValueError:
            pass

    return None


def _deletar_dependentes(company_id: int) -> None:
    """
    Deleta todos os registros vinculados à empresa na ordem correta de FKs.

    Ordem baseada no mapa de dependências do models.py — nunca alterar
    sem reverificar quais FKs são NOT NULL em cada tabela.
    """
    cid = company_id

    # 1. checkin_pins: FK NOT NULL para clients, companies, users
    CheckinPin.query.filter_by(company_id=cid).delete()

    # 2. service_checkins: FK NOT NULL para clients, users, companies
    ServiceCheckin.query.filter_by(company_id=cid).delete()

    # 3-4. tabelas Restaura Glass sem FK formal (colunas simples)
    LimpezaOccurrence.query.filter_by(company_id=cid).delete()
    LimpezaServiceCard.query.filter_by(company_id=cid).delete()

    # 5. stock_movements: FK NOT NULL para products e users
    StockMovement.query.filter_by(company_id=cid).delete()

    # 6. service_records: FK NOT NULL para products e users
    ServiceRecord.query.filter_by(company_id=cid).delete()

    # 7-11. tabelas que dependem apenas de users (NOT NULL) e company (nullable)
    CommissionRule.query.filter_by(company_id=cid).delete()
    ImportLog.query.filter_by(company_id=cid).delete()
    Goal.query.filter_by(company_id=cid).delete()
    BrandAsset.query.filter_by(company_id=cid).delete()
    BrandProject.query.filter_by(company_id=cid).delete()

    # 12. bills: FK NOT NULL para users; nullable para transactions
    Bill.query.filter_by(company_id=cid).delete()

    # 13. orders: FK NOT NULL para clients e users; nullable para quotes/transactions
    Order.query.filter_by(company_id=cid).delete()

    # 14. quotes: FK NOT NULL para users; nullable para clients
    Quote.query.filter_by(company_id=cid).delete()

    # 15-17. transactions, products, clients: FK NOT NULL para users
    Transaction.query.filter_by(company_id=cid).delete()
    Product.query.filter_by(company_id=cid).delete()
    Client.query.filter_by(company_id=cid).delete()

    # 18. subscriptions: FK NOT NULL para companies
    Subscription.query.filter_by(company_id=cid).delete()

    # 19. users: FK nullable para companies
    User.query.filter_by(company_id=cid).delete()


def listar_candidatas() -> list[tuple[Company, date | None]]:
    """Retorna empresas QA com mais de LIMITE_DIAS dias."""
    corte = date.today() - timedelta(days=LIMITE_DIAS)
    empresas = Company.query.filter(Company.name.like(f"{PREFIXO_QA}%")).all()

    candidatas = []
    for emp in empresas:
        data_criacao = _data_da_empresa(emp)
        if data_criacao is None or data_criacao <= corte:
            candidatas.append((emp, data_criacao))

    return candidatas


def main(confirmar: bool = False) -> None:
    app = create_app()
    with app.app_context():
        candidatas = listar_candidatas()

        if not candidatas:
            print("Nenhuma empresa QA elegível para remoção.")
            return

        print(f"\nEmpresas QA para remover (>{LIMITE_DIAS} dias):")
        for emp, data_criacao in candidatas:
            data_str = data_criacao.isoformat() if data_criacao else "data desconhecida"
            print(f"  id={emp.id:>5}  criada={data_str}  nome={emp.name!r}")

        if not confirmar:
            print(
                f"\n[dry-run] Nenhuma empresa foi removida.\n"
                f"  Para confirmar, rode com --confirm"
            )
            return

        print("\nRemovendo...")
        for emp, _ in candidatas:
            _deletar_dependentes(emp.id)
            db.session.delete(emp)
            print(f"  Removida: id={emp.id}  nome={emp.name!r}")

        db.session.commit()
        print(f"\n{len(candidatas)} empresa(s) removida(s) com sucesso.")


if __name__ == "__main__":
    confirmar = "--confirm" in sys.argv
    main(confirmar=confirmar)
