"""
crud.py
Camada de serviço: operações de persistência e regras de negócio.
As exceções de domínio aqui definidas são convertidas em respostas HTTP em main.py.
"""
from datetime import date, timedelta
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

import models
import schemas


# ---------------------------------------------------------------------------
# Exceções de domínio
# ---------------------------------------------------------------------------
class ItemNaoEncontradoError(Exception):
    """Item inexistente (HTTP 404)."""


class RegraDeNegocioError(Exception):
    """Violação de regra de negócio (HTTP 409)."""


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------
def _existe_duplicidade(
    db: Session,
    nome: str,
    categoria: models.CategoriaEnum,
    data_validade: Optional[date],
    ignorar_id: Optional[int] = None,
) -> bool:
    """
    RN05: verifica duplicidade por nome (case-insensitive), categoria e validade.
    A checagem em código é necessária porque, no SQLite, valores NULL não
    colidem em restrições UNIQUE.
    """
    consulta = db.query(models.ItemDoacao).filter(
        func.lower(models.ItemDoacao.nome) == nome.lower(),
        models.ItemDoacao.categoria == categoria,
        models.ItemDoacao.data_validade == data_validade,  # None vira IS NULL
    )
    if ignorar_id is not None:
        consulta = consulta.filter(models.ItemDoacao.id != ignorar_id)
    return db.query(consulta.exists()).scalar()


def _registrar_movimentacao(
    db: Session, item: models.ItemDoacao, tipo: models.TipoMovimentacao, quantidade: int
) -> None:
    """
    RN11 e RN12: grava o histórico da movimentação com o saldo resultante.
    Não faz commit: a atualização do saldo e o histórico são confirmados
    juntos, na mesma transação.
    """
    db.add(
        models.MovimentacaoEstoque(
            item_id=item.id,
            tipo=tipo,
            quantidade=quantidade,
            saldo_apos=item.quantidade,
        )
    )


# ---------------------------------------------------------------------------
# Operações CRUD
# ---------------------------------------------------------------------------
def criar_item(db: Session, dados: schemas.ItemCreate) -> models.ItemDoacao:
    if _existe_duplicidade(db, dados.nome, dados.categoria, dados.data_validade):
        raise RegraDeNegocioError(
            "Já existe um item com o mesmo nome, categoria e validade. "
            "Registre uma entrada no item existente."
        )
    item = models.ItemDoacao(**dados.model_dump())
    db.add(item)
    db.flush()  # gera o id do item antes de registrar a movimentação inicial
    if item.quantidade > 0:
        _registrar_movimentacao(db, item, models.TipoMovimentacao.ENTRADA, item.quantidade)
    db.commit()
    db.refresh(item)
    return item


def listar_itens(
    db: Session,
    categoria: Optional[models.CategoriaEnum] = None,
    apenas_estoque_baixo: bool = False,
    skip: int = 0,
    limit: int = 100,
) -> list[models.ItemDoacao]:
    consulta = db.query(models.ItemDoacao)
    if categoria is not None:
        consulta = consulta.filter(models.ItemDoacao.categoria == categoria)
    if apenas_estoque_baixo:  # RN08
        consulta = consulta.filter(
            models.ItemDoacao.quantidade <= models.ItemDoacao.estoque_minimo
        )
    return consulta.order_by(models.ItemDoacao.nome).offset(skip).limit(limit).all()


def obter_item(db: Session, item_id: int) -> models.ItemDoacao:
    item = db.get(models.ItemDoacao, item_id)
    if item is None:
        raise ItemNaoEncontradoError(f"Item {item_id} não encontrado.")
    return item


def atualizar_item(
    db: Session, item_id: int, dados: schemas.ItemUpdate
) -> models.ItemDoacao:
    item = obter_item(db, item_id)
    if _existe_duplicidade(
        db, dados.nome, dados.categoria, dados.data_validade, ignorar_id=item_id
    ):
        raise RegraDeNegocioError(
            "A atualização geraria duplicidade de nome, categoria e validade."
        )
    for campo, valor in dados.model_dump().items():
        setattr(item, campo, valor)
    db.commit()
    db.refresh(item)
    return item


def excluir_item(db: Session, item_id: int) -> None:
    item = obter_item(db, item_id)
    if item.quantidade != 0:  # RN09
        raise RegraDeNegocioError(
            "Somente itens com saldo zero podem ser excluídos. "
            "Registre a saída do saldo remanescente antes."
        )
    db.delete(item)  # o histórico do item é removido em cascata
    db.commit()


# ---------------------------------------------------------------------------
# Movimentações de estoque
# ---------------------------------------------------------------------------
def registrar_entrada(db: Session, item_id: int, quantidade: int) -> models.ItemDoacao:
    item = obter_item(db, item_id)
    if item.vencido:  # RN07
        raise RegraDeNegocioError("Não é possível registrar entrada em item vencido.")
    item.quantidade += quantidade
    _registrar_movimentacao(db, item, models.TipoMovimentacao.ENTRADA, quantidade)
    db.commit()
    db.refresh(item)
    return item


def registrar_saida(db: Session, item_id: int, quantidade: int) -> models.ItemDoacao:
    item = obter_item(db, item_id)
    if quantidade > item.quantidade:  # RN06
        raise RegraDeNegocioError(
            f"Saldo insuficiente: disponível {item.quantidade}, solicitado {quantidade}."
        )
    item.quantidade -= quantidade
    _registrar_movimentacao(db, item, models.TipoMovimentacao.SAIDA, quantidade)
    db.commit()
    db.refresh(item)
    return item


def listar_movimentacoes(db: Session, item_id: int) -> list[models.MovimentacaoEstoque]:
    """RF08: histórico cronológico de movimentações de um item."""
    obter_item(db, item_id)  # garante o 404 para item inexistente
    return (
        db.query(models.MovimentacaoEstoque)
        .filter(models.MovimentacaoEstoque.item_id == item_id)
        .order_by(models.MovimentacaoEstoque.id)
        .all()
    )


# ---------------------------------------------------------------------------
# Alertas
# ---------------------------------------------------------------------------
def listar_a_vencer(db: Session, dias: int = 7) -> list[models.ItemDoacao]:
    """RN10: itens com saldo que vencem em até `dias` dias (inclui já vencidos)."""
    limite = date.today() + timedelta(days=dias)
    return (
        db.query(models.ItemDoacao)
        .filter(
            models.ItemDoacao.data_validade.is_not(None),
            models.ItemDoacao.data_validade <= limite,
            models.ItemDoacao.quantidade > 0,
        )
        .order_by(models.ItemDoacao.data_validade)
        .all()
    )
