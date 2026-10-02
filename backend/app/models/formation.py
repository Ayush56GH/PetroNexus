from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from backend.app.database import Base

class Formation(Base):
    __tablename__ = "formations"

    id = Column(Integer, primary_key=True, index=True)
    formation_name = Column(String(100), unique=True, index=True, nullable=False) # e.g. Formation-X, Barail Group, Tipam Sandstone
    aliases = Column(JSON, default=list) # e.g. ["Barail", "Barail Group", "Barail Fm.", "Barail Sandstone"]
    code = Column(String(50), nullable=True)
    age = Column(String(100), default="Oligocene / Miocene")
    lithology = Column(String(100), default="Interbedded Sandstone, Siltstone & Shale")
    description = Column(Text, nullable=True)
    typical_overpressure_risk = Column(String(50), default="MODERATE") # LOW, MODERATE, HIGH
    typical_loss_risk = Column(String(50), default="HIGH")
    reservoir_flag = Column(Boolean, default=False)
    source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=True)
    confidence = Column(Float, default=0.95)

    intervals = relationship("FormationInterval", back_populates="formation")


class FormationInterval(Base):
    __tablename__ = "formation_intervals"

    id = Column(Integer, primary_key=True, index=True)
    well_id = Column(Integer, ForeignKey("wells.id"), nullable=False, index=True)
    formation_id = Column(Integer, ForeignKey("formations.id"), nullable=False, index=True)
    top_depth_md_m = Column(Float, nullable=False, index=True)
    bottom_depth_md_m = Column(Float, nullable=False, index=True)
    top_depth_tvd_m = Column(Float, nullable=True)
    bottom_depth_tvd_m = Column(Float, nullable=True)
    top_depth_tvdss_m = Column(Float, nullable=True)
    bottom_depth_tvdss_m = Column(Float, nullable=True)
    thickness_m = Column(Float, nullable=True)
    lithology = Column(String(100), default="Sandstone / Shale")
    reservoir_unit = Column(String(100), nullable=True)
    comments = Column(Text, nullable=True)

    well = relationship("Well", back_populates="formation_intervals")
    formation = relationship("Formation", back_populates="intervals")

