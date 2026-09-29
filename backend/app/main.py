import asyncio
import json
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

from backend.app.config import settings
from backend.app.database import engine, Base
from backend.app.api import api_router
from backend.app.realtime.ertmac_simulator import ertmac_simulator
from backend.app.utils.logger import logger

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="PetroNexus: AI-Powered Nearby Well Intelligence & Drilling Decision Support Platform. Smart India Hackathon 2026 — SIH26121 for Oil India Limited (OIL).",
    version=settings.VERSION
)

# CORS middleware for development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# WebSocket for simulated eRTMAC live telemetry
@app.websocket("/ws/drilling/{well_id}")
async def websocket_drilling_endpoint(websocket: WebSocket, well_id: int):
    await ertmac_simulator.connect(websocket, well_id)
    try:
        while True:
            # Wait for client control commands (e.g. START, PAUSE, RESET)
            data = await websocket.receive_text()
            cmd = data.strip().upper()
            if cmd.startswith("{"):
                try:
                    payload = json.loads(data)
                    cmd = str(payload.get("command", "")).strip().upper()
                except Exception:
                    pass
            if cmd == "START":
                ertmac_simulator.start(well_id)
            elif cmd == "PAUSE":
                ertmac_simulator.pause(well_id)
            elif cmd == "RESET":
                ertmac_simulator.reset(well_id)
            elif cmd == "TICK":
                await ertmac_simulator.broadcast_tick(well_id)
            
            # Immediately send updated state
            await ertmac_simulator.broadcast_tick(well_id)
    except WebSocketDisconnect:
        ertmac_simulator.disconnect(websocket, well_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ertmac_simulator.disconnect(websocket, well_id)

# Background task for auto-ticking simulated eRTMAC when running
@app.on_event("startup")
async def startup_event():
    async def simulation_loop():
        while True:
            await asyncio.sleep(1.0)
            for w_id in list(ertmac_simulator.active_connections.keys()):
                state = ertmac_simulator.get_or_create_state(w_id)
                if state.get("is_running", False):
                    await ertmac_simulator.broadcast_tick(w_id)
    asyncio.create_task(simulation_loop())
    logger.info("PetroNexus backend started successfully.")

# Mount frontend directory for full-stack unified single-port hosting
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/{page_name}.html")
    def serve_html_page(page_name: str):
        page_file = FRONTEND_DIR / f"{page_name}.html"
        if page_file.exists():
            return FileResponse(page_file)
        return RedirectResponse(url="/")
