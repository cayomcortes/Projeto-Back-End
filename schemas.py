"""
schemas.py
Contratos de entrada e saída da API, validados com Pydantic v2.
"""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from models import CategoriaEnum, TipoMovimentacao


class ItemBase(BaseModel):
    """Campos descritivos comuns a cadastro, atualização e resposta."""
    nome: str = Field(..., min_length=1, max_length=120, examples=["Arroz tipo 1"])
    categoria: CategoriaEnum = Field(..., examples=["alimento"])
    descricao: Optional[str] = Field(None, max_length=255)
    unidade: str = Field(..., min_length=1, max_length=20, examples=["kg"])
    estoque_minimo: int = Field(0, ge=0, examples=[10])  # RN02
    data_validade: Optional[date] = Field(None, examples=["2027-12-31"])

    @field_validator("nome", "unidade")
    @classmethod
    def normalizar_texto(cls, valor: str) -> str:
        """RN01: remove espaços excedentes e rejeita texto vazio."""
        valor = " ".join(valor.split())
        if not valor:
            raise ValueError("O campo não pode ser vazio.")
        return valor

    @model_validator(mode="after")
    def exigir_validade_para_alimento(self):
        """RN03: alimentos exigem data de validade."""
        if self.categoria == CategoriaEnum.ALIMENTO and self.data_validade is None:
            raise ValueError("Itens da categoria 'alimento' exigem data_validade.")
        return self


class ItemCreate(ItemBase):
    """Corpo da requisição de cadastro."""
    quantidade: int = Field(0, ge=0, examples=[50])  # RN02

    @field_validator("data_validade")
    @classmethod
    def validade_nao_pode_estar_no_passado(cls, valor: Optional[date]) -> Optional[date]:
        """RN04: não se cadastra item já vencido."""
        if valor is not None and valor < date.today():
            raise ValueError("A data de validade não pode ser anterior à data atual.")
        return valor


class ItemUpdate(ItemBase):
    """
    Corpo da requisição de atualização (PUT).
    A quantidade NÃO é alterada aqui: deve ser movimentada por entrada/saída,
    garantindo rastreabilidade do estoque.
    """


class Movimentacao(BaseModel):
    """Corpo das requisições de entrada e saída de estoque."""
    quantidade: int = Field(..., gt=0, examples=[5])


class ItemResponse(ItemBase):
    """Representação do item retornada pela API."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    quantidade: int
    data_entrada: date
    estoque_baixo: bool
    vencido: bool


class MovimentacaoResponse(BaseModel):
    """Registro histórico de movimentação retornado pela API."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_id: int
    tipo: TipoMovimentacao
    quantidade: int
    saldo_apos: int
    data_hora: datetime
