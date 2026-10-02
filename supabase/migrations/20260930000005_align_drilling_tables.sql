-- Migration 005: Align drilling_parameters and add auxiliary drilling tables
-- PetroNexus Schema Alignment

-- 1. Align drilling_parameters with backend models
ALTER TABLE public.drilling_parameters
ADD COLUMN IF NOT EXISTS timestamp TIMESTAMPTZ DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS depth_md_m DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS depth_tvd_m DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS wob_ton DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS standpipe_pressure_psi DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS hook_load_ton DOUBLE PRECISION;

UPDATE public.drilling_parameters
SET timestamp = COALESCE(timestamp, created_at),
    depth_md_m = COALESCE(depth_md_m, depth_m),
    wob_ton = COALESCE(wob_ton, wob_klbf / 2.20462),
    standpipe_pressure_psi = COALESCE(standpipe_pressure_psi, spp_psi);

CREATE INDEX IF NOT EXISTS idx_drilling_parameters_timestamp ON public.drilling_parameters(timestamp);
CREATE INDEX IF NOT EXISTS idx_drilling_parameters_depth_md ON public.drilling_parameters(depth_md_m);

-- 2. Mud Properties
CREATE TABLE IF NOT EXISTS public.mud_properties (
    id SERIAL PRIMARY KEY,
    well_id INT NOT NULL REFERENCES public.wells(id) ON DELETE CASCADE,
    depth_m DOUBLE PRECISION NOT NULL,
    mud_type TEXT DEFAULT 'Water-Based Polymer Mud (WBM)',
    mud_weight_sg DOUBLE PRECISION DEFAULT 1.22,
    plastic_viscosity_cp DOUBLE PRECISION DEFAULT 18.0,
    yield_point_pa DOUBLE PRECISION DEFAULT 14.0,
    gel_strength_10s DOUBLE PRECISION DEFAULT 6.0,
    gel_strength_10m DOUBLE PRECISION DEFAULT 12.0,
    ph DOUBLE PRECISION DEFAULT 9.5,
    fluid_loss_ml DOUBLE PRECISION DEFAULT 5.2,
    solids_pct DOUBLE PRECISION DEFAULT 7.0,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_mud_properties_well ON public.mud_properties(well_id);

-- 3. BHA Records
CREATE TABLE IF NOT EXISTS public.bha_records (
    id SERIAL PRIMARY KEY,
    well_id INT NOT NULL REFERENCES public.wells(id) ON DELETE CASCADE,
    run_number INT DEFAULT 1,
    bit_size_in DOUBLE PRECISION DEFAULT 8.5,
    bit_type TEXT DEFAULT 'PDC 5-Blade Matrix Body',
    depth_in_m DOUBLE PRECISION DEFAULT 2100.0,
    depth_out_m DOUBLE PRECISION DEFAULT 2846.0,
    total_hours DOUBLE PRECISION DEFAULT 52.5,
    bha_description TEXT DEFAULT 'Bit + RSS + MWD/LWD + Stabilizer + Drill Collars + HWDP',
    components_json JSONB DEFAULT '[]'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_bha_records_well ON public.bha_records(well_id);

-- 4. Casing Records
CREATE TABLE IF NOT EXISTS public.casing_records (
    id SERIAL PRIMARY KEY,
    well_id INT NOT NULL REFERENCES public.wells(id) ON DELETE CASCADE,
    casing_string TEXT DEFAULT 'Intermediate Casing',
    outer_diameter_in DOUBLE PRECISION DEFAULT 9.625,
    weight_ppf DOUBLE PRECISION DEFAULT 40.0,
    grade TEXT DEFAULT 'L-80',
    shoe_depth_md_m DOUBLE PRECISION DEFAULT 2150.0,
    shoe_depth_tvd_m DOUBLE PRECISION DEFAULT 2080.0,
    hole_size_in DOUBLE PRECISION DEFAULT 12.25,
    date_set TEXT DEFAULT '2026-01-28'
);
CREATE INDEX IF NOT EXISTS idx_casing_records_well ON public.casing_records(well_id);

-- 5. Cementing Records
CREATE TABLE IF NOT EXISTS public.cementing_records (
    id SERIAL PRIMARY KEY,
    well_id INT NOT NULL REFERENCES public.wells(id) ON DELETE CASCADE,
    casing_string TEXT DEFAULT 'Intermediate 9-5/8 in',
    slurry_type TEXT DEFAULT 'Class G + 35% Silica Flour + Extender',
    slurry_density_sg DOUBLE PRECISION DEFAULT 1.58,
    top_of_cement_m DOUBLE PRECISION DEFAULT 1200.0,
    pumped_volume_bbl DOUBLE PRECISION DEFAULT 320.0,
    return_volume_bbl DOUBLE PRECISION DEFAULT 315.0,
    is_successful BOOLEAN DEFAULT TRUE,
    notes TEXT
);
CREATE INDEX IF NOT EXISTS idx_cementing_records_well ON public.cementing_records(well_id);

-- 6. Reservoir Data
CREATE TABLE IF NOT EXISTS public.reservoir_data (
    id SERIAL PRIMARY KEY,
    well_id INT NOT NULL REFERENCES public.wells(id) ON DELETE CASCADE,
    formation_name TEXT DEFAULT 'Formation-X',
    top_m DOUBLE PRECISION DEFAULT 2810.0,
    bottom_m DOUBLE PRECISION DEFAULT 2940.0,
    porosity_pct DOUBLE PRECISION DEFAULT 19.5,
    permeability_md DOUBLE PRECISION DEFAULT 85.0,
    initial_pressure_psi DOUBLE PRECISION DEFAULT 3820.0,
    fluid_type TEXT DEFAULT 'Light Crude / Gas Cap'
);
CREATE INDEX IF NOT EXISTS idx_reservoir_data_well ON public.reservoir_data(well_id);
