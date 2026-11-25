"""
seed.py
Popula o banco com dados sintéticos para demonstração e testes manuais.
Uso: python seed.py
"""
from datetime import date, timedelta

import crud
import models
import schemas
from database import Base, SessionLocal, engine


def main() -> None:
    Base.metadata.create_all(bind=engine)
    hoje = date.today()
    itens = [
        schemas.ItemCreate(nome="Arroz tipo 1", categoria="alimento", unidade="kg",
                           quantidade=40, estoque_minimo=15,
                           data_validade=hoje + timedelta(days=180)),
        schemas.ItemCreate(nome="Leite integral", categoria="alimento", unidade="un",
                           quantidade=12, estoque_minimo=10,
                           data_validade=hoje + timedelta(days=5)),
        schemas.ItemCreate(nome="Sabonete", categoria="higiene", unidade="un",
                           quantidade=3, estoque_minimo=8),
        schemas.ItemCreate(nome="Cobertor", categoria="vestuario", unidade="un",
                           quantidade=25, estoque_minimo=5),
    ]
    with SessionLocal() as db:
        if db.query(models.ItemDoacao).count() > 0:
            print("Banco já possui dados; nada foi inserido.")
            return
        for dados in itens:
            crud.criar_item(db, dados)
        print(f"{len(itens)} itens de exemplo inseridos.")


if __name__ == "__main__":
    main()
