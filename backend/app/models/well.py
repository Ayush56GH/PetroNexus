import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from backend.app.database import Base

class Well(Base):
    __tablename__ = "wells"

    id = Column(Integer, primary_key=True, index=True)
    well_name = Column(String(100), unique=True, index=True, nullable=False) # e.g. OIL-DEMO-023
    well_code = Column(String(50), nullable=True)
    field = Column(String(100), default="Duliajan Basin")
    operator = Column(String(100), default="Oil India Limited (OIL)")
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    elevation_m = Column(Float, default=112.5)
    spud_date = Column(String(50), default="2026-01-15")
    completion_date = Column(String(50), nullable=True)
    status = Column(String(50), default="DRILLING_ACTIVE") # DRILLING_ACTIVE, COMPLETED, SUSPENDED, OFFSET_REFERENCE
    well_type = Column(String(50), default="DEVELOPMENT_DIRECTIONAL") # EXPLORATORY, DEVELOPMENT_DIRECTIONAL, VERTICAL
    target_depth_m = Column(Float, default=3200.0)
    current_depth_m = Column(Float, default=2846.0)
    current_formation = Column(String(100), default="Formation-X")
    is_active_well = Column(Boolean, default=False)
    owner_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    organization_id = Column(UUID(as_uuid=True), nullable=True)
    visibility = Column(String(50), default="DEMO", nullable=False) # PRIVATE, ORGANIZATION, SHARED, DEMO
    
    # Well Master & Geographic Metadata
    basin = Column(String(100), default="Assam-Arakan Basin")
    block = Column(String(100), nullable=True)
    country = Column(String(100), default="India")
    ground_elevation = Column(Float, default=112.5)
    kb_elevation = Column(Float, default=120.0)
    td_md = Column(Float, default=3200.0)
    td_tvd = Column(Float, default=3136.0)
    td_tvdss = Column(Float, default=3016.0)
    rig = Column(String(100), nullable=True)
    rig_type = Column(String(100), nullable=True)
    purpose = Column(String(100), nullable=True)
    formation_target = Column(String(100), nullable=True)
    reservoir = Column(String(100), nullable=True)
    coordinate_reference_system = Column(String(50), default="EPSG:4326")

    # Data Provenance System
    source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=True)
    source_type = Column(String(50), default="DEMO_SYNTHETIC") # DEMO_SYNTHETIC, PUBLIC_DATASET, USER_UPLOAD, OIL_WITSML, OIL_ERTMAC
    source_name = Column(String(150), default="Synthetic Demonstration Data")
    is_real = Column(Boolean, default=False)
    is_synthetic = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)
    is_user_uploaded = Column(Boolean, default=False)
    provenance_confidence = Column(Float, default=1.0)
    provenance_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    trajectories = relationship("WellTrajectory", back_populates="well", cascade="all, delete-orphan")
    formation_intervals = relationship("FormationInterval", back_populates="well", cascade="all, delete-orphan")
    drilling_parameters = relationship("DrillingParameter", back_populates="well", cascade="all, delete-orphan")
    events = relationship("DrillingEvent", back_populates="well", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="well", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="well", cascade="all, delete-orphan")
    upload_sessions = relationship("WellUploadSession", back_populates="well", cascade="all, delete-orphan")


class WellUploadSession(Base):
    __tablename__ = "well_upload_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=True)
    well_id = Column(Integer, ForeignKey("wells.id"), nullable=True)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False) # PDF, CSV, XLSX, LAS, TXT, JSON
    processing_status = Column(String(50), default="COMPLETED") # PENDING, PROCESSING, COMPLETED, FAILED
    extracted_fields = Column(JSON, default=dict) # Structured dictionary of all extracted fields
    missing_fields = Column(JSON, default=list) # List of fields still missing
    quality_score = Column(Float, default=0.0) # 0 to 100%
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    well = relationship("Well", back_populates="upload_sessions")
