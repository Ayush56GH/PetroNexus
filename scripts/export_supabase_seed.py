"""
Generate supabase/seed.sql containing synthetic demonstration data.
"""
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

wells_file = DATA_DIR / "demo_wells.json"
events_file = DATA_DIR / "demo_events.json"

with open(wells_file, "r") as f:
    wells = json.load(f)

with open(events_file, "r") as f:
    events = json.load(f)

out_sql = BASE_DIR / "supabase" / "seed.sql"

lines = [
    "-- =============================================================================",
    "-- PetroNexus Synthetic Demonstration Seed Data (SIH26121)",
    "-- Oil India Limited (OIL) Demonstration Dataset",
    "-- NOTE: ALL DATA IS SYNTHETIC FOR EVALUATION PURPOSES. NO CONFIDENTIAL DATA.",
    "-- =============================================================================",
    "",
    "-- 1. Default Organization",
    "INSERT INTO public.organizations (id, name, slug) VALUES",
    "('00000000-0000-0000-0000-000000000001', 'Oil India Limited (OIL)', 'oil-india')",
    "ON CONFLICT (id) DO NOTHING;",
    "",
    "-- 2. Demo Wells",
]

for w in wells:
    name = w["well_name"]
    code = w.get("well_code", name)
    field = w.get("field", "Duliajan Basin").replace("'", "''")
    operator = w.get("operator", "Oil India Limited (OIL)").replace("'", "''")
    lat = w["latitude"]
    lon = w["longitude"]
    elev = w.get("elevation_m", 112.5)
    spud = w.get("spud_date", "2026-01-15")
    status = w.get("status", "OFFSET_REFERENCE")
    wtype = w.get("well_type", "DEVELOPMENT_DIRECTIONAL")
    target = w.get("target_depth_m", 3200.0)
    current = w.get("current_depth_m", 2846.0)
    form = w.get("current_formation", "Formation-X").replace("'", "''")
    is_act = "TRUE" if w.get("is_active_well", False) else "FALSE"
    vis = "DEMO"

    lines.append(
        f"INSERT INTO public.wells (id, well_name, well_code, field, operator, latitude, longitude, elevation_m, spud_date, status, well_type, target_depth_m, current_depth_m, current_formation, is_active_well, visibility) "
        f"VALUES ({w['id']}, '{name}', '{code}', '{field}', '{operator}', {lat}, {lon}, {elev}, '{spud}', '{status}', '{wtype}', {target}, {current}, '{form}', {is_act}, '{vis}') "
        f"ON CONFLICT (well_name) DO UPDATE SET latitude=EXCLUDED.latitude, longitude=EXCLUDED.longitude;"
    )

lines.append("")
lines.append("-- Reset wells sequence")
lines.append("SELECT setval('wells_id_seq', (SELECT MAX(id) FROM public.wells));")
lines.append("")
lines.append("-- 3. Demo Historical Drilling Events")

for idx, ev in enumerate(events[:100], 1): # Seed initial 100 historical incidents
    wid = ev["well_id"]
    etype = ev["event_type"]
    md = ev["depth_md_m"]
    tvd = ev.get("depth_tvd_m", md)
    fname = ev["formation_name"].replace("'", "''")
    sev = ev.get("severity", "MEDIUM")
    cause = (ev.get("primary_cause") or "Permeable micro-fractured sand").replace("'", "''")
    mit = (ev.get("immediate_mitigation") or "Circulated LCM pill and throttled flow rate").replace("'", "''")
    rec = (ev.get("preventative_recommendation") or "Review offset fracture gradient before drilling ahead").replace("'", "''")
    sdoc = (ev.get("source_document_name") or f"WCR-OIL-DEMO-{wid:03d}.pdf").replace("'", "''")
    spg = ev.get("source_page_number", 37)

    lines.append(
        f"INSERT INTO public.drilling_events (well_id, event_type, depth_md_m, depth_tvd_m, formation_name, severity, primary_cause, immediate_mitigation, preventative_recommendation, source_document_name, source_page_number) "
        f"VALUES ({wid}, '{etype}', {md}, {tvd}, '{fname}', '{sev}', '{cause}', '{mit}', '{rec}', '{sdoc}', {spg});"
    )

with open(out_sql, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Generated {out_sql} successfully with {len(wells)} wells and {min(100, len(events))} events.")
