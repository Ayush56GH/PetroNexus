from sqlalchemy import Column, Integer, Float, String, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base

class WellTrajectory(Base):
    __tablename__ = "well_trajectories"

    id = Column(Integer, primary_key=True, index=True)
    well_id = Column(Integer, ForeignKey("wells.id"), nullable=False, index=True)
    measured_depth_m = Column(Float, nullable=False, index=True) # MD
    inclination_deg = Column(Float, default=0.0) # Inc (degrees)
    azimuth_deg = Column(Float, default=0.0) # Azi (degrees)
    true_vertical_depth_m = Column(Float, nullable=False) # TVD
    tvdss_m = Column(Float, nullable=True) # TVDSS (Subsea)
    dogleg_severity = Column(Float, default=0.0) # deg/30m
    northing_m = Column(Float, default=0.0)
    easting_m = Column(Float, default=0.0)
    survey_time = Column(String(50), nullable=True)
    source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=True)

    well = relationship("Well", back_populates="trajectories")
