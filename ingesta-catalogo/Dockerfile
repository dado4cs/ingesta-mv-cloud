# ── Imagen base ─────────────────────────────────────────────────────────────
FROM python:3.12-slim

# Metadatos
LABEL maintainer="dado4cs"
LABEL description="Ingesta de datos: backend_catalogo (PostgreSQL) → CSV → S3"

# Variables de entorno por defecto (override en docker-compose o en la MV)
ENV PG_HOST=postgres \
    PG_PORT=5432 \
    PG_DB=cinema_catalog \
    PG_USER=postgres \
    PG_PASSWORD=changeme \
    S3_BUCKET=my-ingesta-bucket \
    S3_PREFIX=catalogo \
    AWS_REGION=us-east-1 \
    OUTPUT_DIR=/tmp/output/catalogo

WORKDIR /app

# Instalar dependencias del sistema necesarias para psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ingest.py .

CMD ["python", "ingest.py"]
