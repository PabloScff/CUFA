"""Creamshaper (MVP CUFA): monólito em camadas  apresentacao -> dominio <- persistencia.
Execução:  uvicorn app.main:app --reload"""
import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .apresentacao.deps import NaoAutenticado
from .apresentacao.rotas import router
from .persistencia.database import engine
from .persistencia.models import Base

log = logging.getLogger("creamshaper")
Base.metadata.create_all(engine)  # MVP: cria as tabelas. Evolução: migrações com Alembic.

app = FastAPI(title="Creamshaper – CUFA", docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "apresentacao" / "static")), name="static")
app.include_router(router)

_CSP = (
    "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; "
    "frame-ancestors 'none'; form-action 'self'; base-uri 'self'"
)


@app.middleware("http")
async def cabecalhos_de_seguranca(request: Request, call_next):
    resposta = await call_next(request)
    resposta.headers["Content-Security-Policy"] = _CSP
    resposta.headers["X-Content-Type-Options"] = "nosniff"
    resposta.headers["Referrer-Policy"] = "no-referrer"
    if not request.url.path.startswith("/static"):
        resposta.headers["Cache-Control"] = "no-store"  # telas com dados de beneficiárias não ficam em cache
    return resposta


@app.exception_handler(NaoAutenticado)
async def _nao_autenticado(request: Request, exc: NaoAutenticado):
    return RedirectResponse("/login", status_code=303)


@app.exception_handler(Exception)
async def _erro_generico(request: Request, exc: Exception):
    log.exception("Erro interno em %s", request.url.path)  # detalhe só no log interno (OWASP A09)
    return HTMLResponse("<h1>Algo deu errado.</h1><p>Tente novamente. Se continuar, avise a coordenação.</p>", status_code=500)

from sqlalchemy import text

@app.get("/saude", include_in_schema=False)
def saude():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok"}