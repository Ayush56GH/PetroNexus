import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, JSON
from backend.app.database import Base

class TelemetryMeasurement(Base):
    __tablename__ = "telemetry_measurements"

    id = Column(Integer, primary_key=True, index=True)
    well_id = Column(Integer, ForeignKey("wells.id"), nullable=False, index=True)
    wellbore_id = Column(String(100), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    depth_md = Column(Float, nullable=False, index=True)
    depth_tvd = Column(Float, nullable=True)
    rop = Column(Float, nullable=True) # m/hr
    wob = Column(Float, nullable=True) # ton or klbf
    rpm = Column(Float, nullable=True) # rpm
    torque = Column(Float, nullable=True) # kN.m
    hookload = Column(Float, nullable=True) # ton
    spp = Column(Float, nullable=True) # psi
    flow_in = Column(Float, nullable=True) # L/min
    flow_out = Column(Float, nullable=True) # L/min
    ecd = Column(Float, nullable=True) # SG
    mud_weight = Column(Float, nullable=True) # SG
    pit_volume = Column(Float, nullable=True) # m3 or bbl
    pit_gain = Column(Float, nullable=True) # m3 or bbl
    pit_loss = Column(Float, nullable=True)
    gas_total = Column(Float, nullable=True) # % or units
    c1 = Column(Float, nullable=True)
    c2 = Column(Float, nullable=True)
    c3 = Column(Float, nullable=True)
    c4 = Column(Float, nullable=True)
    mse = Column(Float, nullable=True) # MPa (Teale Mechanical Specific Energy)
    quality_status = Column(String(50), default="GOOD") # GOOD, WARNING, BAD
    quality_flags = Column(JSON, default=list) # e.g. ["SENSOR_FLATLINE", "RATE_SPIKE"]
    source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=True)
    source_type = Column(String(50), default="WITSML_STREAM") # WITSML_STREAM, REPLAY_REAL, SIMULATED, CSV_UPLOAD
    is_real = Column(Boolean, default=False)
    is_synthetic = Column(Boolean, default=True)
    original_units = Column(JSON, default=dict)
    normalized_units = Column(JSON, default=dict)
    ingested_at = Column(DateTime, default=datetime.datetime.utcnow)

