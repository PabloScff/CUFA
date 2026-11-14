"""Gera as capturas das 3 telas (slide 20) sem precisar subir o servidor: renderiza os templates reais
com dados fictícios e tira os prints com Playwright (viewport de celular).
Uso:  python scripts/gerar_capturas.py"""
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright

from app.apresentacao import formatos
from app.dominio.regras import OperadorRef, ResultadoAtendimento, StatusAtendimento

RAIZ = Path(__file__).resolve().parent.parent
APRES = RAIZ / "app" / "apresentacao"
SAIDA = RAIZ / "capturas"
SAIDA.mkdir(exist_ok=True)

env = Environment(loader=FileSystemLoader(APRES / "templates"), autoescape=select_autoescape(["html"]))
env.filters.update(cpf_mascarado=formatos.cpf_mascarado, cpf_formatado=formatos.cpf_formatado, data_local=formatos.data_local)

op = OperadorRef(1, "Voluntário CUFA 01")
operador = type("Op", (), {"usuario": "voluntario.cufa01", "nome": op.nome})()
agora = datetime(2026, 11, 20, 14, 32, tzinfo=timezone.utc)
base = {"ciclo_rotulo": "Ciclo 01/2026"}


def res(status, novo):
    return ResultadoAtendimento(status, "Maria da Silva Santos", "12345678900", "2026-FSET-01", agora, op.nome, novo)


TELAS = {
    "1_tela_login": ("login.html", {"erro": None, "usuario": ""}),
    "1b_tela_login_erro": ("login.html", {"erro": "Usuário ou senha incorretos. Confira os dados e tente de novo.", "usuario": "voluntario.cufa01"}),
    "2_tela_atendimento": ("atendimento.html", {"operador": operador, "valores": {}, "erros": {}}),
    "2b_tela_atendimento_erros": ("atendimento.html", {
        "operador": operador,
        "valores": {"nome_completo": "Maria da Silva Santos", "cpf": "123.456", "telefone": "", "endereco": "Rua das Comunidades, 142", "quantidade_dependentes": "3"},
        "erros": {"cpf": "CPF inválido. Digite os 11 números do CPF."}}),
    "3_tela_resultado_sucesso": ("resultado.html", {"r": res(StatusAtendimento.REGISTRADA, True), "operador": operador}),
    "3b_tela_resultado_bloqueio": ("resultado.html", {"r": res(StatusAtendimento.BLOQUEADA, False), "operador": operador}),
}

with sync_playwright() as p:
    nav = p.chromium.launch()
    pag = nav.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
    for nome, (modelo, ctx) in TELAS.items():
        html = env.get_template(modelo).render({**base, **ctx})
        html = html.replace('"/static/', f'"{(APRES / "static").as_uri()}/')
        arq = SAIDA / f"{nome}.html"
        arq.write_text(html, encoding="utf-8")
        pag.goto(arq.as_uri())
        pag.screenshot(path=str(SAIDA / f"{nome}.png"), full_page=True)
        arq.unlink()
        print("ok", nome)
    nav.close()
