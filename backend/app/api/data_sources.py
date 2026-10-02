"""
PetroNexus Data Sources & Provenance Registry API (SIH 26121 Section 3, 39, 46, 58)
Provides CRUD and live connection status for eRTMAC, WITSML, Public Datasets, and User Uploads.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import datetime

from backend.app.database import get_db
from backend.app.models.data_source import DataSource
from backend.app.ingestion.adapters.witsml_adapter import witsml_connector
from backend.app.utils.logger import logger

router = APIRouter(prefix="/data-sources", tags=["Data Sources & Provenance Registry"])

@router.get("")
def list_data_sources(db: Session = Depends(get_db)):
    """Returns all registered data sources with provenance classification and sync status"""
    sources = db.query(DataSource).order_by(DataSource.id.asc()).all()
    out = []
    for s in sources:
        # If it's WITSML connector, sync live memory status
        status = s.status
        notes = s.notes
        if s.source_type == "OIL_ERTMAC" or s.source_type == "OIL_WITSML":
            w_status = witsml_connector.get_connector_status()
            status = w_status["status"]
            notes = w_status["notes"]

        out.append({
            "id": s.id,
            "name": s.name,
            "source_type": s.source_type,
            "organization": s.organization,
            "url": s.url,
            "license": s.license,
            "description": s.description,
            "is_real": s.is_real,
            "is_synthetic": s.is_synthetic,
            "is_public": s.is_public,
            "is_user_uploaded": s.is_user_uploaded,
            "confidence": s.confidence,
            "status": status,
            "record_count": s.record_count,
            "last_sync": s.last_sync.isoformat() if s.last_sync else None,
            "notes": notes,
            "provenance_badge": "REAL DATA" if s.is_real and not s.is_public and not s.is_user_uploaded else (
                "REAL PUBLIC DATA" if s.is_public else (
                    "USER UPLOADED REAL DATA" if s.is_user_uploaded else "DEMO SYNTHETIC DATA"
                )
            )
        })
    return out

@router.get("/{source_id}/status")
def get_source_status(source_id: int, db: Session = Depends(get_db)):
    source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    if source.source_type in ["OIL_ERTMAC", "OIL_WITSML"]:
        return witsml_connector.get_connector_status()

    return {
        "id": source.id,
        "name": source.name,
        "status": source.status,
        "is_real": source.is_real,
        "is_synthetic": source.is_synthetic,
        "last_sync": source.last_sync.isoformat() if source.last_sync else None,
        "record_count": source.record_count,
        "notes": source.notes
    }

@router.post("/witsml/configure")
def configure_witsml(config: Dict[str, Any], db: Session = Depends(get_db)):
    """Configures eRTMAC / WITSML connection endpoint"""
    success = witsml_connector.connect(config)
    status_info = witsml_connector.get_connector_status()
    
    # Update DB record
    source = db.query(DataSource).filter(DataSource.source_type == "OIL_WITSML").first()
    if source:
        source.status = status_info["status"]
        source.url = status_info["endpoint_url"]
        source.last_sync = datetime.datetime.utcnow() if success else source.last_sync
        source.notes = status_info["notes"]
        db.commit()

    return status_info

@router.get("/witsml/channels")
def get_witsml_channels():
    """Returns discovered WITSML channels"""
    return witsml_connector.discover()

@router.post("/witsml/disconnect")
def disconnect_witsml(db: Session = Depends(get_db)):
    witsml_connector.disconnect()
    source = db.query(DataSource).filter(DataSource.source_type == "OIL_WITSML").first()
    if source:
        source.status = "DISCONNECTED"
        source.notes = "eRTMAC connector configured but not connected"
        db.commit()
    return {"status": "DISCONNECTED", "message": "eRTMAC connector disconnected"}
