"""
PetroNexus Current Well Intelligence Tests
Tests: PDF extraction, CSV extraction, LAS parsing, Completeness scoring, Profile merging.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.database import SessionLocal
from backend.app.models.well import Well
from backend.app.ingestion.file_analyzer import FileAnalyzer
from backend.app.ingestion.completeness_checker import CompletenessChecker
from backend.app.ingestion.profile_merger import ProfileMerger

DOC_DIR = Path(__file__).resolve().parent.parent / "documents"

def test_pdf_extraction():
    pdf_path = DOC_DIR / "Current_Well_Report_OIL-DEMO-023.pdf"
    if not pdf_path.exists():
        print("Skipping PDF test (file not found)")
        return
    extracted = FileAnalyzer.extract_from_pdf(pdf_path)
    assert extracted.get("well_name") == "OIL-DEMO-023"
    assert extracted.get("current_depth_m") == 2846.0
    assert extracted.get("current_formation") == "Formation-X"
    assert extracted.get("rop") == 14.5
    assert extracted.get("wob") == 12.0
    print("[PASS] test_pdf_extraction passed.")

def test_csv_extraction():
    csv_path = DOC_DIR / "Current_Well_Telemetry_OIL-DEMO-023.csv"
    if not csv_path.exists():
        print("Skipping CSV test (file not found)")
        return
    extracted = FileAnalyzer.extract_from_csv_or_excel(csv_path)
    assert extracted.get("current_depth_m") == 2846.0
    assert extracted.get("rop") is not None
    print("[PASS] test_csv_extraction passed.")

def test_las_extraction():
    las_path = DOC_DIR / "Current_Well_Log_OIL-DEMO-023.las"
    if not las_path.exists():
        print("Skipping LAS test (file not found)")
        return
    extracted = FileAnalyzer.extract_from_las(las_path)
    assert extracted.get("well_name") == "OIL-DEMO-023"
    assert extracted.get("current_depth_m") == 2846.0
    print("[PASS] test_las_extraction passed.")

def test_completeness_scoring():
    sample_profile = {
        "well_name": "OIL-DEMO-023",
        "latitude": 27.352,
        "longitude": 95.318,
        "current_depth_m": 2846.0,
        "current_formation": "Formation-X",
        "has_trajectory": False,
        "rop": 14.5,
        "wob": 12.0,
        "rpm": 110.0,
        "torque": 16.8,
        "ecd": 1.28
    }
    comp = CompletenessChecker.evaluate_profile(sample_profile)
    assert comp["readiness_score"] >= 70.0
    assert "Directional survey / trajectory stations" in comp["critical_missing"]
    assert len(comp["next_best_actions"]) > 0
    print(f"[PASS] test_completeness_scoring passed (Readiness: {comp['readiness_score']}%).")

def test_profile_merger():
    db = SessionLocal()
    try:
        well = db.query(Well).filter(Well.well_name == "OIL-DEMO-023").first()
        assert well is not None
        # Merge new survey stations
        new_data = {
            "survey_stations": [
                {"md": 0.0, "inc": 0.0, "azi": 0.0},
                {"md": 1000.0, "inc": 5.0, "azi": 45.0},
                {"md": 2846.0, "inc": 32.0, "azi": 55.0}
            ],
            "rop": 15.2
        }
        res = ProfileMerger.merge_into_well(db, well, new_data, file_name="Test_Survey.csv", file_type="CSV")
        assert res["status"] == "SUCCESS"
        assert len(well.trajectories) == 3
        print("[PASS] test_profile_merger passed.")
    finally:
        db.close()

if __name__ == "__main__":
    test_pdf_extraction()
    test_csv_extraction()
    test_las_extraction()
    test_completeness_scoring()
    test_profile_merger()
    print("All Current Well Ingestion tests passed successfully!")
