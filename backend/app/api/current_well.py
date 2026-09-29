import shutil
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models.well import Well, WellUploadSession
from backend.app.models.drilling import DrillingParameter
from backend.app.models.audit import AuditLog
from backend.app.ingestion.file_analyzer import FileAnalyzer
from backend.app.ingestion.completeness_checker import CompletenessChecker
from backend.app.ingestion.profile_merger import ProfileMerger
from backend.app.schemas.well import CompletenessCheckResponse

router = APIRouter(prefix="/current-well", tags=["Current Well Intelligence"])

@router.post("/upload")
async def upload_current_well_file(
    file: UploadFile = File(...),
    well_id: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    # Save file to uploads folder
    upload_path = settings.UPLOAD_DIR / file.filename
    with open(upload_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Detect & extract structured parameters
    extracted_fields = FileAnalyzer.analyze_file(upload_path)

    # Target active well
    if well_id:
        well = db.query(Well).filter(Well.id == well_id).first()
    else:
        # Check active well or primary demo well OIL-DEMO-023
        well = db.query(Well).filter(Well.is_active_well == True).first()
        if not well:
            well = db.query(Well).filter(Well.well_name == "OIL-DEMO-023").first()
        if not well:
            well = db.query(Well).first()

    if not well:
        raise HTTPException(status_code=404, detail="No active well found to update.")

    # Merge extracted fields into active well profile
    ext = upload_path.suffix.upper().replace(".", "")
    ProfileMerger.merge_into_well(db, well, extracted_fields, file_name=file.filename, file_type=ext)

    # Assemble comprehensive current well profile for completeness check
    current_profile = {
        "well_name": well.well_name,
        "latitude": well.latitude,
        "longitude": well.longitude,
        "current_depth_m": well.current_depth_m,
        "current_formation": well.current_formation,
        "has_trajectory": bool(well.trajectories),
        "survey_stations": extracted_fields.get("survey_stations"),
        "bha": extracted_fields.get("bha"),
        "mud_weight": extracted_fields.get("mud_weight"),
        "rop": extracted_fields.get("rop", 14.5),
        "wob": extracted_fields.get("wob", 12.0),
        "rpm": extracted_fields.get("rpm", 110.0),
        "torque": extracted_fields.get("torque", 16.8),
        "ecd": extracted_fields.get("ecd", 1.28),
        "spp": extracted_fields.get("spp", 2450.0),
        "flow_rate": extracted_fields.get("flow_rate", 2150.0)
    }

    completeness = CompletenessChecker.evaluate_profile(current_profile)

    # Audit log
    audit = AuditLog(
        action="WELL_UPLOAD",
        resource=f"well:{well.id}",
        details={"file": file.filename, "type": ext, "readiness": completeness["readiness_score"]}
    )
    db.add(audit)
    db.commit()

    return {
        "status": "SUCCESS",
        "message": f"Successfully analyzed and integrated '{file.filename}' into active well '{well.well_name}'",
        "well_id": well.id,
        "well_name": well.well_name,
        "extracted_fields": extracted_fields,
        "completeness": completeness
    }

@router.get("/profile")
def get_current_well_profile(well_id: Optional[int] = None, db: Session = Depends(get_db)):
    if well_id:
        well = db.query(Well).filter(Well.id == well_id).first()
    else:
        well = db.query(Well).filter(Well.is_active_well == True).first()
        if not well:
            well = db.query(Well).filter(Well.well_name == "OIL-DEMO-023").first()
        if not well:
            well = db.query(Well).first()

    if not well:
        raise HTTPException(status_code=404, detail="No active well found.")

    latest_param = db.query(DrillingParameter).filter(
        DrillingParameter.well_id == well.id
    ).order_by(DrillingParameter.timestamp.desc()).first()

    recent_sessions = db.query(WellUploadSession).filter(
        WellUploadSession.well_id == well.id
    ).order_by(WellUploadSession.created_at.desc()).limit(5).all()

    profile_dict = {
        "well_id": well.id,
        "well_name": well.well_name,
        "field": well.field,
        "operator": well.operator,
        "latitude": well.latitude,
        "longitude": well.longitude,
        "elevation_m": well.elevation_m,
        "current_depth_m": well.current_depth_m,
        "current_formation": well.current_formation,
        "target_depth_m": well.target_depth_m,
        "status": well.status,
        "well_type": well.well_type,
        "latest_telemetry": {
            "rop": latest_param.rop_m_hr if latest_param else 14.5,
            "wob": latest_param.wob_ton if latest_param else 12.0,
            "rpm": latest_param.rpm if latest_param else 110.0,
            "torque": latest_param.torque_kn_m if latest_param else 16.8,
            "ecd": latest_param.ecd_sg if latest_param else 1.28,
            "mud_weight": latest_param.mud_weight_sg if latest_param else 1.22,
            "spp": latest_param.standpipe_pressure_psi if latest_param else 2450.0,
            "flow_rate": latest_param.flow_rate_lpm if latest_param else 2150.0,
            "mse_mpa": latest_param.mse_mpa if latest_param else 210.0
        },
        "trajectories_count": len(well.trajectories),
        "upload_sessions": [
            {
                "id": s.id,
                "file_name": s.file_name,
                "file_type": s.file_type,
                "quality_score": s.quality_score,
                "created_at": s.created_at.strftime("%Y-%m-%d %H:%M:%S")
            } for s in recent_sessions
        ]
    }

    # Evaluate completeness
    comp_input = {
        "well_name": well.well_name,
        "latitude": well.latitude,
        "longitude": well.longitude,
        "current_depth_m": well.current_depth_m,
        "current_formation": well.current_formation,
        "has_trajectory": len(well.trajectories) > 0,
        "rop": latest_param.rop_m_hr if latest_param else 14.5,
        "wob": latest_param.wob_ton if latest_param else 12.0,
        "rpm": latest_param.rpm if latest_param else 110.0,
        "torque": latest_param.torque_kn_m if latest_param else 16.8,
        "ecd": latest_param.ecd_sg if latest_param else 1.28,
        "mud_weight": latest_param.mud_weight_sg if latest_param else 1.22,
        "bha": "8-1/2 in PDC + RSS assembly"
    }
    profile_dict["completeness"] = CompletenessChecker.evaluate_profile(comp_input)

    return profile_dict

@router.get("/completeness", response_model=CompletenessCheckResponse)
def get_completeness(well_id: Optional[int] = None, db: Session = Depends(get_db)):
    profile = get_current_well_profile(well_id, db)
    comp = profile["completeness"]

    return CompletenessCheckResponse(
        well_id=profile["well_id"],
        well_name=profile["well_name"],
        readiness_score=comp["readiness_score"],
        readiness_breakdown=comp["readiness_breakdown"],
        critical_missing=comp["critical_missing"],
        recommended_missing=comp["recommended_missing"],
        optional_missing=comp["optional_missing"],
        next_best_actions=comp["next_best_actions"],
        extracted_summary={
            "Depth": f"{profile['current_depth_m']} m MD",
            "Formation": profile['current_formation'],
            "Coordinates": f"{profile['latitude']}, {profile['longitude']}",
            "Status": profile['status']
        }
    )

@router.get("/missing-data")
def get_missing_data_report(well_id: Optional[int] = None, db: Session = Depends(get_db)):
    profile = get_current_well_profile(well_id, db)
    comp = profile["completeness"]
    return {
        "well_name": profile["well_name"],
        "readiness_score": comp["readiness_score"],
        "critical": comp["critical_missing"],
        "recommended": comp["recommended_missing"],
        "optional": comp["optional_missing"],
        "next_actions": comp["next_best_actions"]
    }

@router.post("/demo-ingest")
def demo_ingest_file(payload: dict, db: Session = Depends(get_db)):
    demo_type = payload.get("demo_type", "pdf")
    file_map = {
        "pdf": ("Current_Well_Report_OIL-DEMO-023.pdf", "PDF_REPORT"),
        "csv": ("Current_Well_Telemetry_OIL-DEMO-023.csv", "TELEMETRY_CSV"),
        "survey": ("OIL-DEMO-023_Directional_Survey.csv", "DIRECTIONAL_SURVEY"),
        "las": ("Current_Well_Log_OIL-DEMO-023.las", "PETROPHYSICAL_LAS")
    }
    if demo_type not in file_map:
        raise HTTPException(status_code=400, detail="Invalid demo type")

    file_name, file_category = file_map[demo_type]
    file_path = settings.DOCUMENTS_DIR / file_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Demo file {file_name} not found.")

    extracted = FileAnalyzer.analyze_file(file_path)
    well_id = payload.get("well_id", 23)
    well = db.query(Well).filter(Well.id == well_id).first()
    if not well:
        well = db.query(Well).filter(Well.well_name == "OIL-DEMO-023").first()
    if not well:
        well = db.query(Well).first()

    ProfileMerger.merge_into_well(db, well, extracted, file_name=file_name, file_type=file_category)

    # Calculate updated completeness
    current_profile = {
        "well_name": well.well_name,
        "latitude": well.latitude,
        "longitude": well.longitude,
        "current_depth_m": well.current_depth_m,
        "current_formation": well.current_formation,
        "has_trajectory": bool(well.trajectories),
        "survey_stations": extracted.get("survey_stations"),
        "bha": extracted.get("bha"),
        "mud_weight": extracted.get("mud_weight"),
        "rop": extracted.get("rop"),
        "wob": extracted.get("wob"),
        "rpm": extracted.get("rpm"),
        "torque": extracted.get("torque"),
        "ecd": extracted.get("ecd"),
        "events_count": len(well.events)
    }
    completeness = CompletenessChecker.evaluate_profile(current_profile)

    return {
        "status": "SUCCESS",
        "message": f"Successfully ingested demo file '{file_name}' into active well '{well.well_name}'",
        "well_id": well.id,
        "well_name": well.well_name,
        "extracted_fields": extracted,
        "completeness": completeness
    }
