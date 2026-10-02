CLAUDE.md — PetroNexus Agent Instructions

1. Project identity

Project name: PetroNexus

Purpose: SIH 26121 — Nearby Wells Intelligence System (NWIS) for Oil India Limited.

PetroNexus is a standalone decision-support platform intended to work alongside an operational real-time drilling monitoring system such as OIL's eRTMAC.

Core problem:

Show nearby/offset wells around an active well.

Retrieve historical drilling experiences from WCRs, DDRs and other well documents.

Correlate current drilling state with historical wells by depth, formation, trajectory and drilling parameters.

Detect/look ahead for historical hazards.

Generate engineering-focused alerts and evidence-backed explanations.

Eventually consume authorized real-time drilling telemetry through standards such as WITSML/ETP or OPC-UA.

IMPORTANT:

The current public/demo application must NOT claim to have access to confidential OIL eRTMAC data.

Synthetic/demo data may remain for development.

Public real petroleum data can be used for validation.

Production OIL integration should be represented as an adapter/interface requiring authorized access.

2. Primary agent rule

Do NOT re-analyze the entire repository on every task.

Before changing anything:

Read this file.

Inspect only the files directly relevant to the requested change.

Search for the existing implementation before creating a new implementation.

Reuse the existing architecture, functions, API routes, styles and components whenever possible.

Do not rewrite unrelated code.

Do not replace working backend/data/intelligence logic just to solve a frontend problem.

Keep changes minimal, reversible and scoped.

After modifying code, run the smallest relevant validation/test.

If a required implementation detail is unknown:

Search the relevant directory first.

Do not blindly scan the entire repository.

Do not create duplicate files/functions when an existing one can be extended.

3. Current known architecture

The application is a full-stack web application with:

Frontend:

HTML/CSS/JavaScript and/or existing frontend structure.

Leaflet-based spatial map.

Dark industrial dashboard UI.

Existing panels for spatial intelligence, wells, alerts, documents, intelligence/RAG and scenario/live data.

Backend:

Existing API/backend implementation.

Existing well, offset, historical-event and telemetry logic.

Existing real-time/simulated stream logic.

Existing database integration.

Data/intelligence:

Wells

Well trajectories

Formations

Historical events

Drilling parameters

WCR/DDR-style documents

Historical hazards

Offset relevance

Depth/formation correlation

Look-ahead corridors

Alerts

Physics indicators such as MSE/ECD

RAG/evidence functionality

Do not remove these capabilities while modifying the map.

4. Current map issue

The current map previously used:

L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    maxZoom: 18,
    subdomains: 'abcd'
}).addTo(mapInstance);

This produces a CARTO "API KEY REQUIRED" basemap watermark.

Required immediate solution

Use OpenStreetMap tiles for the public/demo version:

const osmLayer = L.tileLayer(
    'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
    {
        maxZoom: 19,
        attribution:
            '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors'
    }
);

osmLayer.addTo(mapInstance);

Do not add a fake API key.
Do not hide the CARTO watermark with CSS.
Do not continue using the unauthenticated CARTO raster endpoint.

5. Map visual requirements

PetroNexus uses a dark industrial UI.

The OpenStreetMap basemap should visually fit the existing dashboard without changing map intelligence.

Use a subtle tile-pane filter only if needed:

.leaflet-tile-pane {
    filter: brightness(0.72) contrast(1.12) saturate(0.75);
}

.leaflet-control-zoom a {
    background: #111827 !important;
    color: #ffffff !important;
    border-color: #334155 !important;
}

.leaflet-control-zoom a:hover {
    background: #1e293b !important;
}

.leaflet-control-attribution {
    background: rgba(15, 23, 42, 0.85) !important;
    color: #94a3b8 !important;
}

.leaflet-control-attribution a {
    color: #60a5fa !important;
}

Do not alter existing marker logic just to style the map.

6. Map intelligence that must remain intact

The map currently distinguishes:

Active Well — blue

Historical Hazard Offset — red

Reference Offset — green

Keep these meanings.

Existing functionality that must not regress:

Search radius selector.

Active-well marker.

Offset-well markers.

Historical hazard markers.

Reference offset markers.

Radius/coverage visualization.

Well popups.

Existing well details.

Existing API/backend calls.

Existing spatial calculations.

Existing PostGIS logic.

Existing relevance/scoring logic.

Do not replace the map with a static image or mock map.

7. Desired future map intelligence

The map should evolve from "nearby dots" into an engineering intelligence map.

Preferred future layers:

Active well

Reference offsets

Historical hazard offsets

Risk-matched offsets

Search radius

Historical hazard corridors

Formation/depth correlation visualization

Optional trajectory display

Optional event-depth indicators

A "Risk-Matched Offset" means a well that is technically relevant, not merely geographically close.

Relevance can consider:

Distance

Formation similarity

Depth overlap

Trajectory similarity

Reservoir/geological similarity

Historical event similarity

Drilling parameter similarity

Do not reduce offset relevance to distance alone.

8. SIH 26121 functional requirements

The implementation should map to these requirements:

i. Nearby wells

Interactive map with active well and configurable-radius offsets.

ii. Historical drilling knowledge

Search/retrieve WCR, DDR and historical event information with source evidence.

iii. Correlation

Correlate:

Depth

Formation

Reservoir characteristics

ROP

WOB

RPM

Torque

ECD

Mud weight

SPP

Flow

Trajectory

Mud losses

Kicks

Stuck pipe

Cementing

Fishing/NPT where available

iv. Proactive alerts

When the active well approaches a historical hazard depth/formation, show an alert with:

Current MD

Historical event MD

Distance ahead

Formation

Source well

Event type

Evidence/source document

Relevant current indicators

v. Predictive analytics

Long-term goal:

Stuck pipe

Mud loss

Kick/overpressure

Torque anomaly

Cementing issues

Do not claim a predictive ML model exists unless it is actually implemented and evaluated.

vi. Real-time alerts

Support a normalized telemetry ingestion layer.

vii. Dashboard

Keep the current dark industrial dashboard and improve information density without unnecessary redesign.

9. Real-time telemetry architecture

Do not hard-code PetroNexus directly to one source.

Use an adapter/normalization architecture:

WITSML / ETP
      \
       \
OPC-UA ---> Telemetry Normalizer ---> PetroNexus Internal Schema
       /
CSV/JSON simulator

The internal telemetry object should be conceptually similar to:

{
  "well_id": "WELL-001",
  "timestamp": "2026-10-02T09:00:00Z",
  "md": 2848.5,
  "tvd": 2761.3,
  "rop": 18.4,
  "wob": 72.1,
  "rpm": 125,
  "torque": 19.7,
  "spp": 2850,
  "flow_rate": 2100,
  "ecd": 1.42,
  "mud_weight": 1.34,
  "hookload": 145,
  "block_position": 12.5,
  "formation": "Formation-X"
}

Existing simulated telemetry must continue to work.

Do not fabricate an OIL eRTMAC API endpoint.

10. Public-data validation strategy

For public validation, prefer real petroleum datasets such as:

Equinor Volve dataset

NLOG/public well datasets where appropriate

Do not label public datasets as OIL data.

Use explicit source labels such as:

SYNTHETIC DEMO

PUBLIC PETROLEUM DATA

OIL AUTHORIZED INTEGRATION

Production OIL integration should be represented as:

authorized WITSML/ETP gateway, or

authorized OPC-UA/data gateway,
depending on OIL's actual integration environment.

11. Documents / OCR / RAG

The document pipeline should follow:

PDF
 |
 +-- text PDF --> PyMuPDF/text extraction
 |
 +-- scanned PDF --> OCR
                         |
                         v
                    structured text
                         |
                         v
                    NLP extraction
                         |
                         v
                  historical knowledge

Potential extraction entities:

Well

Formation

Depth

Event type

Mud loss

Kick

Stuck pipe

Torque

Cement

Casing

Mud weight

Mitigation

NPT

RAG should explain and retrieve evidence.

Do not make an LLM the sole risk detector.

Preferred order:

Telemetry
  -> deterministic calculations/rules
  -> anomaly/ML
  -> historical correlation
  -> evidence retrieval
  -> LLM explanation

12. Engineering alert philosophy

Alerts must be evidence-backed.

Bad:

High risk detected.

Good:

HISTORICAL HAZARD AHEAD

Current MD: 2850 m
Historical event: Mud Loss
Historical MD: 2870 m
Distance ahead: 20 m
Formation: Barail
Source well: OIL-DEMO-018

Current indicators:
- Torque increasing
- ROP declining
- ECD above local baseline

Historical evidence:
- DDR page X
- WCR page Y

Do not present recommendations as guaranteed engineering instructions.

Use language such as:

"Engineering review recommended"

"Historical precedent indicates..."

"Potential risk"

"Comparable wells experienced..."

13. Formation intelligence

A future Formation Risk Profile should summarize:

FORMATION: BARAIL

Historical wells: 18

Mud Loss: 7
Stuck Pipe: 4
Kick: 3
Torque Spike: 6
Pack-off: 5
Cementing issue: 2

Then correlate the active well's current formation with the profile.

This is a core SIH 26121 capability.

14. Database principles

Prefer:

PostgreSQL

PostGIS for spatial data

TimescaleDB or an equivalent time-series design where appropriate

Conceptual entities:

wells
wellbores
trajectories
formations
telemetry
drilling_events
documents
document_chunks
mitigations
alerts

Do not migrate the entire database unless explicitly requested.

If SQLite currently supports the demo, preserve compatibility until a migration is intentionally planned.

15. Code-change rules

Before editing:

Search for the relevant implementation.

Identify the smallest file/function/component that needs modification.

Make the smallest safe change.

Preserve existing API contracts.

Preserve existing data schemas unless migration is required.

Preserve UI behavior outside the requested feature.

Run a targeted validation.

Report exactly what changed.

Avoid:

Large rewrites

Framework migrations

React conversion

Unnecessary microservices

Blockchain

Unnecessary 3D

Unnecessary satellite imagery

Generic chatbot additions

Replacing working features with placeholders

16. Current immediate task: map repair

When asked to fix the current map:

Required:

Remove unauthenticated CARTO raster layer.

Use OSM HTTPS tile endpoint.

Add attribution.

Keep Leaflet.

Keep all existing PetroNexus map overlays.

Keep radius selector.

Keep active/hazard/reference markers.

Keep popups.

Make the OSM layer visually fit the dark UI.

Do not:

Change backend.

Change database.

Change API contracts.

Rewrite the map module.

Remove markers.

Remove intelligence logic.

Add a new map framework.

17. Validation checklist

After map changes verify:

No "API KEY REQUIRED" watermark.

Map loads over HTTPS.

Zoom works.

Active well appears.

Historical hazard offset appears.

Reference offset appears.

Search radius still works.

Popups still work.

Existing API calls still work.

No console errors related to the map.

No CARTO raster URL remains in active code.

OpenStreetMap attribution is visible.

Existing dark dashboard styling remains intact.

18. Agent response format

When completing a task, report:

Changed

file

function/component

exact purpose

Preserved

existing features that were intentionally not changed

Validation

command/test performed

result

Next

only the next relevant step

Do not dump a repository-wide analysis unless explicitly requested.

19. Important project principle

PetroNexus should demonstrate this engineering workflow:

ACTIVE WELL
    |
    v
CURRENT DEPTH + FORMATION + TELEMETRY
    |
    v
FIND COMPARABLE OFFSET WELLS
    |
    v
CORRELATE DEPTH + FORMATION + TRAJECTORY
    |
    v
FIND HISTORICAL EVENTS
    |
    v
LOOK AHEAD
    |
    v
RISK / ANOMALY ANALYSIS
    |
    v
EVIDENCE-BACKED ALERT
    |
    v
ENGINEER REVIEWS HISTORICAL MITIGATION

The purpose is decision support and institutional memory, not autonomous drilling control.

20. CRITICAL: PETRONEXUS AI ASSISTANT / CHATBOT BEHAVIOR

The PetroNexus assistant must behave like a natural modern AI chat assistant while remaining grounded when answering PetroNexus engineering questions.

Current relevant files are expected to include:

frontend/js/assistant.js

frontend/assistant.html

backend/app/api/ai.py

backend/app/rag/

related API/client files

Before changing the assistant:

Inspect only these relevant files and their direct dependencies.

Do not re-analyze the whole repository.

Preserve the existing RAG/evidence system.

Preserve the existing demo/fallback mode.

A. The assistant MUST answer normal/general questions

Examples:

User:
"What is Azure?"

Assistant:
"Azure is Microsoft's cloud computing platform. It provides services for computing, storage, databases, networking, AI, analytics, security, and more."

User:
"What is the capital of India?"

Assistant:
"The capital of India is New Delhi."

User:
"Explain machine learning."

Assistant:
"Machine learning is a branch of AI where models learn patterns from data to make predictions or decisions."

These questions must NOT trigger the full PetroNexus engineering context.

Do not answer general questions with:

Active well context

offset wells

drilling telemetry

historical hazards

formations

WCR/DDR evidence
unless the user actually asks about them.

B. The assistant MUST NOT repeat the entire context on every message

Current problematic behavior:

The assistant repeats active well data every turn.

The assistant repeats the entire retrieved context.

The assistant repeats the same historical wells/evidence even when irrelevant.

The assistant uses a fixed long response structure for every question.

Fix this.

The assistant should use contextual retrieval selectively.

BAD:

User:
"What is Azure?"

Assistant:
"CURRENT CONTEXT:
Active well OIL-DEMO-023...
Formation...
Telemetry...
Historical wells...
..."

GOOD:

"Azure is Microsoft's cloud computing platform..."

C. Query classification

Before retrieval, classify the user's message into:

GENERAL

PETRONEXUS_PRODUCT

DRILLING_ENGINEERING

HISTORICAL_WELL_KNOWLEDGE

ACTIVE_WELL_ANALYSIS

DOCUMENT_SEARCH

FOLLOW_UP_TO_CURRENT_TOPIC

Do NOT use expensive historical retrieval for GENERAL questions.

Examples:

"What is Azure?" -> GENERAL

"Capital of India?" -> GENERAL

"What is WITSML?" -> PETRONEXUS_PRODUCT / DRILLING_ENGINEERING

"Which offset well had mud loss ahead of the bit?" -> HISTORICAL_WELL_KNOWLEDGE

"Why am I getting this alert?" -> ACTIVE_WELL_ANALYSIS

"Show me the evidence for the stuck pipe event." -> DOCUMENT_SEARCH

"Explain this alert in simple terms." -> FOLLOW_UP_TO_CURRENT_TOPIC

D. Retrieval policy

For GENERAL:

No PetroNexus retrieval.

No active-well context.

Answer directly.

For PETRONEXUS_PRODUCT:

Retrieve only product-specific context if needed.

Do not include unrelated telemetry.

For DRILLING_ENGINEERING:

Retrieve relevant engineering context.

Include only parameters relevant to the question.

For HISTORICAL_WELL_KNOWLEDGE:

Retrieve relevant offset wells/events/documents.

Cite evidence.

For ACTIVE_WELL_ANALYSIS:

Retrieve the current active well state.

Retrieve only relevant telemetry/formation/hazards.

Compare against relevant offsets.

For DOCUMENT_SEARCH:

Retrieve the relevant documents/chunks.

Provide source/page evidence.

E. Context compression

Never send the entire database state or entire dashboard state to the LLM.

Build a compact context object.

Example:

{
  "active_well": {
    "well_id": "OIL-DEMO-023",
    "md": 2846,
    "formation": "Formation-X"
  },
  "question_relevant_telemetry": {
    "rop": 18.4,
    "torque": 19.7,
    "ecd": 1.42
  },
  "relevant_offsets": [
    {
      "well_id": "OIL-DEMO-018",
      "distance_km": 4.8,
      "event": "Mud Loss",
      "event_md": 2860
    }
  ],
  "evidence": [
    {
      "document": "WCR-OIL-DEMO-018.pdf",
      "page": 37
    }
  ]
}

Only include fields relevant to the user's question.

F. Conversation memory

The assistant should remember the immediate conversation naturally.

Example:

User:
"What is the current depth?"

Assistant:
"The active well is currently at 2,846 m MD."

User:
"What happened ahead of it?"

Assistant:
"Based on the current look-ahead data, a historical mud-loss event occurs at 2,860 m, about 14 m ahead."

The second answer should NOT repeat the entire first response.

Use a compact conversation history/window where supported.

Do not continuously append the same retrieved context to the conversation.

G. Deduplication

Before sending context to the LLM:

Deduplicate repeated documents.

Deduplicate repeated events.

Deduplicate repeated well records.

Remove repeated telemetry fields.

Remove previously supplied context when it has not changed.

If the active telemetry changes, send only the changed/relevant values when possible.

H. Natural conversational response

The assistant should sound like a modern AI assistant.

It should:

Understand short questions.

Understand follow-up questions.

Use natural language.

Be concise by default.

Expand when asked.

Explain technical concepts at the user's requested level.

Avoid unnecessary headings.

Avoid repeating the user's question.

Avoid repeating all context.

Avoid robotic templates.

Do NOT force every answer into:

SUMMARY
CURRENT CONTEXT
HISTORICAL EVIDENCE
COMPARABLE WELLS
MITIGATION HISTORY
WHY THIS MATTERS
RECOMMENDED ENGINEERING REVIEW
SOURCES

That structure should only be used when it is genuinely useful for an engineering investigation or formal evidence response.

For a simple question, answer simply.

I. Engineering safety / grounding

For drilling-engineering questions:

Never invent historical events.

Never invent document citations.

Never invent telemetry.

Never claim OIL confidential data access.

Clearly distinguish demo/synthetic data from real data.

Use "potential risk", "historical precedent", or "engineering review recommended" where appropriate.

Do not present the assistant as autonomous drilling control.

J. Streaming / chat UX

The assistant UI should feel like a real chat application:

User messages aligned consistently.

Assistant messages clearly distinguished.

Input remains available after sending.

Enter sends the message.

Shift+Enter creates a new line if supported.

Show a lightweight typing/processing state.

Disable duplicate submissions while a request is processing.

Render Markdown safely.

Render code blocks correctly.

Preserve conversation history during the current chat session.

Do not reload the entire dashboard for every chat response.

Handle API/network errors gracefully.

Do not create a separate page or redesign the whole application unless necessary.

21. ONE-CLICK PETRONEXUS STARTUP

The repository must provide a single Windows launcher so the user does NOT have to manually start backend and frontend servers.

Create/maintain:

START_PETRONEXUS.bat

at the repository root.

The launcher must:

Change directory to the repository root automatically.

Check whether Python exists.

Prefer .venv\Scripts\python.exe if available.

Fall back to venv\Scripts\python.exe.

Otherwise use python.

Check/install missing backend requirements from backend\requirements.txt only when necessary.

Start the existing FastAPI application through main.py.

Use the existing backend entry point:
backend.app.main:app

Use port 8000 unless the existing project configuration explicitly requires another port.

Automatically open:
http://127.0.0.1:8000/

Print useful URLs:

Main application

Assistant

API docs

Keep the server window visible so errors can be diagnosed.

Stop cleanly with CTRL+C.

Do not start a separate python -m http.server frontend server if FastAPI already serves the frontend.

The current repository's README documents:

python main.py

http://127.0.0.1:8000/

http://127.0.0.1:8000/assistant.html

http://127.0.0.1:8000/docs

Use the existing architecture rather than inventing another server.

If the launcher encounters a dependency error, show the actual error instead of silently failing.

22. STARTUP VALIDATION

After modifying startup:

Run:

.\START_PETRONEXUS.bat

Verify:

Backend starts.

Browser opens.

Landing page loads.

Login loads.

Dashboard loads.

Assistant loads.

/docs loads.

WebSocket functionality remains available.

No second frontend server is required.

Do not add multiple launcher files unless explicitly requested.

23. CHATBOT ACCEPTANCE TESTS

Before considering the assistant work complete, test these exact conversations.

TEST 1:

User:
"What is Azure?"

Expected:
A normal general answer.
No PetroNexus context dump.

TEST 2:

User:
"What is the capital of India?"

Expected:
"New Delhi" with a normal concise answer.

TEST 3:

User:
"What is WITSML?"

Expected:
A concise explanation of WITSML, optionally connected to PetroNexus if useful.

TEST 4:

User:
"What is the current depth?"

Expected:
Answer using the current active well context.

TEST 5:

User:
"What happened ahead of it?"

Expected:
Use the previous conversation + relevant look-ahead data.
Do not repeat all active-well information.

TEST 6:

User:
"Why did you flag this well?"

Expected:
Explain the relevant offset relevance factors and evidence only.

TEST 7:

User:
"Show me the source."

Expected:
Return the relevant document/page citation rather than regenerating the entire analysis.

TEST 8:

User:
"Explain mud loss in simple terms."

Expected:
Normal educational explanation.
Do not inject unrelated active-well telemetry.

TEST 9:

User:
"Compare OIL-DEMO-018 and OIL-DEMO-021 for the current formation."

Expected:
Retrieve only the two relevant wells and current formation context.

TEST 10:

User:
"Tell me a joke."

Expected:
A normal conversational response.
No drilling context.

24. DO NOT OVERENGINEER THE CHATBOT

Do NOT:

Send the complete dashboard state on every request.

Send all database rows to the LLM.

Retrieve every document for every question.

Force every response into an engineering report.

Repeat all previous answers.

Repeat all context.

Add a second LLM framework unnecessarily.

Replace the existing LangChain/Grok integration unless explicitly requested.

Improve the existing assistant instead.

25. PRIORITY ORDER

When implementing future requests, use this priority:

P0:

Application starts reliably.

Existing dashboard works.

Existing authentication works.

Existing map works.

P1:

Natural assistant behavior.

No context repetition.

Correct general-question handling.

Relevant RAG retrieval.

P2:

Real/public petroleum data.

WITSML/ETP adapter.

Better telemetry normalization.

P3:

Predictive risk models.

Formation risk profiles.

More advanced engineering intelligence.
Do not sacrifice P0 functionality for P3 features.