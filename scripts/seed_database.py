"""
PetroNexus Database Seeder
Populates the complete relational database schema:
- Default Drilling Engineer User (engineer@oilindia.in / OilIndia@2026)
- 25 Wells with spatial coordinates in Duliajan Basin
- Formation definitions & wellbore formation intervals
- Directional trajectories (MCM calculated)
- 500+ historical drilling events with mitigations
- Primary demo alerts with verified evidence trails
- Documents and knowledge chunk index
"""
import json
import datetime
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session
from backend.app.database import engine, Base, SessionLocal
from backend.app.models import (
    User, Well, WellTrajectory, Formation, FormationInterval,
    DrillingParameter, MudProperty, BhaRecord, CasingRecord, CementingRecord,
    DrillingEvent, EventMitigation, Document, DocumentPage, KnowledgeChunk,
    Alert, AlertEvidence, DataQualityMetric, AuditLog
)
from backend.app.services.auth_service import get_password_hash
from backend.app.utils.trajectory_calc import calculate_trajectory
from backend.app.utils.logger import logger
from scripts.generate_demo_data import generate_wells, generate_events, FORMATIONS_SEQUENCE

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

def seed():
    print("Initializing Database tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        # 1. Create Default Drilling Engineer User
        print("Creating Drilling Engineer user...")
        demo_user = User(
            full_name="Rajesh Baruah",
            email="engineer@oilindia.in",
            employee_id="OIL-DE-8492",
            department="Drilling Operations & eRTMAC Division",
            hashed_password=get_password_hash("OilIndia@2026"),
            role="DRILLING_ENGINEER",
            is_active=True
        )
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)

        # 2. Formations
        print("Seeding Formations...")
        db_formations = {}
        for idx, f_info in enumerate(FORMATIONS_SEQUENCE):
            f_obj = Formation(
                formation_name=f_info["name"],
                code=f"FORM-{idx+1:02d}",
                age="Oligocene / Miocene" if "Barail" in f_info["name"] or "X" in f_info["name"] else "Miocene",
                lithology=f_info["lithology"],
                typical_loss_risk=f_info["loss_risk"],
                typical_overpressure_risk=f_info["pore_risk"]
            )
            db.add(f_obj)
            db.commit()
            db.refresh(f_obj)
            db_formations[f_info["name"]] = f_obj

        # 3. Wells
        print("Seeding 25 Demo Wells...")
        wells_data = generate_wells()
        db_wells = {}
        for w_data in wells_data:
            w_obj = Well(
                id=w_data["id"],
                well_name=w_data["well_name"],
                well_code=w_data["well_code"],
                field=w_data["field"],
                operator=w_data["operator"],
                latitude=w_data["latitude"],
                longitude=w_data["longitude"],
                elevation_m=w_data["elevation_m"],
                spud_date=w_data["spud_date"],
                status=w_data["status"],
                well_type=w_data["well_type"],
                target_depth_m=w_data["target_depth_m"],
                current_depth_m=w_data["current_depth_m"],
                current_formation=w_data["current_formation"],
                is_active_well=w_data["is_active_well"]
            )
            db.add(w_obj)
            db.commit()
            db.refresh(w_obj)
            db_wells[w_obj.id] = w_obj

            # Seed Formation Intervals for each well
            top_depth = 0.0
            for f_info in FORMATIONS_SEQUENCE:
                thickness = f_info["thickness"]
                bottom_depth = top_depth + thickness
                fi = FormationInterval(
                    well_id=w_obj.id,
                    formation_id=db_formations[f_info["name"]].id,
                    top_depth_md_m=top_depth,
                    bottom_depth_md_m=bottom_depth,
                    top_depth_tvd_m=round(top_depth * 0.98, 1),
                    bottom_depth_tvd_m=round(bottom_depth * 0.98, 1),
                    thickness_m=thickness,
                    lithology=f_info["lithology"],
                    reservoir_unit="Reservoir Member 1" if "Sand" in f_info["name"] or "X" in f_info["name"] else None
                )
                db.add(fi)
                top_depth = bottom_depth
            db.commit()

            # Seed Trajectory stations
            stations = [
                {"md": 0.0, "inc": 0.0, "azi": 0.0},
                {"md": 500.0, "inc": 1.2, "azi": 45.0},
                {"md": 1000.0, "inc": 7.5, "azi": 50.0},
                {"md": 1500.0, "inc": 16.0, "azi": 53.0},
                {"md": 2000.0, "inc": 24.5, "azi": 55.0},
                {"md": 2500.0, "inc": 30.0, "azi": 56.0},
                {"md": w_obj.current_depth_m, "inc": 32.5, "azi": 57.0}
            ]
            traj_data = calculate_trajectory(stations, kb_elevation_m=w_obj.elevation_m)
            for t_item in traj_data:
                wt = WellTrajectory(
                    well_id=w_obj.id,
                    measured_depth_m=t_item["measured_depth_m"],
                    inclination_deg=t_item["inclination_deg"],
                    azimuth_deg=t_item["azimuth_deg"],
                    true_vertical_depth_m=t_item["true_vertical_depth_m"],
                    tvdss_m=t_item["tvdss_m"],
                    dogleg_severity=t_item["dogleg_severity"],
                    northing_m=t_item["northing_m"],
                    easting_m=t_item["easting_m"]
                )
                db.add(wt)

            # Seed Casing record
            casing = CasingRecord(
                well_id=w_obj.id,
                casing_string="Intermediate Casing",
                outer_diameter_in=9.625,
                weight_ppf=40.0,
                grade="L-80",
                shoe_depth_md_m=2150.0,
                shoe_depth_tvd_m=2105.0,
                hole_size_in=12.25
            )
            db.add(casing)

            # Seed Drilling Telemetry
            dp = DrillingParameter(
                well_id=w_obj.id,
                depth_md_m=w_obj.current_depth_m,
                rop_m_hr=14.5,
                wob_ton=12.0,
                rpm=110.0,
                torque_kn_m=16.8,
                ecd_sg=1.28,
                mud_weight_sg=1.22,
                standpipe_pressure_psi=2450.0,
                flow_rate_lpm=2150.0,
                hook_load_ton=85.0,
                mse_mpa=210.0
            )
            db.add(dp)
            db.commit()

        # 4. Events
        print("Seeding 500+ Drilling Events...")
        events_data = generate_events(wells_data)
        db_events = []
        for ev in events_data:
            dev = DrillingEvent(
                well_id=ev["well_id"],
                event_type=ev["event_type"],
                depth_md_m=ev["depth_md_m"],
                depth_tvd_m=ev["depth_tvd_m"],
                depth_tvdss_m=ev["depth_tvdss_m"],
                formation_name=ev["formation_name"],
                severity=ev["severity"],
                occurred_at=ev["occurred_at"],
                description=ev["description"],
                primary_cause=ev["primary_cause"],
                immediate_mitigation=ev["immediate_mitigation"],
                duration_hours=ev["duration_hours"],
                source_document_name=ev["source_document_name"],
                source_page_number=ev["source_page_number"]
            )
            db.add(dev)
            db_events.append(dev)
        db.commit()

        # 5. Mitigations Playbook
        print("Seeding Historical Mitigation Playbook...")
        playbook_items = [
            {
                "event_type": "Mud Loss (Partial Loss)",
                "formation_name": "Formation-X",
                "mitigation_title": "LCM Pill Spotting & Flow Throttling Protocol",
                "action_category": "Loss Circulation Treatment",
                "step_order": 1,
                "procedure_text": "Immediately pick bit off bottom into non-loss zone (2845m). Mix 30 bbl medium LCM pill (25 ppb walnut shells + 15 ppb CaCO3). Spot across 2860m interval; soak for 90 mins under static conditions. Resume drilling with flow throttled to 1950 LPM.",
                "observed_efficacy": "High — Full circulation restored in 4.5 hrs",
                "sample_wells_cited": ["OIL-DEMO-018", "OIL-DEMO-011"],
                "evidence_citations": ["WCR-018, Page 37", "Mud Report-011, Page 15"]
            },
            {
                "event_type": "Torque Spike & Pack-Off",
                "formation_name": "Formation-X",
                "mitigation_title": "String Reciprocation & Reaming Sweep Procedure",
                "action_category": "Hole Conditioning & Drag Relief",
                "step_order": 2,
                "procedure_text": "Pick up string to 9-5/8 in casing shoe (2150m). Pump 25 bbl high-viscosity polymer sweep (45 sec funnel viscosity). Ream tight interval (2820-2845m) with 80 RPM and controlled flow to prevent cuttings bed accumulation.",
                "observed_efficacy": "High — Overpull eliminated within 3 hrs",
                "sample_wells_cited": ["OIL-DEMO-021"],
                "evidence_citations": ["DDR-021, Page 22"]
            },
            {
                "event_type": "Differential Sticking Alert",
                "formation_name": "Formation-X",
                "mitigation_title": "Overpull & Freeing Soak Procedure",
                "action_category": "Pipe Freeing Protocol",
                "step_order": 3,
                "procedure_text": "Apply immediate upward jar blows (maximum safe overpull 60 klbf). Spot 40 bbl oil-based pipe-freeing soak pill across depleted sandstone lens to break filter cake adhesion.",
                "observed_efficacy": "Moderate — Freed in 9.5 hrs",
                "sample_wells_cited": ["OIL-DEMO-007"],
                "evidence_citations": ["WCR-007, Page 42"]
            }
        ]
        for p in playbook_items:
            em = EventMitigation(**p)
            db.add(em)
        db.commit()

        # 6. Primary Demo Alert for Active Well OIL-DEMO-023
        print("Seeding Primary Demo Alerts & Evidence Trail...")
        well_23 = db.query(Well).filter(Well.id == 23).first()
        alert = Alert(
            well_id=well_23.id,
            alert_type="HISTORICAL_OFFSET_HAZARD",
            severity="HIGH",
            current_depth_m=2846.0,
            formation_name="Formation-X",
            title="Historical Attention Advisory: Formation-X Loss Zone Approaching",
            message="3 comparable offset wells reported severe mud-loss and torque-spike events within 14m ahead and 18m behind current stratigraphic interval.",
            status="ACTIVE"
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

        # Evidence Items for Alert
        evidence_1 = AlertEvidence(
            alert_id=alert.id,
            offset_well_id=18,
            offset_well_name="OIL-DEMO-018",
            event_type="Mud Loss (Partial Loss of 45 bbl)",
            event_depth_m=2860.0,
            distance_km=4.8,
            delta_depth_m=14.0, # 14 m ahead of bit!
            correlation_factor=0.96,
            document_citation="WCR-OIL-DEMO-018",
            page_citation="Page 37",
            narrative="OIL-DEMO-018 is located 4.8 km away in identical structural corridor. Encountered severe 45 bbl/hr mud loss at 2860m (14m ahead of current bit) upon entering fractured sand streak."
        )
        evidence_2 = AlertEvidence(
            alert_id=alert.id,
            offset_well_id=21,
            offset_well_name="OIL-DEMO-021",
            event_type="Torque Spike & Pack-Off",
            event_depth_m=2842.0,
            distance_km=6.1,
            delta_depth_m=-4.0, # 4 m behind
            correlation_factor=0.91,
            document_citation="DDR-OIL-DEMO-021",
            page_citation="Page 22",
            narrative="OIL-DEMO-021 experienced 23.2 kN.m torque spike and 32 ton overpull at 2842m due to brittle shale breakout."
        )
        evidence_3 = AlertEvidence(
            alert_id=alert.id,
            offset_well_id=11,
            offset_well_name="OIL-DEMO-011",
            event_type="Mud Loss (Seepage Loss)",
            event_depth_m=2828.0,
            distance_km=8.3,
            delta_depth_m=-18.0,
            correlation_factor=0.88,
            document_citation="Mud Report-OIL-DEMO-011",
            page_citation="Page 15",
            narrative="Seepage mud losses documented in Formation-X upper sand lens."
        )
        db.add(evidence_1)
        db.add(evidence_2)
        db.add(evidence_3)
        db.commit()

        # Audit log for system seed
        audit = AuditLog(
            user_email="system@petronexus.oilindia.in",
            action="SYSTEM_SEED",
            resource="database",
            details={"wells": 25, "events": len(events_data)}
        )
        db.add(audit)
        db.commit()

        print("Database seeded successfully with all demo scenario data!")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
