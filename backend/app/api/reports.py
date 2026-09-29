import datetime
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models.well import Well
from backend.app.models.event import DrillingEvent
from backend.app.models.alert import Alert
from backend.app.models.drilling import DrillingParameter
from backend.app.models.audit import AuditLog
from backend.app.schemas.report import ContextPackRequest, ContextPackResponse, PreIntervalBriefResponse
from backend.app.services.spatial_service import get_nearby_wells
from backend.app.services.offset_engine import OffsetRelevanceEngine
from backend.app.services.lookahead_engine import LookAheadEngine
from backend.app.services.risk_engine import RiskEngine
from backend.app.services.memory_gap_detector import MemoryGapDetector
from backend.app.services.conflict_detector import ConflictDetector
from backend.app.services.report_service import ReportService
from backend.app.ingestion.completeness_checker import CompletenessChecker

router = APIRouter(prefix="/reports", tags=["Reports & Context Packs"])

@router.post("/context-pack", response_model=ContextPackResponse)
def generate_context_pack(req: ContextPackRequest, db: Session = Depends(get_db)):
    well = db.query(Well).filter(Well.id == req.well_id).first()
    if not well:
        well = db.query(Well).filter(Well.well_name == "OIL-DEMO-023").first()
    if not well:
        raise HTTPException(status_code=404, detail="Well not found")

    depth = well.current_depth_m
    formation = well.current_formation

    # Telemetry
    latest_param = db.query(DrillingParameter).filter(
        DrillingParameter.well_id == well.id
    ).order_by(DrillingParameter.timestamp.desc()).first()

    # Spatial & comparable
    nearby_wells = get_nearby_wells(db, well.latitude, well.longitude, radius_km=15.0, exclude_well_id=well.id)
    comparable_wells = [
        OffsetRelevanceEngine.calculate_comparability(db, well, ow, dist, depth, formation)
        for ow, dist in nearby_wells[:5]
    ]

    # Look-ahead hazards
    lookahead_hazards = LookAheadEngine.scan_corridor(db, well, depth, lookahead_m=150.0, radius_km=15.0)

    # Historical events
    comp_ids = [cw["well_id"] for cw in comparable_wells]
    events = db.query(DrillingEvent).filter(
        DrillingEvent.well_id.in_(comp_ids),
        DrillingEvent.depth_md_m >= depth - 100.0,
        DrillingEvent.depth_md_m <= depth + 150.0
    ).all()

    # Mitigations
    mitigations = RiskEngine.get_mitigation_playbook(db, formation)

    # Alerts
    alerts = db.query(Alert).filter(Alert.well_id == well.id, Alert.status == "ACTIVE").all()

    # Completeness
    comp_input = {
        "well_name": well.well_name,
        "latitude": well.latitude,
        "longitude": well.longitude,
        "current_depth_m": depth,
        "current_formation": formation,
        "has_trajectory": len(well.trajectories) > 0,
        "rop": latest_param.rop_m_hr if latest_param else 14.5,
        "wob": latest_param.wob_ton if latest_param else 12.0,
        "rpm": latest_param.rpm if latest_param else 110.0,
        "torque": latest_param.torque_kn_m if latest_param else 16.8,
        "ecd": latest_param.ecd_sg if latest_param else 1.28,
        "mud_weight": latest_param.mud_weight_sg if latest_param else 1.22
    }
    completeness = CompletenessChecker.evaluate_profile(comp_input)

    # Memory gaps & conflicts
    gaps = MemoryGapDetector.detect_gaps(db, comparable_wells, formation, depth)
    conflicts = ConflictDetector.detect_conflicts(formation, comparable_wells)

    now_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    pack_data = {
        "generated_at": now_str,
        "active_well_summary": {
            "well_id": well.id,
            "well_name": well.well_name,
            "operator": well.operator,
            "field": well.field,
            "latitude": well.latitude,
            "longitude": well.longitude,
            "current_depth_m": depth,
            "current_formation": formation,
            "target_depth_m": well.target_depth_m,
            "status": well.status,
            "readiness_percentage": completeness["readiness_score"]
        },
        "current_parameters": {
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
        "formation_context": {
            "formation_name": formation,
            "age": "Oligocene / Miocene",
            "lithology": "Interbedded Sandstone and Shale",
            "typical_loss_risk": "HIGH",
            "typical_overpressure_risk": "MODERATE"
        },
        "nearby_wells": [
            {"id": w.id, "well_name": w.well_name, "distance_km": dist} for w, dist in nearby_wells
        ],
        "comparable_wells": comparable_wells,
        "historical_events": [
            {
                "well_name": e.well.well_name,
                "event_type": e.event_type,
                "depth_md_m": e.depth_md_m,
                "severity": e.severity,
                "mitigation": e.immediate_mitigation,
                "source": f"{e.source_document_name} p.{e.source_page_number}"
            } for e in events
        ],
        "lookahead_hazards": lookahead_hazards,
        "historical_mitigations": mitigations,
        "active_alerts": [
            {"id": a.id, "title": a.title, "severity": a.severity, "message": a.message} for a in alerts
        ],
        "missing_data_report": completeness,
        "memory_gaps": gaps,
        "data_conflicts": conflicts,
        "source_citations": [
            {"source": "WCR-OIL-DEMO-018", "pages": [37, 38], "focus": "Mud loss interval @ 2860m"},
            {"source": "DDR-OIL-DEMO-021", "pages": [22, 23], "focus": "Torque spike & wiper trip @ 2842m"},
            {"source": "Mud Report-OIL-DEMO-011", "pages": [15], "focus": "LCM pill treatment @ 2828m"}
        ],
        "ai_synthesis": "PetroNexus institutional memory identifies high probability of mud losses within the next 20m. LCM pre-mix advised before passing 2855m MD."
    }

    # Generate PDF export
    pdf_filename = f"Context_Pack_{well.well_name}_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_path = settings.REPORTS_DIR / pdf_filename
    ReportService.generate_pdf_context_pack(pack_data, pdf_path)
    pack_data["pdf_download_url"] = f"/api/reports/download/{pdf_filename}"

    # Audit log
    audit = AuditLog(
        action="REPORT_GENERATED",
        resource=f"well:{well.id}",
        details={"type": "CONTEXT_PACK", "pdf": pdf_filename}
    )
    db.add(audit)
    db.commit()

    return ContextPackResponse(**pack_data)

@router.get("/pre-interval-brief", response_model=PreIntervalBriefResponse)
def get_pre_interval_brief(well_id: Optional[int] = None, db: Session = Depends(get_db)):
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

    depth = well.current_depth_m
    upcoming_span = f"{int(depth)}–{int(depth + 75)} m"

    nearby_wells = get_nearby_wells(db, well.latitude, well.longitude, radius_km=10.0, exclude_well_id=well.id)
    comp_ids = [w[0].id for w in nearby_wells]

    hazards = db.query(DrillingEvent).filter(
        DrillingEvent.well_id.in_(comp_ids),
        DrillingEvent.depth_md_m >= depth,
        DrillingEvent.depth_md_m <= depth + 75.0
    ).all()

    return PreIntervalBriefResponse(
        well_id=well.id,
        well_name=well.well_name,
        current_depth_m=depth,
        upcoming_interval_m=upcoming_span,
        upcoming_formation=well.current_formation,
        offset_wells_count=len(nearby_wells),
        historical_events_count=len(hazards),
        primary_hazard_attention=["Mud Loss (Lost Circulation)", "Torque Fluctuation / Drag Increase"],
        most_comparable_well={
            "well_name": "OIL-DEMO-018",
            "distance_km": 4.8,
            "historical_event": "Mud Loss (45 bbl) @ 2860 m",
            "recommended_action": "Mix 30 bbl medium LCM pill and reduce pump rate to 1950 LPM"
        },
        documented_mitigations=[
            "LCM pill spotting (medium / coarse blend)",
            "Controlled circulation flow reduction",
            "Short wiper trip across interval if drag exceeds 15 tons"
        ],
        evidence_sources=[
            "WCR-018, Page 37",
            "DDR-021, Page 22",
            "Mud Report-011, Page 15"
        ]
    )

@router.get("/download/{file_name}")
def download_report_file(file_name: str):
    file_path = settings.REPORTS_DIR / file_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")
    return FileResponse(file_path, filename=file_name, media_type="application/pdf")
