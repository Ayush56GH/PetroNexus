"""
PetroNexus CSV & Excel Data Source Adapter (SIH 26121 Section 4 & 10)
Supports structured ingestion for Well Headers, Trajectories, Drilling Parameters,
Formation Tops, Historical Events, and Live Telemetry with column preview and mapping.
"""
from pathlib import Path
from typing import Dict, Any, List, Optional
import datetime
import pandas as pd
from sqlalchemy.orm import Session

from backend.app.ingestion.adapters.base import DataSourceAdapter
from backend.app.utils.unit_converter import unit_converter
from backend.app.services.data_quality_service import data_quality_service
from backend.app.models.well import Well
from backend.app.models.trajectory import WellTrajectory
from backend.app.models.formation import Formation, FormationInterval
from backend.app.models.event import DrillingEvent
from backend.app.models.telemetry import TelemetryMeasurement
from backend.app.models.drilling import DrillingParameter
from backend.app.utils.logger import logger

# Canonical Column Synonyms for Automatic Field Mapping
SYNONYMS = {
    "well_name": ["well", "well_name", "wellname", "well_id", "uwi", "api_number", "well_code"],
    "latitude": ["lat", "latitude", "y", "surface_lat", "northing_dd"],
    "longitude": ["lon", "long", "longitude", "x", "surface_lon", "easting_dd"],
    "elevation_m": ["elevation", "elev", "kb", "kb_elev", "ground_elev", "elevation_m"],
    "target_depth_m": ["td", "target_depth", "total_depth", "target_depth_m", "td_md"],
    "current_depth_m": ["current_depth", "current_depth_m"],
    "depth_md": ["depth_md", "bit_depth", "depth", "md", "measured_depth", "hole_depth"],
    "current_formation": ["formation", "fm", "zone", "stratigraphy", "current_formation"],
    "spud_date": ["spud", "spud_date", "start_date", "drill_date"],
    "well_type": ["well_type", "type", "profile", "trajectory_type"],
    "status": ["status", "well_status", "activity"],
    
    # Trajectory
    "inclination_deg": ["inc", "inclination", "dev", "angle", "inclination_deg"],
    "azimuth_deg": ["azi", "azimuth", "direction", "azimuth_deg"],
    "true_vertical_depth_m": ["tvd", "true_vertical_depth", "true_vertical_depth_m"],
    "tvdss_m": ["tvdss", "subsea", "tvd_subsea", "tvdss_m"],
    "dogleg_severity": ["dls", "dogleg", "dogleg_severity"],

    # Drilling Telemetry / Parameters
    "rop": ["rop", "rate_of_penetration", "drilling_speed", "rop_m_hr"],
    "wob": ["wob", "weight_on_bit", "bit_weight", "wob_ton", "wob_klbf"],
    "rpm": ["rpm", "rotary_speed", "surface_rpm", "motor_rpm"],
    "torque": ["torque", "drilling_torque", "torq", "torque_kn_m", "torque_kft_lbs"],
    "spp": ["spp", "standpipe_pressure", "pump_pressure", "pressure"],
    "flow_rate": ["flow", "flow_rate", "flow_in", "pump_rate", "gpm", "lpm"],
    "ecd": ["ecd", "equivalent_circulating_density"],
    "mud_weight": ["mw", "mud_weight", "mud_density", "sg"],
    "hookload": ["hookload", "hook_load", "hkld"],
    "gas_total": ["gas", "total_gas", "gas_total", "gas_units"],

    # Formation Intervals
    "formation_name": ["formation", "formation_name", "top_name", "unit"],
    "top_depth_md_m": ["top", "top_md", "top_depth", "depth_top", "top_depth_md_m"],
    "bottom_depth_md_m": ["bottom", "base", "bottom_md", "base_md", "bottom_depth", "bottom_depth_md_m"],
    "lithology": ["lithology", "lith", "rock_type", "litho"],

    # Historical Events
    "event_type": ["event", "event_type", "incident", "hazard", "problem", "npt_type"],
    "severity": ["severity", "impact", "risk_level"],
    "description": ["description", "remarks", "narrative", "details", "event_description"],
    "immediate_mitigation": ["mitigation", "action", "treatment", "response", "remedy"],
    "primary_cause": ["cause", "primary_cause", "root_cause", "mechanism"],
}

class CsvExcelAdapter(DataSourceAdapter):

    def __init__(self, source_name: str = "CSV/Excel Ingestion Engine", source_type: str = "USER_UPLOAD"):
        super().__init__(source_name, source_type)

    def connect(self, config: Dict[str, Any]) -> bool:
        self.status = "CONNECTED"
        return True

    def validate(self, source_data: Any) -> Dict[str, Any]:
        path = Path(source_data)
        if not path.exists():
            return {"valid": False, "error": f"File {path.name} not found"}
        
        ext = path.suffix.lower()
        if ext not in [".csv", ".xlsx", ".xls", ".tsv"]:
            return {"valid": False, "error": f"Unsupported file extension: {ext}"}

        try:
            df = self._read_dataframe(path, nrows=5)
            return {
                "valid": True,
                "columns": list(df.columns),
                "row_preview_count": len(df),
                "file_size_bytes": path.stat().st_size
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}

    def discover(self, source_data: Any) -> Dict[str, Any]:
        """Reads file header and auto-detects column mappings and likely data types"""
        path = Path(source_data)
        df = self._read_dataframe(path, nrows=20)
        columns = list(df.columns)

        mapping = {}
        for col in columns:
            col_clean = str(col).lower().strip().replace(" ", "_")
            for canonical, syn_list in SYNONYMS.items():
                if col_clean in syn_list or any(s in col_clean for s in syn_list):
                    mapping[col] = canonical
                    break

        # Guess data category
        guessed_category = "WELL_HEADER"
        mapped_canonicals = set(mapping.values())
        if "inclination_deg" in mapped_canonicals or "azimuth_deg" in mapped_canonicals:
            guessed_category = "WELL_TRAJECTORY"
        elif "event_type" in mapped_canonicals or "severity" in mapped_canonicals:
            guessed_category = "HISTORICAL_EVENTS"
        elif "top_depth_md_m" in mapped_canonicals or "bottom_depth_md_m" in mapped_canonicals:
            guessed_category = "FORMATION_TOPS"
        elif "rop" in mapped_canonicals or "torque" in mapped_canonicals or "wob" in mapped_canonicals:
            guessed_category = "TELEMETRY"

        return {
            "file_name": path.name,
            "total_rows": len(df),
            "total_columns": len(columns),
            "columns": columns,
            "detected_mapping": mapping,
            "suggested_mapping": mapping,
            "suggested_category": guessed_category,
            "preview_rows": df.head(5).to_dict(orient="records")
        }

    def ingest(self, source_data: Any, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        options = options or {}
        path = Path(source_data)
        column_mapping = options.get("column_mapping") or {}
        data_category = options.get("data_category") or "WELL_HEADER"
        units_hint = options.get("units_hint") or {}

        df = self._read_dataframe(path)
        
        # Apply mapping
        mapped_records = []
        for _, row in df.iterrows():
            record = {}
            for orig_col, val in row.items():
                target_field = column_mapping.get(orig_col, orig_col)
                if pd.notna(val):
                    record[target_field] = val
            mapped_records.append(record)

        # Normalize units
        normalized_records = self.normalize(mapped_records, units_hint=units_hint)

        # Evaluate quality
        quality_eval = data_quality_service.evaluate_batch(normalized_records)

        return {
            "file_name": path.name,
            "data_category": data_category,
            "total_rows": len(df),
            "records": quality_eval["annotated_records"],
            "normalized_rows": normalized_records,
            "quality_summary": {
                "score": quality_eval["quality_score_pct"],
                "status": quality_eval["overall_status"],
                "flags": quality_eval["top_flags"]
            }
        }

    def normalize(self, raw_records: List[Dict[str, Any]], units_hint: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        normalized = []
        for r in raw_records:
            conv = unit_converter.convert_record(r, units_hint=units_hint)
            normalized.append(conv)
        return normalized

    def store(self, db: Session, ingestion_result: Dict[str, Any], well_id: Optional[int] = None, source_id: Optional[int] = 4) -> Dict[str, Any]:
        data_category = ingestion_result.get("data_category")
        records = ingestion_result.get("records", [])
        imported_count = 0

        target_well = None
        if well_id:
            target_well = db.query(Well).filter(Well.id == well_id).first()

        try:
            if data_category == "WELL_HEADER":
                for r in records:
                    wname = str(r.get("well_name") or f"WELL-{int(datetime.datetime.utcnow().timestamp())}")
                    lat = float(r.get("latitude", 27.35))
                    lon = float(r.get("longitude", 95.31))
                    
                    well = db.query(Well).filter(Well.well_name == wname).first()
                    if not well:
                        well = Well(
                            well_name=wname,
                            latitude=lat,
                            longitude=lon,
                            field=r.get("field", "Assam Basin"),
                            operator=r.get("operator", "Authorized Operator"),
                            status=r.get("status", "OFFSET_REFERENCE"),
                            well_type=r.get("well_type", "DEVELOPMENT_DIRECTIONAL"),
                            current_depth_m=float(r.get("current_depth_m", 2500.0)),
                            target_depth_m=float(r.get("target_depth_m", 3200.0)),
                            current_formation=r.get("current_formation", "Barail Group"),
                            source_id=source_id,
                            source_type=self.source_type,
                            is_real=True,
                            is_synthetic=False,
                            is_user_uploaded=(self.source_type == "USER_UPLOAD"),
                            is_public=(self.source_type == "PUBLIC_DATASET"),
                            visibility="PUBLIC" if self.source_type == "PUBLIC_DATASET" else "ORGANIZATION"
                        )
                        db.add(well)
                    else:
                        well.latitude = lat
                        well.longitude = lon
                        well.is_real = True
                        well.is_synthetic = False
                    db.commit()
                    imported_count += 1

            elif data_category == "WELL_TRAJECTORY":
                if not target_well:
                    target_well = db.query(Well).first()
                for r in records:
                    md = float(r.get("depth_md") or r.get("current_depth_m") or 0.0)
                    tvd = float(r.get("true_vertical_depth_m") or r.get("depth_tvd") or md * 0.98)
                    wt = WellTrajectory(
                        well_id=target_well.id,
                        measured_depth_m=md,
                        inclination_deg=float(r.get("inclination_deg", 0.0)),
                        azimuth_deg=float(r.get("azimuth_deg", 0.0)),
                        true_vertical_depth_m=tvd,
                        tvdss_m=float(r.get("tvdss_m") or tvd - target_well.elevation_m),
                        dogleg_severity=float(r.get("dogleg_severity", 0.0)),
                        source_id=source_id
                    )
                    db.add(wt)
                    imported_count += 1
                db.commit()

            elif data_category == "HISTORICAL_EVENTS":
                if not target_well:
                    target_well = db.query(Well).first()
                for r in records:
                    md = float(r.get("depth_md") or r.get("depth_md_m") or target_well.current_depth_m)
                    ev = DrillingEvent(
                        well_id=target_well.id,
                        event_type=str(r.get("event_type", "Operational Anomaly")),
                        depth_md_m=md,
                        depth_tvd_m=float(r.get("depth_tvd", md * 0.98)),
                        formation_name=str(r.get("formation_name") or target_well.current_formation),
                        severity=str(r.get("severity", "MEDIUM")).upper(),
                        description=str(r.get("description", "Imported operational event from real record.")),
                        primary_cause=str(r.get("primary_cause", "")),
                        immediate_mitigation=str(r.get("immediate_mitigation", "")),
                        source_document_name=str(ingestion_result.get("file_name", "Imported Data")),
                        source_page_number=1,
                        confidence=0.95,
                        source_id=source_id,
                        source_type=self.source_type,
                        is_real=True,
                        is_synthetic=False
                    )
                    db.add(ev)
                    imported_count += 1
                db.commit()

            elif data_category in ["TELEMETRY", "DRILLING_PARAMETERS"]:
                if not target_well:
                    target_well = db.query(Well).first()
                for r in records:
                    md = float(r.get("depth_md") or r.get("current_depth_m") or target_well.current_depth_m)
                    tm = TelemetryMeasurement(
                        well_id=target_well.id,
                        depth_md=md,
                        depth_tvd=float(r.get("depth_tvd", md * 0.98)),
                        rop=r.get("rop"),
                        wob=r.get("wob"),
                        rpm=r.get("rpm"),
                        torque=r.get("torque"),
                        spp=r.get("spp"),
                        flow_in=r.get("flow_rate") or r.get("flow_in"),
                        ecd=r.get("ecd"),
                        mud_weight=r.get("mud_weight"),
                        hookload=r.get("hookload"),
                        quality_status=r.get("quality_status", "GOOD"),
                        source_id=source_id,
                        source_type=self.source_type,
                        is_real=True,
                        is_synthetic=False
                    )
                    db.add(tm)
                    imported_count += 1
                db.commit()

            self.status = "CONNECTED"
            self.last_update = datetime.datetime.utcnow().isoformat()
            return {
                "status": "SUCCESS",
                "imported_records": imported_count,
                "data_category": data_category,
                "target_well_id": target_well.id if target_well else None
            }
        except Exception as e:
            db.rollback()
            self.status = "ERROR"
            self.error_message = str(e)
            logger.error(f"Failed to store imported records: {e}")
            return {"status": "FAILED", "error": str(e), "imported_records": 0}

    def _read_dataframe(self, path: Path, nrows: Optional[int] = None) -> pd.DataFrame:
        ext = path.suffix.lower()
        if ext == ".csv":
            return pd.read_csv(path, nrows=nrows)
        elif ext in [".tsv", ".txt"]:
            return pd.read_csv(path, sep="\t", nrows=nrows)
        else:
            return pd.read_excel(path, nrows=nrows)

csv_excel_adapter = CsvExcelAdapter()
