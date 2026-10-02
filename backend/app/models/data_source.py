import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, JSON
from backend.app.database import Base

class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), unique=True, index=True, nullable=False)
    source_type = Column(String(50), nullable=False, default="USER_UPLOAD") # USER_UPLOAD, PUBLIC_DATASET, OIL_WITSML, OIL_ERTMAC, DEMO_SYNTHETIC
    organization = Column(String(150), default="Oil India Limited (OIL)")
    url = Column(String(255), nullable=True)
    source_file = Column(String(255), nullable=True)
    license = Column(String(100), default="Proprietary / Evaluated Public Domain")
    description = Column(Text, nullable=True)
    is_real = Column(Boolean, default=True)
    is_synthetic = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    is_user_uploaded = Column(Boolean, default=False)
    confidence = Column(Float, default=1.0)
    status = Column(String(50), default="STANDBY") # CONNECTED, DISCONNECTED, CONNECTING, ERROR, STANDBY, SYNCING
    endpoint_config = Column(JSON, default=dict) # URL, username, well_uid, wellbore_uid, polling_interval, channel_mapping
    last_sync = Column(DateTime, nullable=True)
    data_date = Column(String(50), nullable=True)
    acquisition_time = Column(DateTime, default=datetime.datetime.utcnow)
    record_count = Column(Integer, default=0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

