"""
Camada de APRESENTAÇÃO: as 3 telas do protótipo (slides 19 e 20).
  Tela 1  GET/POST /login                  Autenticação
  Tela 2  GET/POST /operacao/atendimento   Cadastro + registro de entrega (RF01-RF03)
  Tela 3  (resposta do POST da Tela 2)     Resultado: sucesso ou bloqueio por duplicidade
RF04 (relatórios) está fora do protótipo, conforme o slide 19.
"""
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.orm import Session

from ..config import carregar
from ..dominio.entradas import AtendimentoEntrada
from ..dominio.regras import DadosBeneficiaria, OperadorRef, registrar_atendimento
from ..persistencia.database import get_db
from ..persistencia.repositorio import RepositorioSQL, buscar_operador_por_usuario
from ..seguranca import criar_token, limitador, revogar_token, verificar_senha
from . import formatos
from .deps import COOKIE, exigir_perfil

settings = carregar()
router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))  # autoescape ativo (defesa XSS)
templates.env.filters.update(
    cpf_mascarado=formatos.cpf_mascarado, cpf_formatado=formatos.cpf_formatado, data_local=formatos.data_local
)

PERFIS_OPERACAO = ("voluntario", "coordenador")


def _render(request: Request, nome: str, contexto: dict, status: int = 200):
    contexto = {"ciclo_rotulo": settings.ciclo_rotulo, **contexto}
    return templates.TemplateResponse(request, nome, contexto, status_code=status)


@router.get("/", include_in_schema=False)
def raiz():
    return RedirectResponse("/login", status_code=303)


# ------------------------------ Tela 1: Login ------------------------------
@router.get("/login")
def login_tela(request: Request):
    return _render(request, "login.html", {"erro": None, "usuario": ""})


@router.post("/login")
def login_enviar(
    request: Request,
    usuario: str = Form(""),
    senha: str = Form(""),
    db: Session = Depends(get_db),
):
    usuario = usuario.strip()[:60]
    ip = request.client.host if request.client else "?"
    chave = f"{ip}|{usuario.lower()}"

    if limitador.bloqueado(chave):
        minutos = settings.login_janela_segundos // 60
        msg = f"Muitas tentativas incorretas. Aguarde {minutos} minutos e tente de novo."
        return _render(request, "login.html", {"erro": msg, "usuario": usuario}, 429)

    operador = buscar_operador_por_usuario(db, usuario) if usuario else None
    hash_salvo = operador.senha_hash if operador and operador.ativo else None
    senha_ok = bool(senha) and len(senha) <= 128 and verificar_senha(senha, hash_salvo)

    if not (operador and operador.ativo and senha_ok):
        limitador.registrar_falha(chave)
        msg = "Usuário ou senha incorretos. Confira os dados e tente de novo."  # genérica: não revela qual campo errou
        return _render(request, "login.html", {"erro": msg, "usuario": usuario}, 401)

    limitador.limpar(chave)
    resposta = RedirectResponse("/operacao/atendimento", status_code=303)
    resposta.set_cookie(
        COOKIE, criar_token(operador.id, operador.usuario, operador.perfil),
        httponly=True, samesite="lax", secure=settings.cookie_secure,
        max_age=settings.jwt_expira_minutos * 60, path="/",
    )
    return resposta


@router.post("/logout")
def logout(request: Request):
    token = request.cookies.get(COOKIE)
    if token:
        revogar_token(token)
    resposta = RedirectResponse("/login", status_code=303)
    resposta.delete_cookie(COOKIE, path="/")
    return resposta


# ------------------------------ Tela 2: Atendimento ------------------------------
@router.get("/operacao/atendimento")
def atendimento_tela(request: Request, operador=Depends(exigir_perfil(*PERFIS_OPERACAO))):
    return _render(request, "atendimento.html", {"operador": operador, "valores": {}, "erros": {}})


@router.post("/operacao/atendimento")
def atendimento_enviar(
    request: Request,
    nome_completo: str = Form(""),
    cpf: str = Form(""),
    telefone: str = Form(""),
    endereco: str = Form(""),
    quantidade_dependentes: str = Form(""),
    operador=Depends(exigir_perfil(*PERFIS_OPERACAO)),
    db: Session = Depends(get_db),
):
    brutos = {
        "nome_completo": nome_completo, "cpf": cpf, "telefone": telefone,
        "endereco": endereco, "quantidade_dependentes": quantidade_dependentes,
    }
    try:
        entrada = AtendimentoEntrada(**brutos)
    except ValidationError as exc:
        erros: dict[str, str] = {}
        for e in exc.errors():
            campo = str(e["loc"][0]) if e["loc"] else "_"
            erros.setdefault(campo, e["msg"].removeprefix("Value error, "))
        return _render(request, "atendimento.html", {"operador": operador, "valores": brutos, "erros": erros}, 422)

    resultado = registrar_atendimento(
        RepositorioSQL(db),
        DadosBeneficiaria(**entrada.model_dump()),
        ciclo=settings.ciclo_id,
        operador=OperadorRef(id=operador.id, nome=operador.nome),
    )
    # Tela 3: 200 quando a entrega foi gravada, 409 quando bloqueada por duplicidade no ciclo.
    return _render(request, "resultado.html", {"r": resultado, "operador": operador}, 200 if resultado.registrada else 409)
