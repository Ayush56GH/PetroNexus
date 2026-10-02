"""
PetroNexus PDF Document Processor
Uses PyMuPDF to extract pages, text, metadata, tables, generates 384-dim BAAI/bge-small-en-v1.5
embeddings locally, and inserts multi-tenant knowledge chunks into Supabase pgvector.
"""
from pathlib import Path
from typing import Dict, Any, List, Optional
import uuid
import fitz # PyMuPDF
from sqlalchemy.orm import Session
from backend.app.models.document import Document, DocumentPage, KnowledgeChunk
from backend.app.document_processing.table_extractor import TableExtractor
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
        Parses PDF file, segments into pages, extracts tables and text,
        generates 384-dim local embeddings, and creates KnowledgeChunks in pgvector.
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
            is_processed=True
        )
        db.add(db_doc)
        db.commit()
        db.refresh(db_doc)

        pending_chunks = []
        chunk_texts = []

        for page_idx, page in enumerate(doc_fitz):
            page_num = page_idx + 1
            page_text = page.get_text()

            # Extract structured tables
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
                # Search for depth reference (e.g. 2860 m, 2842m)
                depth_ref = None
                words = para.split()
                for w in words:
                    cleaned_w = w.lower().replace("m", "").replace(",", "")
                    try:
                        val = float(cleaned_w)
                        if 500.0 <= val <= 6000.0:
                            depth_ref = val
                            break
                    except ValueError:
                        pass

                chunk = KnowledgeChunk(
                    document_id=db_doc.id,
                    page_id=db_page.id,
                    well_id=well_id,
                    chunk_index=c_idx,
                    chunk_text=para,
                    section_header=f"Page {page_num} Section {c_idx + 1}",
                    depth_reference_m=depth_ref,
                    formation_reference="Formation-X" if "formation" in para.lower() else None,
                    owner_id=owner_id,
                    organization_id=organization_id,
                    visibility=visibility
                )
                pending_chunks.append(chunk)
                chunk_texts.append(para)

        # Batch compute 384-dimensional embeddings locally
        if chunk_texts:
            logger.info(f"Generating 384-dim local embeddings for {len(chunk_texts)} chunks...")
            embeddings = embedding_service.embed_documents(chunk_texts)
            for chunk_obj, emb in zip(pending_chunks, embeddings):
                chunk_obj.embedding = emb
                db.add(chunk_obj)

            db.commit()
            logger.info(f"Embedded and saved {len(pending_chunks)} knowledge chunks to pgvector.")

        logger.info(f"Successfully processed PDF: {file_path.name} ({len(doc_fitz)} pages, {len(pending_chunks)} chunks)")
        return db_doc
