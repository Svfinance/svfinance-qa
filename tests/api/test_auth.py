"""
Testes de API para autenticação.

Cenários cobertos:
  1. Login válido → 200 + token + company_id + role
  2. Login com senha errada → 401
  3. Login com email não verificado → 403 + email_unverified: true
  4. Acesso a rota protegida sem token → 401
  5. Acesso com token malformado → 422 (Flask-JWT-Extended retorna 422 para token inválido)
  6. GET /me com token válido → 200 com dados do usuário

Sem rota de logout: o logoutUser() do frontend apenas limpa o localStorage
— não existe rota POST /logout na API (stateless com JWT).

Padrão de docstring: primeira linha = resultado esperado (alimenta o relatório automático).
"""

import requests as _requests


class TestLogin:

    def test_login_valido_retorna_token_e_dados(self, qa_company, base_url):
        """POST /login com credenciais válidas deve retornar 200 com token, company_id e role."""
        resp = _requests.post(
            f"{base_url}/login",
            json={"email": qa_company["email"], "password": qa_company["password"]},
            timeout=15,
        )
        assert resp.status_code == 200, f"Esperado 200, obtido {resp.status_code}: {resp.text}"
        body = resp.json()
        assert "token"      in body, "Response deve conter 'token'"
        assert "company_id" in body, "Response deve conter 'company_id'"
        assert "role"       in body, "Response deve conter 'role'"
        assert body["company_id"] == qa_company["company_id"]
        assert body["role"]       == "admin"

    def test_login_senha_errada_retorna_401(self, base_url, qa_company):
        """POST /login com senha incorreta deve retornar 401."""
        resp = _requests.post(
            f"{base_url}/login",
            json={"email": qa_company["email"], "password": "senhaerrada123"},
            timeout=15,
        )
        assert resp.status_code == 401, f"Esperado 401, obtido {resp.status_code}: {resp.text}"
        assert "msg" in resp.json()

    def test_login_email_nao_verificado_retorna_403(self, base_url):
        """POST /login com email não verificado deve retornar 403 com email_unverified: true."""
        # Cria uma empresa via /register — email_verified nasce False
        import time
        ts    = str(int(time.time()))
        email = f"qa+unverified{ts}@svfinance.com.br"
        resp_reg = _requests.post(
            f"{base_url}/register",
            json={
                "email":        email,
                "password":     "Sv2026QaTeste!",
                "name":         "[QA] Usuário Não Verificado",
                "company_name": f"[QA] Empresa Não Verificada {ts}",
                "nicho":        "generic",
            },
            timeout=15,
        )
        # Se o registro falhar por limite ou outro motivo, pula o teste
        if resp_reg.status_code != 201:
            import pytest
            pytest.skip(f"Registro de usuário não verificado falhou: {resp_reg.text}")

        resp = _requests.post(
            f"{base_url}/login",
            json={"email": email, "password": "Sv2026QaTeste!"},
            timeout=15,
        )
        assert resp.status_code == 403, (
            f"Esperado 403 (email não verificado), obtido {resp.status_code}: {resp.text}"
        )
        body = resp.json()
        assert body.get("email_unverified") is True, (
            f"Response deve conter 'email_unverified: true', obtido: {body}"
        )

    def test_login_campos_ausentes_retorna_400(self, base_url):
        """POST /login sem email e senha deve retornar 400."""
        resp = _requests.post(f"{base_url}/login", json={}, timeout=15)
        assert resp.status_code == 400, f"Esperado 400, obtido {resp.status_code}: {resp.text}"


class TestRotasProtegidas:

    def test_acesso_sem_token_retorna_401(self, base_url):
        """GET /me sem Authorization header deve retornar 401."""
        resp = _requests.get(f"{base_url}/me", timeout=15)
        assert resp.status_code == 401, f"Esperado 401, obtido {resp.status_code}: {resp.text}"

    def test_acesso_token_malformado_retorna_422(self, base_url):
        """GET /me com token JWT malformado deve retornar 422 (Flask-JWT-Extended)."""
        resp = _requests.get(
            f"{base_url}/me",
            headers={"Authorization": "Bearer isso.nao.e.um.jwt"},
            timeout=15,
        )
        # Flask-JWT-Extended retorna 422 para tokens inválidos (não 401)
        assert resp.status_code == 422, (
            f"Esperado 422 (token inválido), obtido {resp.status_code}: {resp.text}"
        )

    def test_get_me_com_token_valido_retorna_dados(self, api, base_url, qa_company):
        """GET /me com token válido deve retornar 200 com id, email e role."""
        resp = api.get(f"{base_url}/me", timeout=15)
        assert resp.status_code == 200, f"Esperado 200, obtido {resp.status_code}: {resp.text}"
        body = resp.json()
        assert body.get("id")    == qa_company["user_id"]
        assert body.get("email") == qa_company["email"]
        assert body.get("role")  == "admin"
