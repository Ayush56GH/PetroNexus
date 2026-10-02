import os
import psycopg
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

db_url = os.getenv("DATABASE_URL").replace("postgresql+psycopg://", "postgresql://")
migration_file = BASE_DIR / "supabase" / "migrations" / "20260930000003_update_embedding_dimension_384.sql"

print(f"Applying migration: {migration_file.name}...")
with open(migration_file, "r", encoding="utf-8") as f:
    sql = f.read()

with psycopg.connect(db_url) as conn:
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()

    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name, data_type, udt_name 
            FROM information_schema.columns 
            WHERE table_name = 'document_chunks' AND column_name = 'embedding';
        """)
        row = cur.fetchone()
        print("Updated column info in document_chunks:", row)

        # Check index
        cur.execute("""
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE tablename = 'document_chunks' AND indexname = 'idx_chunks_embedding';
        """)
        idx = cur.fetchone()
        print("Updated HNSW index:", idx)

print("Migration 003 applied successfully!")
