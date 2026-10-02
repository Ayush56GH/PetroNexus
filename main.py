"""
PetroNexus Server Runner
Run with: python main.py
"""
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("  Starting PetroNexus Backend Server (SIH26121)")
    print("  Web Interface: http://127.0.0.1:8000")
    print("  AI Assistant:  http://127.0.0.1:8000/assistant.html")
    print("  API Docs:      http://127.0.0.1:8000/docs")
    print("=" * 60)
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
