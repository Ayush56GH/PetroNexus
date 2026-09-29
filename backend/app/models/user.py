import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from backend.app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    employee_id = Column(String(100), unique=True, index=True, nullable=False)
    department = Column(String(100), default="Drilling Operations")
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="DRILLING_ENGINEER", nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
