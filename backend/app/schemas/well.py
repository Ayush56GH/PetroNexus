from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class WellBase(BaseModel):
    well_name: str
    well_code: Optional[str] = None
    field: Optional[str] = "Duliajan Basin"
    operator: Optional[str] = "Oil India Limited (OIL)"
    latitude: float
    longitude: float
    elevation_m: Optional[float] = 112.5
    spud_date: Optional[str] = None
    completion_date: Optional[str] = None
    status: Optional[str] = "OFFSET_REFERENCE"
    well_type: Optional[str] = "DEVELOPMENT_DIRECTIONAL"
    target_depth_m: Optional[float] = 3200.0
    current_depth_m: Optional[float] = 2846.0
    current_formation: Optional[str] = "Formation-X"
    is_active_well: Optional[bool] = False

class WellCreate(WellBase):
    pass

class WellOut(WellBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class WellDetailOut(WellOut):
    trajectories_count: int = 0
    formations_count: int = 0
    events_count: int = 0
    documents_count: int = 0
    alerts_count: int = 0

class CompletenessCheckResponse(BaseModel):
    well_id: Optional[int] = None
    well_name: str
    readiness_score: float
    readiness_breakdown: Dict[str, Any]
    critical_missing: List[str]
    recommended_missing: List[str]
    optional_missing: List[str]
    next_best_actions: List[str]
    extracted_summary: Dict[str, Any]

class WellUploadSessionOut(BaseModel):
    id: int
    file_name: str
    file_type: str
    processing_status: str
    extracted_fields: Dict[str, Any]
    missing_fields: List[str]
    quality_score: float
    created_at: datetime

    class Config:
        from_attributes = True
