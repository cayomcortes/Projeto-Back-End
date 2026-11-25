"""
config.py
Configuração da aplicação por variáveis de ambiente (princípio 12-factor).
"""
import os
from pathlib import Path

APP_VERSION = "1.1.0"


def _carregar_dotenv(caminho: Path) -> None:
    """Carrega pares CHAVE=VALOR de um arquivo .env, se ele existir."""
    if not caminho.is_file():
        return
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, _, valor = linha.partition("=")
        # setdefault: uma variável já definida no ambiente (ex.: Docker)
        # tem precedência sobre o valor do arquivo .env.
        os.environ.setdefault(chave.strip(), valor.strip().strip('"').strip("'"))


_carregar_dotenv(Path(__file__).resolve().parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./doacoes.db")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
