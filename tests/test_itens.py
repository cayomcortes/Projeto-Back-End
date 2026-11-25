"""Testes de cadastro, consulta, atualização e exclusão de itens."""
from datetime import date, timedelta


def _arroz(**alteracoes):
    corpo = {
        "nome": "Arroz tipo 1",
        "categoria": "alimento",
        "unidade": "kg",
        "quantidade": 20,
        "estoque_minimo": 10,
        "data_validade": (date.today() + timedelta(days=365)).isoformat(),
    }
    corpo.update(alteracoes)
    return corpo


def _sabonete(**alteracoes):
    corpo = {
        "nome": "Sabonete",
        "categoria": "higiene",
        "unidade": "un",
        "quantidade": 3,
        "estoque_minimo": 5,
    }
    corpo.update(alteracoes)
    return corpo


def test_cria_item_valido(client):  # CT01 | RF01
    r = client.post("/itens", json=_arroz())
    assert r.status_code == 201
    corpo = r.json()
    assert corpo["id"] >= 1
    assert corpo["quantidade"] == 20
    assert corpo["estoque_baixo"] is False
    assert corpo["vencido"] is False


def test_nome_normalizado(client):  # CT02 | RN01
    r = client.post("/itens", json=_arroz(nome="  Arroz    tipo 1  "))
    assert r.status_code == 201
    assert r.json()["nome"] == "Arroz tipo 1"


def test_rejeita_valores_negativos(client):  # CT03 | RN02
    assert client.post("/itens", json=_arroz(quantidade=-1)).status_code == 422
    assert client.post("/itens", json=_arroz(estoque_minimo=-1)).status_code == 422


def test_alimento_exige_validade(client):  # CT04 | RN03
    r = client.post("/itens", json=_arroz(data_validade=None))
    assert r.status_code == 422


def test_rejeita_validade_no_passado(client):  # CT05 | RN04
    ontem = (date.today() - timedelta(days=1)).isoformat()
    r = client.post("/itens", json=_arroz(data_validade=ontem))
    assert r.status_code == 422


def test_rejeita_duplicidade(client):  # CT06 | RN05
    assert client.post("/itens", json=_arroz()).status_code == 201
    assert client.post("/itens", json=_arroz()).status_code == 409
    # A comparação do nome ignora maiúsculas e minúsculas.
    assert client.post("/itens", json=_arroz(nome="ARROZ TIPO 1")).status_code == 409


def test_rejeita_duplicidade_sem_validade(client):  # CT07 | RN05 (caso NULL)
    assert client.post("/itens", json=_sabonete()).status_code == 201
    assert client.post("/itens", json=_sabonete()).status_code == 409


def test_lista_com_filtros(client):  # CT08 | RF02, RN08
    client.post("/itens", json=_arroz())
    client.post("/itens", json=_sabonete())

    todos = client.get("/itens").json()
    assert len(todos) == 2

    higiene = client.get("/itens", params={"categoria": "higiene"}).json()
    assert [i["nome"] for i in higiene] == ["Sabonete"]

    baixo = client.get("/itens", params={"apenas_estoque_baixo": True}).json()
    assert [i["nome"] for i in baixo] == ["Sabonete"]


def test_obtem_item_e_retorna_404(client):  # CT09 | RF03
    criado = client.post("/itens", json=_arroz()).json()
    assert client.get(f"/itens/{criado['id']}").status_code == 200
    assert client.get("/itens/999").status_code == 404


def test_atualiza_item_sem_alterar_saldo(client):  # CT10 | RF04, RN08
    criado = client.post("/itens", json=_sabonete()).json()
    assert criado["estoque_baixo"] is True

    novo = _sabonete(descricao="Barra 90 g", estoque_minimo=2)
    novo.pop("quantidade")  # o PUT não aceita alterar o saldo
    r = client.put(f"/itens/{criado['id']}", json=novo)
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["descricao"] == "Barra 90 g"
    assert corpo["quantidade"] == 3
    assert corpo["estoque_baixo"] is False


def test_atualizacao_nao_pode_duplicar(client):  # CT11 | RN05
    client.post("/itens", json=_sabonete())
    outro = client.post("/itens", json=_sabonete(nome="Shampoo")).json()
    novo = _sabonete(nome="Sabonete")
    novo.pop("quantidade")
    assert client.put(f"/itens/{outro['id']}", json=novo).status_code == 409


def test_exclusao_exige_saldo_zero(client):  # CT12 | RF05, RN09
    criado = client.post("/itens", json=_arroz()).json()
    item_id = criado["id"]
    assert client.delete(f"/itens/{item_id}").status_code == 409

    client.post(f"/itens/{item_id}/saida", json={"quantidade": 20})
    assert client.delete(f"/itens/{item_id}").status_code == 204
    assert client.get(f"/itens/{item_id}").status_code == 404
