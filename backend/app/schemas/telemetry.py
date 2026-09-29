from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class TelemetryRecord(BaseModel):
    timestamp: str
    depth: float # MD (m)
    tvd: Optional[float] = None
    rop: float # m/hr
    wob: float # tons
    rpm: float # rpm
    torque: float # kN.m
    ecd: float # SG
    mud_weight: float # SG
    spp: float # psi
    flow_rate: float # lpm
    hook_load: float # tons
    mse: Optional[float] = None # MPa (Mechanical Specific Energy)

class TelemetryAnomalies(BaseModel):
    has_anomaly: bool
    anomaly_types: List[str] # ROP_DROP, TORQUE_SPIKE, ECD_HIGH, SPP_SPIKE, BIT_AT_HAZARD_ZONE
    severity: str # NORMAL, WARNING, CRITICAL
    details: List[str]
    suggested_actions: List[str]

class TelemetryStreamMessage(BaseModel):
    well_id: int
    well_name: str
    telemetry: TelemetryRecord
    anomalies: TelemetryAnomalies
    historical_proximity_alert: Optional[Dict[str, Any]] = None
