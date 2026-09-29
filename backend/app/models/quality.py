import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
from backend.app.database import Base

class DataQualityMetric(Base):
    __tablename__ = "data_quality_metrics"

    id = Column(Integer, primary_key=True, index=True)
    well_id = Column(Integer, ForeignKey("wells.id"), nullable=False, index=True)
    readiness_percentage = Column(Float, default=82.0)
    identity_score = Column(Float, default=100.0)
    location_score = Column(Float, default=100.0)
    depth_score = Column(Float, default=100.0)
    formation_score = Column(Float, default=100.0)
    drilling_param_score = Column(Float, default=100.0)
    trajectory_score = Column(Float, default=50.0)
    mud_score = Column(Float, default=40.0)
    bha_score = Column(Float, default=100.0)
    casing_score = Column(Float, default=40.0)
    pressure_score = Column(Float, default=40.0)
    reservoir_score = Column(Float, default=50.0)
    missing_items = Column(JSON, default=list)
    next_actions = Column(JSON, default=list)
    evaluated_at = Column(DateTime, default=datetime.datetime.utcnow)


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, index=True)
    well_id = Column(Integer, ForeignKey("wells.id"), nullable=False, index=True)
    depth_m = Column(Float, nullable=False)
    formation_name = Column(String(100), default="Formation-X")
    mud_loss_risk_level = Column(String(50), default="HIGH") # LOW, MODERATE, HIGH
    stuck_pipe_risk_level = Column(String(50), default="MODERATE")
    kick_risk_level = Column(String(50), default="LOW")
    torque_risk_level = Column(String(50), default="HIGH")
    overall_attention_level = Column(String(50), default="HIGH")
    rationale = Column(Text, nullable=False)
    lookahead_window_m = Column(Float, default=150.0)
    evaluated_at = Column(DateTime, default=datetime.datetime.utcnow)
