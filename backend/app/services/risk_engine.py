"""
PetroNexus Transparent Historical Attention & Decision Trace Engine
Evaluates historical risk context, provides deterministic Decision Traces,
and compiles the Historical Mitigation Playbook grounded in offset evidence.
"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.well import Well
from backend.app.models.event import DrillingEvent, EventMitigation

class RiskEngine:

    @staticmethod
    def evaluate_historical_attention(
        comparable_wells: List[Dict[str, Any]],
        lookahead_hazards: List[Dict[str, Any]],
        current_depth_m: float,
        formation_name: str
    ) -> Dict[str, Any]:
        """
        Determines transparent attention level and provides clear engineering rationale.
        """
        mud_losses = [h for h in lookahead_hazards if "Loss" in h["event_type"]]
        torque_spikes = [h for h in lookahead_hazards if "Torque" in h["event_type"]]
        stuck_pipes = [h for h in lookahead_hazards if "Stuck" in h["event_type"]]
        kicks = [h for h in lookahead_hazards if "Kick" in h["event_type"]]

        # Calculate evidence level
        total_nearby_hazards = len(lookahead_hazards)
        if total_nearby_hazards >= 3 or len(stuck_pipes) >= 1 or len(mud_losses) >= 2:
            level = "HIGH"
            badge_class = "danger"
        elif total_nearby_hazards >= 1:
            level = "MODERATE"
            badge_class = "warning"
        else:
            level = "LOW"
            badge_class = "success"

        rationale_parts = []
        if mud_losses:
            rationale_parts.append(
                f"{len(mud_losses)} comparable offset event(s) experienced mud losses ahead in this stratigraphic zone."
            )
        if torque_spikes:
            rationale_parts.append(
                f"{len(torque_spikes)} documented torque increase/spike event(s) recorded within current corridor."
            )
        if stuck_pipes:
            rationale_parts.append(
                f"{len(stuck_pipes)} stuck pipe event historically occurred in comparable formation offset."
            )
        if not rationale_parts:
            rationale_parts.append("No critical offset operational hazards flagged within lookahead corridor.")

        return {
            "attention_level": level,
            "badge_class": badge_class,
            "mud_loss_indicator": "HIGH" if len(mud_losses) >= 2 else ("MODERATE" if mud_losses else "LOW"),
            "torque_indicator": "HIGH" if torque_spikes else "MODERATE",
            "stuck_pipe_indicator": "HIGH" if stuck_pipes else "LOW",
            "kick_indicator": "HIGH" if kicks else "LOW",
            "rationale": " ".join(rationale_parts),
            "hazard_count": total_nearby_hazards,
            "comparable_wells_count": len(comparable_wells),
            "disclaimer": "Historical attention indicator based on offset-well documented data. Drilling engineer remains responsible for operational decisions."
        }

    @staticmethod
    def generate_decision_trace(
        active_well: Well,
        nearby_count: int,
        comparable_count: int,
        events_found_count: int,
        lookahead_hazards_count: int,
        attention_level: str
    ) -> List[Dict[str, Any]]:
        """
        Creates an auditable step-by-step decision trace explaining why PetroNexus flagged this context.
        """
        return [
            {
                "step": 1,
                "title": "Bit Context Ingestion",
                "detail": f"Active Well: {active_well.well_name} @ {active_well.current_depth_m} m MD in {active_well.current_formation}."
            },
            {
                "step": 2,
                "title": "Geospatial Boundary Query",
                "detail": f"Identified {nearby_count} offset wells within active search radius."
            },
            {
                "step": 3,
                "title": "Technical Comparability Filter",
                "detail": f"Filtered to {comparable_count} technically comparable wells based on formation, depth, trajectory, and drilling parameters."
            },
            {
                "step": 4,
                "title": "Subsurface Memory Correlation",
                "detail": f"Identified {events_found_count} historical operational events in comparable offset wells."
            },
            {
                "step": 5,
                "title": "Look-Ahead Corridor Scan",
                "detail": f"Located {lookahead_hazards_count} historical events situated in the upcoming depth corridor ahead of the bit."
            },
            {
                "step": 6,
                "title": "Deterministic Engineering Alert",
                "detail": f"Generated {attention_level} Historical Attention Advisory backed by verified document citations."
            }
        ]

    @staticmethod
    def get_mitigation_playbook(db: Session, formation_name: str) -> List[Dict[str, Any]]:
        """
        Compiles the Historical Mitigation Playbook from documented offset actions.
        """
        mitigations = db.query(EventMitigation).filter(
            EventMitigation.formation_name == formation_name
        ).order_by(EventMitigation.step_order.asc()).all()

        if not mitigations:
            # Fallback to general mitigations
            mitigations = db.query(EventMitigation).order_by(EventMitigation.step_order.asc()).limit(5).all()

        results = []
        for m in mitigations:
            results.append({
                "id": m.id,
                "event_type": m.event_type,
                "action_category": m.action_category,
                "title": m.mitigation_title,
                "procedure": m.procedure_text,
                "observed_efficacy": m.observed_efficacy,
                "sample_wells": m.sample_wells_cited,
                "evidence_sources": m.evidence_citations
            })
        return results
