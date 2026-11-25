# Changelog

Todas as mudanças relevantes deste projeto são registradas aqui.
O formato segue o [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o
projeto adota o [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [1.1.0] - 2026-11-24

### Adicionado
- Tabela `movimentacoes_estoque` e rota `GET /itens/{id}/movimentacoes` com o histórico de entradas e saídas (RN11, RN12).
- Endpoints de integridade `GET /healthz` (liveness) e `GET /readyz` (readiness).
- Configuração por variáveis de ambiente (`config.py`, `.env.example`).
- Testes automatizados com pytest (`tests/`) e script de dados de exemplo (`seed.py`).
- `Dockerfile`, `docker-compose.yml` e pipeline de CI no GitHub Actions.
- Documentação técnica completa em `docs/` (PDF) e README técnico.

### Alterado
- A conexão com o banco passou a ser lida de `DATABASE_URL`.
- O SQLite passou a ter chaves estrangeiras ativadas por conexão.
- Registros de log nas respostas 404 e 409.

## [1.0.0] - 2026-10-14

### Adicionado
- API REST de gestão de estoque de doações (FastAPI, SQLAlchemy, Pydantic e SQLite).
- Rotas de CRUD de itens, entrada e saída de estoque e alerta de vencimento.
- Regras de negócio RN01 a RN10.
