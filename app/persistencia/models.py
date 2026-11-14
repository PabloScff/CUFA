"""Entidades do PDF (slide 10): beneficiarias e entregas, mais operadores para autenticação (RNF01)."""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def agora_utc() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Operador(Base):
    __tablename__ = "operadores"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    nome: Mapped[str] = mapped_column(String(120))
    senha_hash: Mapped[str] = mapped_column(String(255))  # bcrypt via Passlib, nunca texto limpo
    perfil: Mapped[str] = mapped_column(String(20))  # "voluntario" | "coordenador"
    ativo: Mapped[bool] = mapped_column(default=True)


class Beneficiaria(Base):
    __tablename__ = "beneficiarias"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome_completo: Mapped[str] = mapped_column(String(120))
    cpf: Mapped[str] = mapped_column(String(11), unique=True, index=True)  # chave lógica de unicidade
    endereco: Mapped[str] = mapped_column(String(200))
    telefone: Mapped[str | None] = mapped_column(String(11), nullable=True)
    quantidade_dependentes: Mapped[int] = mapped_column(Integer)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora_utc)

    entregas: Mapped[list["Entrega"]] = relationship(back_populates="beneficiaria")  # 1 para N


class Entrega(Base):
    __tablename__ = "entregas"
    # Prevenção de duplicidade (slide 10): a mesma família não recebe duas vezes no mesmo ciclo.
    __table_args__ = (UniqueConstraint("beneficiaria_id", "ciclo_campanha", name="uq_entrega_beneficiaria_ciclo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    beneficiaria_id: Mapped[int] = mapped_column(ForeignKey("beneficiarias.id"))
    ciclo_campanha: Mapped[str] = mapped_column(String(40))  # ex.: "2026-FSET-01"
    data_entrega: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora_utc)
    operador_id: Mapped[int] = mapped_column(ForeignKey("operadores.id"))  # RF03: identificador do operador
    status: Mapped[str] = mapped_column(String(20), default="concluido")  # RF03

    beneficiaria: Mapped[Beneficiaria] = relationship(back_populates="entregas")
    operador: Mapped[Operador] = relationship()
