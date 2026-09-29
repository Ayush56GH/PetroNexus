from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.database import Base

class DrillingEvent(Base):
    __tablename__ = "drilling_events"

    id = Column(Integer, primary_key=True, index=True)
    well_id = Column(Integer, ForeignKey("wells.id"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True) 
    # e.g. Mud Loss, Partial Loss, Total Loss, Kick, Stuck Pipe, Differential Sticking,
    # Pack-Off, Torque Spike, Drag Increase, Wellbore Instability, Overpressure, Lost Circulation, Casing Issue
    depth_md_m = Column(Float, nullable=False, index=True)
    depth_tvd_m = Column(Float, nullable=True)
    depth_tvdss_m = Column(Float, nullable=True)
    formation_name = Column(String(100), nullable=False, index=True)
    severity = Column(String(50), default="HIGH") # CRITICAL, HIGH, MODERATE, LOW
    occurred_at = Column(String(50), nullable=True)
    description = Column(Text, nullable=False)
    primary_cause = Column(Text, nullable=True)
    immediate_mitigation = Column(Text, nullable=True)
    duration_hours = Column(Float, default=4.5)
    source_document_id = Column(Integer, nullable=True)
    source_document_name = Column(String(150), default="WCR-OIL-DEMO-018")
    source_page_number = Column(Integer, default=37)

    well = relationship("Well", back_populates="events")


class EventMitigation(Base):
    __tablename__ = "event_mitigations"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    formation_name = Column(String(100), nullable=False, index=True)
    mitigation_title = Column(String(200), nullable=False)
    action_category = Column(String(100), default="Loss Circulation Protocol") # LCM, Mud Adjustment, Hydraulics, Mechanical, Tripping
    step_order = Column(Integer, default=1)
    procedure_text = Column(Text, nullable=False)
    observed_efficacy = Column(String(50), default="High (Resolved within 4 hrs)")
    sample_wells_cited = Column(JSON, default=list) # e.g. ["OIL-DEMO-018", "OIL-DEMO-021"]
    evidence_citations = Column(JSON, default=list) # e.g. ["WCR-018 p37", "DDR-021 p22", "Mud Report-011 p15"]
