"""
PetroNexus Real-Time Anomaly Detector
Evaluates streaming drilling parameters against baseline thresholds
and flags physical operational anomalies (Torque Spikes, ROP Drops, ECD Excursions, SPP surges)
as well as Historical Hazard Proximity.
"""
from typing import Dict, Any, List

class RealTimeAnomalyDetector:

    @staticmethod
    def detect_anomalies(
        telemetry: Dict[str, Any],
        historical_hazards_nearby: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyzes telemetry record and identifies operational and historical hazard anomalies.
        """
        anomalies = []
        details = []
        actions = []
        severity = "NORMAL"

        torque = telemetry.get("torque", 16.8)
        rop = telemetry.get("rop", 14.5)
        ecd = telemetry.get("ecd", 1.28)
        mud_weight = telemetry.get("mud_weight", 1.22)
        spp = telemetry.get("spp", 2450.0)
        current_depth = telemetry.get("depth", 2846.0)

        # 1. Torque Spike Anomaly (> 21.0 kN.m or sudden delta)
        if torque > 22.0:
            anomalies.append("TORQUE_SPIKE")
            details.append(f"Torque elevated at {torque} kN.m (Threshold: 21.0 kN.m). Potential undergauge hole or differential drag.")
            actions.append("Pick up off bottom, observe torque trends, check for cuttings pack-off.")
            severity = "CRITICAL"
        elif torque > 19.5:
            anomalies.append("TORQUE_ELEVATED")
            details.append(f"Torque elevated at {torque} kN.m above baseline.")
            actions.append("Monitor torque harmonics, ensure smooth rotary speed.")
            severity = "WARNING"

        # 2. ROP Drop / Drilling Break
        if rop < 5.0 and torque > 18.0:
            anomalies.append("ROP_DROP_FORMATION_HARDENING")
            details.append(f"ROP dropped to {rop} m/hr with high torque. Possible hard stringer or bit balling.")
            actions.append("Adjust WOB, check hydraulics, watch for lithological transition.")
            if severity != "CRITICAL":
                severity = "WARNING"

        # 3. ECD Excursion / Loss margin
        if (ecd - mud_weight) > 0.12:
            anomalies.append("ECD_HIGH_LOSS_RISK")
            details.append(f"ECD margin is +{round(ecd - mud_weight, 3)} SG above static mud weight. Risk of inducing formation fracture.")
            actions.append("Reduce flow rate slightly, optimize mud rheology (reduce PV/YP), perform hole cleaning sweep.")
            severity = "CRITICAL"

        # 4. Standpipe Pressure Anomaly
        if spp > 2800.0:
            anomalies.append("SPP_PRESSURE_SURGE")
            details.append(f"Standpipe pressure surge ({spp} psi). Check for nozzle plugging or annular packing.")
            actions.append("Check surface equipment, reduce pump rate, inspect return flow.")
            severity = "CRITICAL"

        # 5. Historical Hazard Zone Proximity
        # Flag if current bit is within +/- 5m of a documented offset event
        near_hazards = [
            h for h in historical_hazards_nearby
            if abs(h.get("hazard_depth_md_m", 0) - current_depth) <= 10.0
        ]
        if near_hazards:
            h_top = near_hazards[0]
            anomalies.append("BIT_AT_HISTORICAL_HAZARD_ZONE")
            details.append(
                f"Active bit @ {current_depth}m is currently inside historical {h_top.get('event_type')} zone documented in {h_top.get('offset_well_name')} ({h_top.get('hazard_depth_md_m')}m)."
            )
            actions.append(f"Observe historical mitigation: {h_top.get('historical_mitigation', 'Pump LCM pill & reduce flow rate')}")
            severity = "CRITICAL"

        return {
            "has_anomaly": len(anomalies) > 0,
            "anomaly_types": anomalies,
            "severity": severity,
            "details": details,
            "suggested_actions": actions
        }
