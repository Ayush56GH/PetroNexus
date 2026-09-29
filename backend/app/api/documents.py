import shutil
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models.document import Document, DocumentPage
from backend.app.models.audit import AuditLog
from backend.app.document_processing.pdf_processor import PDFProcessor

router = APIRouter(prefix="/documents", tags=["Document Intelligence"])

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    well_id: Optional[int] = Form(None),
    doc_type: str = Form("WCR"),
    db: Session = Depends(get_db)
):
    save_path = settings.DOCUMENTS_DIR / file.filename
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Process PDF document
    doc = PDFProcessor.process_pdf(db, save_path, well_id=well_id, doc_type=doc_type)

    audit = AuditLog(
        action="DOCUMENT_UPLOAD",
        resource=f"document:{doc.id}",
        details={"file": file.filename, "pages": doc.page_count}
    )
    db.add(audit)
    db.commit()

    return {
        "status": "SUCCESS",
        "document_id": doc.id,
        "title": doc.title,
        "page_count": doc.page_count,
        "file_name": doc.file_name
    }

@router.get("")
def list_documents(well_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Document)
    if well_id:
        query = query.filter(Document.well_id == well_id)
    docs = query.order_by(Document.id.desc()).all()
    return [
        {
            "id": d.id,
            "title": d.title,
            "document_type": d.document_type,
            "file_name": d.file_name,
            "page_count": d.page_count,
            "upload_date": d.upload_date.strftime("%Y-%m-%d %H:%M:%S") if d.upload_date else None,
            "well_id": d.well_id,
            "well_name": d.well.well_name if d.well else "Regional"
        }
        for d in docs
    ]

@router.get("/{document_id}")
def get_document_detail(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    pages = db.query(DocumentPage).filter(DocumentPage.document_id == document_id).order_by(DocumentPage.page_number.asc()).all()
    return {
        "id": doc.id,
        "title": doc.title,
        "document_type": doc.document_type,
        "file_name": doc.file_name,
        "page_count": doc.page_count,
        "well_name": doc.well.well_name if doc.well else "Regional",
        "pages": [
            {
                "page_number": p.page_number,
                "text_snippet": p.extracted_text[:250] + ("..." if len(p.extracted_text) > 250 else ""),
                "tables_count": len(p.structured_tables_json)
            } for p in pages
        ]
    }

@router.get("/{document_id}/pages/{page_num}")
def get_document_page(document_id: int, page_num: int, db: Session = Depends(get_db)):
    page = db.query(DocumentPage).filter(
        DocumentPage.document_id == document_id,
        DocumentPage.page_number == page_num
    ).first()
    if not page:
        raise HTTPException(status_code=404, detail="Document page not found")

    # Audit log
    audit = AuditLog(
        action="DOCUMENT_VIEW",
        resource=f"document:{document_id}:page:{page_num}",
        details={"page": page_num}
    )
    db.add(audit)
    db.commit()

    return {
        "document_id": document_id,
        "page_number": page.page_number,
        "extracted_text": page.extracted_text,
        "structured_tables": page.structured_tables_json,
        "metadata": page.metadata_json
    }

@router.get("/{document_id}/download")
def download_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc or not Path(doc.file_path).exists():
        raise HTTPException(status_code=404, detail="File not found on server")
    return FileResponse(doc.file_path, filename=doc.file_name)
