import datetime
import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from backend.app.database import Base

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    employee_id = Column(String(100), unique=True, index=True, nullable=True)
    department = Column(String(100), default="Drilling Operations & eRTMAC Division")
    role = Column(String(50), default="DRILLING_ENGINEER", nullable=False)
    organization_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

# Alias for seamless compatibility
User = Profile
