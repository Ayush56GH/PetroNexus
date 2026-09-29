import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.database import Base

class DrillingParameter(Base):
    __tablename__ = "drilling_parameters"

    id = Column(Integer, primary_key=True, index=True)
    well_id = Column(Integer, ForeignKey("wells.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    depth_md_m = Column(Float, nullable=False, index=True)
    depth_tvd_m = Column(Float, nullable=True)
    rop_m_hr = Column(Float, default=14.5) # Rate of Penetration
    wob_ton = Column(Float, default=12.0) # Weight on Bit
    rpm = Column(Float, default=110.0) # Rotary Speed
    torque_kn_m = Column(Float, default=16.8) # Torque
    ecd_sg = Column(Float, default=1.28) # Equivalent Circulating Density
    mud_weight_sg = Column(Float, default=1.22) # Mud Weight (Specific Gravity)
    standpipe_pressure_psi = Column(Float, default=2450.0) # SPP
    flow_rate_lpm = Column(Float, default=2150.0) # Flow rate
    hook_load_ton = Column(Float, default=85.0) # Hook load
    mse_mpa = Column(Float, default=210.0) # Mechanical Specific Energy (Teale formula)

    well = relationship("Well", back_populates="drilling_parameters")


class MudProperty(Base):
    __tablename__ = "mud_properties"

    id = Column(Integer, primary_key=True, index=True)
    well_id = Column(Integer, ForeignKey("wells.id"), nullable=False, index=True)
    depth_m = Column(Float, nullable=False)
    mud_type = Column(String(50), default="Water-Based Polymer Mud (WBM)")
    mud_weight_sg = Column(Float, default=1.22)
    plastic_viscosity_cp = Column(Float, default=18.0)
    yield_point_pa = Column(Float, default=14.0)
    gel_strength_10s = Column(Float, default=6.0)
    gel_strength_10m = Column(Float, default=12.0)
    ph = Column(Float, default=9.5)
    fluid_loss_ml = Column(Float, default=5.2)
    solids_pct = Column(Float, default=7.0)
    recorded_at = Column(DateTime, default=datetime.datetime.utcnow)


class BhaRecord(Base):
    __tablename__ = "bha_records"

    id = Column(Integer, primary_key=True, index=True)
    well_id = Column(Integer, ForeignKey("wells.id"), nullable=False, index=True)
    run_number = Column(Integer, default=1)
    bit_size_in = Column(Float, default=8.5)
    bit_type = Column(String(100), default="PDC 5-Blade Matrix Body")
    depth_in_m = Column(Float, default=2100.0)
    depth_out_m = Column(Float, default=2846.0)
    total_hours = Column(Float, default=52.5)
    bha_description = Column(String(255), default="Bit + RSS + MWD/LWD + Stabilizer + Drill Collars + HWDP")
    components_json = Column(JSON, default=list)


class CasingRecord(Base):
    __tablename__ = "casing_records"

    id = Column(Integer, primary_key=True, index=True)
    well_id = Column(Integer, ForeignKey("wells.id"), nullable=False, index=True)
    casing_string = Column(String(50), default="Intermediate Casing") # Conductor, Surface, Intermediate, Production
    outer_diameter_in = Column(Float, default=9.625)
    weight_ppf = Column(Float, default=40.0)
    grade = Column(String(50), default="L-80")
    shoe_depth_md_m = Column(Float, default=2150.0)
    shoe_depth_tvd_m = Column(Float, default=2080.0)
    hole_size_in = Column(Float, default=12.25)
    date_set = Column(String(50), default="2026-01-28")


class CementingRecord(Base):
    __tablename__ = "cementing_records"

    id = Column(Integer, primary_key=True, index=True)
    well_id = Column(Integer, ForeignKey("wells.id"), nullable=False, index=True)
    casing_string = Column(String(50), default="Intermediate 9-5/8 in")
    slurry_type = Column(String(100), default="Class G + 35% Silica Flour + Extender")
    slurry_density_sg = Column(Float, default=1.58)
    top_of_cement_m = Column(Float, default=1200.0)
    pumped_volume_bbl = Column(Float, default=320.0)
    return_volume_bbl = Column(Float, default=315.0)
    is_successful = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)


class ReservoirData(Base):
    __tablename__ = "reservoir_data"

    id = Column(Integer, primary_key=True, index=True)
    well_id = Column(Integer, ForeignKey("wells.id"), nullable=False, index=True)
    formation_name = Column(String(100), default="Formation-X")
    top_m = Column(Float, default=2810.0)
    bottom_m = Column(Float, default=2940.0)
    porosity_pct = Column(Float, default=19.5)
    permeability_md = Column(Float, default=85.0)
    initial_pressure_psi = Column(Float, default=3820.0)
    fluid_type = Column(String(50), default="Light Crude / Gas Cap")
