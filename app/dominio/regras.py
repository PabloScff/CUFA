"""
Camada de DOMÍNIO: regra central da CUFA (RF01 + RF02 + RF03).
Não importa SQLAlchemy nem FastAPI: depende só do contrato `RepositorioAtendimento`.
Isso permite testar a regra de duplicidade sem banco (Pytest) e trocar o armazenamento sem tocar aqui.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol


class StatusAtendimento(str, Enum):
    REGISTRADA = "registrada"
    BLOQUEADA = "bloqueada_duplicidade"


@dataclass(frozen=True)
class DadosBeneficiaria:
    nome_completo: str
    cpf: str  # 11 dígitos
    telefone: str | None
    endereco: str
    quantidade_dependentes: int


@dataclass(frozen=True)
class Beneficiaria:
    id: int
    nome_completo: str
    cpf: str


@dataclass(frozen=True)
class Entrega:
    id: int
    beneficiaria_id: int
    ciclo_campanha: str
    data_entrega: datetime
    operador_nome: str
    status: str = "concluido"


@dataclass(frozen=True)
class OperadorRef:
    id: int
    nome: str


@dataclass(frozen=True)
class ResultadoAtendimento:
    status: StatusAtendimento
    nome_completo: str
    cpf: str
    ciclo_campanha: str
    data_entrega: datetime
    operador_nome: str
    cadastro_novo: bool

    @property
    def registrada(self) -> bool:
        return self.status is StatusAtendimento.REGISTRADA


class EntregaDuplicada(Exception):
    """A beneficiária já tem entrega no ciclo (violação da unicidade beneficiaria_id + ciclo_campanha)."""


class RepositorioAtendimento(Protocol):
    def buscar_beneficiaria_por_cpf(self, cpf: str) -> Beneficiaria | None: ...
    def criar_beneficiaria(self, dados: DadosBeneficiaria) -> Beneficiaria: ...
    def buscar_entrega(self, beneficiaria_id: int, ciclo: str) -> Entrega | None: ...
    def registrar_entrega(self, beneficiaria_id: int, ciclo: str, operador_id: int) -> Entrega: ...


def registrar_atendimento(
    repo: RepositorioAtendimento,
    dados: DadosBeneficiaria,
    ciclo: str,
    operador: OperadorRef,
) -> ResultadoAtendimento:
    """
    1) RF01: cadastra a beneficiária se o CPF ainda não existe (CPF é único; nunca cria cópia).
    2) RF02: se já há entrega no ciclo ativo, BLOQUEIA e informa quando foi a entrega anterior.
    3) RF03: caso contrário grava a entrega com data/hora e operador.
    A trava final é a restrição única do banco: duas voluntárias simultâneas não conseguem duplicar.
    """
    beneficiaria = repo.buscar_beneficiaria_por_cpf(dados.cpf)
    cadastro_novo = beneficiaria is None
    if cadastro_novo:
        beneficiaria = repo.criar_beneficiaria(dados)

    anterior = repo.buscar_entrega(beneficiaria.id, ciclo)
    if anterior is None:
        try:
            entrega = repo.registrar_entrega(beneficiaria.id, ciclo, operador.id)
            return ResultadoAtendimento(
                StatusAtendimento.REGISTRADA, beneficiaria.nome_completo, beneficiaria.cpf,
                ciclo, entrega.data_entrega, entrega.operador_nome, cadastro_novo,
            )
        except EntregaDuplicada:
            anterior = repo.buscar_entrega(beneficiaria.id, ciclo)

    return ResultadoAtendimento(
        StatusAtendimento.BLOQUEADA, beneficiaria.nome_completo, beneficiaria.cpf,
        ciclo, anterior.data_entrega, anterior.operador_nome, False,
    )
