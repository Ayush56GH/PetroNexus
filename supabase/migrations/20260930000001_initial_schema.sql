-- =============================================================================
-- PetroNexus Schema Migration (PostgreSQL + PostGIS + pgvector + RLS)
-- Smart India Hackathon 2026 — SIH26121 (Oil India Limited)
-- =============================================================================

-- 1. Enable Required Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";
CREATE EXTENSION IF NOT EXISTS "vector";

-- 2. Organizations & Multi-Tenant Support
CREATE TABLE IF NOT EXISTS public.organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Profiles (Linked to Supabase Auth auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    employee_id TEXT UNIQUE,
    department TEXT DEFAULT 'Drilling Operations & eRTMAC Division',
    role TEXT NOT NULL DEFAULT 'DRILLING_ENGINEER', -- DRILLING_ENGINEER, GEOLOGIST, ADMIN
    organization_id UUID REFERENCES public.organizations(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.organization_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'MEMBER', -- OWNER, ADMIN, MEMBER
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(organization_id, user_id)
);

-- 4. Wells Catalogue with Spatial PostGIS Geometry & Visibility
CREATE TABLE IF NOT EXISTS public.wells (
    id SERIAL PRIMARY KEY,
    well_name TEXT UNIQUE NOT NULL,
    well_code TEXT,
    field TEXT DEFAULT 'Duliajan Basin',
    operator TEXT DEFAULT 'Oil India Limited (OIL)',
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    geom geometry(Point, 4326),
    elevation_m DOUBLE PRECISION DEFAULT 112.5,
    spud_date TEXT DEFAULT '2026-01-15',
    completion_date TEXT,
    status TEXT DEFAULT 'DRILLING_ACTIVE',
    well_type TEXT DEFAULT 'DEVELOPMENT_DIRECTIONAL',
    target_depth_m DOUBLE PRECISION DEFAULT 3200.0,
    current_depth_m DOUBLE PRECISION DEFAULT 2846.0,
    current_formation TEXT DEFAULT 'Formation-X',
    is_active_well BOOLEAN DEFAULT FALSE,
    owner_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    organization_id UUID REFERENCES public.organizations(id) ON DELETE SET NULL,
    visibility TEXT NOT NULL DEFAULT 'DEMO', -- PRIVATE, ORGANIZATION, SHARED, DEMO
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Spatial trigger to synchronize geometry point from lat/lon
CREATE OR REPLACE FUNCTION update_well_geom()
RETURNS TRIGGER AS $$
BEGIN
    NEW.geom = ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_well_geom ON public.wells;
CREATE TRIGGER trg_well_geom
BEFORE INSERT OR UPDATE OF latitude, longitude ON public.wells
FOR EACH ROW EXECUTE FUNCTION update_well_geom();

CREATE INDEX IF NOT EXISTS idx_wells_geom ON public.wells USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_wells_visibility ON public.wells(visibility);

-- 5. Well Trajectories (Directional Surveys)
CREATE TABLE IF NOT EXISTS public.well_trajectories (
    id SERIAL PRIMARY KEY,
    well_id INT NOT NULL REFERENCES public.wells(id) ON DELETE CASCADE,
    measured_depth_m DOUBLE PRECISION NOT NULL,
    inclination_deg DOUBLE PRECISION NOT NULL,
    azimuth_deg DOUBLE PRECISION NOT NULL,
    true_vertical_depth_m DOUBLE PRECISION NOT NULL,
    tvdss_m DOUBLE PRECISION NOT NULL,
    dogleg_severity_deg_30m DOUBLE PRECISION DEFAULT 0.0,
    northing_m DOUBLE PRECISION DEFAULT 0.0,
    easting_m DOUBLE PRECISION DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_well_trajectories_well_depth ON public.well_trajectories(well_id, measured_depth_m);

-- 6. Formations & Stratigraphic Intervals
CREATE TABLE IF NOT EXISTS public.formations (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    code TEXT,
    sequence_order INT NOT NULL,
    typical_lithology TEXT,
    typical_top_depth_m DOUBLE PRECISION,
    typical_thickness_m DOUBLE PRECISION,
    pore_pressure_gradient_sg DOUBLE PRECISION DEFAULT 1.15,
    fracture_gradient_sg DOUBLE PRECISION DEFAULT 1.65,
    unconfined_compressive_strength_mpa DOUBLE PRECISION DEFAULT 45.0,
    risk_level TEXT DEFAULT 'MEDIUM',
    known_hazards JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.formation_intervals (
    id SERIAL PRIMARY KEY,
    well_id INT NOT NULL REFERENCES public.wells(id) ON DELETE CASCADE,
    formation_id INT REFERENCES public.formations(id) ON DELETE SET NULL,
    formation_name TEXT NOT NULL,
    top_depth_md_m DOUBLE PRECISION NOT NULL,
    bottom_depth_md_m DOUBLE PRECISION NOT NULL,
    top_tvd_m DOUBLE PRECISION NOT NULL,
    bottom_tvd_m DOUBLE PRECISION NOT NULL,
    lithology TEXT DEFAULT 'Sandstone / Shale',
    pore_pressure_gradient_sg DOUBLE PRECISION DEFAULT 1.15,
    fracture_gradient_sg DOUBLE PRECISION DEFAULT 1.65,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_formation_intervals_well ON public.formation_intervals(well_id);

-- 7. Historical Drilling Events & Incidents
CREATE TABLE IF NOT EXISTS public.drilling_events (
    id SERIAL PRIMARY KEY,
    well_id INT NOT NULL REFERENCES public.wells(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL, -- MUD_LOSS, TORQUE_SPIKE, STUCK_PIPE, PACK_OFF, KICK, OVERPRESSURE
    depth_md_m DOUBLE PRECISION NOT NULL,
    depth_tvd_m DOUBLE PRECISION NOT NULL,
    formation_name TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'MEDIUM', -- LOW, MEDIUM, HIGH, CRITICAL
    loss_rate_bph DOUBLE PRECISION,
    excess_torque_knm DOUBLE PRECISION,
    npt_hours DOUBLE PRECISION DEFAULT 0.0,
    primary_cause TEXT,
    immediate_mitigation TEXT,
    preventative_recommendation TEXT,
    source_document_name TEXT,
    source_page_number INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_drilling_events_depth ON public.drilling_events(depth_md_m);
CREATE INDEX IF NOT EXISTS idx_drilling_events_well ON public.drilling_events(well_id);

-- 8. Drilling Parameter Baselines
CREATE TABLE IF NOT EXISTS public.drilling_parameters (
    id SERIAL PRIMARY KEY,
    well_id INT NOT NULL REFERENCES public.wells(id) ON DELETE CASCADE,
    depth_m DOUBLE PRECISION NOT NULL,
    rop_m_hr DOUBLE PRECISION NOT NULL,
    wob_klbf DOUBLE PRECISION NOT NULL,
    rpm DOUBLE PRECISION NOT NULL,
    torque_kn_m DOUBLE PRECISION NOT NULL,
    flow_rate_lpm DOUBLE PRECISION NOT NULL,
    spp_psi DOUBLE PRECISION NOT NULL,
    mud_weight_sg DOUBLE PRECISION NOT NULL,
    ecd_sg DOUBLE PRECISION NOT NULL,
    mse_mpa DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_drilling_parameters_well_depth ON public.drilling_parameters(well_id, depth_m);

-- 9. Knowledge Documents & Chunk Embeddings (pgvector)
CREATE TABLE IF NOT EXISTS public.documents (
    id SERIAL PRIMARY KEY,
    well_id INT REFERENCES public.wells(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    document_type TEXT DEFAULT 'WCR',
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size_bytes INT DEFAULT 0,
    page_count INT DEFAULT 1,
    owner_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    organization_id UUID REFERENCES public.organizations(id) ON DELETE SET NULL,
    visibility TEXT NOT NULL DEFAULT 'DEMO', -- PRIVATE, ORGANIZATION, SHARED, DEMO
    is_processed BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_documents_visibility ON public.documents(visibility, owner_id);

CREATE TABLE IF NOT EXISTS public.document_pages (
    id SERIAL PRIMARY KEY,
    document_id INT NOT NULL REFERENCES public.documents(id) ON DELETE CASCADE,
    page_number INT NOT NULL,
    extracted_text TEXT NOT NULL,
    structured_tables_json JSONB DEFAULT '[]'::jsonb,
    detected_topics JSONB DEFAULT '[]'::jsonb,
    metadata_json JSONB DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_document_pages_doc ON public.document_pages(document_id, page_number);

CREATE TABLE IF NOT EXISTS public.document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INT NOT NULL REFERENCES public.documents(id) ON DELETE CASCADE,
    page_id INT REFERENCES public.document_pages(id) ON DELETE SET NULL,
    well_id INT REFERENCES public.wells(id) ON DELETE SET NULL,
    chunk_index INT DEFAULT 0,
    chunk_text TEXT NOT NULL,
    section_header TEXT,
    depth_reference_m DOUBLE PRECISION,
    formation_reference TEXT,
    owner_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    organization_id UUID REFERENCES public.organizations(id) ON DELETE SET NULL,
    visibility TEXT NOT NULL DEFAULT 'DEMO', -- PRIVATE, ORGANIZATION, SHARED, DEMO
    embedding vector(1536), -- Standard OpenAI / modern embedding size (compatible with pgvector)
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_document_chunks_visibility ON public.document_chunks(visibility, owner_id);
-- Vector index for cosine similarity search
CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON public.document_chunks USING hnsw (embedding vector_cosine_ops);

-- 10. Persistent Multi-User Chat Conversations & Messages
CREATE TABLE IF NOT EXISTS public.conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES public.organizations(id) ON DELETE SET NULL,
    title TEXT NOT NULL DEFAULT 'Drilling Intelligence Session',
    active_well_id INT REFERENCES public.wells(id) ON DELETE SET NULL,
    summary TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_conversations_user ON public.conversations(user_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS public.messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL, -- user, assistant, system
    content TEXT NOT NULL,
    citations JSONB DEFAULT '[]'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON public.messages(conversation_id, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_messages_user ON public.messages(user_id);

-- 11. Alerts & Operational Notifications
CREATE TABLE IF NOT EXISTS public.alerts (
    id SERIAL PRIMARY KEY,
    well_id INT NOT NULL REFERENCES public.wells(id) ON DELETE CASCADE,
    alert_title TEXT NOT NULL,
    alert_type TEXT NOT NULL, -- LOOK_AHEAD, ANOMALY, RISK, MEMORY_GAP
    severity TEXT NOT NULL DEFAULT 'MEDIUM', -- LOW, MEDIUM, HIGH, CRITICAL
    current_depth_m DOUBLE PRECISION NOT NULL,
    target_depth_m DOUBLE PRECISION NOT NULL,
    delta_ahead_m DOUBLE PRECISION NOT NULL,
    historical_event_id INT REFERENCES public.drilling_events(id) ON DELETE SET NULL,
    historical_well_id INT REFERENCES public.wells(id) ON DELETE SET NULL,
    source_citation TEXT NOT NULL,
    rationale_summary TEXT NOT NULL,
    playbook_recommendation TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE', -- ACTIVE, ACKNOWLEDGED, RESOLVED
    owner_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    organization_id UUID REFERENCES public.organizations(id) ON DELETE SET NULL,
    visibility TEXT NOT NULL DEFAULT 'DEMO',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_alerts_well_status ON public.alerts(well_id, status);

-- 12. Audit Logs
CREATE TABLE IF NOT EXISTS public.audit_logs (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    user_email TEXT,
    action TEXT NOT NULL,
    resource TEXT NOT NULL,
    details JSONB DEFAULT '{}'::jsonb,
    ip_address TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON public.audit_logs(user_id, created_at DESC);

-- 13. Granular Resource Permissions
CREATE TABLE IF NOT EXISTS public.resource_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_type TEXT NOT NULL, -- document, well, conversation
    resource_id TEXT NOT NULL,
    granted_to_user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    permission TEXT NOT NULL DEFAULT 'READ', -- READ, WRITE, ADMIN
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =============================================================================

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

-- Profiles: Users manage their own profile
DROP POLICY IF EXISTS "profiles_select_own" ON public.profiles;
CREATE POLICY "profiles_select_own" ON public.profiles
    FOR SELECT USING (auth.uid() = id);

DROP POLICY IF EXISTS "profiles_update_own" ON public.profiles;
CREATE POLICY "profiles_update_own" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);

-- Conversations: Users manage their own conversations
DROP POLICY IF EXISTS "conversations_manage_own" ON public.conversations;
CREATE POLICY "conversations_manage_own" ON public.conversations
    FOR ALL USING (auth.uid() = user_id);

-- Messages: Users manage their own messages
DROP POLICY IF EXISTS "messages_manage_own" ON public.messages;
CREATE POLICY "messages_manage_own" ON public.messages
    FOR ALL USING (auth.uid() = user_id);

-- Documents: Visible if DEMO, or owned by user, or in user's organization, or explicitly granted
DROP POLICY IF EXISTS "documents_visibility" ON public.documents;
CREATE POLICY "documents_visibility" ON public.documents
    FOR SELECT USING (
        visibility = 'DEMO'
        OR owner_id = auth.uid()
        OR (visibility = 'ORGANIZATION' AND organization_id IN (
            SELECT organization_id FROM public.organization_members WHERE user_id = auth.uid()
        ))
        OR id::text IN (
            SELECT resource_id FROM public.resource_permissions 
            WHERE resource_type = 'document' AND granted_to_user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "documents_insert_own" ON public.documents;
CREATE POLICY "documents_insert_own" ON public.documents
    FOR INSERT WITH CHECK (auth.uid() = owner_id OR owner_id IS NULL);

-- Document Chunks: Same visibility as documents
DROP POLICY IF EXISTS "document_chunks_visibility" ON public.document_chunks;
CREATE POLICY "document_chunks_visibility" ON public.document_chunks
    FOR SELECT USING (
        visibility = 'DEMO'
        OR owner_id = auth.uid()
        OR (visibility = 'ORGANIZATION' AND organization_id IN (
            SELECT organization_id FROM public.organization_members WHERE user_id = auth.uid()
        ))
        OR document_id::text IN (
            SELECT resource_id FROM public.resource_permissions 
            WHERE resource_type = 'document' AND granted_to_user_id = auth.uid()
        )
    );

-- Alerts: Visible if DEMO or owned by user
DROP POLICY IF EXISTS "alerts_visibility" ON public.alerts;
CREATE POLICY "alerts_visibility" ON public.alerts
    FOR SELECT USING (
        visibility = 'DEMO'
        OR owner_id = auth.uid()
        OR owner_id IS NULL
    );

-- Audit logs: Users can view their own, service role can manage
DROP POLICY IF EXISTS "audit_logs_select_own" ON public.audit_logs;
CREATE POLICY "audit_logs_select_own" ON public.audit_logs
    FOR SELECT USING (auth.uid() = user_id);

-- =============================================================================
-- SECURE VECTOR RETRIEVAL FUNCTION (PERMISSION-AWARE)
-- =============================================================================
CREATE OR REPLACE FUNCTION match_authorized_document_chunks(
    query_embedding vector(1536),
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
        1 - (dc.embedding <=> query_embedding) AS similarity,
        d.file_name AS source_document_name,
        COALESCE(dp.page_number, 1) AS page_number
    FROM public.document_chunks dc
    JOIN public.documents d ON dc.document_id = d.id
    LEFT JOIN public.document_pages dp ON dc.page_id = dp.id
    WHERE
        -- Multi-User Permission Enforcement:
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
        AND (1 - (dc.embedding <=> query_embedding)) >= match_threshold
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
