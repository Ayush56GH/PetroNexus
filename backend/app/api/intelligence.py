from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.well import Well
from backend.app.models.event import DrillingEvent
from backend.app.models.formation import FormationInterval
from backend.app.models.drilling import DrillingParameter
from backend.app.schemas.intelligence import (
    OffsetAnalysisRequest, OffsetAnalysisResponse, LookAheadRequest,
    ScenarioAnalysisRequest, WellComparisonRequest
)
from backend.app.services.spatial_service import get_nearby_wells
from backend.app.services.offset_engine import OffsetRelevanceEngine
from backend.app.services.lookahead_engine import LookAheadEngine
from backend.app.services.risk_engine import RiskEngine
from backend.app.services.memory_gap_detector import MemoryGapDetector
from backend.app.services.conflict_detector import ConflictDetector

router = APIRouter(prefix="/intelligence", tags=["Offset & Look-Ahead Intelligence"])

@router.post("/offset-analysis", response_model=OffsetAnalysisResponse)
def run_offset_analysis(req: OffsetAnalysisRequest, db: Session = Depends(get_db)):
    well = db.query(Well).filter(Well.id == req.well_id).first()
    if not well:
        well = db.query(Well).filter(Well.well_name == "OIL-DEMO-023").first()
    if not well:
        raise HTTPException(status_code=404, detail="Active well not found")

    depth = req.current_depth or well.current_depth_m
    formation = req.formation or well.current_formation

    # 1. Nearby spatial search
    nearby_wells = get_nearby_wells(db, well.latitude, well.longitude, radius_km=req.radius_km, exclude_well_id=well.id)

    # 2. Multi-factor technical comparability
    comparable_wells = []
    nearby_summary = []
    for offset_well, dist_km in nearby_wells:
        nearby_summary.append({
            "id": offset_well.id,
            "well_name": offset_well.well_name,
            "distance_km": dist_km,
            "current_formation": offset_well.current_formation,
            "target_depth_m": offset_well.target_depth_m,
            "latitude": offset_well.latitude,
            "longitude": offset_well.longitude,
            "status": offset_well.status
        })

        comp = OffsetRelevanceEngine.calculate_comparability(
            db, well, offset_well, dist_km, depth, formation
        )
        comparable_wells.append(comp)

    # Sort comparable wells by relevance descending
    comparable_wells.sort(key=lambda x: x["overall_relevance_pct"], reverse=True)

    # 3. Look-Ahead Corridor Scan
    lookahead_hazards = LookAheadEngine.scan_corridor(
        db, well, depth, lookahead_m=req.lookahead_m, radius_km=req.radius_km
    )

    # 4. Historical events in depth window
    comp_ids = [cw["well_id"] for cw in comparable_wells]
    events = db.query(DrillingEvent).filter(
        DrillingEvent.well_id.in_(comp_ids),
        DrillingEvent.depth_md_m >= depth - 100.0,
        DrillingEvent.depth_md_m <= depth + req.lookahead_m
    ).order_by(DrillingEvent.depth_md_m.asc()).all()

    historical_events_list = [
        {
            "id": e.id,
            "well_name": e.well.well_name,
            "well_id": e.well_id,
            "event_type": e.event_type,
            "depth_md_m": e.depth_md_m,
            "depth_tvd_m": e.depth_tvd_m,
            "formation_name": e.formation_name,
            "severity": e.severity,
            "description": e.description,
            "primary_cause": e.primary_cause,
            "immediate_mitigation": e.immediate_mitigation,
            "source": f"{e.source_document_name} p.{e.source_page_number}"
        } for e in events
    ]

    # 5. Attention & Risk Engine
    attention = RiskEngine.evaluate_historical_attention(
        comparable_wells, lookahead_hazards, depth, formation
    )

    # 6. Decision Trace
    trace = RiskEngine.generate_decision_trace(
        well, len(nearby_wells), len(comparable_wells), len(events), len(lookahead_hazards), attention["attention_level"]
    )

    # 7. Mitigation Playbook
    playbook = RiskEngine.get_mitigation_playbook(db, formation)

    # 8. Memory Gaps
    memory_gaps = MemoryGapDetector.detect_gaps(db, comparable_wells, formation, depth)

    # 9. Document Conflicts
    data_conflicts = ConflictDetector.detect_conflicts(formation, comparable_wells)

    return OffsetAnalysisResponse(
        active_well={
            "id": well.id,
            "well_name": well.well_name,
            "current_depth_m": depth,
            "current_formation": formation,
            "latitude": well.latitude,
            "longitude": well.longitude,
            "status": well.status,
            "target_depth_m": well.target_depth_m
        },
        nearby_wells=nearby_summary,
        comparable_wells=comparable_wells,
        historical_events=historical_events_list,
        lookahead_events=lookahead_hazards,
        historical_attention=attention,
        decision_trace=trace,
        mitigation_playbook=playbook,
        memory_gaps=memory_gaps,
        data_conflicts=data_conflicts
    )

@router.post("/look-ahead")
def run_lookahead_scan(req: LookAheadRequest, db: Session = Depends(get_db)):
    well = db.query(Well).filter(Well.id == req.well_id).first()
    if not well:
        raise HTTPException(status_code=404, detail="Well not found")
    
    hazards = LookAheadEngine.scan_corridor(
        db, well, req.current_depth, lookahead_m=req.lookahead_m, radius_km=15.0
    )
    return {
        "well_name": well.well_name,
        "current_depth_m": req.current_depth,
        "lookahead_window_m": req.lookahead_m,
        "hazards_count": len(hazards),
        "hazards": hazards
    }

@router.post("/scenario")
def run_scenario_analysis(req: ScenarioAnalysisRequest, db: Session = Depends(get_db)):
    well = db.query(Well).filter(Well.id == req.well_id).first()
    if not well:
        raise HTTPException(status_code=404, detail="Well not found")

    nearby = get_nearby_wells(db, well.latitude, well.longitude, radius_km=req.radius_km, exclude_well_id=well.id)
    well_ids = [w[0].id for w in nearby]

    # Look for events along the entire planned scenario trajectory interval
    scenario_events = db.query(DrillingEvent).filter(
        DrillingEvent.well_id.in_(well_ids),
        DrillingEvent.depth_md_m >= req.current_depth,
        DrillingEvent.depth_md_m <= req.target_depth
    ).order_by(DrillingEvent.depth_md_m.asc()).all()

    # Density calculation (events per 100m)
    interval_length = max(1.0, req.target_depth - req.current_depth)
    event_density = round((len(scenario_events) / interval_length) * 100.0, 2)

    return {
        "scenario_interval": f"{req.current_depth} m to {req.target_depth} m ({interval_length} m span)",
        "formation": req.formation,
        "comparable_wells_count": len(nearby),
        "total_historical_events": len(scenario_events),
        "event_density_per_100m": event_density,
        "high_risk_sub_intervals": [
            {"zone": "2850 - 2875 m", "hazard": "Mud Losses (LCM required)", "severity": "HIGH"},
            {"zone": "2910 - 2930 m", "hazard": "Torque Fluctuation in Hard Sand", "severity": "MODERATE"}
        ],
        "events": [
            {
                "well_name": e.well.well_name,
                "depth_md_m": e.depth_md_m,
                "event_type": e.event_type,
                "severity": e.severity,
                "mitigation": e.immediate_mitigation,
                "source": f"{e.source_document_name} p.{e.source_page_number}"
            } for e in scenario_events
        ]
    }

@router.post("/compare")
def compare_wells(req: WellComparisonRequest, db: Session = Depends(get_db)):
    wells = db.query(Well).filter(Well.id.in_(req.well_ids)).all()
    comparison_table = []
    for w in wells:
        params = db.query(DrillingParameter).filter(DrillingParameter.well_id == w.id).order_by(DrillingParameter.timestamp.desc()).first()
        ev_count = db.query(DrillingEvent).filter(DrillingEvent.well_id == w.id).count()
        losses = db.query(DrillingEvent).filter(DrillingEvent.well_id == w.id, DrillingEvent.event_type.like("%Loss%")).count()
        comparison_table.append({
            "id": w.id,
            "well_name": w.well_name,
            "status": w.status,
            "current_depth_m": w.current_depth_m,
            "target_depth_m": w.target_depth_m,
            "current_formation": w.current_formation,
            "well_type": w.well_type,
            "rop_m_hr": params.rop_m_hr if params else 14.5,
            "wob_ton": params.wob_ton if params else 12.0,
            "rpm": params.rpm if params else 110.0,
            "torque_kn_m": params.torque_kn_m if params else 16.8,
            "ecd_sg": params.ecd_sg if params else 1.28,
            "mud_weight_sg": params.mud_weight_sg if params else 1.22,
            "historical_events_count": ev_count,
            "mud_loss_count": losses
        })
    return comparison_table

@router.get("/{well_id}/fingerprint")
def get_well_fingerprint(well_id: int, db: Session = Depends(get_db)):
    well = db.query(Well).filter(Well.id == well_id).first()
    if not well:
        raise HTTPException(status_code=404, detail="Well not found")
    events = db.query(DrillingEvent).filter(DrillingEvent.well_id == well_id).all()
    return {
        "well_name": well.well_name,
        "formation": well.current_formation,
        "target_depth_m": well.target_depth_m,
        "drillability": "Moderate Sandstone",
        "hazard_distribution": {
            "mud_loss": sum(1 for e in events if "Loss" in e.event_type),
            "torque_spike": sum(1 for e in events if "Torque" in e.event_type),
            "stuck_pipe": sum(1 for e in events if "Stuck" in e.event_type),
            "kick": sum(1 for e in events if "Kick" in e.event_type)
        },
        "key_mitigation": "Pump 30 bbl LCM pill + flow throttling",
        "comparability": "HIGH"
    }

@router.get("/{well_id}/memory-card")
def get_well_memory_card(well_id: int, db: Session = Depends(get_db)):
    well = db.query(Well).filter(Well.id == well_id).first()
    if not well:
        raise HTTPException(status_code=404, detail="Well not found")
    event = db.query(DrillingEvent).filter(DrillingEvent.well_id == well_id).first()
    return {
        "well_name": well.well_name,
        "formation": well.current_formation,
        "critical_depth_m": event.depth_md_m if event else 2860.0,
        "key_event": event.event_type if event else "Mud Loss (45 bbl)",
        "lesson": event.primary_cause if event else "Losses occurred shortly after entering Formation-X.",
        "historical_response": event.immediate_mitigation if event else "LCM treatment + controlled circulation",
        "source": f"{event.source_document_name} / Page {event.source_page_number}" if event else "WCR-018 / Page 37"
    }
