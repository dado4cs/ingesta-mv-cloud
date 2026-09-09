import os
import csv
import logging
import boto3
import pymysql
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

# ── MySQL connection ────────────────────────────────────────────────────────
MYSQL_HOST     = os.getenv("MYSQL_HOST",     "mysql")
MYSQL_PORT     = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_DB       = os.getenv("MYSQL_DB",       "community_db")
MYSQL_USER     = os.getenv("MYSQL_USER",     "community")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "changeme")

# ── S3 config ───────────────────────────────────────────────────────────────
S3_BUCKET      = os.getenv("S3_BUCKET",  "my-ingesta-bucket")
S3_PREFIX      = os.getenv("S3_PREFIX",  "comunity")
AWS_REGION     = os.getenv("AWS_REGION", "us-east-1")
OUTPUT_DIR     = os.getenv("OUTPUT_DIR", "/tmp/output/comunity")

# ── Tables to extract ────────────────────────────────────────────────────────
TABLES = [
    "users",
    "clubs",
    "memberships",
    "watch_rooms",
    "watch_participants",
]

def get_connection():
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        database=MYSQL_DB,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        cursorclass=pymysql.cursors.DictCursor,
    )

def export_table_to_csv(cursor, table: str, output_path: str) -> int:
    """Dump all rows of a table into a CSV file. Returns row count."""
    log.info(f"Exporting table '{table}'...")
    cursor.execute(f"SELECT * FROM {table};")
    rows = cursor.fetchall()

    if not rows:
        log.info(f"  → Table '{table}' is empty, skipping.")
        return 0

    columns = list(rows[0].keys())
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
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
    log.info("=== Ingesta Comunity (MySQL) ===")
    log.info(f"Connecting to MySQL at {MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}")

    conn = get_connection()
    cursor = conn.cursor()

    total_rows = 0
    for table in TABLES:
        filename   = f"{table}.csv"
        local_path = os.path.join(OUTPUT_DIR, date_partition, filename)
        s3_key     = f"{S3_PREFIX}/{date_partition}/{filename}"

        rows = export_table_to_csv(cursor, table, local_path)
        total_rows += rows
        if rows > 0:
            upload_to_s3(local_path, s3_key)

    cursor.close()
    conn.close()

    log.info(f"=== Ingesta Comunity finalizada. Total registros exportados: {total_rows} ===")

if __name__ == "__main__":
    main()
