from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class ContextPackRequest(BaseModel):
    well_id: int
    include_ai_synthesis: bool = True
    export_format: str = "json" # "json" or "pdf"

class ContextPackResponse(BaseModel):
    generated_at: str
    active_well_summary: Dict[str, Any]
    current_parameters: Dict[str, Any]
    formation_context: Dict[str, Any]
    nearby_wells: List[Dict[str, Any]]
    comparable_wells: List[Dict[str, Any]]
    historical_events: List[Dict[str, Any]]
    lookahead_hazards: List[Dict[str, Any]]
    historical_mitigations: List[Dict[str, Any]]
    active_alerts: List[Dict[str, Any]]
    missing_data_report: Dict[str, Any]
    memory_gaps: List[Dict[str, Any]]
    data_conflicts: List[Dict[str, Any]]
    source_citations: List[Dict[str, Any]]
    ai_synthesis: Optional[str] = None
    pdf_download_url: Optional[str] = None

class PreIntervalBriefResponse(BaseModel):
    well_id: int
    well_name: str
    current_depth_m: float
    upcoming_interval_m: str
    upcoming_formation: str
    offset_wells_count: int
    historical_events_count: int
    primary_hazard_attention: List[str]
    most_comparable_well: Dict[str, Any]
    documented_mitigations: List[str]
    evidence_sources: List[str]
