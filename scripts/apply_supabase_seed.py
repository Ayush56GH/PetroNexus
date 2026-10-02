"""
Seeds Supabase database with synthetic demonstration data from supabase/seed.sql.
"""
import os
import psycopg
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

db_url = os.getenv("DATABASE_URL")
if db_url.startswith("postgresql+psycopg://"):
    raw_conn_url = db_url.replace("postgresql+psycopg://", "postgresql://")
else:
    raw_conn_url = db_url

seed_file = BASE_DIR / "supabase" / "seed.sql"
print(f"Reading seed file: {seed_file.name}...")
with open(seed_file, "r", encoding="utf-8") as f:
    sql_script = f.read()

print("Applying seed data to Supabase...")
with psycopg.connect(raw_conn_url, connect_timeout=15) as conn:
    with conn.cursor() as cur:
        cur.execute(sql_script)
    conn.commit()

    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM public.wells;")
        wells_cnt = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM public.drilling_events;")
        events_cnt = cur.fetchone()[0]
        print(f"Seeding completed successfully! Database now contains {wells_cnt} wells and {events_cnt} drilling events.")
