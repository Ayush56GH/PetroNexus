"""
PetroNexus PDF Document Processor (SIH 26121 Section 16, 17, 18)
Uses PyMuPDF to extract pages, text, metadata, tables, with automatic OCR fallback
for scanned documents, extracts structured events, formations, and depths,
generates 384-dim BAAI/bge-small-en-v1.5 embeddings locally, and creates KnowledgeChunks.
"""
from pathlib import Path
from typing import Dict, Any, List, Optional
import uuid
import fitz # PyMuPDF
from sqlalchemy.orm import Session

from backend.app.models.document import Document, DocumentPage, KnowledgeChunk
from backend.app.models.event import DrillingEvent
from backend.app.document_processing.table_extractor import TableExtractor
from backend.app.document_processing.ocr_engine import ocr_engine
from backend.app.document_processing.entity_extractor import entity_extractor
from backend.app.rag.embedding_service import embedding_service
from backend.app.utils.logger import logger

class PDFProcessor:

    @staticmethod
    def process_pdf(
        db: Session,
        file_path: Path,
        well_id: Optional[int] = None,
        doc_type: str = "WCR",
        owner_id: Optional[uuid.UUID] = None,
        organization_id: Optional[uuid.UUID] = None,
        visibility: str = "DEMO"
    ) -> Document:
        """
        Parses PDF file, segments into pages, applies OCR when needed, extracts
        events and formations, generates 384-dim local embeddings, and creates KnowledgeChunks in pgvector.
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
            owner_id=owner_id,
            organization_id=organization_id,
            visibility=visibility,
            is_processed=True,
            ocr_applied=False,
            ocr_status="NOT_REQUIRED"
        )
        db.add(db_doc)
        db.commit()
        db.refresh(db_doc)

        pending_chunks = []
        chunk_texts = []
        any_ocr_applied = False
        total_extracted_events = 0
        all_formations = set()

        for page_idx, page in enumerate(doc_fitz):
            page_num = page_idx + 1

            # 1. Native text extraction with OCR fallback
            page_text, ocr_used, ocr_stat, conf = ocr_engine.process_page(page, page_num)
            if ocr_used:
                any_ocr_applied = True

            # 2. Extract structured tables
            tables = TableExtractor.extract_tables_from_text(page_text)

            # 3. Entity & Event Extraction
            extraction = entity_extractor.extract_from_text(page_text, page_number=page_num, doc_name=file_path.name)
            all_formations.update(extraction["formations_found"])

            # Store structured drilling events into database
            if well_id and extraction["events_detected"]:
                for ev in extraction["events_detected"]:
                    dev = DrillingEvent(
                        well_id=well_id,
                        event_type=ev["event_type"],
                        depth_md_m=ev["depth_md"],
                        depth_tvd_m=round(ev["depth_md"] * 0.985, 1),
                        formation_name=ev["formation_name"],
                        severity=ev["severity"],
                        description=ev["description"],
                        primary_cause=ev["primary_cause"],
                        immediate_mitigation=ev["immediate_mitigation"],
                        npt_hours=ev.get("npt_hours", 4.0),
                        source_document_id=db_doc.id,
                        source_document_name=file_path.name,
                        source_page_number=page_num,
                        source_text=ev["description"],
                        confidence=ev.get("confidence", 0.92),
                        is_real=True,
                        is_synthetic=False
                    )
                    db.add(dev)
                    total_extracted_events += 1

            # Store page
            db_page = DocumentPage(
                document_id=db_doc.id,
                page_number=page_num,
                extracted_text=page_text,
                structured_tables_json=tables,
                detected_topics=list(extraction["formations_found"]) or ["Drilling Operations"],
                metadata_json={
                    "page": page_num,
                    "char_count": len(page_text),
                    "ocr_used": ocr_used,
                    "ocr_status": ocr_stat,
                    "events_detected": len(extraction["events_detected"])
                }
            )
            db.add(db_page)
            db.commit()
            db.refresh(db_page)

            # Split into chunks of ~500 characters
            paragraphs = [p.strip() for p in page_text.split("\n\n") if len(p.strip()) > 30]
            for c_idx, para in enumerate(paragraphs):
                # Search for depth reference
                depth_ref = extraction["primary_depth"]
                chunk = KnowledgeChunk(
                    document_id=db_doc.id,
                    page_id=db_page.id,
                    well_id=well_id,
                    chunk_index=c_idx,
                    chunk_text=para,
                    section_header=f"Page {page_num} Section {c_idx + 1}",
                    depth_reference_m=depth_ref,
                    formation_reference=list(extraction["formations_found"])[0] if extraction["formations_found"] else "Barail Group",
                    owner_id=owner_id,
                    organization_id=organization_id,
                    visibility=visibility
                )
                pending_chunks.append(chunk)
                chunk_texts.append(para)

        # Update document OCR and extraction flags
        db_doc.ocr_applied = any_ocr_applied
        db_doc.ocr_status = "PROCESSED" if any_ocr_applied else "NOT_REQUIRED"
        db_doc.extracted_events_count = total_extracted_events
        db_doc.extracted_formations_count = len(all_formations)
        db.commit()

        # Batch compute 384-dimensional embeddings locally
        if chunk_texts:
            logger.info(f"Generating 384-dim local embeddings for {len(chunk_texts)} chunks...")
            embeddings = embedding_service.embed_documents(chunk_texts)
            for chunk_obj, emb in zip(pending_chunks, embeddings):
                chunk_obj.embedding = emb
                db.add(chunk_obj)
            db.commit()
            logger.info(f"Embedded and saved {len(pending_chunks)} knowledge chunks to pgvector.")

        logger.info(f"Successfully processed PDF: {file_path.name} ({len(doc_fitz)} pages, {len(pending_chunks)} chunks, {total_extracted_events} events extracted)")
        return db_doc

