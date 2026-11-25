"""
database.py
Infraestrutura de acesso a dados: engine, fábrica de sessões e base declarativa.
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import DATABASE_URL

_eh_sqlite = DATABASE_URL.startswith("sqlite")

# check_same_thread=False é necessário no SQLite, pois o FastAPI pode
# atender requisições em threads distintas da que criou a conexão.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if _eh_sqlite else {},
)


@event.listens_for(engine, "connect")
def _ativar_chaves_estrangeiras(dbapi_connection, _registro):
    """O SQLite não impõe chaves estrangeiras por padrão; ativa por conexão."""
    if _eh_sqlite:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Classe base para todos os modelos ORM."""


def get_db():
    """
    Dependência do FastAPI: fornece uma sessão por requisição
    e garante seu fechamento ao final do ciclo.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
