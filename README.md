# PetroNexus (SIH26121)

> **Connect the Well. Remember the Past. Anticipate the Next.**

*AI-Powered Nearby Well Intelligence & Drilling Decision Support Platform*  
**Smart India Hackathon 2026 — Problem Statement SIH26121**  
**Organization:** Oil India Limited (OIL)  
**Primary Persona (V1):** Drilling Engineer  

---

> ### ⚠️ PROMINENT DEMONSTRATION & DATA DISCLAIMER
> **DEMONSTRATION DATA — SYNTHETIC DATA, NOT OIL CONFIDENTIAL DATA.**  
> All well trajectories, formations, drilling telemetry parameters, daily drilling reports (DDRs), well completion reports (WCRs), and operational incidents used within this demonstration dataset are synthetically generated for technical evaluation of SIH26121. No confidential or proprietary Oil India Limited records are stored or exposed.

---

## 1. The SIH26121 Problem Statement

Oil India Limited (OIL) operates state-of-the-art Real-Time Monitoring and Analytics Centers (**eRTMAC**) that capture high-frequency surface and downhole drilling telemetry (ROP, WOB, RPM, Torque, SPP, Flow Rate, ECD). 

However, **real-time information from the active well alone is not enough**. Effective drilling engineering decisions depend heavily on institutional knowledge scattered across nearby offset wells:
- Stratigraphic formation tops and bottom boundaries
- Historical drilling events: severe mud losses, differential sticking, kicks, pack-offs, overpressured intervals, and NPT incidents
- Well Completion Reports (WCR), Daily Drilling Reports (DDR), mud logging sheets, casing programs, and petrophysical logs
- Historical mitigation strategies that successfully cured problems in the same geological horizon

Today, this critical knowledge remains locked in static PDF reports, unstructured operational archives, and the personal memory of senior drillers. When the active bit enters a hazardous zone, engineers often lack instant, contextual insight into what offset wells experienced at that exact depth.

---

## 2. The PetroNexus Solution

**PetroNexus** transforms distributed drilling archives into an **active institutional memory layer** for drilling operations. 

```text
eRTMAC (Real-Time Operations) + PetroNexus (Institutional Memory) = Zero-Surprise Drilling
```

PetroNexus pairs live operational telemetry with multi-factor offset intelligence:
1. **Current Well Intelligence Ingestion:** Drop any active well report (PDF, CSV, XLSX, LAS, TXT), extract structured drilling parameters, and immediately receive a **Data Completeness & Readiness Score** with actionable **Next Best Data Actions**.
2. **Multi-Factor Offset Relevance Engine:** Evaluates offset wells not just by geographic distance, but across 7 technical dimensions (formation, depth, trajectory, parameters, reservoir, events, spatial distance).
3. **Look-Ahead Corridor (+50m, +100m, +150m):** Proactively projects historical hazards ahead of the bit before the drillstring penetrates problematic intervals.
4. **Subsurface Memory Visualizer:** Synchronized vertical wellbore column aligning stratigraphic formations, offset incidents, and active bit trajectory.
5. **Auditable Evidence Trail ("Why am I seeing this?"):** Every alert and recommendation is deterministically grounded with exact offset well names, depths, and citations (WCR Page 37, DDR Page 22).
6. **Unique Engineering Differentiators:**
   - **Memory Gap Detector:** Identifies where historical institutional records are incomplete rather than pretending omniscience.
   - **Conflict Detector:** Highlights discrepancies between historical documents (e.g., WCR vs. DDR formation top mismatch).
   - **Pre-Interval Brief & Context Pack:** Automated one-click PDF & JSON engineering briefs generated before entering critical zones.
   - **Grounded LangChain + Grok Assistant:** Engineering assistant that answers queries with strict zero-hallucination citations.
   - **Simulated eRTMAC Stream:** Built-in WebSocket telemetry engine with real-time anomaly detection (Torque spikes, ECD excursions, MSE analysis).

---

## 3. High-Level System Architecture

```text
                                  PETRONEXUS SYSTEM
                                          │
            ┌─────────────────────────────┴─────────────────────────────┐
            │                                                           │
   CURRENT WELL INGESTION                                      HISTORICAL ARCHIVE
  (PDF, CSV, XLSX, LAS, TXT)                                  (WCR, DDR, Mud, Survey)
            │                                                           │
            ▼                                                           ▼
   File Analyzer Pipeline                                      Document Parser & OCR
  (PyMuPDF, Tables, Regex)                                    (Knowledge Chunks & Citations)
            │                                                           │
            ▼                                                           ▼
   Profile & Completeness                                      Normalized Database
  (0-100% Readiness Engine)                                   (PostgreSQL / PostGIS / SQLite)
            │                                                           │
            └─────────────────────────────┬─────────────────────────────┘
                                          ▼
                       MULTI-DIMENSIONAL RELEVANCE ENGINE
                     (Distance, Stratigraphy, Depth, Physics)
                                          │
            ┌─────────────────────────────┼─────────────────────────────┐
            ▼                             ▼                             ▼
    LOOK-AHEAD ENGINE             SUBSURFACE MEMORY             ALERT & ANOMALY ENGINE
(+50m / +100m / +150m Hazards)   (Interactive Wellbore)       (Torque, ECD, MSE, Bit Balling)
            │                             │                             │
            └─────────────────────────────┼─────────────────────────────┘
                                          ▼
                               EVIDENCE TRAIL & PLAYBOOK
                           ("Why am I seeing this?" + Citations)
                                          │
            ┌─────────────────────────────┴─────────────────────────────┐
            ▼                                                           ▼
   LANGCHAIN + GROK RAG                                      SIMULATED eRTMAC WEBSOCKET
(Deterministic Context Pipeline)                             (Real-time live telemetry stream)
            │                                                           │
            └─────────────────────────────┬─────────────────────────────┘
                                          ▼
                        DRILLING COMMAND CENTER (COCKPIT)
                        (Industrial Dark Theme, Chart.js, Leaflet)
```

---

## 4. Feature Highlights & Technical Implementation

### A. Current Well Intelligence Ingestion & Completeness Engine
- **File Parsing Pipeline:** Analyzes uploaded PDFs (WCR/DDR), CSV telemetry, XLSX sheets, Directional Surveys, and LAS well-log files using `PyMuPDF` and `pandas`.
- **Structured Field Extraction:** Automatically extracts well identity, coordinates, current measured depth, formation name, ROP, WOB, RPM, Torque, ECD, Mud Weight, SPP, Flow Rate, and BHA.
- **Completeness & Readiness Score (0–100%):** Evaluates profile availability across 11 key operational dimensions (Identity, Location, Depth, Formation, Drilling parameters, Trajectory, Mud program, BHA, Casing, Pressure, Reservoir).
- **Missing Data Checklist:** Categorizes unpopulated parameters into Critical, Recommended, and Optional.
- **Next Best Data Actions:** Suggests the exact files needed next (e.g., *"Upload Directional Survey CSV to enable 3D TVD/TVDSS Minimum Curvature comparison"*).
- **Multi-File Profile Merge:** Merges incremental uploads into the persistent active well profile without overwriting populated attributes.

### B. Multi-Factor Offset Relevance Engine
Unlike simplistic spatial-only search, PetroNexus computes technical comparability across 7 dimensions:
$$\text{Relevance} = 0.25 S_{\text{dist}} + 0.20 S_{\text{form}} + 0.15 S_{\text{depth}} + 0.15 S_{\text{traj}} + 0.10 S_{\text{param}} + 0.05 S_{\text{res}} + 0.10 S_{\text{event}}$$
- **Spatial:** Haversine / PostGIS ST_Distance.
- **Stratigraphic:** Formation match and offset interval overlap.
- **Depth:** Proximity within target depth windows.
- **Trajectory:** Minimum Curvature Method (MCM) 3D spatial alignment (MD, TVD, TVDSS, DLS).
- **Drilling Parameters:** Baseline energy and hydraulic comparability.
- **Historical Events:** Offset incident severity and frequency.

### C. Look-Ahead Corridor Engine
Drilling engineers need to anticipate hazards ahead of the bit, not just react to what was passed:
- Scans forward at user-selected windows (+50m, +100m, +150m).
- Detects upcoming formation changes, fault zones, and historical loss/stuck-pipe intervals.
- Example: Active well at 2846m MD detects `OIL-DEMO-018 Mud Loss at 2860m MD (+14m ahead)` and `OIL-DEMO-007 Stuck Pipe at 2872m MD (+26m ahead)`.

### D. Subsurface Memory View
- Vertical synchronized cross-section of the wellbore.
- Dynamic bit marker tracks simulated or live drilling progress.
- Historical offset events (Mud Losses, Torque Spikes, Kicks, Stuck Pipe) pinned alongside formation depths.

### E. Physics-Informed Drilling Indicators
- **Mechanical Specific Energy (MSE):** Implements Teale's Specific Energy formula:
  $$\text{MSE} = \frac{\text{WOB}}{A_b} + \frac{120 \pi \cdot \text{RPM} \cdot \text{Torque}}{A_b \cdot \text{ROP}}$$
  Identifies bit balling, vibration, and drilling inefficiencies in real time.
- **ECD Delta Margin:** Dynamic circulating density vs. static mud weight boundary surveillance ($\Delta \text{ECD} \le 0.10 \text{ SG}$).

### F. Unique Engineering Differentiators
1. **Memory Gap Detector:** Identifies where offset intelligence is sparse (e.g., missing trajectory or mud program in offset wells) so engineers know when confidence is limited.
2. **Document Conflict Detector:** Flags inconsistencies between historical records (e.g., WCR vs. DDR formation top delta of 14m).
3. **Engineering Playbook:** Summarizes documented field remedies (LCM pills, controlled flow, wiper trips) used in comparable wells.
4. **Pre-Interval Brief & Context Pack:** Automated one-click generation of PDF and JSON decision briefs containing full active well telemetry, offset comparisons, upcoming hazards, and citations.

### G. LangChain + Grok Assistant (Zero Hallucination)
- Context-aware retrieval engine feeds active well parameters, nearby wells, look-ahead hazards, and document chunks into xAI Grok.
- Enforces an 8-part grounded engineering response structure:
  `SUMMARY | CURRENT CONTEXT | HISTORICAL EVIDENCE | COMPARABLE WELLS | MITIGATION HISTORY | WHY THIS MATTERS | RECOMMENDED ENGINEERING REVIEW | SOURCES`
- Built-in High-Fidelity Grounded Demo Mode ensures deterministic, citation-backed responses even when no external API key is configured.

---

## 5. Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | Pure HTML5, Vanilla Modern CSS, JavaScript (ES6+), Bootstrap 5 Icons, Leaflet (Spatial Map), Chart.js (Real-time Telemetry curves) |
| **Backend** | Python 3.11, FastAPI (REST & WebSockets), Pydantic v2, SQLAlchemy 2.0, AnyIO |
| **Database** | SQLite with custom Haversine spatial math (zero-config local demo) / PostgreSQL 16 + PostGIS 3.4 (Enterprise profile) |
| **Document Processing** | PyMuPDF (fitz), Tabular Extractors, PDF Formatter (ReportLab) |
| **Analytics & Physics** | NumPy, Pandas, Scikit-learn (Isolation Forest & Anomaly Detection), Teale's MSE Engine, Minimum Curvature Trajectory Engine |
| **AI / RAG** | LangChain, xAI Grok API (`grok-2-latest`), Deterministic Fallback Grounding Engine |

*(No React, No Ollama, No unexplainable black-box models).*

---

## 6. Project Structure

```text
PetroNexus/
├── backend/
│   ├── app/
│   │   ├── api/                     # REST API routers
│   │   │   ├── auth.py              # Authentication (JWT + Bcrypt)
│   │   │   ├── wells.py             # Well catalogue & details
│   │   │   ├── current_well.py      # Active well upload & completeness
│   │   │   ├── intelligence.py      # Offset relevance & look-ahead
│   │   │   ├── alerts.py            # Alert center & evidence trail
│   │   │   ├── documents.py         # Knowledge repository & OCR
│   │   │   ├── ai.py                # LangChain & Grok assistant
│   │   │   ├── reports.py           # Pre-interval brief & Context Pack PDF
│   │   │   ├── quality.py           # Data quality metrics
│   │   │   └── audit.py             # Audit trail logging
│   │   ├── ingestion/               # File parsers & completeness engine
│   │   ├── document_processing/     # PyMuPDF & table extraction
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   ├── rag/                     # LangChain & Grok client
│   │   ├── realtime/                # eRTMAC simulator & anomaly detector
│   │   ├── schemas/                 # Pydantic validation schemas
│   │   ├── services/                # Offset, Look-Ahead, Physics, Spatial
│   │   ├── utils/                   # Trajectory math, units, logger
│   │   ├── config.py                # Settings & paths
│   │   ├── database.py              # DB connection & spatial functions
│   │   └── main.py                  # FastAPI app & WebSocket endpoints
│   ├── requirements.txt             # Python dependencies
│   └── .env.example                 # Backend environment template
│
├── frontend/                        # Industrial Control-Console UI
│   ├── css/
│   │   └── style.css                # Petroleum dark industrial theme
│   ├── js/
│   │   ├── api.js                   # API client & token handling
│   │   ├── auth.js                  # Login & registration controller
│   │   ├── dashboard.js             # 4-panel Command Center & WebSockets
│   │   ├── current_well.js          # Ingestion & completeness meter
│   │   ├── intelligence.js          # Offset ranking & corridor UI
│   │   ├── alerts.js                # Alert center & evidence modal
│   │   ├── assistant.js             # AI drilling assistant chat
│   │   ├── scenario.js              # What-If scenario planner
│   │   └── reports.js               # Context Pack & Brief generator
│   ├── index.html                   # Landing page
│   ├── login.html                   # Engineer login
│   ├── register.html                # Engineer registration
│   ├── dashboard.html               # 4-panel Drilling Command Center
│   ├── current-well.html            # Active Well Ingestion & Readiness
│   ├── wells.html                   # Offset Well Catalogue
│   ├── intelligence.html            # Look-Ahead & Relevance Engine
│   ├── alerts.html                  # Operational Alert Center
│   ├── documents.html               # Institutional Knowledge Repository
│   ├── assistant.html               # PetroNexus AI Assistant
│   ├── scenario.html                # What-If Corridor Scenario
│   ├── data-quality.html            # Readiness & Completeness Center
│   └── reports.html                 # Engineering Context Pack & Reports
│
├── data/                            # Deterministic demo datasets
│   ├── wells.csv                    # 25 exploration & development wells
│   ├── formations.csv               # 150 stratigraphic intervals
│   ├── events.csv                   # 526 historical drilling events
│   ├── parameters.csv               # Drilling parameter baselines
│   └── trajectories.csv             # 3D directional surveys
│
├── documents/                       # Demo drilling reports & logs
│   ├── WCR-OIL-DEMO-018.pdf         # Well Completion Report (Mud Loss @ p.37)
│   ├── DDR-OIL-DEMO-021.pdf         # Daily Drilling Report (Torque Spike @ p.22)
│   ├── Current_Well_Report_OIL-DEMO-023.pdf  # Active well report
│   ├── Current_Well_Telemetry_OIL-DEMO-023.csv # Real-time telemetry CSV
│   ├── OIL-DEMO-023_Directional_Survey.csv   # Directional survey CSV
│   └── Current_Well_Log_OIL-DEMO-023.las     # Petrophysical well log
│
├── scripts/                         # Automation & database seeding
│   ├── generate_demo_data.py        # Seed 26121 generator
│   ├── generate_demo_documents.py   # Synthesizes test PDFs, CSVs, LAS
│   ├── seed_database.py             # Populates database tables
│   └── index_demo_documents.py      # Indexes text chunks & tables
│
├── tests/                           # Complete test suite
│   ├── test_auth.py                 # Password & JWT verification
│   ├── test_current_well.py         # File ingestion & completeness tests
│   ├── test_intelligence.py         # Spatial, offset, lookahead tests
│   ├── test_physics.py              # MSE & MCM trajectory tests
│   ├── test_alerts_and_reports.py   # Alerts, PDF generation & RAG tests
│   ├── test_ws.py                   # WebSocket eRTMAC live stream test
│   └── run_all_tests.py             # Master test runner (20/20 checks)
│
├── Dockerfile                       # Production container definition
├── docker-compose.yml               # Compose stack (App + PostGIS)
├── README.md                        # Complete documentation
└── .env                             # Environment configuration
```

---

## 7. Quickstart & Local Setup

### Prerequisites
- Python 3.10+ (Python 3.11 recommended)
- `pip` package manager
- Modern Web Browser (Chrome, Edge, Firefox)

### Step 1: Clone and Navigate to Project
```bash
git clone https://github.com/your-org/PetroNexus.git
cd PetroNexus
```

### Step 2: Install Python Dependencies
```bash
pip install -r backend/requirements.txt
```

### Step 3: Populate Demo Database & Documents
```bash
python scripts/generate_demo_data.py
python scripts/generate_demo_documents.py
python scripts/seed_database.py
python scripts/index_demo_documents.py
```

### Step 4: Run the Automated Verification Test Suite
```bash
python tests/run_all_tests.py
```
*(All 20 tests will pass with 100% verification).*

### Step 5: Start the PetroNexus Server
```bash
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### Step 6: Open the Application
Access PetroNexus in your web browser:
```text
http://localhost:8000/
```

---

## 8. Docker Deployment

### Run Standalone Container
```bash
docker build -t petronexus:latest .
docker run -d -p 8000:8000 --name petronexus petronexus:latest
```
Open `http://localhost:8000/` in your browser.

### Run with Docker Compose (with optional PostGIS)
```bash
docker-compose up -d --build
```

---

## 9. Demo Credentials & Key URLs

### Default Demo Credentials (Drilling Engineer)
- **Role:** `DRILLING_ENGINEER`
- **Email:** `engineer@oilindia.in`
- **Password:** `OilIndia@2026`
*(Quick Login button available on the login page for instantaneous 1-click access).*

### Primary Application URLs
- **Landing Page:** `http://localhost:8000/`
- **Drilling Command Center:** `http://localhost:8000/dashboard.html`
- **Active Well Intelligence & Ingestion:** `http://localhost:8000/current-well.html`
- **Offset Relevance & Look-Ahead:** `http://localhost:8000/intelligence.html`
- **Alert Center & Evidence Trail:** `http://localhost:8000/alerts.html`
- **AI Drilling Assistant:** `http://localhost:8000/assistant.html`
- **What-If Scenario Planner:** `http://localhost:8000/scenario.html`
- **Institutional Knowledge Base:** `http://localhost:8000/documents.html`
- **Context Pack & Reports:** `http://localhost:8000/reports.html`
- **Interactive Swagger API Documentation:** `http://localhost:8000/docs`
- **ReDoc API Documentation:** `http://localhost:8000/redoc`

---

## 10. End-to-End Demonstration Storyline (SIH Judging Flow)

| Step | Persona Action | PetroNexus Technical Response |
|---|---|---|
| **1. Ingestion** | Engineer uploads `Current_Well_Report_OIL-DEMO-023.pdf` on `current-well.html` (or clicks *"⚡ Ingest Report PDF"*). | Detects PDF, extracts well identity, depth (2846m), formation (Formation-X), and parameters. Computes **Well Intelligence Readiness: 90.5%**. |
| **2. Completeness** | Engineer reviews Data Completeness Report. | Displays populated fields vs. missing fields (Trajectory survey, Mud sheet). Recommends **Next Best Data Actions**. |
| **3. Spatial Offset** | Engineer opens `dashboard.html`. | Map centers on active well `OIL-DEMO-023` in Duliajan Basin. Ranks nearby wells by 7-factor technical similarity. Highlights key offsets: `OIL-DEMO-018` (4.8 km), `OIL-DEMO-021` (6.1 km), `OIL-DEMO-011` (8.3 km). |
| **4. Subsurface Memory** | Engineer views the Subsurface Memory panel. | Vertical wellbore column aligns Formation-X with historical offset incidents: Mud Loss at 2828m, Torque Spike at 2842m, Mud Loss at 2860m, Stuck Pipe at 2872m. |
| **5. Look-Ahead Alert** | PetroNexus automatically scans look-ahead corridor (+100m). | Generates **HIGH ATTENTION ALERT**: *"3 comparable offset wells reported mud-loss and torque anomalies in the upcoming Formation-X interval"*. |
| **6. Evidence Trail** | Engineer clicks *"Why am I seeing this?"*. | Modal provides verifiable audit trace: Cites `WCR-OIL-DEMO-018 Page 37` and `DDR-OIL-DEMO-021 Page 22`. Documented mitigation: *"35 ppb Mica/Nutplug LCM pill, reduced flow to 1800 LPM"*. |
| **7. Live Telemetry** | Engineer clicks **START** on eRTMAC toolbar. | WebSocket streams live telemetry: bit advances from 2846.0m to 2847.5m, Torque climbs to 22.4 kN.m, Anomaly Detector flags `TORQUE_SPIKE` and elevated MSE. |
| **8. AI Consultation** | Engineer clicks prompt chip on `assistant.html`: *"What happened in Formation-X?"* | Grok + LangChain RAG synthesizes grounded 8-part response citing verified WCR/DDR historical page numbers. Zero hallucination. |
| **9. Decision Pack** | Engineer clicks *"Generate Context Pack"* on `reports.html`. | Compiles all active well telemetry, offset rankings, look-ahead hazards, playbooks, and missing data gaps into a downloadable PDF & JSON brief. |

---

## 11. Implemented Requirements Checklist

- [x] **Single Persona (V1):** Strictly `DRILLING_ENGINEER` with future-ready `role` database architecture.
- [x] **Current Well Intelligence Ingestion:** Multi-format parser (PDF, CSV, XLSX, LAS, TXT, JSON).
- [x] **Well Intelligence Readiness:** 0–100% completeness scoring across 11 operational dimensions.
- [x] **Next Best Data Actions:** Automated missing data recommendations.
- [x] **Geospatial Offset Well Map:** Interactive Leaflet map with search radii (1km, 5km, 10km, 15km, 20km, 50km).
- [x] **Multi-Factor Offset Relevance Engine:** 7-factor technical similarity algorithm.
- [x] **Look-Ahead Corridor:** Configurable look-ahead hazard projection (+50m, +100m, +150m).
- [x] **Trajectory-Aware Depth Correlation:** Minimum Curvature Method (MD, TVD, TVDSS, DLS).
- [x] **Formation Correlation & Subsurface Memory:** Vertical wellbore view with moving bit position.
- [x] **Historical Mitigation Playbook:** Proven field remediation procedures linked to comparable events.
- [x] **Evidence Trail ("Why am I seeing this?"):** Verifiable citations linked to source documents and page numbers.
- [x] **Memory Gap Detector:** Flags incomplete offset well institutional archives.
- [x] **Conflict Detector:** Detects contradictory stratigraphic or drilling data between documents.
- [x] **Physics-Informed Indicators:** Mechanical Specific Energy (Teale's MSE) and ECD delta surveillance.
- [x] **Simulated eRTMAC WebSocket:** Real-time bi-directional telemetry stream (`/ws/drilling/{well_id}`).
- [x] **Real-Time Anomaly Detection:** Real-time flagging of Torque spikes, ROP drops, and ECD excursions.
- [x] **AI Drilling Assistant:** LangChain RAG with Grok API integration and deterministic fallback grounding.
- [x] **Pre-Interval Brief & Context Pack:** Automated PDF and JSON report generation.
- [x] **Audit Trail:** Comprehensive audit logging of logins, uploads, queries, and alert acknowledgments.
- [x] **Automated Test Suite:** 20 automated tests verifying authentication, ingestion, spatial math, physics, and RAG.

---

## 12. Known Limitations & Roadmap

1. **V1 Persona Scope:** Only `DRILLING_ENGINEER` is activated for V1. Geologist, Petrophysicist, and Operations Manager consoles are reserved for future phases.
2. **Real eRTMAC Integration:** Production deployment will interface with real WITSML/OPC-UA telemetry streams via secure OIL network gateways.
3. **Enterprise Storage:** Demonstrations use local SQLite with spatial math and local storage; production deployments scale to PostgreSQL/PostGIS and S3-compatible document storage.

---

## 13. License & Acknowledgments

Developed for the **Smart India Hackathon 2026** (Problem Statement SIH26121).  
Dedicated to **Oil India Limited (OIL)** and the front-line drilling engineers powering India's energy security.
