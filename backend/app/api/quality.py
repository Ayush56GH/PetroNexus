from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.well import Well
from backend.app.ingestion.completeness_checker import CompletenessChecker

router = APIRouter(prefix="/data-quality", tags=["Data Quality"])

@router.get("")
def get_data_quality(well_id: Optional[int] = None, db: Session = Depends(get_db)):
    if well_id:
        well = db.query(Well).filter(Well.id == well_id).first()
    else:
        well = db.query(Well).filter(Well.is_active_well == True).first()
        if not well:
            well = db.query(Well).filter(Well.well_name == "OIL-DEMO-023").first()
        if not well:
            well = db.query(Well).first()

    if not well:
        raise HTTPException(status_code=404, detail="Well not found")

    profile_data = {
        "well_name": well.well_name,
        "latitude": well.latitude,
        "longitude": well.longitude,
        "current_depth_m": well.current_depth_m,
        "current_formation": well.current_formation,
        "has_trajectory": len(well.trajectories) > 0,
        "rop": 14.5,
        "wob": 12.0,
        "rpm": 110.0,
        "torque": 16.8,
        "ecd": 1.28,
        "mud_weight": 1.22,
        "bha": "8-1/2 in PDC + RSS assembly"
    }

    comp = CompletenessChecker.evaluate_profile(profile_data)
    return {
        "well_id": well.id,
        "well_name": well.well_name,
        "readiness_score": comp["readiness_score"],
        "breakdown": comp["readiness_breakdown"],
        "critical_missing": comp["critical_missing"],
        "recommended_missing": comp["recommended_missing"],
        "optional_missing": comp["optional_missing"],
        "next_actions": comp["next_best_actions"]
    }
