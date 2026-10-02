import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.database import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    well_id = Column(Integer, ForeignKey("wells.id"), nullable=False, index=True)
    alert_type = Column(String(100), nullable=False) # HISTORICAL_OFFSET_HAZARD, LOOKAHEAD_CORRIDOR, TORQUE_ANOMALY, ECD_MARGIN, ROP_DROP
    severity = Column(String(50), default="HIGH") # CRITICAL, HIGH, MEDIUM, LOW, INFO
    current_depth_m = Column(Float, nullable=False)
    formation_name = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(50), default="ACTIVE") # ACTIVE, ACKNOWLEDGED, DISMISSED, ESCALATED, RESOLVED
    rule_id = Column(String(100), default="RULE_OFFSET_HAZARD")
    what_happened = Column(Text, nullable=True)
    why_it_matters = Column(Text, nullable=True)
    historical_evidence_text = Column(Text, nullable=True)
    current_indicator_text = Column(Text, nullable=True)
    recommended_action = Column(Text, nullable=True)
    engineer_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(100), nullable=True)
    dismissed_at = Column(DateTime, nullable=True)
    escalated_at = Column(DateTime, nullable=True)
    source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=True)

    well = relationship("Well", back_populates="alerts")
    evidence_items = relationship("AlertEvidence", back_populates="alert", cascade="all, delete-orphan")


class AlertEvidence(Base):
    __tablename__ = "alert_evidence"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False, index=True)
    offset_well_id = Column(Integer, ForeignKey("wells.id"), nullable=True)
    offset_well_name = Column(String(100), nullable=False)
    event_id = Column(Integer, ForeignKey("drilling_events.id"), nullable=True)
    event_type = Column(String(100), nullable=False)
    event_depth_m = Column(Float, nullable=False)
    distance_km = Column(Float, nullable=False)
    delta_depth_m = Column(Float, nullable=False) # Distance from current bit
    correlation_factor = Column(Float, default=0.92) # 0 to 1
    document_citation = Column(String(200), default="WCR-OIL-DEMO-018")
    page_citation = Column(String(50), default="Page 37")
    narrative = Column(Text, nullable=False)

    alert = relationship("Alert", back_populates="evidence_items")
