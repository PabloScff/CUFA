"""Configuração lida de variáveis de ambiente (.env). Segredos nunca ficam no código (RNF01/RNF03)."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    jwt_secret: str
    jwt_expira_minutos: int
    database_url: str
    ciclo_id: str
    ciclo_rotulo: str
    cookie_secure: bool
    login_max_tentativas: int
    login_janela_segundos: int


def carregar() -> Settings:
    segredo = os.getenv("JWT_SECRET", "")
    if len(segredo) < 32:
        raise RuntimeError("Defina JWT_SECRET no .env com pelo menos 32 caracteres (veja .env.example).")
    return Settings(
        jwt_secret=segredo,
        jwt_expira_minutos=int(os.getenv("JWT_EXPIRA_MINUTOS", "480")),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./creamshaper.db"),
        ciclo_id=os.getenv("CICLO_ID", "2026-FSET-01"),
        ciclo_rotulo=os.getenv("CICLO_ROTULO", "Ciclo 01/2026"),
        cookie_secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
        login_max_tentativas=int(os.getenv("LOGIN_MAX_TENTATIVAS", "5")),
        login_janela_segundos=int(os.getenv("LOGIN_JANELA_SEGUNDOS", "300")),
    )
