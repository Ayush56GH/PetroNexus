-- Migration 009: Align audit_logs table timestamp and created_at columns
ALTER TABLE public.audit_logs ADD COLUMN IF NOT EXISTS timestamp TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE public.audit_logs ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();

-- Ensure sync between timestamp and created_at
CREATE OR REPLACE FUNCTION sync_audit_logs_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.timestamp IS NOT NULL AND NEW.created_at IS NULL THEN
        NEW.created_at := NEW.timestamp;
    END IF;
    IF NEW.created_at IS NOT NULL AND NEW.timestamp IS NULL THEN
        NEW.timestamp := NEW.created_at;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sync_audit_logs_timestamp ON public.audit_logs;
CREATE TRIGGER trg_sync_audit_logs_timestamp
BEFORE INSERT OR UPDATE ON public.audit_logs
FOR EACH ROW EXECUTE FUNCTION sync_audit_logs_timestamp();
