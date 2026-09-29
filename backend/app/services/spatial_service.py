"""
PetroNexus Geospatial Service
Calculates geodetic distances between wellheads and executes radius queries.
Compatible with SQLite (using registered haversine_distance) and PostgreSQL/PostGIS.
"""
import math
from typing import List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.models.well import Well
from backend.app.config import settings

def calculate_haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes great-circle distance between two GPS coordinates in kilometers.
    """
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


def get_nearby_wells(
    db: Session,
    center_lat: float,
    center_lon: float,
    radius_km: float = 15.0,
    exclude_well_id: int = None
) -> List[Tuple[Well, float]]:
    """
    Retrieves all offset wells within the specified radius in kilometers,
    returning a sorted list of (Well, distance_km) pairs.
    """
    # Fetch candidate wells
    query = db.query(Well)
    if exclude_well_id:
        query = query.filter(Well.id != exclude_well_id)
    
    all_wells = query.all()
    results = []

    for well in all_wells:
        dist = calculate_haversine_km(center_lat, center_lon, well.latitude, well.longitude)
        if dist <= radius_km:
            results.append((well, dist))

    # Sort ascending by distance
    results.sort(key=lambda x: x[1])
    return results
