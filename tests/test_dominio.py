"""Testes da regra crítica (RF01-RF03): bloqueio de entrega duplicada no ciclo vigente. Rodam sem banco."""
from datetime import datetime, timezone
from itertools import count

import pytest

from app.dominio.cpf import normalizar_cpf
from app.dominio.regras import (
    Beneficiaria, DadosBeneficiaria, Entrega, EntregaDuplicada, OperadorRef, StatusAtendimento, registrar_atendimento,
)

OP = OperadorRef(1, "Voluntário CUFA 01")
DADOS = DadosBeneficiaria("Maria da Silva Santos", "12345678900", "11987654321", "Rua das Comunidades, 142", 3)
CICLO = "2026-FSET-01"


class RepoFalso:
    def __init__(self):
        self.beneficiarias, self.entregas, self._ids = {}, {}, count(1)

    def buscar_beneficiaria_por_cpf(self, cpf):
        return self.beneficiarias.get(cpf)

    def criar_beneficiaria(self, d):
        b = Beneficiaria(next(self._ids), d.nome_completo, d.cpf)
        self.beneficiarias[d.cpf] = b
        return b

    def buscar_entrega(self, bid, ciclo):
        return self.entregas.get((bid, ciclo))

    def registrar_entrega(self, bid, ciclo, operador_id):
        if (bid, ciclo) in self.entregas:
            raise EntregaDuplicada()
        e = Entrega(next(self._ids), bid, ciclo, datetime.now(timezone.utc), OP.nome)
        self.entregas[(bid, ciclo)] = e
        return e


def test_primeira_entrega_cadastra_e_registra():
    repo = RepoFalso()
    r = registrar_atendimento(repo, DADOS, CICLO, OP)
    assert r.status is StatusAtendimento.REGISTRADA and r.cadastro_novo
    assert len(repo.beneficiarias) == 1 and len(repo.entregas) == 1


def test_segunda_tentativa_no_mesmo_ciclo_e_bloqueada_sem_duplicar():
    repo = RepoFalso()
    registrar_atendimento(repo, DADOS, CICLO, OP)
    r = registrar_atendimento(repo, DADOS, CICLO, OP)
    assert r.status is StatusAtendimento.BLOQUEADA and not r.cadastro_novo
    assert len(repo.beneficiarias) == 1 and len(repo.entregas) == 1  # nada duplicado no banco


def test_mesma_familia_pode_receber_em_outro_ciclo():
    repo = RepoFalso()
    registrar_atendimento(repo, DADOS, CICLO, OP)
    r = registrar_atendimento(repo, DADOS, "2026-FSET-02", OP)
    assert r.registrada and not r.cadastro_novo and len(repo.beneficiarias) == 1


def test_corrida_entre_voluntarias_vira_bloqueio():
    """A outra voluntária grava entre a checagem e a gravação: a restrição única derruba a 2ª entrega."""
    class RepoCorrida(RepoFalso):
        def buscar_entrega(self, bid, ciclo):
            return super().buscar_entrega(bid, ciclo) if getattr(self, "_gravou", False) else None

        def registrar_entrega(self, bid, ciclo, operador_id):
            super().registrar_entrega(bid, ciclo, operador_id)  # "a outra" voluntária
            self._gravou = True
            raise EntregaDuplicada()

    r = registrar_atendimento(RepoCorrida(), DADOS, CICLO, OP)
    assert r.status is StatusAtendimento.BLOQUEADA


@pytest.mark.parametrize("texto", ["123.456.789-00", "12345678900", " 123.456.789-00 "])
def test_cpf_aceita_formatos_validos(texto):
    assert normalizar_cpf(texto) == "12345678900"


@pytest.mark.parametrize("texto", ["", "123", "abc.def.ghi-jk", "123.456.789-0", "123456789000"])
def test_cpf_rejeita_formato_invalido(texto):
    with pytest.raises(ValueError):
        normalizar_cpf(texto)
