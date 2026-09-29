"""
PetroNexus Offset Relevance Engine & Memory Profiler
Scores technical comparability between the active drilling well and nearby offset wells
across 7 dimensions: Distance, Formation, Depth, Trajectory, Drilling Parameters,
Reservoir context, and Historical Event overlap.
Also generates Offset Fingerprints and Well Memory Cards.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models.well import Well
from backend.app.models.formation import FormationInterval
from backend.app.models.event import DrillingEvent
from backend.app.models.drilling import DrillingParameter, CasingRecord
from backend.app.models.trajectory import WellTrajectory
from backend.app.services.spatial_service import calculate_haversine_km

class OffsetRelevanceEngine:

    @staticmethod
    def calculate_comparability(
        db: Session,
        active_well: Well,
        offset_well: Well,
        distance_km: float,
        current_depth_m: float,
        current_formation: str,
        active_params: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Calculates multi-dimensional comparability between active well and an offset candidate.
        """
        # 1. Distance similarity (e.g. 100% at 0km, dropping smoothly up to 25km)
        dist_score = max(0.0, min(100.0, 100.0 - (distance_km / 25.0) * 80.0))

        # 2. Formation similarity
        # Check if offset well penetrates the active formation
        offset_formations = db.query(FormationInterval).filter(FormationInterval.well_id == offset_well.id).all()
        offset_form_names = [f.formation.formation_name for f in offset_formations if f.formation]
        
        form_match_score = 0.0
        if current_formation and (current_formation in offset_form_names or current_formation == offset_well.current_formation):
            form_match_score = 96.0
        elif any(f in str(offset_form_names) for f in ["Formation-X", "Barail", "Tipam"]):
            form_match_score = 75.0
        else:
            form_match_score = 45.0

        # 3. Depth similarity (proximity of TD or intervals to current_depth)
        depth_diff = abs(offset_well.target_depth_m - current_depth_m)
        depth_score = max(20.0, min(100.0, 100.0 - (depth_diff / 1500.0) * 70.0))

        # 4. Trajectory / Well type similarity
        traj_score = 85.0
        if active_well.well_type == offset_well.well_type:
            traj_score = 95.0
        elif "DIRECTIONAL" in str(active_well.well_type) and "DIRECTIONAL" in str(offset_well.well_type):
            traj_score = 90.0
        else:
            traj_score = 70.0

        # 5. Drilling parameter similarity (WOB, RPM, mud weight)
        offset_params = db.query(DrillingParameter).filter(
            DrillingParameter.well_id == offset_well.id
        ).order_by(DrillingParameter.timestamp.desc()).first()

        param_score = 80.0
        if offset_params and active_params:
            wob_sim = max(0, 100 - abs(offset_params.wob_ton - active_params.get("wob", 12.0)) * 5)
            mw_sim = max(0, 100 - abs(offset_params.mud_weight_sg - active_params.get("mud_weight", 1.22)) * 100)
            param_score = (wob_sim + mw_sim) / 2.0

        # 6. Event similarity (documented events around this depth)
        offset_events = db.query(DrillingEvent).filter(
            DrillingEvent.well_id == offset_well.id
        ).all()

        nearby_depth_events = [
            e for e in offset_events 
            if abs(e.depth_md_m - current_depth_m) <= 150.0
        ]
        
        event_score = 50.0
        if nearby_depth_events:
            event_score = 88.0 + min(12.0, len(nearby_depth_events) * 4.0)

        # Weighted composite score
        # Formation & Event & Distance carry highest engineering significance
        weights = {
            "dist": 0.20,
            "form": 0.25,
            "depth": 0.15,
            "traj": 0.10,
            "param": 0.10,
            "event": 0.20
        }
        overall_score = (
            dist_score * weights["dist"] +
            form_match_score * weights["form"] +
            depth_score * weights["depth"] +
            traj_score * weights["traj"] +
            param_score * weights["param"] +
            event_score * weights["event"]
        )

        overall_score = round(overall_score, 1)

        # Categorize
        if overall_score >= 82.0:
            category = "HIGH"
        elif overall_score >= 65.0:
            category = "MODERATE"
        else:
            category = "LOW"

        # Explainable rationale bullets
        why_bullets = []
        if distance_km <= 5.0:
            why_bullets.append(f"Located within high-proximity structural corridor ({distance_km} km away)")
        else:
            why_bullets.append(f"Regional offset located {distance_km} km away in same structural block")

        if form_match_score >= 90:
            why_bullets.append(f"Penetrates identical target stratigraphic sequence ({current_formation})")
        
        if nearby_depth_events:
            event_names = list(set([e.event_type for e in nearby_depth_events]))
            why_bullets.append(f"Documented {len(nearby_depth_events)} historical operational events ({', '.join(event_names)}) near current bit depth interval (+/- 150m)")
        
        if traj_score >= 90:
            why_bullets.append(f"Shares comparable wellbore profile and directional trajectory type ({offset_well.well_type})")

        # Create Offset Fingerprint (Section 45)
        fingerprint = {
            "formation": current_formation,
            "drillability": "Moderate to Hard Sandstone" if "Sand" in current_formation or "X" in current_formation else "Interbedded",
            "hazard_distribution": {
                "mud_loss_count": sum(1 for e in offset_events if "Loss" in e.event_type),
                "torque_spike_count": sum(1 for e in offset_events if "Torque" in e.event_type),
                "stuck_pipe_count": sum(1 for e in offset_events if "Stuck" in e.event_type),
                "kick_count": sum(1 for e in offset_events if "Kick" in e.event_type)
            },
            "similarity_badge": category,
            "overall_relevance_pct": overall_score
        }

        # Create Well Memory Card (Section 46)
        most_critical_event = nearby_depth_events[0] if nearby_depth_events else (offset_events[0] if offset_events else None)
        memory_card = {
            "well_name": offset_well.well_name,
            "distance_km": distance_km,
            "formation": current_formation,
            "key_events_summary": f"{fingerprint['hazard_distribution']['mud_loss_count']} Mud Loss, {fingerprint['hazard_distribution']['torque_spike_count']} Torque Spike",
            "critical_depth_m": most_critical_event.depth_md_m if most_critical_event else offset_well.target_depth_m,
            "lesson": most_critical_event.primary_cause if most_critical_event else "Normal operational progress through sequence.",
            "historical_response": most_critical_event.immediate_mitigation if most_critical_event else "Standard drilling practice followed.",
            "source": f"{most_critical_event.source_document_name} / Page {most_critical_event.source_page_number}" if most_critical_event else "End of Well Report"
        }

        return {
            "well_id": offset_well.id,
            "well_name": offset_well.well_name,
            "distance_km": distance_km,
            "formation_match_pct": round(form_match_score, 1),
            "depth_match_pct": round(depth_score, 1),
            "trajectory_match_pct": round(traj_score, 1),
            "drilling_param_match_pct": round(param_score, 1),
            "event_similarity_pct": round(event_score, 1),
            "overall_relevance_pct": overall_score,
            "relevance_category": category,
            "why_comparable": why_bullets,
            "critical_events": [
                {
                    "id": e.id,
                    "event_type": e.event_type,
                    "depth_md_m": e.depth_md_m,
                    "severity": e.severity,
                    "description": e.description,
                    "mitigation": e.immediate_mitigation,
                    "source": f"{e.source_document_name} p.{e.source_page_number}"
                } for e in nearby_depth_events[:3]
            ],
            "fingerprint": fingerprint,
            "memory_card": memory_card
        }
