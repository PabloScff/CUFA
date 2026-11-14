"""Regras de CPF. Validação de FORMATO sintático (RF01), sem dependência de tecnologia."""
import re

_PADRAO = re.compile(r"^\d{3}\.?\d{3}\.?\d{3}-?\d{2}$")


def normalizar_cpf(texto: str) -> str:
    """Aceita 123.456.789-00 ou 12345678900 e devolve só os 11 dígitos. Levanta ValueError se o formato for inválido."""
    texto = (texto or "").strip()
    if not _PADRAO.match(texto):
        raise ValueError("CPF inválido. Digite os 11 números do CPF.")
    return re.sub(r"\D", "", texto)
