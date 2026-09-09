import os
import csv
import logging
import boto3
import psycopg2
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

# ── Postgres connection ─────────────────────────────────────────────────────
PG_HOST     = os.getenv("PG_HOST",     "postgres")
PG_PORT     = int(os.getenv("PG_PORT", "5432"))
PG_DB       = os.getenv("PG_DB",       "cinema_catalog")
PG_USER     = os.getenv("PG_USER",     "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "changeme")

# ── S3 config ───────────────────────────────────────────────────────────────
S3_BUCKET      = os.getenv("S3_BUCKET",      "my-ingesta-bucket")
S3_PREFIX      = os.getenv("S3_PREFIX",      "catalogo")
AWS_REGION     = os.getenv("AWS_REGION",     "us-east-1")
OUTPUT_DIR     = os.getenv("OUTPUT_DIR",     "/tmp/output/catalogo")

# ── Tables to extract ────────────────────────────────────────────────────────
TABLES = [
    "movie",
    "artist",
    "genre",
    "movie_genre",
    "movie_artist",
    "movie_video_source",
    "movie_subtitle",
]

def get_connection():
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD,
    )

def export_table_to_csv(cursor, table: str, output_path: str) -> int:
    """Dump all rows of a table into a CSV file. Returns row count."""
    log.info(f"Exporting table '{table}'...")
    cursor.execute(f"SELECT * FROM {table};")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)

    log.info(f"  → {len(rows)} rows written to {output_path}")
    return len(rows)

def upload_to_s3(local_path: str, s3_key: str):
    """Upload a local file to S3."""
    s3 = boto3.client("s3", region_name=AWS_REGION)
    log.info(f"Uploading {local_path} → s3://{S3_BUCKET}/{s3_key}")
    s3.upload_file(local_path, S3_BUCKET, s3_key)
    log.info("  → Upload complete.")

def main():
    date_partition = datetime.utcnow().strftime("%Y-%m-%d")
    log.info("=== Ingesta Catálogo (PostgreSQL) ===")
    log.info(f"Connecting to PostgreSQL at {PG_HOST}:{PG_PORT}/{PG_DB}")

    conn = get_connection()
    cursor = conn.cursor()

    total_rows = 0
    for table in TABLES:
        filename   = f"{table}.csv"
        local_path = os.path.join(OUTPUT_DIR, date_partition, filename)
        s3_key     = f"{S3_PREFIX}/{date_partition}/{filename}"

        rows = export_table_to_csv(cursor, table, local_path)
        total_rows += rows
        upload_to_s3(local_path, s3_key)

    cursor.close()
    conn.close()

    log.info(f"=== Ingesta Catálogo finalizada. Total registros exportados: {total_rows} ===")

if __name__ == "__main__":
    main()
