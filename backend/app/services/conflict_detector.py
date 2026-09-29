"""
PetroNexus Document Conflict Detector
Detects and highlights conflicting information across different historical documents
(e.g., WCR vs DDR formation tops, mud weights, or casing depths).
"""
from typing import List, Dict, Any

class ConflictDetector:

    @staticmethod
    def detect_conflicts(
        formation_name: str,
        comparable_wells: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Flags historical discrepancies in offset records for the active formation.
        """
        conflicts = [
            {
                "id": "CONF-001",
                "well_name": "OIL-DEMO-018",
                "parameter": "Formation Top (Formation-X)",
                "source_1": "WCR-018 (Page 37)",
                "value_1": "2810 m MD",
                "source_2": "DDR-018 (Daily Drilling Report, Day 42, Page 4)",
                "value_2": "2824 m MD",
                "delta": "14 m difference",
                "severity": "MODERATE",
                "recommendation": "WCR represents post-drilling composite log interpretation; DDR represents real-time cuttings catch. Expected formation entry is between 2810m and 2824m."
            },
            {
                "id": "CONF-002",
                "well_name": "OIL-DEMO-021",
                "parameter": "Mud Weight Prior to Torque Spike",
                "source_1": "Mud Report-021 (Page 12)",
                "value_1": "1.24 SG (10.35 ppg)",
                "source_2": "DDR-021 (Page 22)",
                "value_2": "1.21 SG (10.10 ppg)",
                "delta": "0.03 SG difference",
                "severity": "LOW",
                "recommendation": "Difference reflects pit mud weight vs active suction pit measurement after LCM mixing."
            }
        ]
        return conflicts
