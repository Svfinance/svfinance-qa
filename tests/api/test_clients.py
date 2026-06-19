"""
Testes de API para o módulo de clientes.

Cenários cobertos:
  1. Criar cliente com dados mínimos válidos → 201
  2. Criar cliente sem nome → 400 (validação de campo obrigatório)
  3. Criar e deletar cliente sem vínculos → 200
  4. Deletar cliente com order vinculada → 400 + lista de vínculos (regressão bug FK)
  5. Deletar cliente inexistente → 404

Padrão de docstring: primeira linha = resultado esperado (alimenta o relatório automático).
"""


class TestCriarCliente:

    def test_criar_cliente_dados_validos(self, api, base_url):
        """POST /clients com dados mínimos válidos deve retornar 201 com id, name e codigo."""
        resp = api.post(f"{base_url}/clients", json={"name": "[QA] Cliente Criação"})
        assert resp.status_code == 201, (
            f"Esperado 201, obtido {resp.status_code}: {resp.text}"
        )
        body = resp.json()
        assert "id" in body, "Response deve conter 'id'"
        assert body.get("name") == "[QA] Cliente Criação", (
            f"Campo 'name' inesperado: {body.get('name')!r}"
        )
        assert "codigo" in body, "Response deve conter 'codigo' (sequencial)"

        # Limpa o cliente criado
        api.delete(f"{base_url}/clients/{body['id']}")

    def test_criar_cliente_sem_nome(self, api, base_url):
        """POST /clients sem campo name deve retornar 400 com mensagem de erro."""
        resp = api.post(f"{base_url}/clients", json={"email": "semname@qa.test"})
        assert resp.status_code == 400, (
            f"Esperado 400, obtido {resp.status_code}: {resp.text}"
        )
        body = resp.json()
        assert "msg" in body, "Response de erro deve conter campo 'msg'"


class TestDeletarCliente:

    def test_deletar_cliente_sem_vinculos(self, api, base_url):
        """DELETE /clients/<id> sem vínculos deve retornar 200 com ok=True."""
        resp_criar = api.post(f"{base_url}/clients", json={"name": "[QA] Cliente Para Deletar"})
        assert resp_criar.status_code == 201, (
            f"Falha ao criar cliente no setup: {resp_criar.text}"
        )
        client_id = resp_criar.json()["id"]

        resp_del = api.delete(f"{base_url}/clients/{client_id}")
        assert resp_del.status_code == 200, (
            f"Esperado 200, obtido {resp_del.status_code}: {resp_del.text}"
        )
        body = resp_del.json()
        assert body.get("ok") is True, f"Campo 'ok' esperado True: {body}"

    def test_deletar_cliente_com_order_vinculada(self, api, base_url):
        """DELETE /clients/<id> com order vinculada deve retornar 400 com lista de vínculos."""
        # Setup: cria cliente
        resp_cliente = api.post(f"{base_url}/clients", json={"name": "[QA] Cliente Com OS"})
        assert resp_cliente.status_code == 201, (
            f"Falha ao criar cliente no setup: {resp_cliente.text}"
        )
        client_id = resp_cliente.json()["id"]

        # Setup: cria order vinculada ao cliente
        resp_order = api.post(f"{base_url}/orders", json={
            "client_id": client_id,
            "items":     [],
            "notes":     "[QA] OS de regressão bug FK constraint",
        })
        assert resp_order.status_code == 201, (
            f"Falha ao criar order no setup: {resp_order.text}"
        )
        order_id = resp_order.json()["id"]

        try:
            # Tenta deletar o cliente — deve bloquear com 400
            resp_del = api.delete(f"{base_url}/clients/{client_id}")
            assert resp_del.status_code == 400, (
                f"Esperado 400 (cliente com OS vinculada), "
                f"obtido {resp_del.status_code}: {resp_del.text}"
            )
            body = resp_del.json()
            assert body.get("ok") is False, f"Campo 'ok' esperado False: {body}"
            assert "vinculos" in body, (
                f"Response deve conter lista 'vinculos', obtido: {body}"
            )
            # Pelo menos um vínculo deve mencionar pedido ou OS
            vinculos = body["vinculos"]
            assert any(
                "pedido" in v.lower() or "os" in v.lower()
                for v in vinculos
            ), f"Nenhum vínculo menciona pedido/OS: {vinculos}"
        finally:
            # Cleanup: deleta order primeiro, depois cliente
            api.delete(f"{base_url}/orders/{order_id}")
            api.delete(f"{base_url}/clients/{client_id}")

    def test_deletar_cliente_inexistente(self, api, base_url):
        """DELETE /clients/99999999 deve retornar 404."""
        resp = api.delete(f"{base_url}/clients/99999999")
        assert resp.status_code == 404, (
            f"Esperado 404, obtido {resp.status_code}: {resp.text}"
        )
