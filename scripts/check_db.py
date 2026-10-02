import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.database import engine
from sqlalchemy import text

def check():
    with engine.connect() as conn:
        res = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;"))
        tables = [r[0] for r in res.fetchall()]
        print("Postgres tables count:", len(tables))
        print("Tables:", tables)
        for t in tables:
            try:
                cnt = conn.execute(text(f'SELECT count(*) FROM "{t}"')).scalar()
                print(f"  {t}: {cnt} rows")
            except Exception as e:
                print(f"  {t}: error {e}")

if __name__ == "__main__":
    check()
