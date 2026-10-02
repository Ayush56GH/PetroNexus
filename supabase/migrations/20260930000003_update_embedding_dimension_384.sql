-- =============================================================================
-- PetroNexus Migration 003: Update Embedding Dimension to 384 (BAAI/bge-small-en-v1.5)
-- =============================================================================

-- 1. Drop existing HNSW index on document_chunks.embedding
DROP INDEX IF EXISTS public.idx_chunks_embedding;

-- 2. Alter column type from vector(1536) to vector(384)
ALTER TABLE public.document_chunks 
ALTER COLUMN embedding TYPE vector(384);

-- 3. Recreate HNSW vector index with cosine similarity operator
CREATE INDEX idx_chunks_embedding 
ON public.document_chunks USING hnsw (embedding vector_cosine_ops);

-- 4. Update the authorized matching function to accept vector(384)
DROP FUNCTION IF EXISTS public.match_authorized_document_chunks(vector, double precision, integer, uuid, integer);
DROP FUNCTION IF EXISTS public.match_authorized_document_chunks(vector, double precision, integer, uuid);

CREATE OR REPLACE FUNCTION public.match_authorized_document_chunks(
    query_embedding vector(384),
    match_threshold DOUBLE PRECISION,
    match_count INT,
    requesting_user_id UUID,
    target_well_id INT DEFAULT NULL
)
RETURNS TABLE (
    id INT,
    document_id INT,
    chunk_index INT,
    chunk_text TEXT,
    section_header TEXT,
    depth_reference_m DOUBLE PRECISION,
    formation_reference TEXT,
    similarity DOUBLE PRECISION,
    source_document_name TEXT,
    page_number INT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT
        dc.id,
        dc.document_id,
        dc.chunk_index,
        dc.chunk_text,
        dc.section_header,
        dc.depth_reference_m,
        dc.formation_reference,
        (1 - (dc.embedding <=> query_embedding))::DOUBLE PRECISION AS similarity,
        d.file_name AS source_document_name,
        COALESCE(dp.page_number, 1) AS page_number
    FROM public.document_chunks dc
    JOIN public.documents d ON dc.document_id = d.id
    LEFT JOIN public.document_pages dp ON dc.page_id = dp.id
    WHERE
        -- Multi-User Permission & Visibility Filter:
        (
            dc.visibility = 'DEMO'
            OR dc.owner_id = requesting_user_id
            OR (dc.visibility = 'ORGANIZATION' AND dc.organization_id IN (
                SELECT om.organization_id FROM public.organization_members om WHERE om.user_id = requesting_user_id
            ))
            OR d.id::text IN (
                SELECT rp.resource_id FROM public.resource_permissions rp 
                WHERE rp.resource_type = 'document' AND rp.granted_to_user_id = requesting_user_id
            )
        )
        AND (target_well_id IS NULL OR dc.well_id = target_well_id)
        AND dc.embedding IS NOT NULL
        AND (1 - (dc.embedding <=> query_embedding)) >= match_threshold
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
