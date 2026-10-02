"""
PetroNexus Database Schema Synchronization Utility
Ensures all tables and required columns exist in both SQLite and PostgreSQL
without breaking existing records or migrations.
"""
from sqlalchemy import inspect, text
from backend.app.database import engine, Base
from backend.app.utils.logger import logger

def sync_database_schema():
    """
    Creates missing tables and ensures all newly introduced columns
    are present in existing tables (SQLite and PostgreSQL).
    """
    # Import all models so metadata knows all tables
    import backend.app.models

    # 1. Create all missing tables
    Base.metadata.create_all(bind=engine)
    
    # 2. Add columns if missing in existing tables
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    columns_to_ensure = {
        "wells": [
            ("basin", "VARCHAR(100) DEFAULT 'Assam-Arakan Basin'"),
            ("block", "VARCHAR(100)"),
            ("country", "VARCHAR(100) DEFAULT 'India'"),
            ("ground_elevation", "FLOAT DEFAULT 112.5"),
            ("kb_elevation", "FLOAT DEFAULT 120.0"),
            ("td_md", "FLOAT DEFAULT 3200.0"),
            ("td_tvd", "FLOAT DEFAULT 3136.0"),
            ("td_tvdss", "FLOAT DEFAULT 3016.0"),
            ("rig", "VARCHAR(100)"),
            ("rig_type", "VARCHAR(100)"),
            ("purpose", "VARCHAR(100)"),
            ("formation_target", "VARCHAR(100)"),
            ("reservoir", "VARCHAR(100)"),
            ("coordinate_reference_system", "VARCHAR(50) DEFAULT 'EPSG:4326'"),
            ("source_id", "INTEGER"),
            ("source_type", "VARCHAR(50) DEFAULT 'DEMO_SYNTHETIC'"),
            ("source_name", "VARCHAR(150) DEFAULT 'Synthetic Demonstration Data'"),
            ("is_real", "BOOLEAN DEFAULT FALSE"),
            ("is_synthetic", "BOOLEAN DEFAULT TRUE"),
            ("is_public", "BOOLEAN DEFAULT FALSE"),
            ("is_user_uploaded", "BOOLEAN DEFAULT FALSE"),
            ("provenance_confidence", "FLOAT DEFAULT 1.0"),
            ("provenance_notes", "TEXT"),
            ("visibility", "VARCHAR(50) DEFAULT 'DEMO'"),
        ],
        "drilling_events": [
            ("start_md", "FLOAT"),
            ("end_md", "FLOAT"),
            ("start_tvd", "FLOAT"),
            ("end_tvd", "FLOAT"),
            ("start_time", "VARCHAR(50)"),
            ("end_time", "VARCHAR(50)"),
            ("indicator", "TEXT"),
            ("outcome", "TEXT"),
            ("npt_hours", "FLOAT DEFAULT 0.0"),
            ("source_text", "TEXT"),
            ("confidence", "FLOAT DEFAULT 0.92"),
            ("source_id", "INTEGER"),
            ("source_type", "VARCHAR(50) DEFAULT 'DEMO_SYNTHETIC'"),
            ("is_real", "BOOLEAN DEFAULT FALSE"),
            ("is_synthetic", "BOOLEAN DEFAULT TRUE"),
        ],
        "formations": [
            ("aliases", "TEXT"), # JSON serialized in sqlite, JSON/TEXT in postgres
            ("reservoir_flag", "BOOLEAN DEFAULT FALSE"),
            ("source_id", "INTEGER"),
            ("confidence", "FLOAT DEFAULT 0.95"),
        ],
        "formation_intervals": [
            ("top_depth_tvdss_m", "FLOAT"),
            ("bottom_depth_tvdss_m", "FLOAT"),
        ],
        "alerts": [
            ("rule_id", "VARCHAR(100) DEFAULT 'RULE_OFFSET_HAZARD'"),
            ("what_happened", "TEXT"),
            ("why_it_matters", "TEXT"),
            ("historical_evidence_text", "TEXT"),
            ("current_indicator_text", "TEXT"),
            ("recommended_action", "TEXT"),
            ("engineer_notes", "TEXT"),
            ("dismissed_at", "TIMESTAMP"),
            ("escalated_at", "TIMESTAMP"),
            ("source_id", "INTEGER"),
        ],
        "documents": [
            ("ocr_applied", "BOOLEAN DEFAULT FALSE"),
            ("ocr_status", "VARCHAR(50) DEFAULT 'NOT_REQUIRED'"),
            ("confidence", "FLOAT DEFAULT 0.92"),
            ("source_id", "INTEGER"),
            ("source_type", "VARCHAR(50) DEFAULT 'DEMO_SYNTHETIC'"),
            ("is_real", "BOOLEAN DEFAULT FALSE"),
            ("is_synthetic", "BOOLEAN DEFAULT TRUE"),
            ("is_user_uploaded", "BOOLEAN DEFAULT FALSE"),
            ("extracted_events_count", "INTEGER DEFAULT 0"),
            ("extracted_formations_count", "INTEGER DEFAULT 0"),
        ],
        "well_trajectories": [
            ("survey_time", "VARCHAR(50)"),
            ("source_id", "INTEGER"),
        ],
        "telemetry_measurements": [
            ("wellbore_id", "VARCHAR(100)"),
            ("mse", "FLOAT"),
            ("quality_flags", "TEXT"),
            ("source_id", "INTEGER"),
            ("is_real", "BOOLEAN DEFAULT FALSE"),
            ("is_synthetic", "BOOLEAN DEFAULT TRUE"),
            ("original_units", "TEXT"),
            ("normalized_units", "TEXT"),
        ]
    }

    with engine.connect() as conn:
        for tbl_name, col_defs in columns_to_ensure.items():
            if tbl_name not in existing_tables:
                continue
            
            existing_cols = {c["name"].lower() for c in inspector.get_columns(tbl_name)}
            for col_name, col_type_sql in col_defs:
                if col_name.lower() not in existing_cols:
                    try:
                        conn.execute(text(f'ALTER TABLE "{tbl_name}" ADD COLUMN {col_name} {col_type_sql};'))
                        conn.commit()
                        logger.info(f"Added column {tbl_name}.{col_name}")
                    except Exception as err:
                        # SQLite might not support some complex DEFAULT expressions in ADD COLUMN
                        try:
                            # Fallback without default value
                            base_type = col_type_sql.split("DEFAULT")[0].strip()
                            conn.execute(text(f'ALTER TABLE "{tbl_name}" ADD COLUMN {col_name} {base_type};'))
                            conn.commit()
                            logger.info(f"Added column {tbl_name}.{col_name} (simplified)")
                        except Exception as e2:
                            logger.warning(f"Could not add column {tbl_name}.{col_name}: {e2}")

    # Seed core data sources if table is empty
    from backend.app.models.data_source import DataSource
    from backend.app.database import SessionLocal
    db = SessionLocal()
    try:
        if db.query(DataSource).count() == 0:
            sources = [
                DataSource(
                    id=1,
                    name="Oil India Limited eRTMAC Stream Gateway",
                    source_type="OIL_ERTMAC",
                    organization="Oil India Limited (OIL)",
                    url="https://ertmac.oilindia.in/witsml/live",
                    license="Proprietary / Authorized OIL Operations Only",
                    description="Live corporate eRTMAC drilling telemetry stream for active Assam-Arakan basin rigs.",
                    is_real=True,
                    is_synthetic=False,
                    is_public=False,
                    status="DISCONNECTED",
                    notes="Requires authenticated Oil India corporate network credentials. Configured as standby adapter.",
                    record_count=0
                ),
                DataSource(
                    id=2,
                    name="Industry Standard WITSML 1.4.1.1 / 2.0 Connector",
                    source_type="OIL_WITSML",
                    organization="Energistics / WITSML Server",
                    url="http://witsml.standard.org/witsml/1.4.1.1",
                    license="Open WITSML Standard Interface",
                    description="Standard WITSML XML/SOAP & ETP real-time telemetry connector with automated channel discovery.",
                    is_real=True,
                    is_synthetic=False,
                    is_public=False,
                    status="STANDBY",
                    notes="Ready for connection with any certified WITSML 1.4.1.1 or 2.x server endpoint.",
                    record_count=0
                ),
                DataSource(
                    id=3,
                    name="Equinor Volve Open Petroleum Dataset",
                    source_type="PUBLIC_DATASET",
                    organization="Equinor / Norwegian Offshore Directorate",
                    url="https://www.equinor.com/energy/volve-data-sharing",
                    license="CC BY 4.0 Open Petroleum License",
                    description="Real public field well logs, trajectories, petrophysical LAS curves and daily drilling reports.",
                    is_real=True,
                    is_synthetic=False,
                    is_public=True,
                    status="CONNECTED",
                    notes="Real open petroleum data used for multi-well spatial and subsurface validation.",
                    record_count=24
                ),
                DataSource(
                    id=4,
                    name="User Uploaded Rig Data & Well Reports",
                    source_type="USER_UPLOAD",
                    organization="PetroNexus User Session",
                    license="User Uploaded Real Operational Data",
                    description="User imported CSV, Excel, LAS, and PDF drilling reports.",
                    is_real=True,
                    is_synthetic=False,
                    is_public=False,
                    is_user_uploaded=True,
                    status="CONNECTED",
                    notes="Directly imported via /data/import portal.",
                    record_count=0
                ),
                DataSource(
                    id=5,
                    name="PetroNexus Synthetic Demonstration Dataset",
                    source_type="DEMO_SYNTHETIC",
                    organization="PetroNexus SIH Evaluation Team",
                    license="SIH 26121 Hackathon Demonstration",
                    description="Synthetic demonstration wells, 526 events, and test scenarios for Assam-Arakan basin.",
                    is_real=False,
                    is_synthetic=True,
                    is_public=False,
                    status="CONNECTED",
                    notes="Clearly identified as synthetic demonstration data for evaluation.",
                    record_count=526
                )
            ]
            for s in sources:
                db.add(s)
            db.commit()
            logger.info("Initialized 5 standard data sources in data_sources table.")
    except Exception as e:
        logger.warning(f"Data source initialization check: {e}")
        db.rollback()
    finally:
        db.close()
