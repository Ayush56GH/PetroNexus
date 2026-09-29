"""
PetroNexus Memory Gap Detector
Flags gaps, missing data fields, and blind spots in offset well institutional memory
so the drilling engineer knows where historical context is incomplete.
"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.well import Well
from backend.app.models.drilling import MudProperty, CasingRecord, CementingRecord
from backend.app.models.trajectory import WellTrajectory

class MemoryGapDetector:

    @staticmethod
    def detect_gaps(
        db: Session,
        comparable_wells: List[Dict[str, Any]],
        current_formation: str,
        current_depth_m: float
    ) -> List[Dict[str, Any]]:
        """
        Inspects available offset wells in the current formation interval to identify missing records.
        """
        gaps = []
        if not comparable_wells:
            return [{
                "title": f"No Technical Offset Wells in {current_formation}",
                "severity": "HIGH",
                "formation": current_formation,
                "interval_m": f"{int(current_depth_m - 50)}–{int(current_depth_m + 150)} m",
                "description": "Zero offset wells meet high technical comparability criteria in this formation.",
                "missing_items": ["All offset well telemetry", "Offset mud programs", "Offset trajectory data"],
                "recommendation": "Expand search radius or use analog field reservoir profiles."
            }]

        well_ids = [cw["well_id"] for cw in comparable_wells]
        well_names = [cw["well_name"] for cw in comparable_wells]

        # 1. Check mud program coverage
        wells_with_mud = db.query(MudProperty.well_id).filter(MudProperty.well_id.in_(well_ids)).distinct().all()
        mud_ids = [w[0] for w in wells_with_mud]
        missing_mud_wells = [name for w_id, name in zip(well_ids, well_names) if w_id not in mud_ids]
        if missing_mud_wells:
            gaps.append({
                "title": f"Missing Mud Program in {len(missing_mud_wells)} Offset Well(s)",
                "severity": "MODERATE",
                "formation": current_formation,
                "interval_m": f"{int(current_depth_m - 50)}–{int(current_depth_m + 150)} m",
                "description": f"Historical rheology and mud weight logs missing for {', '.join(missing_mud_wells)}.",
                "missing_items": [f"Daily mud report for {w}" for w in missing_mud_wells],
                "recommendation": "Review physical mud logs or verify with cementing / fluids specialist before entering suspected loss zones."
            })

        # 2. Check trajectory / survey coverage
        wells_with_traj = db.query(WellTrajectory.well_id).filter(WellTrajectory.well_id.in_(well_ids)).distinct().all()
        traj_ids = [w[0] for w in wells_with_traj]
        missing_traj_wells = [name for w_id, name in zip(well_ids, well_names) if w_id not in traj_ids]
        if missing_traj_wells:
            gaps.append({
                "title": f"Directional Survey Missing for {len(missing_traj_wells)} Well(s)",
                "severity": "LOW",
                "formation": current_formation,
                "interval_m": f"{int(current_depth_m - 50)}–{int(current_depth_m + 150)} m",
                "description": f"No high-resolution directional stations found for {', '.join(missing_traj_wells)}; correlation relies on measured depth (MD).",
                "missing_items": [f"Directional survey stations for {w}" for w in missing_traj_wells],
                "recommendation": "TVD/TVDSS correlation unavailable for these offsets. Avoid assuming true stratigraphic thickness matches raw MD."
            })

        # 3. Check cementing records
        wells_with_cement = db.query(CementingRecord.well_id).filter(CementingRecord.well_id.in_(well_ids)).distinct().all()
        cement_ids = [w[0] for w in wells_with_cement]
        missing_cement = [name for w_id, name in zip(well_ids, well_names) if w_id not in cement_ids]
        if len(missing_cement) == len(well_ids):
            gaps.append({
                "title": "Offset Cementing & Slurry Density Records Unavailable",
                "severity": "LOW",
                "formation": current_formation,
                "interval_m": f"{int(current_depth_m - 50)}–{int(current_depth_m + 150)} m",
                "description": "No documented offset cementing records found in database for this interval.",
                "missing_items": ["Slurry density logs", "Top of cement (TOC) verifications"],
                "recommendation": "Rely on regional OIL casing & cementing standard guidelines."
            })

        return gaps
