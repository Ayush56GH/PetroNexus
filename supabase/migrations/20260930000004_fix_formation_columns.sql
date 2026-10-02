-- Add compatibility columns to formation_intervals and formations
ALTER TABLE public.formation_intervals 
ADD COLUMN IF NOT EXISTS top_depth_tvd_m DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS bottom_depth_tvd_m DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS thickness_m DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS reservoir_unit TEXT,
ADD COLUMN IF NOT EXISTS comments TEXT;

-- Synchronize top_depth_tvd_m with top_tvd_m if present
UPDATE public.formation_intervals 
SET top_depth_tvd_m = COALESCE(top_depth_tvd_m, top_tvd_m),
    bottom_depth_tvd_m = COALESCE(bottom_depth_tvd_m, bottom_tvd_m);

ALTER TABLE public.formations
ADD COLUMN IF NOT EXISTS formation_name TEXT,
ADD COLUMN IF NOT EXISTS age TEXT DEFAULT 'Oligocene / Miocene',
ADD COLUMN IF NOT EXISTS lithology TEXT DEFAULT 'Interbedded Sandstone, Siltstone & Shale',
ADD COLUMN IF NOT EXISTS description TEXT,
ADD COLUMN IF NOT EXISTS typical_overpressure_risk TEXT DEFAULT 'MODERATE',
ADD COLUMN IF NOT EXISTS typical_loss_risk TEXT DEFAULT 'HIGH';

UPDATE public.formations
SET formation_name = COALESCE(formation_name, name);
