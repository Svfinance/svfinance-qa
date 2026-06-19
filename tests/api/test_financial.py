"""
Testes de API para transações financeiras e dashboard de cashflow.

Cenários cobertos:
  1. Criar transação de receita → 201
  2. Criar transação de despesa → 201
  3. Criar transação sem campos obrigatórios → 400
  4. Editar transação → 200, campo alterado reflete no GET
  5. Excluir transação → 200
  6. Listar transações → 200 com lista
  7. Filtrar transações por tipo → retorna apenas do tipo pedido
  8. Dashboard de cashflow (GET /cashflow) → 200 com campos de saldo e totais
  9. Saldo reflete criação de receita e despesa no mesmo período

Padrão de docstring: primeira linha = resultado esperado (alimenta o relatório automático).
"""

from datetime import date


_HOJE = date.today().isoformat()


def _criar_transacao(api, base_url, tipo="income", valor=100.00, descricao="[QA] Transação Teste"):
    """Cria transação e retorna o id. Levanta assertion em falha."""
    resp = api.post(f"{base_url}/transactions", json={
        "description": descricao,
        "amount":      valor,
        "type":        tipo,
        "date":        _HOJE,
    })
    assert resp.status_code == 201, f"Falha ao criar transação: {resp.text}"
    return resp.json()["id"]


class TestCriarTransacao:

    def test_criar_receita_retorna_201(self, api, base_url):
        """POST /transactions de receita deve retornar 201 com id."""
        resp = api.post(f"{base_url}/transactions", json={
            "description": "[QA] Receita Teste",
            "amount":      500.00,
            "type":        "income",
            "date":        _HOJE,
        })
        assert resp.status_code == 201, (
            f"Esperado 201, obtido {resp.status_code}: {resp.text}"
        )
        body = resp.json()
        assert "id" in body
        api.delete(f"{base_url}/transactions/{body['id']}")

    def test_criar_despesa_retorna_201(self, api, base_url):
        """POST /transactions de despesa deve retornar 201 com id."""
        resp = api.post(f"{base_url}/transactions", json={
            "description": "[QA] Despesa Teste",
            "amount":      200.00,
            "type":        "expense",
            "date":        _HOJE,
        })
        assert resp.status_code == 201, (
            f"Esperado 201, obtido {resp.status_code}: {resp.text}"
        )
        body = resp.json()
        assert "id" in body
        api.delete(f"{base_url}/transactions/{body['id']}")

    def test_criar_transacao_sem_campos_obrigatorios_retorna_400(self, api, base_url):
        """POST /transactions sem description, amount e type deve retornar 400."""
        resp = api.post(f"{base_url}/transactions", json={})
        assert resp.status_code == 400, (
            f"Esperado 400, obtido {resp.status_code}: {resp.text}"
        )

    def test_criar_transacao_tipo_invalido_retorna_400(self, api, base_url):
        """POST /transactions com type inválido deve retornar 400."""
        resp = api.post(f"{base_url}/transactions", json={
            "description": "[QA] Tipo Inválido",
            "amount":      100.0,
            "type":        "outro",
        })
        assert resp.status_code == 400, (
            f"Esperado 400, obtido {resp.status_code}: {resp.text}"
        )


class TestListarTransacoes:

    def test_listar_transacoes_retorna_200_com_lista(self, api, base_url):
        """GET /transactions deve retornar 200 com lista."""
        resp = api.get(f"{base_url}/transactions")
        assert resp.status_code == 200, f"Esperado 200, obtido {resp.status_code}: {resp.text}"
        assert isinstance(resp.json(), list)

    def test_filtrar_por_tipo_receita(self, api, base_url):
        """GET /transactions?type=income deve retornar apenas transações de receita."""
        t_id = _criar_transacao(api, base_url, tipo="income", descricao="[QA] Filtro Receita")
        try:
            resp = api.get(f"{base_url}/transactions", params={"type": "income"})
            assert resp.status_code == 200
            items = resp.json()
            tipos = {t["type"] for t in items}
            assert tipos <= {"income"}, (
                f"Filtro por income retornou outros tipos: {tipos}"
            )
        finally:
            api.delete(f"{base_url}/transactions/{t_id}")

    def test_filtrar_por_tipo_despesa(self, api, base_url):
        """GET /transactions?type=expense deve retornar apenas transações de despesa."""
        t_id = _criar_transacao(api, base_url, tipo="expense", descricao="[QA] Filtro Despesa")
        try:
            resp = api.get(f"{base_url}/transactions", params={"type": "expense"})
            assert resp.status_code == 200
            items = resp.json()
            tipos = {t["type"] for t in items}
            assert tipos <= {"expense"}, (
                f"Filtro por expense retornou outros tipos: {tipos}"
            )
        finally:
            api.delete(f"{base_url}/transactions/{t_id}")


class TestEditarTransacao:

    def test_editar_transacao_retorna_200(self, api, base_url):
        """PUT /transactions/<id> deve retornar 200 e valor deve refletir no GET /transactions."""
        t_id = _criar_transacao(api, base_url, descricao="[QA] Antes da Edição")
        try:
            resp_put = api.put(f"{base_url}/transactions/{t_id}", json={
                "description": "[QA] Após Edição",
                "amount":      999.00,
                "type":        "income",
            })
            assert resp_put.status_code == 200, (
                f"Esperado 200, obtido {resp_put.status_code}: {resp_put.text}"
            )
            # Verifica reflexo no GET /transactions
            resp_list = api.get(f"{base_url}/transactions")
            transacoes = resp_list.json()
            t = next((x for x in transacoes if x["id"] == t_id), None)
            assert t is not None, f"Transação {t_id} não encontrada após edição"
            assert t["amount"] == 999.00, f"amount esperado 999.0, obtido: {t['amount']}"
        finally:
            api.delete(f"{base_url}/transactions/{t_id}")


class TestExcluirTransacao:

    def test_excluir_transacao_retorna_200(self, api, base_url):
        """DELETE /transactions/<id> deve retornar 200."""
        t_id = _criar_transacao(api, base_url, descricao="[QA] Para Excluir")
        resp = api.delete(f"{base_url}/transactions/{t_id}")
        assert resp.status_code == 200, (
            f"Esperado 200, obtido {resp.status_code}: {resp.text}"
        )


class TestDashboardCashflow:

    def test_cashflow_retorna_200_com_campos_de_saldo(self, api, base_url):
        """GET /cashflow deve retornar 200 com saldo_final, total_income e total_expense."""
        resp = api.get(f"{base_url}/cashflow")
        assert resp.status_code == 200, (
            f"Esperado 200, obtido {resp.status_code}: {resp.text}"
        )
        body = resp.json()
        assert "saldo_final"   in body, f"Campo 'saldo_final' ausente: {list(body.keys())}"
        assert "total_income"  in body, f"Campo 'total_income' ausente: {list(body.keys())}"
        assert "total_expense" in body, f"Campo 'total_expense' ausente: {list(body.keys())}"

    def test_saldo_reflete_receita_e_despesa_criadas(self, api, base_url):
        """Criar receita e despesa no mês corrente deve refletir no saldo do cashflow."""
        # Captura saldo antes
        antes = api.get(f"{base_url}/cashflow").json()
        income_antes  = antes["total_income"]
        expense_antes = antes["total_expense"]

        receita_id  = _criar_transacao(api, base_url, tipo="income",  valor=1000.00, descricao="[QA] Receita Saldo")
        despesa_id  = _criar_transacao(api, base_url, tipo="expense", valor=400.00,  descricao="[QA] Despesa Saldo")
        try:
            depois = api.get(f"{base_url}/cashflow").json()
            assert depois["total_income"]  >= income_antes  + 1000.00 - 0.01, (
                f"total_income não aumentou: antes={income_antes}, depois={depois['total_income']}"
            )
            assert depois["total_expense"] >= expense_antes + 400.00  - 0.01, (
                f"total_expense não aumentou: antes={expense_antes}, depois={depois['total_expense']}"
            )
        finally:
            api.delete(f"{base_url}/transactions/{receita_id}")
            api.delete(f"{base_url}/transactions/{despesa_id}")
