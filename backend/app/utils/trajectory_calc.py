"""
PetroNexus Minimum Curvature Method (MCM) Wellbore Trajectory Engine
Calculates true vertical depth (TVD), TVDSS, Dogleg Severity (DLS),
and spatial coordinate offsets (North/East) along wellbore surveys.
"""
import math
from typing import List, Dict, Any, Tuple

def minimum_curvature(
    md1: float, inc1_deg: float, azi1_deg: float,
    md2: float, inc2_deg: float, azi2_deg: float
) -> Tuple[float, float, float, float]:
    """
    Computes delta TVD, delta North, delta East, and Dogleg Severity (deg/30m)
    between two survey stations using the industry standard Minimum Curvature Method.
    """
    delta_md = md2 - md1
    if delta_md <= 0:
        return 0.0, 0.0, 0.0, 0.0

    i1 = math.radians(inc1_deg)
    i2 = math.radians(inc2_deg)
    a1 = math.radians(azi1_deg)
    a2 = math.radians(azi2_deg)

    # Dogleg angle calculation
    cos_dl = math.cos(i2 - i1) - (math.sin(i1) * math.sin(i2) * (1.0 - math.cos(a2 - a1)))
    cos_dl = max(-1.0, min(1.0, cos_dl))
    dogleg_rad = math.acos(cos_dl)

    # Ratio factor (RF)
    if abs(dogleg_rad) < 1e-6:
        rf = 1.0
    else:
        rf = (2.0 / dogleg_rad) * math.tan(dogleg_rad / 2.0)

    # Coordinate changes
    delta_tvd = (delta_md / 2.0) * (math.cos(i1) + math.cos(i2)) * rf
    delta_north = (delta_md / 2.0) * (math.sin(i1) * math.cos(a1) + math.sin(i2) * math.cos(a2)) * rf
    delta_east = (delta_md / 2.0) * (math.sin(i1) * math.sin(a1) + math.sin(i2) * math.sin(a2)) * rf

    # DLS in deg per 30m
    dls_deg_30m = (math.degrees(dogleg_rad) / delta_md) * 30.0 if delta_md > 0 else 0.0

    return delta_tvd, delta_north, delta_east, dls_deg_30m


def calculate_trajectory(
    survey_stations: List[Dict[str, float]], 
    kb_elevation_m: float = 112.5
) -> List[Dict[str, Any]]:
    """
    Given a list of survey stations with keys:
    [{"md": ..., "inc": ..., "azi": ...}, ...]
    Calculates full trajectory profile: TVD, TVDSS, Northing, Easting, DLS.
    """
    if not survey_stations:
        return []

    # Sort stations by MD
    sorted_stations = sorted(survey_stations, key=lambda s: s.get("md", 0.0))
    results = []

    # Initialize at surface (MD=0)
    current_md = 0.0
    current_inc = 0.0
    current_azi = 0.0
    current_tvd = 0.0
    current_north = 0.0
    current_east = 0.0

    for stn in sorted_stations:
        next_md = float(stn.get("md", 0.0))
        next_inc = float(stn.get("inc", 0.0))
        next_azi = float(stn.get("azi", 0.0))

        if next_md == 0:
            current_inc = next_inc
            current_azi = next_azi
            results.append({
                "measured_depth_m": 0.0,
                "inclination_deg": next_inc,
                "azimuth_deg": next_azi,
                "true_vertical_depth_m": 0.0,
                "tvdss_m": -kb_elevation_m,
                "dogleg_severity": 0.0,
                "northing_m": 0.0,
                "easting_m": 0.0
            })
            continue

        d_tvd, d_n, d_e, dls = minimum_curvature(
            current_md, current_inc, current_azi,
            next_md, next_inc, next_azi
        )

        current_tvd += d_tvd
        current_north += d_n
        current_east += d_e
        current_md = next_md
        current_inc = next_inc
        current_azi = next_azi

        # TVDSS = TVD - Elevation
        tvdss = current_tvd - kb_elevation_m

        results.append({
            "measured_depth_m": round(current_md, 2),
            "inclination_deg": round(current_inc, 2),
            "azimuth_deg": round(current_azi, 2),
            "true_vertical_depth_m": round(current_tvd, 2),
            "tvdss_m": round(tvdss, 2),
            "dogleg_severity": round(dls, 2),
            "northing_m": round(current_north, 2),
            "easting_m": round(current_east, 2)
        })

    return results
