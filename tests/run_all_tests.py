"""
PetroNexus Complete Test Runner
Executes all unit and integration test suites:
1. Auth & Credentials
2. Current Well Ingestion & Completeness
3. Offset Intelligence & Look-Ahead Corridor
4. Physics & Minimum Curvature Trajectory
5. Alerts, Evidence Trail, and PDF Reports
"""
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests.test_auth import (
    test_password_hashing, test_jwt_token, test_demo_user_exists
)
from tests.test_current_well import (
    test_pdf_extraction, test_csv_extraction, test_las_extraction,
    test_completeness_scoring, test_profile_merger
)
from tests.test_intelligence import (
    test_haversine_distance, test_nearby_wells, test_offset_relevance_engine,
    test_lookahead_corridor, test_memory_gaps_and_conflicts
)
from tests.test_physics import (
    test_mse_calculation, test_physics_evaluation,
    test_minimum_curvature_method, test_unit_conversions
)
from tests.test_alerts_and_reports import (
    test_alerts_and_evidence, test_pdf_report_generation,
    test_rag_assistant_grounded_response
)

def run_all():
    print("=" * 65)
    print("      PETRONEXUS AUTOMATED VERIFICATION TEST SUITE (SIH26121)")
    print("=" * 65)

    print("\n[1/5] Running Authentication Tests...")
    test_password_hashing()
    test_jwt_token()
    test_demo_user_exists()

    print("\n[2/5] Running Current Well Ingestion Tests...")
    test_pdf_extraction()
    test_csv_extraction()
    test_las_extraction()
    test_completeness_scoring()
    test_profile_merger()

    print("\n[3/5] Running Spatial & Offset Intelligence Tests...")
    test_haversine_distance()
    test_nearby_wells()
    test_offset_relevance_engine()
    test_lookahead_corridor()
    test_memory_gaps_and_conflicts()

    print("\n[4/5] Running Physics-Informed Indicators & MCM Tests...")
    test_mse_calculation()
    test_physics_evaluation()
    test_minimum_curvature_method()
    test_unit_conversions()

    print("\n[5/5] Running Alerts, Evidence, PDF Reports, and RAG Tests...")
    test_alerts_and_evidence()
    test_pdf_report_generation()
    test_rag_assistant_grounded_response()

    print("\n" + "=" * 65)
    print("  ALL 20 TEST CASES PASSED WITH 100% SUCCESS!")
    print("=" * 65)

if __name__ == "__main__":
    run_all()
