"""
PetroNexus Log ASCII Standard (LAS) 2.0 / 3.0 Adapter (SIH 26121 Section 4, 10 & 71)
Parses petrophysical well logs, header metadata, curve definitions, and depth-indexed curve readings.
"""
from pathlib import Path
from typing import Dict, Any, List, Optional
import re
import datetime
from sqlalchemy.orm import Session

from backend.app.ingestion.adapters.base import DataSourceAdapter
from backend.app.models.well import Well
from backend.app.models.telemetry import TelemetryMeasurement
from backend.app.models.drilling import DrillingParameter
from backend.app.services.data_quality_service import data_quality_service
from backend.app.utils.logger import logger

class LasAdapter(DataSourceAdapter):

    def __init__(self, source_name: str = "Petrophysical LAS Log Engine", source_type: str = "USER_UPLOAD"):
        super().__init__(source_name, source_type)

    def connect(self, config: Dict[str, Any]) -> bool:
        self.status = "CONNECTED"
        return True

    def validate(self, source_data: Any) -> Dict[str, Any]:
        path = Path(source_data)
        if not path.exists():
            return {"valid": False, "error": f"File {path.name} not found"}
        
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            header_sample = "".join([f.readline() for _ in range(50)])
        
        if "~V" not in header_sample and "~W" not in header_sample:
            return {"valid": False, "error": "Invalid LAS file: missing standard ~VERSION or ~WELL sections"}

        return {"valid": True, "file_name": path.name, "file_size": path.stat().st_size}

    def discover(self, source_data: Any) -> Dict[str, Any]:
        """Parses header blocks, well properties, and curve definitions"""
        path = Path(source_data)
        well_info = {}
        curve_info = []
        current_section = None

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line_str = line.strip()
                if not line_str or line_str.startswith("#"):
                    continue

                if line_str.startswith("~"):
                    sec_char = line_str[1:2].upper()
                    if sec_char == "W":
                        current_section = "WELL"
                    elif sec_char == "C":
                        current_section = "CURVE"
                    elif sec_char == "P":
                        current_section = "PARAM"
                    elif sec_char in ["A", "O"]:
                        current_section = "ASCII"
                        break # Finished header
                    continue

                if current_section == "WELL":
                    m = re.match(r"([A-Za-z0-9_\-]+)\s*\.\s*([^:]*)\s*:\s*(.*)", line_str)
                    if m:
                        mnemonic = m.group(1).strip().upper()
                        val_part = m.group(2).strip()
                        desc = m.group(3).strip()
                        tokens = val_part.split()
                        val = desc
                        if len(tokens) >= 2:
                            try:
                                float(tokens[0])
                                val = tokens[0]
                            except ValueError:
                                val = tokens[1]
                        elif tokens:
                            val = tokens[0]
                        well_info[mnemonic] = {
                            "value": val,
                            "description": desc
                        }

                elif current_section == "CURVE":
                    m = re.match(r"([A-Za-z0-9_\-]+)\s*\.\s*([A-Za-z0-9_/\^%\-]*)\s*(.*?):\s*(.*)", line_str)
                    if m:
                        curve_info.append({
                            "mnemonic": m.group(1).strip().upper(),
                            "unit": m.group(2).strip(),
                            "description": m.group(4).strip()
                        })

        well_name = well_info.get("WELL", {}).get("value", path.stem)
        start_depth = float(well_info.get("STRT", {}).get("value", 0.0))
        stop_depth = float(well_info.get("STOP", {}).get("value", 0.0))
        step = float(well_info.get("STEP", {}).get("value", 0.0))

        curves_list = [{"name": c["mnemonic"], "unit": c["unit"], "desc": c["description"]} for c in curve_info]
        curve_names = [c["mnemonic"] for c in curve_info]

        return {
            "file_name": path.name,
            "well_name": well_name,
            "field": well_info.get("FLD", {}).get("value", "Unknown Basin"),
            "operator": well_info.get("COMP", {}).get("value", "Authorized Operator"),
            "start_depth_m": start_depth,
            "stop_depth_m": stop_depth,
            "step_m": step,
            "curves_detected": curve_info,
            "curves": curves_list,
            "curve_names": curve_names,
            "curve_count": len(curve_info),
            "total_samples": int(abs(stop_depth - start_depth) / step) + 1 if step != 0 else 0,
            "well_info": well_info
        }

    def ingest(self, source_data: Any, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        meta = self.discover(source_data)
        path = Path(source_data)
        curves = [c["mnemonic"] for c in meta["curves_detected"]]

        rows = []
        in_ascii = False
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line_str = line.strip()
                if line_str.startswith("~A") or line_str.startswith("~ASCII"):
                    in_ascii = True
                    continue
                if in_ascii and line_str and not line_str.startswith("#"):
                    parts = line_str.split()
                    if len(parts) >= len(curves):
                        row_dict = {}
                        for i, c_name in enumerate(curves):
                            try:
                                v = float(parts[i])
                                if v != -999.25 and v != -999.0 and v != -9999.0: # Standard nulls
                                    row_dict[c_name] = v
                            except (ValueError, IndexError):
                                pass
                        if row_dict:
                            rows.append(row_dict)

        # Quality check
        quality_eval = data_quality_service.evaluate_batch(rows[:500])

        return {
            "meta": meta,
            "total_samples": len(rows),
            "curves": curves,
            "preview": rows[:10],
            "records": rows,
            "quality_summary": {
                "score": quality_eval["quality_score_pct"],
                "status": quality_eval["overall_status"],
                "flags": quality_eval["top_flags"]
            }
        }

    def normalize(self, raw_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return raw_records

    def store(self, db: Session, ingestion_result: Dict[str, Any], well_id: Optional[int] = None, source_id: Optional[int] = 4) -> Dict[str, Any]:
        meta = ingestion_result.get("meta", {})
        well_name = meta.get("well_name") or f"WELL-LAS-{int(datetime.datetime.utcnow().timestamp())}"
        stop_depth = meta.get("stop_depth_m", 3000.0)

        # Locate or create well
        well = None
        if well_id:
            well = db.query(Well).filter(Well.id == well_id).first()
        if not well:
            well = db.query(Well).filter(Well.well_name == well_name).first()
        if not well:
            well = Well(
                well_name=well_name,
                latitude=27.352,
                longitude=95.318,
                field=meta.get("field", "Duliajan Basin"),
                operator=meta.get("operator", "Oil India Limited (OIL)"),
                status="COMPLETED",
                well_type="EXPLORATORY",
                current_depth_m=stop_depth,
                target_depth_m=stop_depth,
                source_id=source_id,
                source_type=self.source_type,
                is_real=True,
                is_synthetic=False,
                is_user_uploaded=(self.source_type == "USER_UPLOAD"),
                is_public=(self.source_type == "PUBLIC_DATASET")
            )
            db.add(well)
            db.commit()
            db.refresh(well)

        records = ingestion_result.get("records", [])
        imported = 0
        # Ingest representative depth-indexed curves into telemetry / parameters
        step_stride = max(1, len(records) // 100) # Store up to ~100 key stations
        for i in range(0, len(records), step_stride):
            r = records[i]
            depth = r.get("DEPT") or r.get("DEPTH") or meta.get("start_depth_m", 0.0) + (i * meta.get("step_m", 0.15))
            tm = TelemetryMeasurement(
                well_id=well.id,
                depth_md=float(depth),
                depth_tvd=float(depth) * 0.985,
                rop=r.get("ROP"),
                wob=r.get("WOB"),
                rpm=r.get("RPM"),
                torque=r.get("TORQ") or r.get("TORQUE"),
                ecd=r.get("ECD"),
                quality_status="GOOD",
                source_id=source_id,
                source_type=self.source_type,
                is_real=True,
                is_synthetic=False
            )
            db.add(tm)
            imported += 1
        db.commit()

        self.status = "CONNECTED"
        self.last_update = datetime.datetime.utcnow().isoformat()
        return {
            "status": "SUCCESS",
            "well_id": well.id,
            "well_name": well.well_name,
            "imported_curves_count": len(meta.get("curves_detected", [])),
            "stored_measurements": imported
        }

las_adapter = LasAdapter()
