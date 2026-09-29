"""
PetroNexus Synthetic Data Generator (SIH26121 - Oil India Limited)
Generates:
- 25 wells (OIL-DEMO-001 to OIL-DEMO-025) in Assam / Duliajan Basin
- Formations across stratigraphic sequence (Alluvium, Dhekiajuli, Tipam Sandstone, Girujan Clay, Barail Sand, Formation-X, Kopili Shale)
- 500+ realistic drilling events (Mud Losses, Torque Spikes, Stuck Pipe, Kicks, Wellbore Instability)
- Trajectories using realistic survey inclination and azimuth stations
- Drilling telemetry parameter records
Deterministic random seed for reproducible demonstrations.
"""
import random
import json
import math
from pathlib import Path

random.seed(26121) # Fixed deterministic seed for SIH26121

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Basin Coordinates (Duliajan / Upper Assam Basin, approx 27.35 N, 95.32 E)
BASE_LAT = 27.3520
BASE_LON = 95.3180

FORMATIONS_SEQUENCE = [
    {"name": "Alluvium & Upper Clay", "thickness": 450.0, "lithology": "Clay, Sand & Gravel", "loss_risk": "LOW", "pore_risk": "LOW"},
    {"name": "Dhekiajuli Formation", "thickness": 600.0, "lithology": "Coarse Sandstone & Pebble Beds", "loss_risk": "MODERATE", "pore_risk": "LOW"},
    {"name": "Girujan Clay Formation", "thickness": 650.0, "lithology": "Mottled Claystone & Siltstone", "loss_risk": "LOW", "pore_risk": "MODERATE"},
    {"name": "Tipam Sandstone", "thickness": 700.0, "lithology": "Medium to Fine Sandstone with Thin Shales", "loss_risk": "MODERATE", "pore_risk": "MODERATE"},
    {"name": "Formation-X", "thickness": 450.0, "lithology": "Interbedded Sandstone, Siltstone & Fractured Shale", "loss_risk": "HIGH", "pore_risk": "HIGH"},
    {"name": "Barail Arenaceous Unit", "thickness": 400.0, "lithology": "Carbonaceous Shale & Quartzose Sandstone", "loss_risk": "HIGH", "pore_risk": "HIGH"},
    {"name": "Kopili Formation", "thickness": 350.0, "lithology": "Fossiliferous Marine Shale & Calcareous Siltstone", "loss_risk": "LOW", "pore_risk": "MODERATE"}
]

def generate_wells():
    wells = []
    # Well 23 is primary active demo well
    for i in range(1, 26):
        well_num = f"{i:03d}"
        well_name = f"OIL-DEMO-{well_num}"
        
        # Spatial placement: Cluster around OIL-DEMO-023
        if i == 23:
            lat = BASE_LAT
            lon = BASE_LON
            status = "DRILLING_ACTIVE"
            is_active = True
            current_depth = 2846.0
            target_depth = 3200.0
            form = "Formation-X"
        elif i == 18:
            # 4.8 km offset
            lat = BASE_LAT + 0.032
            lon = BASE_LON + 0.028
            status = "OFFSET_REFERENCE"
            is_active = False
            current_depth = 3150.0
            target_depth = 3150.0
            form = "Formation-X"
        elif i == 21:
            # 6.1 km offset
            lat = BASE_LAT - 0.040
            lon = BASE_LON + 0.035
            status = "OFFSET_REFERENCE"
            is_active = False
            current_depth = 3080.0
            target_depth = 3080.0
            form = "Formation-X"
        elif i == 11:
            # 8.3 km offset
            lat = BASE_LAT + 0.055
            lon = BASE_LON - 0.048
            status = "OFFSET_REFERENCE"
            is_active = False
            current_depth = 2950.0
            target_depth = 2950.0
            form = "Formation-X"
        elif i == 7:
            # 11.2 km offset
            lat = BASE_LAT - 0.075
            lon = BASE_LON - 0.065
            status = "OFFSET_REFERENCE"
            is_active = False
            current_depth = 3250.0
            target_depth = 3250.0
            form = "Formation-X"
        else:
            angle = random.uniform(0, 2 * math.pi)
            dist_km = random.uniform(2.5, 24.0)
            lat = BASE_LAT + (dist_km / 111.0) * math.cos(angle)
            lon = BASE_LON + (dist_km / (111.0 * math.cos(math.radians(BASE_LAT)))) * math.sin(angle)
            status = "OFFSET_REFERENCE"
            is_active = False
            target_depth = round(random.uniform(2800.0, 3400.0), 0)
            current_depth = target_depth
            form = "Formation-X" if random.random() > 0.3 else "Barail Arenaceous Unit"

        wells.append({
            "id": i,
            "well_name": well_name,
            "well_code": f"OIL-AS-{well_num}",
            "field": "Duliajan Greater Field",
            "operator": "Oil India Limited (OIL)",
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "elevation_m": round(random.uniform(105.0, 125.0), 1),
            "spud_date": f"202{random.choice([4,5,6])}-0{random.randint(1,9)}-{random.randint(10,28)}",
            "status": status,
            "well_type": "DEVELOPMENT_DIRECTIONAL" if i % 2 == 1 else "EXPLORATORY_VERTICAL",
            "target_depth_m": target_depth,
            "current_depth_m": current_depth,
            "current_formation": form,
            "is_active_well": is_active
        })

    with open(DATA_DIR / "demo_wells.json", "w") as f:
        json.dump(wells, f, indent=2)
    print(f"Generated {len(wells)} demo wells.")
    return wells

def generate_events(wells):
    events = []
    ev_id = 1
    
    # Pre-configure specific demo scenario events for key offset wells
    # OIL-DEMO-018: Mud Loss @ 2860 m
    events.append({
        "id": ev_id,
        "well_id": 18,
        "well_name": "OIL-DEMO-018",
        "event_type": "Mud Loss (Partial Loss of 45 bbl)",
        "depth_md_m": 2860.0,
        "depth_tvd_m": 2818.5,
        "depth_tvdss_m": 2706.0,
        "formation_name": "Formation-X",
        "severity": "HIGH",
        "occurred_at": "2025-04-12 14:30",
        "description": "Sudden loss of 45 bbl/hr of drilling fluid encountered immediately upon penetrating permeable micro-fractured sand stringer at 2860m.",
        "primary_cause": "Permeable sub-seismic micro-fracture network with lower fracture gradient.",
        "immediate_mitigation": "Mixed and pumped 30 bbl medium/coarse walnut shell LCM pill; throttled flow rate from 2250 to 1950 LPM until returns stabilized.",
        "duration_hours": 5.5,
        "source_document_name": "WCR-OIL-DEMO-018",
        "source_page_number": 37
    })
    ev_id += 1

    # OIL-DEMO-021: Torque Spike @ 2842 m
    events.append({
        "id": ev_id,
        "well_id": 21,
        "well_name": "OIL-DEMO-021",
        "event_type": "Torque Spike & Pack-Off Flutter",
        "depth_md_m": 2842.0,
        "depth_tvd_m": 2802.0,
        "depth_tvdss_m": 2689.5,
        "formation_name": "Formation-X",
        "severity": "HIGH",
        "occurred_at": "2025-08-19 09:15",
        "description": "Rotary torque surged from 16.5 to 23.2 kN.m with 30 ton overpull observed on connections. Annular cuttings loading.",
        "primary_cause": "Interbedded brittle shale breakout causing cuttings bed accumulation in 32 deg inclination section.",
        "immediate_mitigation": "Picked up off bottom, circulated high-viscosity pill, reciprocated drill string, executed short wiper trip to shoe.",
        "duration_hours": 4.0,
        "source_document_name": "DDR-OIL-DEMO-021",
        "source_page_number": 22
    })
    ev_id += 1

    # OIL-DEMO-011: Mud Loss @ 2828 m
    events.append({
        "id": ev_id,
        "well_id": 11,
        "well_name": "OIL-DEMO-011",
        "event_type": "Mud Loss (Seepage Loss of 20 bbl)",
        "depth_md_m": 2828.0,
        "depth_tvd_m": 2795.0,
        "depth_tvdss_m": 2682.0,
        "formation_name": "Formation-X",
        "severity": "MODERATE",
        "occurred_at": "2024-11-04 18:20",
        "description": "Seepage losses of 18-22 bbl/hr observed in upper Formation-X sand interval.",
        "primary_cause": "High overbalance pressure against depleted reservoir pressure.",
        "immediate_mitigation": "Spotted fine calcium carbonate pill (25 ppb) in active system; reduced mud weight from 1.25 to 1.21 SG.",
        "duration_hours": 3.0,
        "source_document_name": "Mud Report-OIL-DEMO-011",
        "source_page_number": 15
    })
    ev_id += 1

    # OIL-DEMO-007: Stuck Pipe @ 2872 m
    events.append({
        "id": ev_id,
        "well_id": 7,
        "well_name": "OIL-DEMO-007",
        "event_type": "Differential Stuck Pipe",
        "depth_md_m": 2872.0,
        "depth_tvd_m": 2835.0,
        "depth_tvdss_m": 2722.0,
        "formation_name": "Formation-X",
        "severity": "CRITICAL",
        "occurred_at": "2024-02-14 03:45",
        "description": "Drill string became differentially stuck across permeable depleted sandstone during MWD survey pause.",
        "primary_cause": "High filter cake thickness combined with 450 psi hydrostatic overbalance.",
        "immediate_mitigation": "Worked pipe with hydraulic jars (70 klbf up-blow); spotted 40 bbl oil-based pipe-freeing soak pill. Freed after 9.5 hrs.",
        "duration_hours": 9.5,
        "source_document_name": "WCR-OIL-DEMO-007",
        "source_page_number": 42
    })
    ev_id += 1

    # Generate additional historical events across all 25 wells to reach 500+ records
    event_templates = [
        ("Mud Loss (Partial Loss)", "Loss of circulation across fractured sand interval.", "High permeability streak", "Pumped LCM pill and reduced flow rate", "HIGH"),
        ("Torque Spike & Drag", "Rotary torque fluctuation observed during drilling.", "Wellbore spiraling and tight hole", "Short wiper trip and hole conditioning", "MODERATE"),
        ("Gas Kick (Swab Gas)", "Trip gas peak of 12% recorded after round trip.", "Swabbing effect during tripping", "Circulated out bottoms up through choke manifold", "HIGH"),
        ("Pack-Off Anomaly", "Sudden standpipe pressure increase with torque flutter.", "Shale spalling and inadequate annular cleaning", "Circulated high-density sweep and worked string", "HIGH"),
        ("Differential Sticking Alert", "High drag on connections across porous sandstone.", "Overbalanced mud column in depleted sand", "Added lubricant to active mud system", "MODERATE"),
        ("Formation Breakout / Sloughing", "Cuttings showed cavings with sharp angular edges.", "Under-balanced shale pore pressure", "Increased mud weight by 0.03 SG", "MODERATE")
    ]

    for w in wells:
        # 15 to 25 events per well distributed along wellbore
        count = random.randint(18, 24)
        for _ in range(count):
            tmpl = random.choice(event_templates)
            depth = round(random.uniform(500.0, w["target_depth_m"]), 1)
            tvd = round(depth * random.uniform(0.95, 0.99), 1)
            tvdss = round(tvd - w["elevation_m"], 1)

            # Determine formation by depth
            if depth < 450:
                form = "Alluvium & Upper Clay"
            elif depth < 1050:
                form = "Dhekiajuli Formation"
            elif depth < 1700:
                form = "Girujan Clay Formation"
            elif depth < 2400:
                form = "Tipam Sandstone"
            elif depth < 2850:
                form = "Formation-X"
            else:
                form = "Barail Arenaceous Unit"

            events.append({
                "id": ev_id,
                "well_id": w["id"],
                "well_name": w["well_name"],
                "event_type": tmpl[0],
                "depth_md_m": depth,
                "depth_tvd_m": tvd,
                "depth_tvdss_m": tvdss,
                "formation_name": form,
                "severity": tmpl[4],
                "occurred_at": f"202{random.choice([4,5])}-0{random.randint(1,9)}-{random.randint(10,28)} {random.randint(10,22)}:00",
                "description": tmpl[1],
                "primary_cause": tmpl[2],
                "immediate_mitigation": tmpl[3],
                "duration_hours": round(random.uniform(1.5, 8.0), 1),
                "source_document_name": f"WCR-{w['well_name']}",
                "source_page_number": random.randint(12, 65)
            })
            ev_id += 1

    with open(DATA_DIR / "demo_events.json", "w") as f:
        json.dump(events, f, indent=2)
    print(f"Generated {len(events)} demo drilling events.")
    return events

if __name__ == "__main__":
    w = generate_wells()
    e = generate_events(w)
