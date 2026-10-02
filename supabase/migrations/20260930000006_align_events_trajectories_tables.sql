-- Migration 006: Align drilling_events, well_trajectories and add missing application tables
-- PetroNexus Schema Alignment

-- 1. Drilling Events
ALTER TABLE public.drilling_events
ADD COLUMN IF NOT EXISTS depth_tvdss_m DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS occurred_at TEXT,
ADD COLUMN IF NOT EXISTS description TEXT,
ADD COLUMN IF NOT EXISTS duration_hours DOUBLE PRECISION DEFAULT 4.5,
ADD COLUMN IF NOT EXISTS source_document_id INT;

UPDATE public.drilling_events
SET depth_tvdss_m = COALESCE(depth_tvdss_m, depth_tvd_m - 112.5),
    occurred_at = COALESCE(occurred_at, created_at::text),
    description = COALESCE(description, event_type || ' incident at depth ' || depth_md_m || 'm in ' || formation_name),
    duration_hours = COALESCE(duration_hours, npt_hours, 4.5);

-- 2. Well Trajectories
ALTER TABLE public.well_trajectories
ADD COLUMN IF NOT EXISTS dogleg_severity DOUBLE PRECISION DEFAULT 0.0;

UPDATE public.well_trajectories
SET dogleg_severity = COALESCE(dogleg_severity, dogleg_severity_deg_30m, 0.0);

-- 3. Event Mitigations
CREATE TABLE IF NOT EXISTS public.event_mitigations (
    id SERIAL PRIMARY KEY,
    event_type TEXT NOT NULL,
    formation_name TEXT NOT NULL,
    mitigation_title TEXT NOT NULL,
    action_category TEXT DEFAULT 'Loss Circulation Protocol',
    step_order INT DEFAULT 1,
    procedure_text TEXT NOT NULL,
    observed_efficacy TEXT DEFAULT 'High (Resolved within 4 hrs)',
    sample_wells_cited JSONB DEFAULT '[]'::jsonb,
    evidence_citations JSONB DEFAULT '[]'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_event_mitigations_type_form ON public.event_mitigations(event_type, formation_name);

-- 4. Alert Evidence
CREATE TABLE IF NOT EXISTS public.alert_evidence (
    id SERIAL PRIMARY KEY,
    alert_id INT NOT NULL REFERENCES public.alerts(id) ON DELETE CASCADE,
    offset_well_id INT REFERENCES public.wells(id) ON DELETE SET NULL,
    offset_well_name TEXT NOT NULL,
    event_id INT REFERENCES public.drilling_events(id) ON DELETE SET NULL,
    event_type TEXT NOT NULL,
    event_depth_m DOUBLE PRECISION NOT NULL,
    distance_km DOUBLE PRECISION NOT NULL,
    delta_depth_m DOUBLE PRECISION NOT NULL,
    correlation_factor DOUBLE PRECISION DEFAULT 0.92,
    document_citation TEXT DEFAULT 'WCR-OIL-DEMO-018',
    page_citation TEXT DEFAULT 'Page 37',
    narrative TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_alert_evidence_alert ON public.alert_evidence(alert_id);

-- 5. Well Upload Sessions
CREATE TABLE IF NOT EXISTS public.well_upload_sessions (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    well_id INT REFERENCES public.wells(id) ON DELETE SET NULL,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,
    processing_status TEXT DEFAULT 'COMPLETED',
    extracted_fields JSONB DEFAULT '{}'::jsonb,
    missing_fields JSONB DEFAULT '[]'::jsonb,
    quality_score DOUBLE PRECISION DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_well_upload_sessions_user ON public.well_upload_sessions(user_id);

-- 6. Data Quality Metrics
CREATE TABLE IF NOT EXISTS public.data_quality_metrics (
    id SERIAL PRIMARY KEY,
    well_id INT NOT NULL REFERENCES public.wells(id) ON DELETE CASCADE,
    readiness_percentage DOUBLE PRECISION DEFAULT 82.0,
    identity_score DOUBLE PRECISION DEFAULT 100.0,
    location_score DOUBLE PRECISION DEFAULT 100.0,
    depth_score DOUBLE PRECISION DEFAULT 100.0,
    formation_score DOUBLE PRECISION DEFAULT 100.0,
    drilling_param_score DOUBLE PRECISION DEFAULT 100.0,
    trajectory_score DOUBLE PRECISION DEFAULT 50.0,
    mud_score DOUBLE PRECISION DEFAULT 40.0,
    bha_score DOUBLE PRECISION DEFAULT 100.0,
    casing_score DOUBLE PRECISION DEFAULT 40.0,
    pressure_score DOUBLE PRECISION DEFAULT 40.0,
    reservoir_score DOUBLE PRECISION DEFAULT 50.0,
    missing_items JSONB DEFAULT '[]'::jsonb,
    next_actions JSONB DEFAULT '[]'::jsonb,
    evaluated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_data_quality_metrics_well ON public.data_quality_metrics(well_id);

-- 7. Risk Assessments
CREATE TABLE IF NOT EXISTS public.risk_assessments (
    id SERIAL PRIMARY KEY,
    well_id INT NOT NULL REFERENCES public.wells(id) ON DELETE CASCADE,
    depth_m DOUBLE PRECISION NOT NULL,
    formation_name TEXT DEFAULT 'Formation-X',
    mud_loss_risk_level TEXT DEFAULT 'HIGH',
    stuck_pipe_risk_level TEXT DEFAULT 'MODERATE',
    kick_risk_level TEXT DEFAULT 'LOW',
    torque_risk_level TEXT DEFAULT 'HIGH',
    overall_attention_level TEXT DEFAULT 'HIGH',
    rationale TEXT NOT NULL,
    lookahead_window_m DOUBLE PRECISION DEFAULT 150.0,
    evaluated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_risk_assessments_well ON public.risk_assessments(well_id);
