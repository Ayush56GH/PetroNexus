-- Migration 008: Align alerts table and add sync trigger
ALTER TABLE public.alerts ADD COLUMN IF NOT EXISTS formation_name TEXT DEFAULT 'Formation-X';
ALTER TABLE public.alerts ADD COLUMN IF NOT EXISTS title TEXT;
ALTER TABLE public.alerts ADD COLUMN IF NOT EXISTS message TEXT;
ALTER TABLE public.alerts ADD COLUMN IF NOT EXISTS acknowledged_at TIMESTAMPTZ;
ALTER TABLE public.alerts ADD COLUMN IF NOT EXISTS acknowledged_by TEXT;

ALTER TABLE public.alerts ALTER COLUMN alert_title DROP NOT NULL;
ALTER TABLE public.alerts ALTER COLUMN target_depth_m DROP NOT NULL;
ALTER TABLE public.alerts ALTER COLUMN delta_ahead_m DROP NOT NULL;
ALTER TABLE public.alerts ALTER COLUMN source_citation DROP NOT NULL;
ALTER TABLE public.alerts ALTER COLUMN rationale_summary DROP NOT NULL;
ALTER TABLE public.alerts ALTER COLUMN playbook_recommendation DROP NOT NULL;

CREATE OR REPLACE FUNCTION sync_alerts_columns()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.title IS NOT NULL AND NEW.alert_title IS NULL THEN
        NEW.alert_title := NEW.title;
    END IF;
    IF NEW.alert_title IS NOT NULL AND NEW.title IS NULL THEN
        NEW.title := NEW.alert_title;
    END IF;
    IF NEW.message IS NOT NULL AND NEW.rationale_summary IS NULL THEN
        NEW.rationale_summary := NEW.message;
    END IF;
    IF NEW.rationale_summary IS NOT NULL AND NEW.message IS NULL THEN
        NEW.message := NEW.rationale_summary;
    END IF;
    IF NEW.target_depth_m IS NULL THEN
        NEW.target_depth_m := COALESCE(NEW.current_depth_m + 14.0, 2860.0);
    END IF;
    IF NEW.delta_ahead_m IS NULL THEN
        NEW.delta_ahead_m := 14.0;
    END IF;
    IF NEW.source_citation IS NULL THEN
        NEW.source_citation := 'WCR-OIL-DEMO-018';
    END IF;
    IF NEW.playbook_recommendation IS NULL THEN
        NEW.playbook_recommendation := 'Spot 30 bbl walnut shell LCM pill.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sync_alerts ON public.alerts;
CREATE TRIGGER trg_sync_alerts
BEFORE INSERT OR UPDATE ON public.alerts
FOR EACH ROW EXECUTE FUNCTION sync_alerts_columns();
