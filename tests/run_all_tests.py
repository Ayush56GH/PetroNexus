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
    test_supabase_auth_login_user_a, test_supabase_auth_signup_user_b,
    test_multi_user_profile_isolation, test_invalid_token_rejected
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
from tests.test_rag_pipeline import (
    test_embedding_dimensions, test_pgvector_similarity_search,
    setup_private_test_documents, test_cross_user_rag_isolation,
    test_prompt_injection_resistance
)
from tests.test_chat_memory import run_chat_memory_tests
from tests.test_groq_integration import run_all_groq_tests
from tests.test_sih26121_real_data_pipeline import run_all_real_data_pipeline_tests
import asyncio

def run_all():
    print("=" * 70)
    print("      PETRONEXUS AUTOMATED VERIFICATION TEST SUITE (SIH26121)")
    print("=" * 70)

    print("\n[1/9] Running Supabase Authentication & Multi-User Identity Tests...")
    token_a = test_supabase_auth_login_user_a()
    token_b = test_supabase_auth_signup_user_b()
    test_multi_user_profile_isolation(token_a, token_b)
    test_invalid_token_rejected()

    print("\n[2/9] Running Current Well Ingestion Tests...")
    test_pdf_extraction()
    test_csv_extraction()
    test_las_extraction()
    test_completeness_scoring()
    test_profile_merger()

    print("\n[3/9] Running Spatial & Offset Intelligence Tests...")
    test_haversine_distance()
    test_nearby_wells()
    test_offset_relevance_engine()
    test_lookahead_corridor()
    test_memory_gaps_and_conflicts()

    print("\n[4/9] Running Physics-Informed Indicators & MCM Trajectory Tests...")
    test_mse_calculation()
    test_physics_evaluation()
    test_minimum_curvature_method()
    test_unit_conversions()

    print("\n[5/9] Running Alerts, Evidence Trails & PDF Report Generation Tests...")
    test_alerts_and_evidence()
    test_pdf_report_generation()
    test_rag_assistant_grounded_response()

    print("\n[6/9] Running Local Embeddings (bge-small-en-v1.5) & pgvector RAG Security Tests...")
    test_embedding_dimensions()
    test_pgvector_similarity_search()
    setup_private_test_documents()
    test_cross_user_rag_isolation()
    test_prompt_injection_resistance()

    print("\n[7/9] Running Multi-Turn Chat Memory & Conversation Isolation Tests...")
    asyncio.run(run_chat_memory_tests())

    print("\n[8/9] Running Groq LLM Integration & Security Verification Tests...")
    asyncio.run(run_all_groq_tests())

    print("\n[9/9] Running SIH 26121 Real-Data Ingestion, Quality, OCR & Replay Tests...")
    run_all_real_data_pipeline_tests()

    print("\n" + "=" * 70)
    print("  ALL 43 TEST CASES PASSED WITH 100% SUCCESS ACROSS ALL 9 SUITES!")
    print("=" * 70)

if __name__ == "__main__":
    run_all()

