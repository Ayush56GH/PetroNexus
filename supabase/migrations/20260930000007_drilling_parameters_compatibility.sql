-- Migration 007: Drilling Parameters Compatibility Constraints & Sync Trigger
ALTER TABLE public.drilling_parameters ALTER COLUMN depth_m DROP NOT NULL;
ALTER TABLE public.drilling_parameters ALTER COLUMN wob_klbf DROP NOT NULL;
ALTER TABLE public.drilling_parameters ALTER COLUMN spp_psi DROP NOT NULL;

CREATE OR REPLACE FUNCTION sync_drilling_parameters_columns()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.depth_m IS NULL THEN
        NEW.depth_m := NEW.depth_md_m;
    END IF;
    IF NEW.depth_md_m IS NULL THEN
        NEW.depth_md_m := NEW.depth_m;
    END IF;
    IF NEW.wob_klbf IS NULL AND NEW.wob_ton IS NOT NULL THEN
        NEW.wob_klbf := NEW.wob_ton * 2.20462;
    END IF;
    IF NEW.wob_ton IS NULL AND NEW.wob_klbf IS NOT NULL THEN
        NEW.wob_ton := NEW.wob_klbf / 2.20462;
    END IF;
    IF NEW.spp_psi IS NULL AND NEW.standpipe_pressure_psi IS NOT NULL THEN
        NEW.spp_psi := NEW.standpipe_pressure_psi;
    END IF;
    IF NEW.standpipe_pressure_psi IS NULL AND NEW.spp_psi IS NOT NULL THEN
        NEW.standpipe_pressure_psi := NEW.spp_psi;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sync_drilling_parameters ON public.drilling_parameters;
CREATE TRIGGER trg_sync_drilling_parameters
BEFORE INSERT OR UPDATE ON public.drilling_parameters
FOR EACH ROW EXECUTE FUNCTION sync_drilling_parameters_columns();
