"""
PetroNexus Authorized Vector Search Service
Performs semantic vector search across document_chunks in Supabase pgvector.
Enforces multi-user authorization and visibility rules.
"""
from typing import List, Dict, Any, Optional
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.rag.embedding_service import embedding_service
from backend.app.utils.logger import logger

class VectorSearchService:

    @staticmethod
    def search_authorized_chunks(
        db: Session,
        query: str,
        user_id: Optional[uuid.UUID] = None,
        well_id: Optional[int] = None,
        top_k: int = 5,
        match_threshold: float = 0.25
    ) -> List[Dict[str, Any]]:
        """
        Embeds query using local BAAI/bge-small-en-v1.5 (384 dims) and executes
        permission-aware vector similarity search in Supabase pgvector.
        """
        query_vector = embedding_service.embed_query(query)
        vec_str = "[" + ",".join(str(round(x, 6)) for x in query_vector) + "]"

        # Call PostgreSQL security-definer function
        sql = text("""
            SELECT * FROM public.match_authorized_document_chunks(
                CAST(:query_embedding AS vector),
                :match_threshold,
                :match_count,
                :requesting_user_id,
                :target_well_id
            );
        """)

        try:
            results = db.execute(sql, {
                "query_embedding": vec_str,
                "match_threshold": match_threshold,
                "match_count": top_k,
                "requesting_user_id": str(user_id) if user_id else "00000000-0000-0000-0000-000000000000",
                "target_well_id": well_id
            }).fetchall()

            chunks = []
            for r in results:
                chunks.append({
                    "chunk_id": r.id,
                    "document_id": r.document_id,
                    "chunk_index": r.chunk_index,
                    "text": r.chunk_text,
                    "section_header": r.section_header,
                    "depth_reference_m": r.depth_reference_m,
                    "formation_reference": r.formation_reference,
                    "similarity": round(float(r.similarity), 4),
                    "source_document": r.source_document_name,
                    "page_number": r.page_number
                })

            logger.info(f"Retrieved {len(chunks)} authorized chunks for query '{query[:40]}' (User: {user_id})")
            return chunks
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

vector_service = VectorSearchService()
