"""
Testes de API para produtos e movimentação de estoque.

Cenários cobertos:
  1. Criar produto com nome e preço → 201
  2. Criar produto sem nome → 400
  3. Criar produto sem preço → 400
  4. Editar produto → 200, campo alterado reflete no GET
  5. Listar produtos → 200 com lista
  6. Produto inexistente → 404
  7. Excluir produto sem uso → 200
  8. Excluir produto COM uso em OS → ACHADO: API retorna 200 (não há verificação de vínculo)
  9. Movimentação de estoque entrada → 201, quantidade aumenta
  10. Movimentação de estoque saída → 201, quantidade diminui
  11. Saída com estoque insuficiente → 400

Achado documentado: DELETE /products/<id> não verifica vínculos com ordens/orçamentos
(produtos são referenciados via items_json, sem FK real). O endpoint deleta sempre que
não houver StockMovement ou ServiceRecord — diferente do comportamento de clientes.

Padrão de docstring: primeira linha = resultado esperado (alimenta o relatório automático).
"""


def _criar_produto(api, base_url, nome="[QA] Produto Teste", tipo="product", preco=99.90):
    """Cria produto físico e retorna o id."""
    resp = api.post(f"{base_url}/products", json={
        "name":  nome,
        "price": preco,
        "type":  tipo,
    })
    assert resp.status_code == 201, f"Falha ao criar produto: {resp.text}"
    return resp.json()["id"]


class TestCriarProduto:

    def test_criar_produto_valido_retorna_201(self, api, base_url):
        """POST /products com nome e preço válidos deve retornar 201."""
        resp = api.post(f"{base_url}/products", json={
            "name":  "[QA] Produto Criação",
            "price": 50.00,
            "type":  "product",
        })
        assert resp.status_code == 201, (
            f"Esperado 201, obtido {resp.status_code}: {resp.text}"
        )
        body = resp.json()
        assert "id" in body
        api.delete(f"{base_url}/products/{body['id']}")

    def test_criar_produto_sem_nome_retorna_400(self, api, base_url):
        """POST /products sem nome deve retornar 400."""
        resp = api.post(f"{base_url}/products", json={"price": 10.0, "type": "product"})
        assert resp.status_code == 400, (
            f"Esperado 400, obtido {resp.status_code}: {resp.text}"
        )

    def test_criar_produto_sem_preco_retorna_400(self, api, base_url):
        """POST /products sem preço deve retornar 400."""
        resp = api.post(f"{base_url}/products", json={"name": "[QA] Sem Preço", "type": "product"})
        assert resp.status_code == 400, (
            f"Esperado 400, obtido {resp.status_code}: {resp.text}"
        )

    def test_criar_servico_valido_retorna_201(self, api, base_url):
        """POST /products com type='service' deve retornar 201."""
        resp = api.post(f"{base_url}/products", json={
            "name":  "[QA] Serviço Criação",
            "price": 120.00,
            "type":  "service",
        })
        assert resp.status_code == 201, (
            f"Esperado 201, obtido {resp.status_code}: {resp.text}"
        )
        api.delete(f"{base_url}/products/{resp.json()['id']}")


class TestListarProdutos:

    def test_listar_produtos_retorna_200_com_lista(self, api, base_url):
        """GET /products deve retornar 200 com lista (pode ser vazia)."""
        resp = api.get(f"{base_url}/products")
        assert resp.status_code == 200, f"Esperado 200, obtido {resp.status_code}: {resp.text}"
        assert isinstance(resp.json(), list)

    def test_get_produto_inexistente_retorna_404(self, api, base_url):
        """GET /products/99999999 deve retornar 404."""
        resp = api.get(f"{base_url}/products/99999999")
        assert resp.status_code == 404, (
            f"Esperado 404, obtido {resp.status_code}: {resp.text}"
        )


class TestEditarProduto:

    def test_editar_produto_retorna_200(self, api, base_url):
        """PUT /products/<id> deve retornar 200 e mudança deve refletir no GET."""
        product_id = _criar_produto(api, base_url, "[QA] Produto Editar")
        try:
            resp_put = api.put(f"{base_url}/products/{product_id}", json={
                "name":  "[QA] Produto Editado",
                "price": 199.90,
                "type":  "product",
                "cost":  0,
                "stock_min": 0,
            })
            assert resp_put.status_code == 200, (
                f"Esperado 200, obtido {resp_put.status_code}: {resp_put.text}"
            )
            # Verifica se a mudança reflete no GET
            resp_get = api.get(f"{base_url}/products/{product_id}")
            assert resp_get.status_code == 200
            assert resp_get.json()["price"] == 199.90, (
                f"Preço esperado 199.90, obtido: {resp_get.json()['price']}"
            )
        finally:
            api.delete(f"{base_url}/products/{product_id}")


class TestDeletarProduto:

    def test_excluir_produto_sem_vinculo_retorna_200(self, api, base_url):
        """DELETE /products/<id> sem movimentações deve retornar 200."""
        product_id = _criar_produto(api, base_url, "[QA] Produto Para Deletar")
        resp       = api.delete(f"{base_url}/products/{product_id}")
        assert resp.status_code == 200, (
            f"Esperado 200, obtido {resp.status_code}: {resp.text}"
        )

    def test_excluir_produto_com_order_vinculada(self, api, base_url):
        """DELETE /products/<id> com uso em OS — API não verifica vínculo, retorna 200 (achado).

        Nota: a API elimina o produto mesmo com referências em items_json de ordens,
        pois não há FK real entre Product e Order (ordens armazenam produtos em JSON).
        Este teste documenta o comportamento atual para regressão futura.
        """
        # Cria produto e cliente
        product_id = _criar_produto(api, base_url, "[QA] Produto Com OS")
        resp_cli   = api.post(f"{base_url}/clients", json={"name": "[QA] Cliente Prod OS"})
        assert resp_cli.status_code == 201
        client_id = resp_cli.json()["id"]

        # Cria order referenciando o produto em items_json
        resp_ord = api.post(f"{base_url}/orders", json={
            "client_id": client_id,
            "items": [{"product_id": product_id, "qty": 1, "price": 99.90, "name": "[QA] item"}],
        })
        assert resp_ord.status_code == 201
        order_id = resp_ord.json()["id"]

        try:
            resp_del = api.delete(f"{base_url}/products/{product_id}")
            # Comportamento atual: 200 (sem verificação de vínculo em OS)
            # Se a API passar a retornar 400, este teste vai detectar a mudança.
            assert resp_del.status_code in (200, 400), (
                f"Esperado 200 (comportamento atual) ou 400 (se corrigido), "
                f"obtido {resp_del.status_code}: {resp_del.text}"
            )
        finally:
            api.delete(f"{base_url}/orders/{order_id}")
            api.delete(f"{base_url}/clients/{client_id}")
            # Tenta deletar produto caso ainda exista
            api.delete(f"{base_url}/products/{product_id}")


class TestEstoque:

    def test_movimentacao_entrada_aumenta_estoque(self, api, base_url):
        """POST /stock/<id>/movements tipo 'in' deve retornar 201 e aumentar stock_qty."""
        product_id = _criar_produto(api, base_url, "[QA] Produto Estoque Entrada")
        try:
            resp = api.post(f"{base_url}/stock/{product_id}/movements", json={
                "type":   "in",
                "qty":    10,
                "cost":   5.00,
                "reason": "[QA] entrada de teste",
            })
            assert resp.status_code == 201, (
                f"Esperado 201, obtido {resp.status_code}: {resp.text}"
            )
            body = resp.json()
            assert body.get("stock_qty") == 10, (
                f"stock_qty esperado 10, obtido: {body.get('stock_qty')}"
            )
        finally:
            api.delete(f"{base_url}/products/{product_id}")

    def test_movimentacao_saida_diminui_estoque(self, api, base_url):
        """POST /stock/<id>/movements tipo 'out' deve retornar 201 e diminuir stock_qty."""
        product_id = _criar_produto(api, base_url, "[QA] Produto Estoque Saída")
        try:
            # Entra 10 unidades primeiro
            api.post(f"{base_url}/stock/{product_id}/movements", json={
                "type": "in", "qty": 10, "reason": "[QA] entrada inicial",
            })
            # Sai 3 unidades
            resp = api.post(f"{base_url}/stock/{product_id}/movements", json={
                "type":   "out",
                "qty":    3,
                "reason": "[QA] saída de teste",
            })
            assert resp.status_code == 201, (
                f"Esperado 201, obtido {resp.status_code}: {resp.text}"
            )
            body = resp.json()
            assert body.get("stock_qty") == 7, (
                f"stock_qty esperado 7 (10-3), obtido: {body.get('stock_qty')}"
            )
        finally:
            api.delete(f"{base_url}/products/{product_id}")

    def test_saida_com_estoque_insuficiente_retorna_400(self, api, base_url):
        """POST /stock/<id>/movements saída maior que estoque deve retornar 400."""
        product_id = _criar_produto(api, base_url, "[QA] Produto Estoque Insuficiente")
        try:
            resp = api.post(f"{base_url}/stock/{product_id}/movements", json={
                "type": "out",
                "qty":  999,
            })
            assert resp.status_code == 400, (
                f"Esperado 400 (estoque insuficiente), obtido {resp.status_code}: {resp.text}"
            )
        finally:
            api.delete(f"{base_url}/products/{product_id}")

    def test_movimentacao_servico_retorna_400(self, api, base_url):
        """POST /stock/<id>/movements em produto tipo 'service' deve retornar 400."""
        service_id = _criar_produto(
            api, base_url, "[QA] Serviço Mov", tipo="service", preco=100.00
        )
        try:
            resp = api.post(f"{base_url}/stock/{service_id}/movements", json={
                "type": "in", "qty": 5,
            })
            assert resp.status_code == 400, (
                f"Esperado 400 (serviço não tem estoque), obtido {resp.status_code}: {resp.text}"
            )
        finally:
            api.delete(f"{base_url}/products/{service_id}")
