"""
PetroNexus Demo Document Indexer
Ingests the generated demo PDF files into the database.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session
from backend.app.database import SessionLocal
from backend.app.models.well import Well
from backend.app.document_processing.pdf_processor import PDFProcessor

DOC_DIR = Path(__file__).resolve().parent.parent / "documents"

def index_docs():
    db: Session = SessionLocal()
    try:
        # 1. WCR-OIL-DEMO-018
        w18 = db.query(Well).filter(Well.well_name == "OIL-DEMO-018").first()
        f18 = DOC_DIR / "WCR-OIL-DEMO-018.pdf"
        if f18.exists():
            PDFProcessor.process_pdf(db, f18, well_id=w18.id if w18 else None, doc_type="WCR")

        # 2. DDR-OIL-DEMO-021
        w21 = db.query(Well).filter(Well.well_name == "OIL-DEMO-021").first()
        f21 = DOC_DIR / "DDR-OIL-DEMO-021.pdf"
        if f21.exists():
            PDFProcessor.process_pdf(db, f21, well_id=w21.id if w21 else None, doc_type="DDR")

        # 3. Current_Well_Report_OIL-DEMO-023
        w23 = db.query(Well).filter(Well.well_name == "OIL-DEMO-023").first()
        f23 = DOC_DIR / "Current_Well_Report_OIL-DEMO-023.pdf"
        if f23.exists():
            PDFProcessor.process_pdf(db, f23, well_id=w23.id if w23 else None, doc_type="DDR")

        print("Indexed demo documents successfully.")
    finally:
        db.close()

if __name__ == "__main__":
    index_docs()
