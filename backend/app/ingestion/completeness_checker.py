"""
PetroNexus Well Intelligence Readiness & Completeness Engine
Calculates the Data Readiness Score (0-100%) across 11 key operational dimensions,
identifies critical, recommended, and optional missing fields, and recommends
Next Best Data Actions.
"""
from typing import Dict, Any, List

class CompletenessChecker:

    @staticmethod
    def evaluate_profile(profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates active well profile data dictionary and returns:
        - readiness_score (float %)
        - readiness_breakdown (dict of dimensions with status & score)
        - critical_missing (list)
        - recommended_missing (list)
        - optional_missing (list)
        - next_best_actions (list)
        """
        breakdown = {}

        # 1. Identity
        has_name = bool(profile_data.get("well_name"))
        breakdown["Identity"] = {"status": "✓" if has_name else "✗", "score": 100.0 if has_name else 0.0}

        # 2. Location
        has_coords = bool(profile_data.get("latitude") and profile_data.get("longitude"))
        breakdown["Location"] = {"status": "✓" if has_coords else "✗", "score": 100.0 if has_coords else 0.0}

        # 3. Depth
        has_depth = bool(profile_data.get("current_depth_m"))
        breakdown["Depth"] = {"status": "✓" if has_depth else "✗", "score": 100.0 if has_depth else 0.0}

        # 4. Formation
        has_form = bool(profile_data.get("current_formation"))
        breakdown["Formation"] = {"status": "✓" if has_form else "✗", "score": 100.0 if has_form else 0.0}

        # 5. Drilling Parameters (ROP, WOB, RPM, Torque, ECD)
        drilling_keys = ["rop", "wob", "rpm", "torque", "ecd"]
        drilling_present = sum(1 for k in drilling_keys if profile_data.get(k) is not None)
        drilling_pct = (drilling_present / len(drilling_keys)) * 100.0
        breakdown["Drilling parameters"] = {
            "status": "✓" if drilling_pct >= 80 else ("⚠" if drilling_pct > 0 else "✗"),
            "score": round(drilling_pct, 1)
        }

        # 6. Trajectory / Survey
        has_survey = bool(profile_data.get("survey_stations") or profile_data.get("has_trajectory"))
        breakdown["Trajectory"] = {"status": "✓" if has_survey else "⚠", "score": 100.0 if has_survey else 40.0}

        # 7. Mud Program
        has_mud = bool(profile_data.get("mud_weight") or profile_data.get("mud_program"))
        breakdown["Mud program"] = {"status": "✓" if has_mud else "⚠", "score": 100.0 if has_mud else 30.0}

        # 8. BHA
        has_bha = bool(profile_data.get("bha"))
        breakdown["BHA"] = {"status": "✓" if has_bha else "⚠", "score": 100.0 if has_bha else 30.0}

        # 9. Casing
        has_casing = bool(profile_data.get("casing"))
        breakdown["Casing"] = {"status": "✓" if has_casing else "⚠", "score": 100.0 if has_casing else 30.0}

        # 10. Pressure Information
        has_pressure = bool(profile_data.get("spp") or profile_data.get("pore_pressure"))
        breakdown["Pressure"] = {"status": "✓" if has_pressure else "⚠", "score": 100.0 if has_pressure else 40.0}

        # 11. Reservoir Information
        has_res = bool(profile_data.get("reservoir_unit") or profile_data.get("porosity"))
        breakdown["Reservoir"] = {"status": "✓" if has_res else "⚠", "score": 100.0 if has_res else 40.0}

        # Calculate overall readiness percentage
        weights = {
            "Identity": 0.10,
            "Location": 0.10,
            "Depth": 0.15,
            "Formation": 0.15,
            "Drilling parameters": 0.15,
            "Trajectory": 0.10,
            "Mud program": 0.05,
            "BHA": 0.05,
            "Casing": 0.05,
            "Pressure": 0.05,
            "Reservoir": 0.05
        }

        total_score = sum(breakdown[k]["score"] * weights[k] for k in weights)
        total_score = round(total_score, 1)

        # Missing categories
        critical_missing = []
        if not has_depth:
            critical_missing.append("Current measured depth")
        if not has_form:
            critical_missing.append("Current formation")
        if not has_coords:
            critical_missing.append("Wellhead GPS coordinates")
        if drilling_pct < 60:
            critical_missing.append("Current drilling parameters (ROP, WOB, RPM, Torque, ECD)")
        if not has_survey:
            critical_missing.append("Directional survey / trajectory stations")

        recommended_missing = []
        if not has_mud:
            recommended_missing.append("Mud properties / mud report")
        if not has_bha:
            recommended_missing.append("BHA & drill string assembly details")
        if not has_casing:
            recommended_missing.append("Casing program & shoe depth")
        if not profile_data.get("cementing"):
            recommended_missing.append("Cementing reports & TOC verification")
        if not has_res:
            recommended_missing.append("Reservoir unit / lithological details")
        if not profile_data.get("pore_pressure"):
            recommended_missing.append("Pore pressure / fracture gradient data")

        optional_missing = [
            "Petrophysical log LAS curves",
            "Geological cuttings analysis report",
            "Drilling bit wear grading log"
        ]

        # Determine Next Best Data Actions
        next_actions = []
        if not has_survey:
            next_actions.append("Directional survey (CSV/XLSX with MD, Inc, Azi) for True Vertical Depth correlation")
        if not has_mud:
            next_actions.append("Daily Mud Report (WBM/OBM rheology, MW, PV/YP) for loss risk calibration")
        if not has_casing:
            next_actions.append("Casing program & shoe leak-off test (LOT) record")
        if drilling_pct < 80:
            next_actions.append("Current drilling parameter log (WOB, Torque, ECD) for live MSE calculation")
        if not next_actions:
            next_actions.append("All primary well profiles populated. Ready for full offset correlation analysis.")

        return {
            "readiness_score": total_score,
            "readiness_breakdown": breakdown,
            "critical_missing": critical_missing,
            "recommended_missing": recommended_missing,
            "optional_missing": optional_missing,
            "next_best_actions": next_actions
        }
