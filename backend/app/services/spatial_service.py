"""
PetroNexus Geospatial Engine (SIH 26121 Section 20)
Provides true geodetic distance and compass bearing calculations.
Supports native PostGIS ST_DWithin / ST_Distance when PostgreSQL is active,
and high-speed Haversine geodetic queries on SQLite.
"""
import math
from typing import List, Tuple, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.models.well import Well
from backend.app.config import settings
from backend.app.utils.logger import logger

COMPASS_DIRECTIONS = [
    "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
]

def calculate_haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes great-circle geodetic distance between two GPS coordinates in kilometers."""
    if None in (lat1, lon1, lat2, lon2):
        return 999999.0
    r = 6371.0 # Earth's radius in kilometers
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(r * c, 2)

def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> Tuple[float, str]:
    """Calculates forward azimuth in degrees (0-360) and 16-point compass heading"""
    if None in (lat1, lon1, lat2, lon2):
        return 0.0, "N"
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    bearing_rad = math.atan2(y, x)
    bearing_deg = (math.degrees(bearing_rad) + 360.0) % 360.0
    
    idx = int((bearing_deg + 11.25) / 22.5) % 16
    compass = COMPASS_DIRECTIONS[idx]
    return round(bearing_deg, 1), compass

def get_nearby_wells(
    db: Session,
    center_lat: float,
    center_lon: float,
    radius_km: float = 25.0,
    exclude_well_id: Optional[int] = None
) -> List[Tuple[Well, float]]:
    """
    Retrieves all offset wells within the specified radius in kilometers,
    returning a sorted list of (Well, distance_km) pairs.
    Uses PostGIS if configured on PostgreSQL, else fast Haversine.
    """
    is_postgres = settings.DATABASE_URL.startswith("postgresql")
    
    if is_postgres:
        try:
            # PostGIS ST_DWithin query using geography type (radius in meters)
            query_sql = text("""
                SELECT id, 
                       ST_Distance(
                           ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography,
                           ST_SetSRID(ST_MakePoint(:center_lon, :center_lat), 4326)::geography
                       ) / 1000.0 AS dist_km
                FROM wells
                WHERE ST_DWithin(
                    ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography,
                    ST_SetSRID(ST_MakePoint(:center_lon, :center_lat), 4326)::geography,
                    :radius_m
                )
                AND (:exclude_id IS NULL OR id != :exclude_id)
                ORDER BY dist_km ASC;
            """)
            res = db.execute(query_sql, {
                "center_lat": center_lat,
                "center_lon": center_lon,
                "radius_m": radius_km * 1000.0,
                "exclude_id": exclude_well_id
            }).fetchall()

            if res:
                well_ids = [r[0] for r in res]
                dist_map = {r[0]: round(float(r[1]), 2) for r in res}
                wells = db.query(Well).filter(Well.id.in_(well_ids)).all()
                wells_dict = {w.id: w for w in wells}
                return [(wells_dict[wid], dist_map[wid]) for wid in well_ids if wid in wells_dict]
        except Exception as e:
            logger.warning(f"PostGIS query fallback to python geodetic: {e}")

    # Universal / SQLite geodetic fallback
    query = db.query(Well)
    if exclude_well_id:
        query = query.filter(Well.id != exclude_well_id)
    
    all_wells = query.all()
    results = []

    for well in all_wells:
        dist = calculate_haversine_km(center_lat, center_lon, well.latitude, well.longitude)
        if dist <= radius_km:
            results.append((well, dist))

    results.sort(key=lambda x: x[1])
    return results
