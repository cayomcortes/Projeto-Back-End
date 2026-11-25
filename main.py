"""
main.py
Camada de apresentação: definição da aplicação FastAPI, rotas e tratamento de erros.
"""
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

import crud
import models
import schemas
from config import APP_VERSION, LOG_LEVEL
from database import Base, engine, get_db

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("doacerto")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Cria as tabelas no SQLite (se inexistentes) ao iniciar a aplicação."""
    Base.metadata.create_all(bind=engine)
    logger.info("DoaCerto %s iniciado.", APP_VERSION)
    yield


app = FastAPI(
    title="DoaCerto – API de Gestão de Estoque de Doações",
    description=(
        "Projeto de Extensão Universitária: serviço Back-End para controle de "
        "estoque de doações em ONGs, com alertas de vencimento, estoque mínimo "
        "e histórico de movimentações."
    ),
    version=APP_VERSION,
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Tratamento centralizado das exceções de domínio
# ---------------------------------------------------------------------------
@app.exception_handler(crud.ItemNaoEncontradoError)
async def tratar_nao_encontrado(request: Request, exc: crud.ItemNaoEncontradoError):
    logger.info("404 %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})


@app.exception_handler(crud.RegraDeNegocioError)
async def tratar_regra_negocio(request: Request, exc: crud.RegraDeNegocioError):
    logger.warning("409 %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})


# ---------------------------------------------------------------------------
# Rotas de CRUD
# ---------------------------------------------------------------------------
@app.post(
    "/itens",
    response_model=schemas.ItemResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Itens"],
    summary="Cadastra um novo item de doação",
)
def criar_item(dados: schemas.ItemCreate, db: Session = Depends(get_db)):
    return crud.criar_item(db, dados)


@app.get(
    "/itens",
    response_model=list[schemas.ItemResponse],
    tags=["Itens"],
    summary="Lista itens com filtros opcionais",
)
def listar_itens(
    categoria: Optional[models.CategoriaEnum] = None,
    apenas_estoque_baixo: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return crud.listar_itens(db, categoria, apenas_estoque_baixo, skip, limit)


@app.get(
    "/itens/{item_id}",
    response_model=schemas.ItemResponse,
    tags=["Itens"],
    summary="Consulta um item pelo identificador",
)
def obter_item(item_id: int, db: Session = Depends(get_db)):
    return crud.obter_item(db, item_id)


@app.put(
    "/itens/{item_id}",
    response_model=schemas.ItemResponse,
    tags=["Itens"],
    summary="Atualiza os dados descritivos de um item",
)
def atualizar_item(item_id: int, dados: schemas.ItemUpdate, db: Session = Depends(get_db)):
    return crud.atualizar_item(db, item_id, dados)


@app.delete(
    "/itens/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    tags=["Itens"],
    summary="Exclui um item com saldo zero",
)
def excluir_item(item_id: int, db: Session = Depends(get_db)):
    crud.excluir_item(db, item_id)


# ---------------------------------------------------------------------------
# Rotas de regras de negócio
# ---------------------------------------------------------------------------
@app.post(
    "/itens/{item_id}/entrada",
    response_model=schemas.ItemResponse,
    tags=["Movimentações"],
    summary="Registra entrada (recebimento de doação)",
)
def entrada(item_id: int, mov: schemas.Movimentacao, db: Session = Depends(get_db)):
    return crud.registrar_entrada(db, item_id, mov.quantidade)


@app.post(
    "/itens/{item_id}/saida",
    response_model=schemas.ItemResponse,
    tags=["Movimentações"],
    summary="Registra saída (distribuição ou descarte)",
)
def saida(item_id: int, mov: schemas.Movimentacao, db: Session = Depends(get_db)):
    return crud.registrar_saida(db, item_id, mov.quantidade)


@app.get(
    "/itens/{item_id}/movimentacoes",
    response_model=list[schemas.MovimentacaoResponse],
    tags=["Movimentações"],
    summary="Consulta o histórico de movimentações de um item",
)
def historico(item_id: int, db: Session = Depends(get_db)):
    return crud.listar_movimentacoes(db, item_id)


@app.get(
    "/alertas/vencimento",
    response_model=list[schemas.ItemResponse],
    tags=["Alertas"],
    summary="Lista itens vencidos ou próximos do vencimento",
)
def alertas_vencimento(
    dias: int = Query(7, ge=0, le=365, description="Janela de dias a partir de hoje"),
    db: Session = Depends(get_db),
):
    return crud.listar_a_vencer(db, dias)


# ---------------------------------------------------------------------------
# Operação: verificação de integridade
# ---------------------------------------------------------------------------
@app.get("/healthz", tags=["Operação"], summary="Liveness: o processo está ativo")
def healthz():
    return {"status": "ok", "versao": APP_VERSION}


@app.get("/readyz", tags=["Operação"], summary="Readiness: o banco está acessível")
def readyz(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception:  # qualquer falha de conexão indica indisponibilidade
        logger.exception("Falha na verificação de prontidão do banco de dados.")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "indisponivel"},
        )
    return {"status": "pronto"}
