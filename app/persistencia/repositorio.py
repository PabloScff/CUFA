"""Implementação SQL do contrato `RepositorioAtendimento` do domínio. Só SQLAlchemy ORM (sem SQL bruto) => RNF02."""
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..dominio.regras import Beneficiaria as BeneficiariaDTO
from ..dominio.regras import DadosBeneficiaria, Entrega as EntregaDTO, EntregaDuplicada
from .models import Beneficiaria, Entrega, Operador


def _benef(b: Beneficiaria) -> BeneficiariaDTO:
    return BeneficiariaDTO(id=b.id, nome_completo=b.nome_completo, cpf=b.cpf)


def _entrega(e: Entrega) -> EntregaDTO:
    return EntregaDTO(
        id=e.id, beneficiaria_id=e.beneficiaria_id, ciclo_campanha=e.ciclo_campanha,
        data_entrega=e.data_entrega, operador_nome=e.operador.nome, status=e.status,
    )


class RepositorioSQL:
    def __init__(self, db: Session):
        self.db = db

    def buscar_beneficiaria_por_cpf(self, cpf: str):
        b = self.db.scalar(select(Beneficiaria).where(Beneficiaria.cpf == cpf))
        return _benef(b) if b else None

    def criar_beneficiaria(self, dados: DadosBeneficiaria):
        b = Beneficiaria(
            nome_completo=dados.nome_completo, cpf=dados.cpf, telefone=dados.telefone,
            endereco=dados.endereco, quantidade_dependentes=dados.quantidade_dependentes,
        )
        self.db.add(b)
        try:
            self.db.commit()
        except IntegrityError:  # outra voluntária cadastrou o mesmo CPF no mesmo instante
            self.db.rollback()
            existente = self.buscar_beneficiaria_por_cpf(dados.cpf)
            if existente:
                return existente
            raise
        return _benef(b)

    def buscar_entrega(self, beneficiaria_id: int, ciclo: str):
        e = self.db.scalar(
            select(Entrega).where(Entrega.beneficiaria_id == beneficiaria_id, Entrega.ciclo_campanha == ciclo)
        )
        return _entrega(e) if e else None

    def registrar_entrega(self, beneficiaria_id: int, ciclo: str, operador_id: int):
        e = Entrega(beneficiaria_id=beneficiaria_id, ciclo_campanha=ciclo, operador_id=operador_id, status="concluido")
        self.db.add(e)
        try:
            self.db.commit()
        except IntegrityError as exc:  # restrição única beneficiaria_id + ciclo_campanha
            self.db.rollback()
            raise EntregaDuplicada() from exc
        return _entrega(e)


def buscar_operador_por_usuario(db: Session, usuario: str):
    return db.scalar(select(Operador).where(Operador.usuario == usuario))


def buscar_operador_por_id(db: Session, operador_id: int):
    return db.get(Operador, operador_id)
