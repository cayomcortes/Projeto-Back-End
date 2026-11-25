"""
Fixtures compartilhadas: banco SQLite em memória isolado por teste
e cliente HTTP com a dependência get_db substituída.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app


@pytest.fixture()
def db_session():
    # StaticPool mantém uma única conexão, necessária para o banco em memória
    # ser visto por todas as threads do TestClient.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    sessao = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    try:
        yield sessao
    finally:
        sessao.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session):
    def _db_de_teste():
        yield db_session

    app.dependency_overrides[get_db] = _db_de_teste
    # Sem "with": o lifespan não roda, evitando criar o banco real em disco.
    yield TestClient(app)
    app.dependency_overrides.clear()
