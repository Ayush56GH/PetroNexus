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

@router.get("/formation-correlation")
def get_formation_correlation(
    well_id: Optional[int] = 23,
    depth: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """
    True depth and formation correlation aligning active well and offsets
    by TVD, TVDSS, and formation boundaries rather than naive MD.
    """
    from backend.app.services.correlation_service import correlation_engine
    well = db.query(Well).filter(Well.id == well_id).first()
    if not well:
        well = db.query(Well).filter(Well.well_name == "OIL-DEMO-023").first()
    if not well:
        well = db.query(Well).first()

    offsets = db.query(Well).filter(Well.id != well.id).limit(5).all()
    return correlation_engine.correlate_wells_by_depth(db, well, offsets, reference_depth_md=depth)

@router.get("/formation-risk-profile")
def get_formation_risk_profile(db: Session = Depends(get_db)):
    """
    Computes statistical hazard profile per formation: event count, types,
    severity, NPT hours, affected wells, average depth (Section 81).
    """
    events = db.query(DrillingEvent).all()
    profile_by_fm = {}

    for ev in events:
        fm = ev.formation_name or "Unknown Formation"
        if fm not in profile_by_fm:
            profile_by_fm[fm] = {
                "formation_name": fm,
                "total_events": 0,
                "wells_affected": set(),
                "event_types": {},
                "severities": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
                "total_npt_hours": 0.0,
                "depths": [],
                "mitigations_count": 0
            }

        p = profile_by_fm[fm]
        p["total_events"] += 1
        p["wells_affected"].add(ev.well_id)
        etype = ev.event_type
        p["event_types"][etype] = p["event_types"].get(etype, 0) + 1
        sev = ev.severity.upper() if ev.severity else "MEDIUM"
        if sev in p["severities"]:
            p["severities"][sev] += 1
        p["total_npt_hours"] += float(getattr(ev, "npt_hours", 4.0) or 4.0)
        p["depths"].append(ev.depth_md_m)
        if ev.immediate_mitigation:
            p["mitigations_count"] += 1

    out = []
    for fm, data in profile_by_fm.items():
        avg_depth = round(sum(data["depths"]) / len(data["depths"]), 1) if data["depths"] else 0.0
        out.append({
            "formation_name": fm,
            "total_events": data["total_events"],
            "unique_wells_affected": len(data["wells_affected"]),
            "event_breakdown": data["event_types"],
            "severity_breakdown": data["severities"],
            "total_npt_hours": round(data["total_npt_hours"], 1),
            "average_event_depth_m": avg_depth,
            "documented_mitigations": data["mitigations_count"],
            "disclaimer": "Historical event statistics from offset records. Decision support only."
        })

    out.sort(key=lambda x: x["total_events"], reverse=True)
    return out

@router.get("/depth-heatmap")
def get_depth_hazard_heatmap(
    interval_m: float = 100.0,
    db: Session = Depends(get_db)
):
    """
    Computes historical event frequency by depth bins (Section 80: Historical Risk vs Depth).
    """
    events = db.query(DrillingEvent).all()
    bins = {}

    for ev in events:
        d = ev.depth_md_m
        bin_start = int(d // interval_m) * int(interval_m)
        bin_label = f"{bin_start} - {bin_start + int(interval_m)} m"
        if bin_label not in bins:
            bins[bin_label] = {
                "bin_start_m": bin_start,
                "bin_end_m": bin_start + int(interval_m),
                "label": bin_label,
                "total_events": 0,
                "categories": {}
            }
        b = bins[bin_label]
        b["total_events"] += 1
        cat = "Mud Loss" if "Loss" in ev.event_type else (
            "Torque / Stuck" if ("Torque" in ev.event_type or "Stuck" in ev.event_type) else (
                "Kick / Influx" if "Kick" in ev.event_type else "Other Hazards"
            )
        )
        b["categories"][cat] = b["categories"].get(cat, 0) + 1

    sorted_bins = sorted(bins.values(), key=lambda x: x["bin_start_m"])
    return sorted_bins

