# ── Imagen base ─────────────────────────────────────────────────────────────
FROM python:3.12-slim

# Metadatos
LABEL maintainer="dado4cs"
LABEL description="Ingesta de datos: Frontend microservicio (MongoDB) → CSV → S3"

# Variables de entorno por defecto (override en docker-compose o en la MV)
ENV MONGO_URI=mongodb://mongo:27017 \
    MONGO_DB=frontend_db \
    S3_BUCKET=my-ingesta-bucket \
    S3_PREFIX=frontend \
    AWS_REGION=us-east-1 \
    OUTPUT_DIR=/tmp/output/frontend

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ingest.py .

CMD ["python", "ingest.py"]
