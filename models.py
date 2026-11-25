"""
models.py
Modelos ORM (camada de persistência) mapeados para tabelas do SQLite.
"""
import enum
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class CategoriaEnum(str, enum.Enum):
    """Categorias permitidas para os itens doados."""
    ALIMENTO = "alimento"
    HIGIENE = "higiene"
    VESTUARIO = "vestuario"
    LIMPEZA = "limpeza"
    OUTROS = "outros"


class TipoMovimentacao(str, enum.Enum):
    """Tipos de movimentação de estoque."""
    ENTRADA = "entrada"
    SAIDA = "saida"


class ItemDoacao(Base):
    __tablename__ = "itens_doacao"

    # Restrições em nível de tabela (RN02 e RN05).
    __table_args__ = (
        CheckConstraint("quantidade >= 0", name="ck_quantidade_nao_negativa"),
        CheckConstraint("estoque_minimo >= 0", name="ck_estoque_minimo_nao_negativo"),
        UniqueConstraint("nome", "categoria", "data_validade", name="uq_item_lote"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    categoria: Mapped[CategoriaEnum] = mapped_column(
        Enum(
            CategoriaEnum,
            native_enum=False,
            length=20,
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
    )
    descricao: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    unidade: Mapped[str] = mapped_column(String(20), nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estoque_minimo: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    data_validade: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    data_entrada: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)

    movimentacoes: Mapped[list["MovimentacaoEstoque"]] = relationship(
        back_populates="item",
        cascade="all, delete-orphan",
        order_by="MovimentacaoEstoque.id",
    )

    # Propriedades calculadas (não persistidas), expostas na API.
    @property
    def estoque_baixo(self) -> bool:
        """RN08: sinaliza saldo igual ou inferior ao mínimo definido."""
        return self.quantidade <= self.estoque_minimo

    @property
    def vencido(self) -> bool:
        """Indica se a validade do item já expirou."""
        return self.data_validade is not None and self.data_validade < date.today()


class MovimentacaoEstoque(Base):
    """Registro histórico de cada entrada ou saída de estoque (RN11 e RN12)."""
    __tablename__ = "movimentacoes_estoque"

    __table_args__ = (
        CheckConstraint("quantidade > 0", name="ck_mov_quantidade_positiva"),
        CheckConstraint("saldo_apos >= 0", name="ck_mov_saldo_nao_negativo"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(
        ForeignKey("itens_doacao.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tipo: Mapped[TipoMovimentacao] = mapped_column(
        Enum(
            TipoMovimentacao,
            native_enum=False,
            length=10,
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
    )
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False)
    saldo_apos: Mapped[int] = mapped_column(Integer, nullable=False)
    data_hora: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    item: Mapped["ItemDoacao"] = relationship(back_populates="movimentacoes")
