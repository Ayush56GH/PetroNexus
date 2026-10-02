import sys
import asyncio
import json
from pathlib import Path

# Ensure project root is in sys.path regardless of execution method
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Safe UTF-8 reconfiguration on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

from backend.app.config import settings
from backend.app.database import engine, Base
from backend.app.api import api_router
from backend.app.realtime.ertmac_simulator import ertmac_simulator
from backend.app.realtime.replay_engine import replay_engine
from backend.app.utils.logger import logger

from backend.app.utils.db_sync import sync_database_schema

# Initialize and sync database tables & schema columns
sync_database_schema()

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
            
            await ertmac_simulator.broadcast_tick(well_id)
    except WebSocketDisconnect:
        ertmac_simulator.disconnect(websocket, well_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ertmac_simulator.disconnect(websocket, well_id)

# WebSocket for Real Data Replay
@app.websocket("/ws/replay/{well_id}")
async def websocket_replay_endpoint(websocket: WebSocket, well_id: int):
    await replay_engine.connect(websocket, well_id)
    try:
        while True:
            data = await websocket.receive_text()
            cmd = data.strip().upper()
            speed = 1.0
            if cmd.startswith("{"):
                try:
                    payload = json.loads(data)
                    cmd = str(payload.get("command", "")).strip().upper()
                    speed = float(payload.get("speed", 1.0))
                except Exception:
                    pass
            if cmd in ["START", "PLAY"]:
                replay_engine.play(well_id, speed)
            elif cmd == "PAUSE":
                replay_engine.pause(well_id)
            elif cmd == "RESET":
                replay_engine.reset(well_id)
            elif cmd == "SPEED":
                replay_engine.set_speed(well_id, speed)
            elif cmd in ["TICK", "STEP"]:
                await replay_engine.broadcast_tick(well_id)
            
            await replay_engine.broadcast_tick(well_id)
    except WebSocketDisconnect:
        replay_engine.disconnect(websocket, well_id)
    except Exception as e:
        logger.error(f"Replay WebSocket error: {e}")
        replay_engine.disconnect(websocket, well_id)

# Background tasks for auto-ticking simulation and replay
@app.on_event("startup")
async def startup_event():
    async def simulation_loop():
        while True:
            await asyncio.sleep(1.0)
            for w_id in list(ertmac_simulator.active_connections.keys()):
                state = ertmac_simulator.get_or_create_state(w_id)
                if state.get("is_running", False):
                    await ertmac_simulator.broadcast_tick(w_id)

    async def replay_loop():
        while True:
            await asyncio.sleep(0.5)
            for w_id in list(replay_engine.active_connections.keys()):
                state = replay_engine.get_or_create_state(w_id)
                if state.get("is_running", False):
                    await replay_engine.broadcast_tick(w_id)

    asyncio.create_task(simulation_loop())
    asyncio.create_task(replay_loop())
    logger.info("PetroNexus backend started successfully with Replay and Simulator engines.")

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)

