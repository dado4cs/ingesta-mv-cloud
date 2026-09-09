import os
import csv
import logging
import boto3
from datetime import datetime
from pymongo import MongoClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

# ── MongoDB connection ──────────────────────────────────────────────────────
MONGO_URI  = os.getenv("MONGO_URI",  "mongodb://mongo:27017")
MONGO_DB   = os.getenv("MONGO_DB",   "frontend_db")

# ── S3 config ───────────────────────────────────────────────────────────────
S3_BUCKET  = os.getenv("S3_BUCKET",  "my-ingesta-bucket")
S3_PREFIX  = os.getenv("S3_PREFIX",  "frontend")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/tmp/output/frontend")

# ── Collections to extract ───────────────────────────────────────────────────
# These are the expected collections for the Frontend microservice.
# Adjust the list if your compañero uses different collection names.
COLLECTIONS = os.getenv("MONGO_COLLECTIONS", "sessions,notifications,preferences,activity_logs")

def get_client():
    return MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)

def flatten_doc(doc: dict, parent_key: str = "", sep: str = ".") -> dict:
    """Recursively flatten a nested MongoDB document for CSV serialization."""
    items = {}
    for key, value in doc.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.update(flatten_doc(value, new_key, sep))
        elif isinstance(value, list):
            # Convert lists to a pipe-separated string
            items[new_key] = "|".join(str(v) for v in value)
        else:
            items[new_key] = value
    return items

def export_collection_to_csv(db, collection_name: str, output_path: str) -> int:
    """Dump all documents of a MongoDB collection into a CSV file."""
    log.info(f"Exporting collection '{collection_name}'...")
    collection = db[collection_name]
    documents  = list(collection.find({}, {"_id": 0}))  # exclude Mongo internal _id

    if not documents:
        log.info(f"  → Collection '{collection_name}' is empty, skipping.")
        return 0

    # Flatten all docs and collect all unique keys for the CSV header
    flat_docs = [flatten_doc(doc) for doc in documents]
    all_keys  = list(dict.fromkeys(k for doc in flat_docs for k in doc.keys()))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(flat_docs)

    log.info(f"  → {len(flat_docs)} documents written to {output_path}")
    return len(flat_docs)

def upload_to_s3(local_path: str, s3_key: str):
    """Upload a local file to S3."""
    s3 = boto3.client("s3", region_name=AWS_REGION)
    log.info(f"Uploading {local_path} → s3://{S3_BUCKET}/{s3_key}")
    s3.upload_file(local_path, S3_BUCKET, s3_key)
    log.info("  → Upload complete.")

def main():
    date_partition  = datetime.utcnow().strftime("%Y-%m-%d")
    collections     = [c.strip() for c in COLLECTIONS.split(",") if c.strip()]
    log.info("=== Ingesta Frontend (MongoDB) ===")
    log.info(f"Connecting to MongoDB at {MONGO_URI} / DB: {MONGO_DB}")
    log.info(f"Collections to extract: {collections}")

    client = get_client()
    db     = client[MONGO_DB]

    total_rows = 0
    for collection_name in collections:
        filename   = f"{collection_name}.csv"
        local_path = os.path.join(OUTPUT_DIR, date_partition, filename)
        s3_key     = f"{S3_PREFIX}/{date_partition}/{filename}"

        rows = export_collection_to_csv(db, collection_name, local_path)
        total_rows += rows
        if rows > 0:
            upload_to_s3(local_path, s3_key)

    client.close()
    log.info(f"=== Ingesta Frontend finalizada. Total documentos exportados: {total_rows} ===")

if __name__ == "__main__":
    main()
