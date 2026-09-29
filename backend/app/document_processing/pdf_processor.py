"""
PetroNexus PDF Document Processor
Uses PyMuPDF to extract pages, text, metadata, tables, and generate chunked knowledge records.
"""
from pathlib import Path
from typing import Dict, Any, List
import fitz # PyMuPDF
from sqlalchemy.orm import Session
from backend.app.models.document import Document, DocumentPage, KnowledgeChunk
from backend.app.document_processing.table_extractor import TableExtractor
from backend.app.utils.logger import logger

class PDFProcessor:

    @staticmethod
    def process_pdf(db: Session, file_path: Path, well_id: int = None, doc_type: str = "WCR") -> Document:
        """
        Parses PDF file, segments into pages, extracts tables and text, and creates KnowledgeChunks.
        """
        doc_fitz = fitz.open(file_path)
        doc_title = file_path.stem.replace("_", " ").title()

        db_doc = Document(
            well_id=well_id,
            title=doc_title,
            document_type=doc_type,
            file_name=file_path.name,
            file_path=str(file_path),
            file_size_bytes=file_path.stat().st_size,
            page_count=len(doc_fitz),
            is_processed=True
        )
        db.add(db_doc)
        db.commit()
        db.refresh(db_doc)

        for page_idx, page in enumerate(doc_fitz):
            page_num = page_idx + 1
            page_text = page.get_text()

            # Extract tables
            tables = TableExtractor.extract_tables_from_text(page_text)

            # Store page
            db_page = DocumentPage(
                document_id=db_doc.id,
                page_number=page_num,
                extracted_text=page_text,
                structured_tables_json=tables,
                detected_topics=["Drilling Operations", "Formation Evaluation"],
                metadata_json={"page": page_num, "char_count": len(page_text)}
            )
            db.add(db_page)
            db.commit()
            db.refresh(db_page)

            # Split into chunks of ~500 characters
            paragraphs = [p.strip() for p in page_text.split("\n\n") if len(p.strip()) > 30]
            for c_idx, para in enumerate(paragraphs):
                chunk = KnowledgeChunk(
                    document_id=db_doc.id,
                    page_id=db_page.id,
                    well_id=well_id,
                    chunk_index=c_idx,
                    chunk_text=para,
                    section_header=f"Page {page_num} Section {c_idx + 1}"
                )
                db.add(chunk)

        db.commit()
        logger.info(f"Successfully processed PDF: {file_path.name} ({len(doc_fitz)} pages)")
        return db_doc
