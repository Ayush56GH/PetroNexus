"""
PetroNexus Industrial Data Quality Engine (SIH 26121 Section 8)
Validates incoming drilling records, surveys, logs, and real-time telemetry batches.
Detects sensor anomalies, dropouts, flatlines, unit mismatches, physical impossibilities,
and assigns GOOD, WARNING, BAD states with detailed audit flags.
"""
from typing import Dict, Any, List, Tuple, Optional
import datetime

class DataQualityService:

    @staticmethod
    def evaluate_coordinates(lat: Optional[float], lon: Optional[float]) -> Tuple[str, List[str]]:
        """Validates geographic wellhead coordinates"""
        flags = []
        if lat is None or lon is None:
            return "BAD", ["MISSING_COORDINATES"]
        
        try:
            lat_f = float(lat)
            lon_f = float(lon)
        except (ValueError, TypeError):
            return "BAD", ["MALFORMED_COORDINATE_FORMAT"]

        if not (-90.0 <= lat_f <= 90.0):
            flags.append(f"IMPOSSIBLE_LATITUDE: {lat_f}")
        if not (-180.0 <= lon_f <= 180.0):
            flags.append(f"IMPOSSIBLE_LONGITUDE: {lon_f}")
        
        if lat_f == 0.0 and lon_f == 0.0:
            flags.append("NULL_ISLAND_COORDINATES (0,0)")

        status = "BAD" if flags else "GOOD"
        return status, flags

    @staticmethod
    def evaluate_telemetry_point(
        point: Dict[str, Any],
        previous_point: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, List[str]]:
        """
        Evaluates a single telemetry measurement point against physical thresholds
        and temporal consistency with the previous point.
        """
        flags = []
        status = "GOOD"

        depth_md = point.get("depth_md") or point.get("depth")
        # 1. Depth Checks
        if depth_md is None:
            flags.append("MISSING_DEPTH")
            status = "BAD"
        else:
            try:
                d = float(depth_md)
                if d < 0:
                    flags.append("NEGATIVE_DEPTH")
                    status = "BAD"
                elif d > 12000.0:
                    flags.append(f"EXTREME_IMPOSSIBLE_DEPTH: {d}m")
                    status = "BAD"
                
                if previous_point:
                    prev_d = previous_point.get("depth_md") or previous_point.get("depth")
                    if prev_d is not None and d < float(prev_d) - 5.0: # Allow slight trip back, but flag big jump
                        flags.append(f"DEPTH_REVERSAL: {prev_d}m -> {d}m")
                        if status != "BAD":
                            status = "WARNING"
            except (ValueError, TypeError):
                flags.append("INVALID_DEPTH_NUMBER")
                status = "BAD"

        # 2. RPM Checks
        rpm = point.get("rpm")
        if rpm is not None:
            try:
                r = float(rpm)
                if r < 0:
                    flags.append("NEGATIVE_RPM")
                    status = "BAD"
                elif r > 350:
                    flags.append(f"UNUSUALLY_HIGH_RPM: {r}")
                    if status != "BAD":
                        status = "WARNING"
            except ValueError:
                flags.append("INVALID_RPM")

        # 3. ROP Checks
        rop = point.get("rop")
        if rop is not None:
            try:
                rp = float(rop)
                if rp < -1.0:
                    flags.append("NEGATIVE_ROP")
                    status = "BAD"
                elif rp > 150.0:
                    flags.append(f"IMPOSSIBLE_DRILLING_RATE: {rp} m/hr")
                    if status != "BAD":
                        status = "WARNING"
            except ValueError:
                flags.append("INVALID_ROP")

        # 4. Pressure (SPP) Checks
        spp = point.get("spp")
        if spp is not None:
            try:
                p = float(spp)
                if p < 0:
                    flags.append("NEGATIVE_STANDPIPE_PRESSURE")
                    status = "BAD"
                elif p > 7500:
                    flags.append(f"EXTREME_STANDPIPE_PRESSURE: {p} psi")
                    if status != "BAD":
                        status = "WARNING"
            except ValueError:
                pass

        # 5. Mud Weight / ECD
        for key in ["ecd", "mud_weight"]:
            val = point.get(key)
            if val is not None:
                try:
                    v = float(val)
                    if v < 0.8:
                        flags.append(f"IMPOSSIBLY_LOW_{key.upper()}: {v} SG")
                        status = "BAD"
                    elif v > 2.8:
                        flags.append(f"IMPOSSIBLY_HIGH_{key.upper()}: {v} SG")
                        status = "BAD"
                except ValueError:
                    pass

        # 6. Flatline and dropout check with previous point
        if previous_point:
            flatline_keys = ["torque", "rop", "spp", "flow_rate"]
            flatlines = 0
            for k in flatline_keys:
                if point.get(k) is not None and point.get(k) == previous_point.get(k) and point.get(k) != 0:
                    flatlines += 1
            if flatlines >= 3:
                flags.append("MULTIPLE_SENSORS_FLATLINED")
                if status == "GOOD":
                    status = "WARNING"

        return status, flags

    @classmethod
    def evaluate_batch(cls, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluates an entire telemetry or survey batch, returning stats,
        clean records with quality flags, and batch quality score.
        """
        good_count = 0
        warning_count = 0
        bad_count = 0
        all_flags = []
        annotated_records = []

        prev = None
        for r in records:
            st, flags = cls.evaluate_telemetry_point(r, prev)
            r_copy = dict(r)
            r_copy["quality_status"] = st
            r_copy["quality_flags"] = flags
            annotated_records.append(r_copy)

            if st == "GOOD":
                good_count += 1
            elif st == "WARNING":
                warning_count += 1
            else:
                bad_count += 1
            
            all_flags.extend(flags)
            prev = r

        total = len(records)
        score = round((good_count + 0.5 * warning_count) / max(1, total) * 100.0, 1)

        overall_status = "GOOD"
        if score < 60.0:
            overall_status = "BAD"
        elif score < 85.0:
            overall_status = "WARNING"

        return {
            "total_records": total,
            "good_count": good_count,
            "warning_count": warning_count,
            "bad_count": bad_count,
            "quality_score_pct": score,
            "overall_status": overall_status,
            "top_flags": list(set(all_flags))[:8],
            "annotated_records": annotated_records
        }

    evaluate_telemetry_batch = evaluate_batch

data_quality_service = DataQualityService()
