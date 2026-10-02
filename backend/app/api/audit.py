from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.audit import AuditLog

router = APIRouter(prefix="/audit-logs", tags=["Auditability"])

@router.get("")
def list_audit_logs(
    action: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "user_email": l.user_email,
            "action": l.action,
            "resource": l.resource,
            "details": l.details,
            "ip_address": l.ip_address,
            "timestamp": (l.created_at or l.timestamp).strftime("%Y-%m-%d %H:%M:%S") if (l.created_at or l.timestamp) else ""
        } for l in logs
    ]
