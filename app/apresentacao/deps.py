"""Autenticação por JWT (cookie HttpOnly) e autorização por perfil em cada rota protegida (RNF02)."""
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..persistencia.database import get_db
from ..persistencia.repositorio import buscar_operador_por_id
from ..seguranca import ler_token

COOKIE = "cufa_token"


class NaoAutenticado(Exception):
    pass


def operador_atual(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get(COOKIE)
    dados = ler_token(token) if token else None
    if not dados:
        raise NaoAutenticado()
    operador = buscar_operador_por_id(db, int(dados["sub"]))
    if not operador or not operador.ativo:
        raise NaoAutenticado()
    return operador


def exigir_perfil(*perfis: str):
    def verificador(operador=Depends(operador_atual)):
        if operador.perfil not in perfis:
            raise HTTPException(status_code=403, detail="Acesso negado.")
        return operador

    return verificador
