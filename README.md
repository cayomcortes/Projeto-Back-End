# DoaCerto – API de Gestão de Estoque de Doações

Projeto de Extensão Back-End para controle de estoque de
doações em ONGs, com alertas de vencimento, estoque mínimo e histórico de movimentações.

Versão atual: **1.1.0** (ver `CHANGELOG.md`). A documentação técnica completa está em
`docs/DoaCerto_Documentacao_Tecnica.pdf`.

## Pré-requisitos

- Python 3.10 ou superior (testado com 3.12)
- Git (opcional) e Docker (opcional)

## Configuração do ambiente local

Windows (PowerShell):

    python -m venv .venv
    .venv\Scripts\Activate.ps1
    pip install -r requirements-dev.txt

Linux / macOS:

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements-dev.txt

Se o PowerShell bloquear a ativação: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.

## Variáveis de ambiente

Copie `.env.example` para `.env` (opcional; os padrões já funcionam).

| Variável | Padrão | Descrição |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./doacoes.db` | URL de conexão SQLAlchemy |
| `LOG_LEVEL` | `INFO` | DEBUG, INFO, WARNING ou ERROR |

## Comandos padrão

| Objetivo | Comando |
|---|---|
| Subir o serviço | `uvicorn main:app --reload` |
| Executar os testes | `pytest` |
| Testes com cobertura | `pytest --cov=. --cov-report=term-missing` |
| Dados de exemplo | `python seed.py` |
| Subir com Docker | `docker compose up --build` |

Documentação interativa (Swagger): http://127.0.0.1:8000/docs  
Verificação de integridade: `/healthz` e `/readyz`.

As tabelas são criadas automaticamente na inicialização (`create_all`); o projeto
ainda não usa ferramenta de migração (ver seção de evolução na documentação).

## Estrutura

    main.py          rotas, tratamento de erros e endpoints de integridade
    crud.py          regras de negócio e persistência
    models.py        modelos ORM (SQLAlchemy)
    schemas.py       contratos de entrada e saída (Pydantic)
    database.py      engine, sessão e base declarativa
    config.py        variáveis de ambiente
    seed.py          dados de exemplo
    tests/           testes automatizados
    docs/            documentação técnica e diagramas
