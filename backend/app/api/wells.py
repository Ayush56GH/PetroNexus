from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.well import Well
from backend.app.models.formation import FormationInterval
from backend.app.models.event import DrillingEvent
from backend.app.models.drilling import DrillingParameter
from backend.app.models.trajectory import WellTrajectory
from backend.app.schemas.well import WellOut, WellDetailOut
from backend.app.services.spatial_service import get_nearby_wells

router = APIRouter(prefix="/wells", tags=["Wells"])

@router.get("", response_model=List[WellOut])
def list_wells(
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    query = db.query(Well)
    if status:
        query = query.filter(Well.status == status)
    return query.order_by(Well.id.asc()).limit(limit).all()

@router.get("/{well_id}", response_model=WellDetailOut)
def get_well(well_id: int, db: Session = Depends(get_db)):
    well = db.query(Well).filter(Well.id == well_id).first()
    if not well:
        raise HTTPException(status_code=404, detail="Well not found")
    
    # Enrich counts
    traj_count = db.query(WellTrajectory).filter(WellTrajectory.well_id == well.id).count()
    form_count = db.query(FormationInterval).filter(FormationInterval.well_id == well.id).count()
    ev_count = db.query(DrillingEvent).filter(DrillingEvent.well_id == well.id).count()
    doc_count = len(well.documents)
    alert_count = len(well.alerts)

    return WellDetailOut(
        id=well.id,
        well_name=well.well_name,
        well_code=well.well_code,
        field=well.field,
        operator=well.operator,
        latitude=well.latitude,
        longitude=well.longitude,
        elevation_m=well.elevation_m,
        spud_date=well.spud_date,
        completion_date=well.completion_date,
        status=well.status,
        well_type=well.well_type,
        target_depth_m=well.target_depth_m,
        current_depth_m=well.current_depth_m,
        current_formation=well.current_formation,
        is_active_well=well.is_active_well,
        created_at=well.created_at,
        trajectories_count=traj_count,
        formations_count=form_count,
        events_count=ev_count,
        documents_count=doc_count,
        alerts_count=alert_count
    )

@router.get("/{well_id}/nearby")
def get_well_nearby(
    well_id: int,
    radius_km: float = Query(15.0, ge=1.0, le=100.0),
    db: Session = Depends(get_db)
):
    well = db.query(Well).filter(Well.id == well_id).first()
    if not well:
        raise HTTPException(status_code=404, detail="Well not found")

    nearby = get_nearby_wells(db, well.latitude, well.longitude, radius_km=radius_km, exclude_well_id=well.id)
    
    output = []
    for w, dist in nearby:
        # Check count of historical events
        ev_count = db.query(DrillingEvent).filter(DrillingEvent.well_id == w.id).count()
        losses = db.query(DrillingEvent).filter(DrillingEvent.well_id == w.id, DrillingEvent.event_type.like("%Loss%")).count()
        output.append({
            "id": w.id,
            "well_name": w.well_name,
            "latitude": w.latitude,
            "longitude": w.longitude,
            "distance_km": dist,
            "current_formation": w.current_formation,
            "target_depth_m": w.target_depth_m,
            "status": w.status,
            "historical_events_count": ev_count,
            "mud_losses_count": losses
        })
    return output

@router.get("/{well_id}/formations")
def get_well_formations(well_id: int, db: Session = Depends(get_db)):
    intervals = db.query(FormationInterval).filter(FormationInterval.well_id == well_id).order_by(FormationInterval.top_depth_md_m.asc()).all()
    return [
        {
            "id": i.id,
            "formation_name": i.formation.formation_name if i.formation else "Unknown",
            "top_depth_md_m": i.top_depth_md_m,
            "bottom_depth_md_m": i.bottom_depth_md_m,
            "top_depth_tvd_m": i.top_depth_tvd_m,
            "bottom_depth_tvd_m": i.bottom_depth_tvd_m,
            "thickness_m": i.thickness_m,
            "lithology": i.lithology,
            "reservoir_unit": i.reservoir_unit
        }
        for i in intervals
    ]

@router.get("/{well_id}/events")
def get_well_events(well_id: int, db: Session = Depends(get_db)):
    events = db.query(DrillingEvent).filter(DrillingEvent.well_id == well_id).order_by(DrillingEvent.depth_md_m.asc()).all()
    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "depth_md_m": e.depth_md_m,
            "depth_tvd_m": e.depth_tvd_m,
            "depth_tvdss_m": e.depth_tvdss_m,
            "formation_name": e.formation_name,
            "severity": e.severity,
            "description": e.description,
            "primary_cause": e.primary_cause,
            "immediate_mitigation": e.immediate_mitigation,
            "source_document_name": e.source_document_name,
            "source_page_number": e.source_page_number
        }
        for e in events
    ]

@router.get("/{well_id}/parameters")
def get_well_parameters(well_id: int, limit: int = Query(50, ge=1, le=500), db: Session = Depends(get_db)):
    params = db.query(DrillingParameter).filter(DrillingParameter.well_id == well_id).order_by(DrillingParameter.depth_md_m.asc()).limit(limit).all()
    return [
        {
            "timestamp": p.timestamp.strftime("%Y-%m-%d %H:%M:%S") if p.timestamp else None,
            "depth_md_m": p.depth_md_m,
            "rop_m_hr": p.rop_m_hr,
            "wob_ton": p.wob_ton,
            "rpm": p.rpm,
            "torque_kn_m": p.torque_kn_m,
            "ecd_sg": p.ecd_sg,
            "mud_weight_sg": p.mud_weight_sg,
            "standpipe_pressure_psi": p.standpipe_pressure_psi,
            "flow_rate_lpm": p.flow_rate_lpm,
            "mse_mpa": p.mse_mpa
        }
        for p in params
    ]

@router.get("/{well_id}/trajectories")
def get_well_trajectories(well_id: int, db: Session = Depends(get_db)):
    trajs = db.query(WellTrajectory).filter(WellTrajectory.well_id == well_id).order_by(WellTrajectory.measured_depth_m.asc()).all()
    return [
        {
            "measured_depth_m": t.measured_depth_m,
            "inclination_deg": t.inclination_deg,
            "azimuth_deg": t.azimuth_deg,
            "true_vertical_depth_m": t.true_vertical_depth_m,
            "tvdss_m": t.tvdss_m,
            "dogleg_severity": t.dogleg_severity,
            "northing_m": t.northing_m,
            "easting_m": t.easting_m
        }
        for t in trajs
    ]

@router.post("/{well_id}/activate")
def activate_well(well_id: int, db: Session = Depends(get_db)):
    # Deactivate all wells
    db.query(Well).update({Well.is_active_well: False})
    well = db.query(Well).filter(Well.id == well_id).first()
    if not well:
        raise HTTPException(status_code=404, detail="Well not found")
    well.is_active_well = True
    well.status = "DRILLING_ACTIVE"
    db.commit()
    return {"status": "SUCCESS", "active_well": well.well_name, "current_depth": well.current_depth_m}
