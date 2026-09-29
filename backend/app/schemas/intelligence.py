from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class OffsetAnalysisRequest(BaseModel):
    well_id: int
    radius_km: float = 10.0
    current_depth: float = 2846.0
    formation: Optional[str] = "Formation-X"
    lookahead_m: float = 100.0

class ComparableWellInfo(BaseModel):
    well_id: int
    well_name: str
    distance_km: float
    formation_match_pct: float
    depth_match_pct: float
    trajectory_match_pct: float
    drilling_param_match_pct: float
    event_similarity_pct: float
    overall_relevance_pct: float
    relevance_category: str # HIGH, MODERATE, LOW
    why_comparable: List[str]
    critical_events: List[Dict[str, Any]]
    fingerprint: Dict[str, Any]

class LookAheadRequest(BaseModel):
    well_id: int
    current_depth: float = 2846.0
    lookahead_m: float = 100.0 # 50, 100, 150
    formation: Optional[str] = "Formation-X"

class LookAheadHazard(BaseModel):
    offset_well_id: int
    offset_well_name: str
    distance_km: float
    event_type: str
    hazard_depth_md_m: float
    hazard_depth_tvd_m: Optional[float] = None
    delta_ahead_m: float
    formation_name: str
    severity: str
    description: str
    historical_mitigation: str
    source_citation: str

class OffsetAnalysisResponse(BaseModel):
    active_well: Dict[str, Any]
    nearby_wells: List[Dict[str, Any]]
    comparable_wells: List[ComparableWellInfo]
    historical_events: List[Dict[str, Any]]
    lookahead_events: List[LookAheadHazard]
    historical_attention: Dict[str, Any]
    decision_trace: List[Dict[str, Any]]
    mitigation_playbook: List[Dict[str, Any]]
    memory_gaps: List[Dict[str, Any]]
    data_conflicts: List[Dict[str, Any]]

class ScenarioAnalysisRequest(BaseModel):
    well_id: int
    current_depth: float
    target_depth: float
    formation: str
    radius_km: float = 10.0
    lookahead_m: float = 150.0

class WellComparisonRequest(BaseModel):
    well_ids: List[int]
