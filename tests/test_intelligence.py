"""
PetroNexus Offset Intelligence & Look-Ahead Engine Tests
Tests: Spatial radius search, 7-factor comparability scoring, Look-Ahead scan,
Memory Gaps, and Conflict Detection.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.database import SessionLocal
from backend.app.models.well import Well
from backend.app.services.spatial_service import get_nearby_wells, calculate_haversine_km
from backend.app.services.offset_engine import OffsetRelevanceEngine
from backend.app.services.lookahead_engine import LookAheadEngine
from backend.app.services.memory_gap_detector import MemoryGapDetector
from backend.app.services.conflict_detector import ConflictDetector

def test_haversine_distance():
    # Distance between Base and offset ~0.03 deg lat is ~3.3-4.8 km
    dist = calculate_haversine_km(27.352, 95.318, 27.384, 95.346)
    assert 3.5 <= dist <= 5.5
    print(f"[PASS] test_haversine_distance passed ({dist} km).")

def test_nearby_wells():
    db = SessionLocal()
    try:
        well23 = db.query(Well).filter(Well.well_name == "OIL-DEMO-023").first()
        nearby = get_nearby_wells(db, well23.latitude, well23.longitude, radius_km=15.0, exclude_well_id=well23.id)
        assert len(nearby) > 0
        assert any(w.well_name == "OIL-DEMO-018" for w, _ in nearby)
        print(f"[PASS] test_nearby_wells passed (Found {len(nearby)} wells within 15 km).")
    finally:
        db.close()

def test_offset_relevance_engine():
    db = SessionLocal()
    try:
        well23 = db.query(Well).filter(Well.well_name == "OIL-DEMO-023").first()
        well18 = db.query(Well).filter(Well.well_name == "OIL-DEMO-018").first()
        dist = calculate_haversine_km(well23.latitude, well23.longitude, well18.latitude, well18.longitude)
        
        comp = OffsetRelevanceEngine.calculate_comparability(
            db, well23, well18, dist, 2846.0, "Formation-X"
        )
        assert comp["overall_relevance_pct"] >= 75.0
        assert comp["relevance_category"] in ["HIGH", "MODERATE"]
        assert len(comp["why_comparable"]) > 0
        assert comp["fingerprint"] is not None
        assert comp["memory_card"] is not None
        print(f"[PASS] test_offset_relevance_engine passed (OIL-DEMO-018 relevance: {comp['overall_relevance_pct']}%).")
    finally:
        db.close()

def test_lookahead_corridor():
    db = SessionLocal()
    try:
        well23 = db.query(Well).filter(Well.well_name == "OIL-DEMO-023").first()
        hazards = LookAheadEngine.scan_corridor(
            db, well23, current_depth_m=2846.0, lookahead_m=150.0, radius_km=15.0
        )
        assert len(hazards) > 0
        # Check OIL-DEMO-018 mud loss @ 2860m (14m ahead)
        mud_losses = [h for h in hazards if "018" in h["offset_well_name"] and "Loss" in h["event_type"]]
        assert len(mud_losses) > 0
        assert mud_losses[0]["delta_ahead_m"] == 14.0
        print(f"[PASS] test_lookahead_corridor passed (Detected {len(hazards)} hazards, including OIL-018 Loss @ +14m).")
    finally:
        db.close()

def test_memory_gaps_and_conflicts():
    db = SessionLocal()
    try:
        gaps = MemoryGapDetector.detect_gaps(db, [{"well_id": 18, "well_name": "OIL-DEMO-018"}], "Formation-X", 2846.0)
        assert isinstance(gaps, list)
        
        conflicts = ConflictDetector.detect_conflicts("Formation-X", [])
        assert len(conflicts) > 0
        print(f"[PASS] test_memory_gaps_and_conflicts passed (Detected {len(gaps)} gaps and {len(conflicts)} conflicts).")
    finally:
        db.close()

if __name__ == "__main__":
    test_haversine_distance()
    test_nearby_wells()
    test_offset_relevance_engine()
    test_lookahead_corridor()
    test_memory_gaps_and_conflicts()
    print("All Intelligence tests passed successfully!")
