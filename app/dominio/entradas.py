"""Validação estrita de entrada no servidor com Pydantic (RNF02). Mensagens em português para o voluntário."""
import re

from pydantic import BaseModel, field_validator

from .cpf import normalizar_cpf

_TAGS = re.compile(r"[<>]")  # rejeita tags HTML/JavaScript arbitrárias; a saída ainda é escapada pelo Jinja2


def _sem_tags(valor: str, campo: str) -> str:
    if _TAGS.search(valor):
        raise ValueError(f"{campo} contém caracteres não permitidos (< ou >).")
    return valor


class AtendimentoEntrada(BaseModel):
    nome_completo: str
    cpf: str
    telefone: str | None = None
    endereco: str
    quantidade_dependentes: int

    @field_validator("nome_completo", mode="before")
    @classmethod
    def _nome(cls, v):
        v = str(v or "").strip()
        if len(v) < 3 or len(v) > 120:
            raise ValueError("Informe o nome completo (3 a 120 letras).")
        return _sem_tags(v, "O nome")

    @field_validator("cpf", mode="before")
    @classmethod
    def _cpf(cls, v):
        return normalizar_cpf(str(v or ""))

    @field_validator("telefone", mode="before")
    @classmethod
    def _telefone(cls, v):
        v = str(v or "").strip()
        if not v:
            return None
        digitos = re.sub(r"\D", "", v)
        if len(digitos) not in (10, 11):
            raise ValueError("Telefone inválido. Use DDD + número, ex.: (11) 98765-4321.")
        return digitos

    @field_validator("endereco", mode="before")
    @classmethod
    def _endereco(cls, v):
        v = str(v or "").strip()
        if len(v) < 5 or len(v) > 200:
            raise ValueError("Informe o endereço (5 a 200 caracteres).")
        return _sem_tags(v, "O endereço")

    @field_validator("quantidade_dependentes", mode="before")
    @classmethod
    def _dependentes(cls, v):
        try:
            n = int(str(v).strip())
        except ValueError:
            raise ValueError("Informe a quantidade de dependentes (0 ou mais).") from None
        if not 0 <= n <= 30:
            raise ValueError("A quantidade de dependentes deve estar entre 0 e 30.")
        return n
