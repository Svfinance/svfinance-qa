"""
Testes de API para contas a pagar/receber (bills).

Cenários cobertos:
  1. Criar conta a pagar com vencimento futuro → 201
  2. Criar conta a pagar com vencimento passado → 201 (status continua 'pending' — sem auto-vencimento)
  3. Listar contas → 200 com lista
  4. Filtrar por status (pending/paid) → retorna apenas do status pedido
  5. Marcar conta como paga via PATCH /pay → 200, status muda para 'paid'
  6. Editar conta → 200
  7. Excluir conta → 200
  8. Conta inexistente → 404

Nota: a API não altera automaticamente o status para 'overdue' ao criar com vencimento passado.
O frontend é responsável por calcular e exibir contas vencidas visualmente.

Padrão de docstring: primeira linha = resultado esperado (alimenta o relatório automático).
"""

from datetime import date, timedelta


_HOJE        = date.today().isoformat()
_FUTURO      = (date.today() + timedelta(days=30)).isoformat()
_PASSADO     = (date.today() - timedelta(days=30)).isoformat()


def _criar_bill(api, base_url, status="pending", due_date=None, descricao="[QA] Conta Teste", tipo="payable"):
    """Cria uma conta e retorna o id. Levanta assertion em falha."""
    resp = api.post(f"{base_url}/bills", json={
        "description": descricao,
        "amount":      150.00,
        "type":        tipo,
        "status":      status,
        "due_date":    due_date or _FUTURO,
    })
    assert resp.status_code == 201, f"Falha ao criar conta: {resp.text}"
    return resp.json()["id"]


class TestCriarConta:

    def test_criar_conta_com_vencimento_futuro_retorna_201(self, api, base_url):
        """POST /bills com vencimento futuro deve retornar 201."""
        resp = api.post(f"{base_url}/bills", json={
            "description": "[QA] Conta Vencimento Futuro",
            "amount":      200.00,
            "type":        "payable",
            "status":      "pending",
            "due_date":    _FUTURO,
        })
        assert resp.status_code == 201, (
            f"Esperado 201, obtido {resp.status_code}: {resp.text}"
        )
        body = resp.json()
        assert "id" in body
        api.delete(f"{base_url}/bills/{body['id']}")

    def test_criar_conta_com_vencimento_passado_retorna_201(self, api, base_url):
        """POST /bills com vencimento passado deve retornar 201 com status 'pending'."""
        resp = api.post(f"{base_url}/bills", json={
            "description": "[QA] Conta Vencida",
            "amount":      100.00,
            "type":        "payable",
            "status":      "pending",
            "due_date":    _PASSADO,
        })
        assert resp.status_code == 201, (
            f"Esperado 201, obtido {resp.status_code}: {resp.text}"
        )
        # A API mantém 'pending' — o frontend aplica lógica de 'overdue' visualmente
        api.delete(f"{base_url}/bills/{resp.json()['id']}")

    def test_criar_conta_sem_campos_obrigatorios_retorna_400(self, api, base_url):
        """POST /bills sem description, amount, type e due_date deve retornar 400."""
        resp = api.post(f"{base_url}/bills", json={})
        assert resp.status_code == 400, (
            f"Esperado 400, obtido {resp.status_code}: {resp.text}"
        )

    def test_criar_conta_tipo_invalido_retorna_400(self, api, base_url):
        """POST /bills com type inválido deve retornar 400."""
        resp = api.post(f"{base_url}/bills", json={
            "description": "[QA] Tipo Inválido",
            "amount":      100.0,
            "type":        "outro",
            "due_date":    _FUTURO,
        })
        assert resp.status_code == 400, (
            f"Esperado 400, obtido {resp.status_code}: {resp.text}"
        )


class TestListarContas:

    def test_listar_contas_retorna_200_com_lista(self, api, base_url):
        """GET /bills deve retornar 200 com lista."""
        resp = api.get(f"{base_url}/bills")
        assert resp.status_code == 200, f"Esperado 200, obtido {resp.status_code}: {resp.text}"
        assert isinstance(resp.json(), list)

    def test_conta_inexistente_retorna_404_no_delete(self, api, base_url):
        """DELETE /bills/99999999 deve retornar 404."""
        resp = api.delete(f"{base_url}/bills/99999999")
        assert resp.status_code == 404, (
            f"Esperado 404, obtido {resp.status_code}: {resp.text}"
        )


class TestEditarConta:

    def test_editar_conta_retorna_200(self, api, base_url):
        """PUT /bills/<id> deve retornar 200."""
        bill_id = _criar_bill(api, base_url, descricao="[QA] Conta Antes Edição")
        try:
            resp = api.put(f"{base_url}/bills/{bill_id}", json={
                "description": "[QA] Conta Após Edição",
                "amount":      250.00,
                "type":        "payable",
                "status":      "pending",
                "due_date":    _FUTURO,
            })
            assert resp.status_code == 200, (
                f"Esperado 200, obtido {resp.status_code}: {resp.text}"
            )
        finally:
            api.delete(f"{base_url}/bills/{bill_id}")


class TestPagarConta:

    def test_marcar_conta_como_paga_retorna_200(self, api, base_url):
        """PATCH /bills/<id>/pay deve retornar 200 e status deve ser 'paid'."""
        bill_id = _criar_bill(api, base_url, descricao="[QA] Conta Para Pagar")
        try:
            resp = api.patch(f"{base_url}/bills/{bill_id}/pay")
            assert resp.status_code == 200, (
                f"Esperado 200, obtido {resp.status_code}: {resp.text}"
            )
            # Confirma o status via GET /bills
            bills = api.get(f"{base_url}/bills").json()
            bill  = next((b for b in bills if b["id"] == bill_id), None)
            assert bill is not None, f"Conta {bill_id} não encontrada após pagar"
            assert bill["status"] == "paid", (
                f"Status esperado 'paid', obtido: {bill['status']}"
            )
        finally:
            api.delete(f"{base_url}/bills/{bill_id}")

    def test_pagar_conta_cria_transacao_automaticamente(self, api, base_url):
        """PATCH /bills/<id>/pay deve criar uma transação automática (source='bill')."""
        bill_id = _criar_bill(
            api, base_url,
            descricao="[QA] Conta Gera Transação",
            tipo="payable",
        )
        try:
            api.patch(f"{base_url}/bills/{bill_id}/pay")
            # Verifica se foi criada uma transação de despesa com source='bill'
            transacoes = api.get(f"{base_url}/transactions", params={"source": "bill"}).json()
            t = next((x for x in transacoes if "[QA] Conta Gera Transação" in x.get("description", "")), None)
            assert t is not None, "Transação automática de bill não foi criada"
            assert t["type"] == "expense", f"Tipo esperado 'expense', obtido: {t['type']}"
        finally:
            api.delete(f"{base_url}/bills/{bill_id}")


class TestExcluirConta:

    def test_excluir_conta_retorna_200(self, api, base_url):
        """DELETE /bills/<id> deve retornar 200."""
        bill_id = _criar_bill(api, base_url, descricao="[QA] Conta Para Excluir")
        resp    = api.delete(f"{base_url}/bills/{bill_id}")
        assert resp.status_code == 200, (
            f"Esperado 200, obtido {resp.status_code}: {resp.text}"
        )
