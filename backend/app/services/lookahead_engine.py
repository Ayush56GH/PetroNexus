"""
PetroNexus Look-Ahead Corridor Engine
Scans comparable offset wells ahead of the current bit position (e.g. +50m, +100m, +150m)
to proactively surface upcoming stratigraphic transitions, loss intervals, and hazard zones.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models.well import Well
from backend.app.models.event import DrillingEvent
from backend.app.models.formation import FormationInterval
from backend.app.services.spatial_service import get_nearby_wells

class LookAheadEngine:

    @staticmethod
    def scan_corridor(
        db: Session,
        active_well: Well,
        current_depth_m: float,
        lookahead_m: float = 100.0, # 50, 100, 150
        radius_km: float = 15.0
    ) -> List[Dict[str, Any]]:
        """
        Detects historical hazards and formation transitions within [current_depth, current_depth + lookahead_m].
        """
        nearby_wells = get_nearby_wells(
            db, 
            active_well.latitude, 
            active_well.longitude, 
            radius_km=radius_km, 
            exclude_well_id=active_well.id
        )

        target_max_depth = current_depth_m + lookahead_m
        hazards_detected = []

        for offset_well, dist_km in nearby_wells:
            # Look for drilling events occurring ahead of current bit
            events = db.query(DrillingEvent).filter(
                DrillingEvent.well_id == offset_well.id,
                DrillingEvent.depth_md_m > current_depth_m,
                DrillingEvent.depth_md_m <= target_max_depth
            ).order_by(DrillingEvent.depth_md_m.asc()).all()

            for ev in events:
                delta_ahead = round(ev.depth_md_m - current_depth_m, 1)
                hazards_detected.append({
                    "offset_well_id": offset_well.id,
                    "offset_well_name": offset_well.well_name,
                    "distance_km": dist_km,
                    "event_type": ev.event_type,
                    "hazard_depth_md_m": ev.depth_md_m,
                    "hazard_depth_tvd_m": ev.depth_tvd_m,
                    "delta_ahead_m": delta_ahead,
                    "formation_name": ev.formation_name,
                    "severity": ev.severity,
                    "description": ev.description,
                    "historical_mitigation": ev.immediate_mitigation or "LCM pill & controlled pump rate",
                    "source_citation": f"{ev.source_document_name}, p.{ev.source_page_number}",
                    "corridor_zone": f"+{int(delta_ahead)} m ahead of bit"
                })

            # Check for formation tops ahead of bit
            formation_intervals = db.query(FormationInterval).filter(
                FormationInterval.well_id == offset_well.id,
                FormationInterval.top_depth_md_m > current_depth_m,
                FormationInterval.top_depth_md_m <= target_max_depth
            ).all()

            for fi in formation_intervals:
                form_name = fi.formation.formation_name if fi.formation else "Stratigraphic Transition"
                delta_ahead = round(fi.top_depth_md_m - current_depth_m, 1)
                hazards_detected.append({
                    "offset_well_id": offset_well.id,
                    "offset_well_name": offset_well.well_name,
                    "distance_km": dist_km,
                    "event_type": "Formation Top Transition",
                    "hazard_depth_md_m": fi.top_depth_md_m,
                    "hazard_depth_tvd_m": fi.top_depth_tvd_m,
                    "delta_ahead_m": delta_ahead,
                    "formation_name": form_name,
                    "severity": "MODERATE",
                    "description": f"Enters {form_name} ({fi.lithology}) with potential pressure or permeability contrast.",
                    "historical_mitigation": "Perform flow check and monitor mud return density before penetrating further.",
                    "source_citation": f"Geological Well Report - {offset_well.well_name}",
                    "corridor_zone": f"+{int(delta_ahead)} m ahead of bit"
                })

        # Sort hazards by closest to bit first
        hazards_detected.sort(key=lambda h: h["delta_ahead_m"])
        return hazards_detected
