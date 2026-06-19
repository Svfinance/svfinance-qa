"""
Testes de API para ordens de serviço e pedidos.

Cenários cobertos:
  1. Criar OS sem informar client_id → 400 (campo obrigatório pela API)
  2. Criar OS com cliente vinculado → 201
  3. Listar OS → 200 com lista
  4. Editar OS em aberto → 200
  5. Concluir OS via PATCH /status → 200, status muda para 'done'
  6. Cancelar OS → 200, status muda para 'cancelled'
  7. Deletar OS → 200
  8. Deletar OS inexistente → 404

Nota: a API exige client_id em POST /orders — "sem cliente" retorna 400.
Padrão de docstring: primeira linha = resultado esperado (alimenta o relatório automático).
"""

import pytest


def _criar_cliente(api, base_url, nome="[QA] Cliente OS"):
    """Cria um cliente auxiliar e retorna o id. Levanta assertion em falha."""
    resp = api.post(f"{base_url}/clients", json={"name": nome})
    assert resp.status_code == 201, f"Falha ao criar cliente auxiliar: {resp.text}"
    return resp.json()["id"]


def _criar_order(api, base_url, client_id):
    """Cria uma order e retorna o id. Levanta assertion em falha."""
    resp = api.post(f"{base_url}/orders", json={
        "client_id": client_id,
        "items":     [],
        "notes":     "[QA] OS de teste",
    })
    assert resp.status_code == 201, f"Falha ao criar order: {resp.text}"
    return resp.json()["id"]


class TestCriarOrder:

    def test_criar_order_sem_cliente_retorna_400(self, api, base_url):
        """POST /orders sem client_id deve retornar 400 (campo obrigatório)."""
        resp = api.post(f"{base_url}/orders", json={"items": [], "notes": "[QA] sem cliente"})
        assert resp.status_code == 400, (
            f"Esperado 400 (client_id obrigatório), obtido {resp.status_code}: {resp.text}"
        )

    def test_criar_order_com_cliente_retorna_201(self, api, base_url):
        """POST /orders com client_id válido deve retornar 201 com id e number."""
        client_id = _criar_cliente(api, base_url, "[QA] Cliente Criar OS")
        try:
            resp = api.post(f"{base_url}/orders", json={
                "client_id": client_id,
                "items":     [],
                "notes":     "[QA] OS criada no teste",
            })
            assert resp.status_code == 201, (
                f"Esperado 201, obtido {resp.status_code}: {resp.text}"
            )
            body = resp.json()
            assert "id"     in body, "Response deve conter 'id'"
            assert "number" in body, "Response deve conter 'number'"
            order_id = body["id"]
        finally:
            api.delete(f"{base_url}/orders/{order_id}")
            api.delete(f"{base_url}/clients/{client_id}")


class TestListarOrders:

    def test_listar_orders_retorna_200_com_lista(self, api, base_url):
        """GET /orders deve retornar 200 com lista (pode ser vazia)."""
        resp = api.get(f"{base_url}/orders")
        assert resp.status_code == 200, f"Esperado 200, obtido {resp.status_code}: {resp.text}"
        assert isinstance(resp.json(), list), "Response deve ser uma lista"


class TestEditarOrder:

    def test_editar_order_aberta_retorna_200(self, api, base_url):
        """PUT /orders/<id> em ordem aberta deve retornar 200."""
        client_id = _criar_cliente(api, base_url, "[QA] Cliente Editar OS")
        order_id  = _criar_order(api, base_url, client_id)
        try:
            resp = api.put(f"{base_url}/orders/{order_id}", json={
                "notes": "[QA] Nota editada",
            })
            assert resp.status_code == 200, (
                f"Esperado 200, obtido {resp.status_code}: {resp.text}"
            )
        finally:
            api.delete(f"{base_url}/orders/{order_id}")
            api.delete(f"{base_url}/clients/{client_id}")


class TestMudarStatusOrder:

    def test_concluir_order_muda_status_para_done(self, api, base_url):
        """PATCH /orders/<id>/status para 'done' deve retornar 200 e status='done'."""
        client_id = _criar_cliente(api, base_url, "[QA] Cliente Concluir OS")
        order_id  = _criar_order(api, base_url, client_id)
        try:
            resp = api.patch(
                f"{base_url}/orders/{order_id}/status",
                json={"status": "done"},
            )
            assert resp.status_code == 200, (
                f"Esperado 200, obtido {resp.status_code}: {resp.text}"
            )
            body = resp.json()
            assert body.get("status") == "done", (
                f"Status esperado 'done', obtido: {body.get('status')}"
            )
        finally:
            api.delete(f"{base_url}/orders/{order_id}")
            api.delete(f"{base_url}/clients/{client_id}")

    def test_cancelar_order_muda_status_para_cancelled(self, api, base_url):
        """PATCH /orders/<id>/status para 'cancelled' deve retornar 200 e status='cancelled'."""
        client_id = _criar_cliente(api, base_url, "[QA] Cliente Cancelar OS")
        order_id  = _criar_order(api, base_url, client_id)
        try:
            resp = api.patch(
                f"{base_url}/orders/{order_id}/status",
                json={"status": "cancelled"},
            )
            assert resp.status_code == 200, (
                f"Esperado 200, obtido {resp.status_code}: {resp.text}"
            )
            body = resp.json()
            assert body.get("status") == "cancelled", (
                f"Status esperado 'cancelled', obtido: {body.get('status')}"
            )
        finally:
            api.delete(f"{base_url}/orders/{order_id}")
            api.delete(f"{base_url}/clients/{client_id}")

    def test_status_invalido_retorna_400(self, api, base_url):
        """PATCH /orders/<id>/status com status inválido deve retornar 400."""
        client_id = _criar_cliente(api, base_url, "[QA] Cliente Status Inválido")
        order_id  = _criar_order(api, base_url, client_id)
        try:
            resp = api.patch(
                f"{base_url}/orders/{order_id}/status",
                json={"status": "invalido"},
            )
            assert resp.status_code == 400, (
                f"Esperado 400, obtido {resp.status_code}: {resp.text}"
            )
        finally:
            api.delete(f"{base_url}/orders/{order_id}")
            api.delete(f"{base_url}/clients/{client_id}")


class TestDeletarOrder:

    def test_deletar_order_retorna_200(self, api, base_url):
        """DELETE /orders/<id> deve retornar 200."""
        client_id = _criar_cliente(api, base_url, "[QA] Cliente Deletar OS")
        order_id  = _criar_order(api, base_url, client_id)
        try:
            resp = api.delete(f"{base_url}/orders/{order_id}")
            assert resp.status_code == 200, (
                f"Esperado 200, obtido {resp.status_code}: {resp.text}"
            )
        finally:
            # Tenta deletar novamente caso o teste tenha falhado antes do delete
            api.delete(f"{base_url}/orders/{order_id}")
            api.delete(f"{base_url}/clients/{client_id}")

    def test_deletar_order_inexistente_retorna_404(self, api, base_url):
        """DELETE /orders/99999999 deve retornar 404."""
        resp = api.delete(f"{base_url}/orders/99999999")
        assert resp.status_code == 404, (
            f"Esperado 404, obtido {resp.status_code}: {resp.text}"
        )
