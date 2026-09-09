# ── Imagen base ─────────────────────────────────────────────────────────────
FROM python:3.12-slim

# Metadatos
LABEL maintainer="dado4cs"
LABEL description="Ingesta de datos: backend_comunity (MySQL) → CSV → S3"

# Variables de entorno por defecto (override en docker-compose o en la MV)
ENV MYSQL_HOST=mysql \
    MYSQL_PORT=3306 \
    MYSQL_DB=community_db \
    MYSQL_USER=community \
    MYSQL_PASSWORD=changeme \
    S3_BUCKET=my-ingesta-bucket \
    S3_PREFIX=comunity \
    AWS_REGION=us-east-1 \
    OUTPUT_DIR=/tmp/output/comunity

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ingest.py .

CMD ["python", "ingest.py"]
