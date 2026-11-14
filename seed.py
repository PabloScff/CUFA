"""Cria as tabelas e dois operadores de teste (dados fictícios do roteiro de validação, slide 22).
Uso:  SEED_SENHA='uma-senha-forte' python seed.py     (sem SEED_SENHA, gera uma senha aleatória e imprime)"""
import os
import secrets

from app.persistencia.database import SessionLocal, engine
from app.persistencia.models import Base, Operador
from app.persistencia.repositorio import buscar_operador_por_usuario
from app.seguranca import gerar_hash

Base.metadata.create_all(engine)
senha = os.getenv("SEED_SENHA") or secrets.token_urlsafe(9)

with SessionLocal() as db:
    for usuario, nome, perfil in [
        ("voluntario.cufa01", "Voluntário CUFA 01", "voluntario"),
        ("coordenador.cufa01", "Coordenador CUFA 01", "coordenador"),
    ]:
        if buscar_operador_por_usuario(db, usuario) is None:
            db.add(Operador(usuario=usuario, nome=nome, perfil=perfil, senha_hash=gerar_hash(senha)))
            print(f"criado: {usuario} ({perfil})")
    db.commit()
print(f"Senha dos usuários criados agora: {senha}")
