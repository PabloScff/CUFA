"""Testes de integração das 3 telas e da segurança (requer: pip install -r requirements.txt)."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.persistencia.database import SessionLocal
from app.persistencia.models import Operador
from app.seguranca import gerar_hash

SENHA = "senha-de-teste-123"
FORM = {"nome_completo": "Maria da Silva Santos", "cpf": "123.456.789-00", "telefone": "(11) 98765-4321",
        "endereco": "Rua das Comunidades, 142", "quantidade_dependentes": "3"}


@pytest.fixture(scope="module")
def client():
    with SessionLocal() as db:
        db.add(Operador(usuario="voluntario.cufa01", nome="Voluntário CUFA 01", perfil="voluntario", senha_hash=gerar_hash(SENHA)))
        db.commit()
    return TestClient(app, follow_redirects=False)


def _login(c):
    return c.post("/login", data={"usuario": "voluntario.cufa01", "senha": SENHA})


def test_tela_atendimento_exige_login(client):
    c = TestClient(app, follow_redirects=False)
    assert c.get("/operacao/atendimento").status_code == 303


def test_login_invalido_usa_mensagem_generica(client):
    r = client.post("/login", data={"usuario": "voluntario.cufa01", "senha": "errada"})
    assert r.status_code == 401 and "Usuário ou senha incorretos" in r.text


def test_fluxo_completo_sucesso_e_bloqueio(client):
    assert _login(client).status_code == 303
    assert "Ciclo 01/2026" in client.get("/operacao/atendimento").text
    ok = client.post("/operacao/atendimento", data=FORM)
    assert ok.status_code == 200 and "Entrega registrada" in ok.text
    bloqueio = client.post("/operacao/atendimento", data=FORM)
    assert bloqueio.status_code == 409 and "Entrega bloqueada" in bloqueio.text


def test_xss_e_escapado_e_rejeitado(client):
    _login(client)
    r = client.post("/operacao/atendimento", data={**FORM, "nome_completo": "<script>alert(1)</script>", "cpf": "98765432100"})
    assert r.status_code == 422 and "<script>alert(1)</script>" not in r.text


def test_logout_revoga_token(client):
    _login(client)
    client.post("/logout")
    client.cookies.clear()
    assert client.get("/operacao/atendimento").status_code == 303
