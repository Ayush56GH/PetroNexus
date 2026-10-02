import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import synonym
from backend.app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    user_email = Column(String(255), default="engineer@oilindia.in")
    action = Column(String(100), nullable=False, index=True)
    # Actions: LOGIN, WELL_UPLOAD, WELL_ANALYSIS, OFFSET_ANALYSIS, ALERT_GENERATED, ALERT_ACKNOWLEDGED, AI_QUERY, DOCUMENT_VIEW, REPORT_GENERATED
    resource = Column(String(255), nullable=True)
    details = Column(JSON, default=dict)
    ip_address = Column(String(50), default="127.0.0.1")
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    timestamp = synonym("created_at")

