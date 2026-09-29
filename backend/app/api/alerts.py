import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.alert import Alert, AlertEvidence
from backend.app.models.audit import AuditLog
from backend.app.schemas.alert import AlertOut, AlertAcknowledge

router = APIRouter(prefix="/alerts", tags=["Alert Center"])

@router.get("", response_model=List[AlertOut])
def list_alerts(
    well_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Alert)
    if well_id:
        query = query.filter(Alert.well_id == well_id)
    if status:
        query = query.filter(Alert.status == status)
    return query.order_by(Alert.created_at.desc()).all()

@router.get("/{alert_id}", response_model=AlertOut)
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@router.post("/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: int, ack: AlertAcknowledge, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = "ACKNOWLEDGED"
    alert.acknowledged_at = datetime.datetime.utcnow()
    alert.acknowledged_by = ack.acknowledged_by or "Drilling Engineer"
    db.commit()

    # Audit log
    audit = AuditLog(
        action="ALERT_ACKNOWLEDGED",
        resource=f"alert:{alert.id}",
        details={"acknowledged_by": alert.acknowledged_by, "alert_title": alert.title}
    )
    db.add(audit)
    db.commit()

    return {"status": "SUCCESS", "message": f"Alert {alert_id} acknowledged by {alert.acknowledged_by}"}

@router.get("/{alert_id}/evidence")
def get_alert_evidence(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    evidence_items = alert.evidence_items
    return {
        "alert_id": alert.id,
        "title": alert.title,
        "severity": alert.severity,
        "current_depth_m": alert.current_depth_m,
        "formation_name": alert.formation_name,
        "evidence_trail": [
            {
                "id": ev.id,
                "offset_well": ev.offset_well_name,
                "distance_km": ev.distance_km,
                "event_type": ev.event_type,
                "event_depth_m": ev.event_depth_m,
                "delta_depth_m": ev.delta_depth_m,
                "correlation_factor": ev.correlation_factor,
                "document_citation": ev.document_citation,
                "page_citation": ev.page_citation,
                "narrative": ev.narrative
            }
            for ev in evidence_items
        ]
    }
