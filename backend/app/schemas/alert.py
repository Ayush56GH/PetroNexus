from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

class AlertEvidenceOut(BaseModel):
    id: int
    offset_well_name: str
    event_type: str
    event_depth_m: float
    distance_km: float
    delta_depth_m: float
    correlation_factor: float
    document_citation: str
    page_citation: str
    narrative: str

    class Config:
        from_attributes = True

class AlertOut(BaseModel):
    id: int
    well_id: int
    alert_type: str
    severity: str
    current_depth_m: float
    formation_name: str
    title: str
    message: str
    status: str
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    evidence_items: List[AlertEvidenceOut] = []

    class Config:
        from_attributes = True

class AlertAcknowledge(BaseModel):
    acknowledged_by: Optional[str] = "Drilling Engineer"
