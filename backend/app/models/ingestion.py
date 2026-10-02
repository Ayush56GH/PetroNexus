import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey
from backend.app.database import Base

class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id = Column(Integer, primary_key=True, index=True)
    well_id = Column(Integer, ForeignKey("wells.id"), nullable=True)
    data_type = Column(String(50), nullable=False) # WELL_HEADER, TRAJECTORY, DRILLING_PARAMETERS, FORMATION_TOPS, HISTORICAL_EVENTS, LAS_LOG, WCR_DOCUMENT, TELEMETRY
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=True)
    status = Column(String(50), default="PENDING") # PENDING, PREVIEWED, COMPLETED, FAILED
    rows_total = Column(Integer, default=0)
    rows_imported = Column(Integer, default=0)
    detected_columns = Column(JSON, default=list)
    column_mapping = Column(JSON, default=dict)
    validation_errors = Column(JSON, default=list)
    quality_summary = Column(JSON, default=dict) # e.g. {"completeness": 92.5, "warnings": 1}
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
