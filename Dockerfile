FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./

# Usuário sem privilégios e diretório persistente para o arquivo SQLite.
RUN useradd --create-home app \
    && mkdir -p /data \
    && chown app:app /data
USER app

ENV DATABASE_URL=sqlite:////data/doacoes.db
VOLUME ["/data"]
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
  CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/healthz')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
