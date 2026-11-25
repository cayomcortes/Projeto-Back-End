"""Testes dos endpoints de verificação de integridade."""
from config import APP_VERSION


def test_healthz(client):  # CT21 | RF10
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "versao": APP_VERSION}


def test_readyz(client):  # CT22 | RF11
    r = client.get("/readyz")
    assert r.status_code == 200
    assert r.json() == {"status": "pronto"}
