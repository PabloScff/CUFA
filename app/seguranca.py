"""RNF01: hash bcrypt (Passlib), sessão JWT com expiração, logout e limite de tentativas (força bruta)."""
import time
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from .config import carregar

settings = carregar()
_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
_HASH_FALSO = _pwd.hash("senha-falsa-para-igualar-tempo")  # evita revelar se o usuário existe pelo tempo de resposta


def gerar_hash(senha: str) -> str:
    return _pwd.hash(senha)


def verificar_senha(senha: str, hash_salvo: str | None) -> bool:
    if hash_salvo is None:
        _pwd.verify(senha, _HASH_FALSO)
        return False
    return _pwd.verify(senha, hash_salvo)


# ---- JWT ----
_revogados: dict[str, float] = {}  # jti -> expiração (logout). Em produção com várias instâncias, use Redis/tabela.


def criar_token(operador_id: int, usuario: str, perfil: str) -> str:
    agora = datetime.now(timezone.utc)
    payload = {
        "sub": str(operador_id), "usr": usuario, "perfil": perfil, "jti": uuid.uuid4().hex,
        "iat": agora, "exp": agora + timedelta(minutes=settings.jwt_expira_minutos),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def ler_token(token: str) -> dict | None:
    try:
        dados = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
    if dados.get("jti") in _revogados:
        return None
    return dados


def revogar_token(token: str) -> None:
    dados = ler_token(token)
    if dados:
        agora = time.time()
        for jti in [j for j, exp in _revogados.items() if exp < agora]:  # limpeza dos já expirados
            _revogados.pop(jti, None)
        _revogados[dados["jti"]] = float(dados["exp"])


# ---- Limite de tentativas de login ----
class LimitadorLogin:
    def __init__(self, maximo: int, janela_s: int):
        self.maximo, self.janela_s = maximo, janela_s
        self._falhas: dict[str, list[float]] = {}

    def _recentes(self, chave: str) -> list[float]:
        corte = time.time() - self.janela_s
        lista = [t for t in self._falhas.get(chave, []) if t > corte]
        self._falhas[chave] = lista
        return lista

    def bloqueado(self, chave: str) -> bool:
        return len(self._recentes(chave)) >= self.maximo

    def registrar_falha(self, chave: str) -> None:
        self._recentes(chave).append(time.time())

    def limpar(self, chave: str) -> None:
        self._falhas.pop(chave, None)


limitador = LimitadorLogin(settings.login_max_tentativas, settings.login_janela_segundos)
