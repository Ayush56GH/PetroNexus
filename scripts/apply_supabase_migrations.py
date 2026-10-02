"""
Applies Supabase migrations to the live database configured in .env.
"""
import os
import psycopg
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

db_url = os.getenv("DATABASE_URL")
if not db_url or "sqlite" in db_url:
    print("Error: DATABASE_URL is not configured for PostgreSQL/Supabase.")
    exit(1)

# Ensure psycopg-compatible URI
if db_url.startswith("postgresql+psycopg://"):
    raw_conn_url = db_url.replace("postgresql+psycopg://", "postgresql://")
else:
    raw_conn_url = db_url

migration_file = BASE_DIR / "supabase" / "migrations" / "20260930000001_initial_schema.sql"
print(f"Reading migration file: {migration_file.name}...")
with open(migration_file, "r", encoding="utf-8") as f:
    sql_script = f.read()

print("Connecting to Supabase PostgreSQL...")
try:
    with psycopg.connect(raw_conn_url, connect_timeout=15) as conn:
        print("Connected successfully! Applying migration script...")
        with conn.cursor() as cur:
            cur.execute(sql_script)
        conn.commit()
        print("Migration applied successfully!")

        # Verify created tables
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            tables = [row[0] for row in cur.fetchall()]
            print(f"Verified {len(tables)} public tables in database:")
            for t in tables:
                print(f"  - {t}")

            # Verify extensions
            cur.execute("SELECT extname, extversion FROM pg_extension WHERE extname IN ('postgis', 'vector', 'uuid-ossp');")
            exts = cur.fetchall()
            print(f"Verified extensions: {exts}")

except Exception as e:
    print(f"Migration error: {e}")
    exit(1)
