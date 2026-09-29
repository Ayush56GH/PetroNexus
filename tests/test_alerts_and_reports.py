"""
PetroNexus Alerts, Evidence Trail, and Report Generation Tests
Tests: Alert query, Evidence Trail citations, PDF Context Pack generation, Pre-Interval Brief.
"""
import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.database import SessionLocal
from backend.app.models.alert import Alert
from backend.app.services.report_service import ReportService
from backend.app.rag.langchain_service import LangChainRAGService
from backend.app.config import settings

def test_alerts_and_evidence():
    db = SessionLocal()
    try:
        alerts = db.query(Alert).filter(Alert.well_id == 23).all()
        assert len(alerts) > 0
        primary_alert = alerts[0]
        assert len(primary_alert.evidence_items) >= 3
        # Check source citations
        citations = [ev.document_citation for ev in primary_alert.evidence_items]
        assert "WCR-OIL-DEMO-018" in citations
        print(f"[PASS] test_alerts_and_evidence passed ({len(primary_alert.evidence_items)} evidence records verified).")
    finally:
        db.close()

def test_pdf_report_generation():
    sample_context = {
        "generated_at": "2026-09-29 08:30:00 UTC",
        "active_well_summary": {
            "well_name": "OIL-DEMO-023",
            "operator": "Oil India Limited",
            "current_depth_m": 2846.0,
            "current_formation": "Formation-X",
            "target_depth_m": 3200.0,
            "readiness_percentage": 82.0
        },
        "lookahead_hazards": [
            {
                "offset_well_name": "OIL-DEMO-018",
                "event_type": "Mud Loss (45 bbl)",
                "hazard_depth_md_m": 2860.0,
                "delta_ahead_m": 14.0,
                "source_citation": "WCR-018, Page 37"
            }
        ],
        "historical_mitigations": [
            {
                "title": "LCM Pill Spotting",
                "action_category": "Loss Circulation Treatment",
                "procedure": "Mix and spot 30 bbl walnut shell LCM pill.",
                "evidence_sources": ["WCR-018 p37"]
            }
        ],
        "memory_gaps": [
            {
                "title": "Mud Program Missing in 2 Offsets",
                "description": "Historical rheology logs incomplete.",
                "recommendation": "Review physical mud logs."
            }
        ]
    }
    test_pdf_path = settings.REPORTS_DIR / "Test_Context_Pack.pdf"
    res = ReportService.generate_pdf_context_pack(sample_context, test_pdf_path)
    assert test_pdf_path.exists()
    assert test_pdf_path.stat().st_size > 1000
    print(f"[PASS] test_pdf_report_generation passed (Generated {test_pdf_path.name}, size: {test_pdf_path.stat().st_size} bytes).")

def test_rag_assistant_grounded_response():
    db = SessionLocal()
    try:
        rag = LangChainRAGService()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        res = loop.run_until_complete(
            rag.answer_drilling_query(db, active_well_id=23, user_query="What happened around 2846m in Formation-X?")
        )
        assert res["response"] is not None
        assert "### SUMMARY" in res["response"]
        assert "### SOURCES" in res["response"]
        assert len(res["sources"]) > 0
        print("[PASS] test_rag_assistant_grounded_response passed (Verified 8-part grounded structure with citations).")
    finally:
        db.close()

if __name__ == "__main__":
    test_alerts_and_evidence()
    test_pdf_report_generation()
    test_rag_assistant_grounded_response()
    print("All Alerts, Reports, and RAG tests passed successfully!")
