"""Filtros de exibição usados nas telas (sem dependência de FastAPI)."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

_FUSO = ZoneInfo("America/Sao_Paulo")


def cpf_mascarado(cpf: str) -> str:
    """Privacidade: mostra só parte do CPF na tela de resultado (***.456.789-**)."""
    return f"***.{cpf[3:6]}.{cpf[6:9]}-**" if len(cpf) == 11 else "***"


def cpf_formatado(cpf: str) -> str:
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}" if len(cpf) == 11 else cpf


def data_local(valor: datetime) -> str:
    if valor.tzinfo is None:  # SQLite devolve datas sem fuso; gravamos em UTC
        valor = valor.replace(tzinfo=timezone.utc)
    return valor.astimezone(_FUSO).strftime("%d/%m/%Y às %H:%M")
