"""
PetroNexus Ingestion Portal API (SIH 26121 Section 10, 48, 58, 68)
Provides file upload, preview, field mapping confirmation, LAS curve extraction,
and Real Data Replay controls.
"""
from pathlib import Path
from typing import Optional, Dict, Any
import shutil
import json
import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models.ingestion import IngestionJob
from backend.app.models.well import Well
from backend.app.models.audit import AuditLog
from backend.app.ingestion.adapters.csv_adapter import csv_excel_adapter
from backend.app.ingestion.adapters.las_adapter import las_adapter
from backend.app.realtime.replay_engine import replay_engine
from backend.app.utils.logger import logger

router = APIRouter(prefix="/ingestion", tags=["Data Ingestion & Replay Portal"])

@router.post("/preview")
async def preview_file(
    file: UploadFile = File(...)
):
    """
    Saves uploaded file temporarily, detects format, extracts header,
    identifies available columns, suggests field mappings, and returns row previews.
    """
    upload_path = settings.UPLOAD_DIR / file.filename
    with open(upload_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    ext = upload_path.suffix.lower()
    if ext in [".csv", ".xlsx", ".xls", ".tsv"]:
        discovery = csv_excel_adapter.discover(upload_path)
        return {
            "file_name": file.filename,
            "file_type": ext.upper().replace(".", ""),
            "adapter": "CsvExcelAdapter",
            "discovery": discovery
        }
    elif ext == ".las":
        discovery = las_adapter.discover(upload_path)
        return {
            "file_name": file.filename,
            "file_type": "LAS",
            "adapter": "LasAdapter",
            "discovery": discovery
        }
    else:
        return {
            "file_name": file.filename,
            "file_type": ext.upper().replace(".", ""),
            "adapter": "GenericDocument",
            "message": "File ready for document/OCR ingestion."
        }

@router.post("/import")
async def execute_import(
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Executes confirmed import: applies column mapping, unit conversion,
    evaluates quality, stores in database, and creates IngestionJob record.
    """
    file_name = payload.get("file_name")
    if not file_name:
        raise HTTPException(status_code=400, detail="file_name is required")
    
    file_path = settings.UPLOAD_DIR / file_name
    if not file_path.exists():
        # Check documents dir
        file_path = settings.DOCUMENTS_DIR / file_name
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File {file_name} not found on server")

    data_category = payload.get("data_category", "WELL_HEADER")
    column_mapping = payload.get("column_mapping", {})
    well_id = payload.get("well_id")
    units_hint = payload.get("units_hint", {})

    ext = file_path.suffix.lower()
    job = IngestionJob(
        well_id=well_id,
        data_type=data_category,
        file_name=file_name,
        file_path=str(file_path),
        status="PROCESSING",
        column_mapping=column_mapping
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        if ext == ".las":
            ingest_res = las_adapter.ingest(file_path)
            store_res = las_adapter.store(db, ingest_res, well_id=well_id, source_id=4)
            job.rows_total = ingest_res.get("total_samples", 0)
            job.rows_imported = store_res.get("stored_measurements", 0)
            job.quality_summary = ingest_res.get("quality_summary", {})
        else:
            options = {
                "column_mapping": column_mapping,
                "data_category": data_category,
                "units_hint": units_hint
            }
            ingest_res = csv_excel_adapter.ingest(file_path, options)
            store_res = csv_excel_adapter.store(db, ingest_res, well_id=well_id, source_id=4)
            job.rows_total = ingest_res.get("total_rows", 0)
            job.rows_imported = store_res.get("imported_records", 0)
            job.quality_summary = ingest_res.get("quality_summary", {})

        job.status = "COMPLETED"
        job.completed_at = datetime.datetime.utcnow()
        db.commit()

        # Audit log
        audit = AuditLog(
            action="DATA_IMPORT",
            resource=f"ingestion_job:{job.id}",
            details={"file": file_name, "category": data_category, "imported": job.rows_imported}
        )
        db.add(audit)
        db.commit()

        return {
            "status": "SUCCESS",
            "job_id": job.id,
            "file_name": file_name,
            "data_category": data_category,
            "imported_records": job.rows_imported,
            "quality_summary": job.quality_summary,
            "target_well_id": store_res.get("well_id") or well_id
        }
    except Exception as e:
        job.status = "FAILED"
        job.validation_errors = [str(e)]
        db.commit()
        logger.error(f"Import failed for {file_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Import execution failed: {str(e)}")

@router.get("/jobs")
def list_ingestion_jobs(db: Session = Depends(get_db)):
    """Lists recent ingestion jobs"""
    jobs = db.query(IngestionJob).order_by(IngestionJob.created_at.desc()).limit(20).all()
    return [
        {
            "id": j.id,
            "file_name": j.file_name,
            "data_type": j.data_type,
            "status": j.status,
            "rows_total": j.rows_total,
            "rows_imported": j.rows_imported,
            "quality_summary": j.quality_summary,
            "created_at": j.created_at.isoformat() if j.created_at else None,
            "completed_at": j.completed_at.isoformat() if j.completed_at else None
        } for j in jobs
    ]

# Real Data Replay Control Endpoints (Section 68 & 69)
@router.get("/replay/status")
def get_replay_status(well_id: Optional[int] = 23):
    state = replay_engine.get_or_create_state(well_id)
    return {
        "well_id": state["well_id"],
        "is_running": state["is_running"],
        "speed": state["speed"],
        "current_index": state["current_index"],
        "total_records": state["total_records"],
        "dataset_name": state["dataset_name"],
        "current_depth": state.get("current_point", {}).get("depth_md", 2846.0),
        "provenance": "REPLAYING REAL DATA"
    }

@router.post("/replay/control")
def control_replay(payload: Dict[str, Any]):
    """Controls Real Data Replay (play, pause, speed, reset, step)"""
    action = str(payload.get("action", "")).upper()
    well_id = int(payload.get("well_id", 23))
    speed = float(payload.get("speed", 1.0))

    if action == "PLAY":
        replay_engine.play(well_id, speed)
    elif action == "PAUSE":
        replay_engine.pause(well_id)
    elif action == "SPEED":
        replay_engine.set_speed(well_id, speed)
    elif action == "RESET":
        replay_engine.reset(well_id)
    elif action == "STEP":
        return replay_engine.step(well_id)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action}")

    return get_replay_status(well_id)
