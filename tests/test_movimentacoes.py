"""Testes de entradas, saídas, histórico e alertas de vencimento."""
from datetime import date, timedelta

import models


def _item(nome="Arroz tipo 1", quantidade=20, dias_validade=365):
    return {
        "nome": nome,
        "categoria": "alimento",
        "unidade": "kg",
        "quantidade": quantidade,
        "estoque_minimo": 10,
        "data_validade": (date.today() + timedelta(days=dias_validade)).isoformat(),
    }


def test_entrada_soma_saldo(client):  # CT13 | RF06
    item = client.post("/itens", json=_item()).json()
    r = client.post(f"/itens/{item['id']}/entrada", json={"quantidade": 15})
    assert r.status_code == 200
    assert r.json()["quantidade"] == 35


def test_rejeita_quantidade_invalida(client):  # CT14 | RF06, RF07
    item = client.post("/itens", json=_item()).json()
    for rota in ("entrada", "saida"):
        r = client.post(f"/itens/{item['id']}/{rota}", json={"quantidade": 0})
        assert r.status_code == 422


def test_saida_subtrai_saldo(client):  # CT15 | RF07
    item = client.post("/itens", json=_item()).json()
    r = client.post(f"/itens/{item['id']}/saida", json={"quantidade": 5})
    assert r.status_code == 200
    assert r.json()["quantidade"] == 15


def test_saida_maior_que_saldo_e_recusada(client):  # CT16 | RN06
    item = client.post("/itens", json=_item()).json()
    r = client.post(f"/itens/{item['id']}/saida", json={"quantidade": 100})
    assert r.status_code == 409
    # O saldo permanece intacto após a recusa.
    assert client.get(f"/itens/{item['id']}").json()["quantidade"] == 20


def test_entrada_em_item_vencido_e_recusada(client, db_session):  # CT17 | RN07
    vencido = models.ItemDoacao(
        nome="Leite",
        categoria=models.CategoriaEnum.ALIMENTO,
        unidade="un",
        quantidade=5,
        estoque_minimo=0,
        data_validade=date.today() - timedelta(days=1),
    )
    db_session.add(vencido)
    db_session.commit()
    r = client.post(f"/itens/{vencido.id}/entrada", json={"quantidade": 1})
    assert r.status_code == 409


def test_historico_registra_movimentacoes(client):  # CT18 | RF08, RN11, RN12
    item = client.post("/itens", json=_item()).json()
    item_id = item["id"]
    client.post(f"/itens/{item_id}/entrada", json={"quantidade": 15})
    client.post(f"/itens/{item_id}/saida", json={"quantidade": 5})

    r = client.get(f"/itens/{item_id}/movimentacoes")
    assert r.status_code == 200
    historico = r.json()
    assert [m["tipo"] for m in historico] == ["entrada", "entrada", "saida"]
    assert [m["saldo_apos"] for m in historico] == [20, 35, 30]


def test_historico_de_item_inexistente(client):  # CT19 | RF08
    assert client.get("/itens/999/movimentacoes").status_code == 404


def test_alertas_de_vencimento(client, db_session):  # CT20 | RF09, RN10
    client.post("/itens", json=_item(nome="Iogurte", quantidade=10, dias_validade=3))
    client.post("/itens", json=_item(nome="Feijão", quantidade=10, dias_validade=100))
    client.post("/itens", json=_item(nome="Queijo", quantidade=0, dias_validade=2))
    db_session.add(
        models.ItemDoacao(
            nome="Leite vencido",
            categoria=models.CategoriaEnum.ALIMENTO,
            unidade="un",
            quantidade=4,
            estoque_minimo=0,
            data_validade=date.today() - timedelta(days=2),
        )
    )
    db_session.commit()

    r = client.get("/alertas/vencimento", params={"dias": 7})
    assert r.status_code == 200
    # Inclui o já vencido e o que vence em 3 dias; exclui o de saldo zero
    # (Queijo) e o de validade distante (Feijão). Ordem: por validade.
    assert [i["nome"] for i in r.json()] == ["Leite vencido", "Iogurte"]
