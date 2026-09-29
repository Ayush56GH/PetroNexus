"""
PetroNexus Live Simulated eRTMAC WebSocket Service
Simulates real-time telemetry streaming from Oil India Limited rig sensors.
Supports START, PAUSE, RESET controls, parameter fluctuation, and triggers live anomalies.
"""
import asyncio
import datetime
import json
import random
from typing import Dict, Any, Set
from fastapi import WebSocket
from backend.app.services.physics_service import calculate_mse
from backend.app.realtime.anomaly_detector import RealTimeAnomalyDetector
from backend.app.utils.logger import logger

class ERTMACSimulator:

    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        self.simulation_state: Dict[int, Dict[str, Any]] = {}

    def get_or_create_state(self, well_id: int) -> Dict[str, Any]:
        if well_id not in self.simulation_state:
            self.simulation_state[well_id] = {
                "is_running": False,
                "current_depth": 2846.0,
                "base_depth": 2846.0,
                "rop": 14.5,
                "wob": 12.0,
                "rpm": 110.0,
                "torque": 16.8,
                "ecd": 1.28,
                "mud_weight": 1.22,
                "spp": 2450.0,
                "flow_rate": 2150.0,
                "hook_load": 85.0,
                "step_count": 0
            }
        return self.simulation_state[well_id]

    async def connect(self, websocket: WebSocket, well_id: int):
        await websocket.accept()
        if well_id not in self.active_connections:
            self.active_connections[well_id] = set()
        self.active_connections[well_id].add(websocket)
        logger.info(f"WebSocket client connected to eRTMAC stream for Well {well_id}")

        # Send initial state snapshot
        state = self.get_or_create_state(well_id)
        msg = self._generate_payload(well_id, state)
        await websocket.send_text(json.dumps(msg))

    def disconnect(self, websocket: WebSocket, well_id: int):
        if well_id in self.active_connections:
            self.active_connections[well_id].discard(websocket)
            if not self.active_connections[well_id]:
                del self.active_connections[well_id]
        logger.info(f"WebSocket client disconnected from Well {well_id}")

    def start(self, well_id: int):
        state = self.get_or_create_state(well_id)
        state["is_running"] = True
        logger.info(f"eRTMAC simulation STARTED for Well {well_id}")

    def pause(self, well_id: int):
        state = self.get_or_create_state(well_id)
        state["is_running"] = False
        logger.info(f"eRTMAC simulation PAUSED for Well {well_id}")

    def reset(self, well_id: int):
        state = self.get_or_create_state(well_id)
        state["is_running"] = False
        state["current_depth"] = state["base_depth"]
        state["torque"] = 16.8
        state["rop"] = 14.5
        state["ecd"] = 1.28
        state["spp"] = 2450.0
        state["step_count"] = 0
        logger.info(f"eRTMAC simulation RESET for Well {well_id}")

    def step_simulation(self, well_id: int) -> Dict[str, Any]:
        """
        Advances the simulated drilling parameters by one second tick.
        Produces realistic slight variance and induces an anomaly near ~2855-2860m!
        """
        state = self.get_or_create_state(well_id)
        if not state["is_running"]:
            return self._generate_payload(well_id, state)

        state["step_count"] += 1
        
        # Advance depth slowly (e.g. 0.05m per tick at ~15m/hr)
        state["current_depth"] = round(state["current_depth"] + 0.08, 2)

        # Base noise
        state["rop"] = max(2.0, min(30.0, round(state["rop"] + random.uniform(-0.4, 0.4), 1)))
        state["wob"] = max(8.0, min(18.0, round(state["wob"] + random.uniform(-0.2, 0.2), 1)))
        state["rpm"] = max(90.0, min(130.0, round(state["rpm"] + random.uniform(-1.0, 1.0), 0)))
        state["spp"] = max(2200.0, min(2900.0, round(state["spp"] + random.uniform(-15.0, 15.0), 0)))
        state["flow_rate"] = max(2000.0, min(2300.0, round(state["flow_rate"] + random.uniform(-10.0, 10.0), 0)))

        # Demonstration Scenario: As bit approaches 2855-2860m (offset OIL-DEMO-018 mud loss zone @ 2860m),
        # torque increases and ECD climbs!
        depth = state["current_depth"]
        if 2852.0 <= depth <= 2862.0:
            # Anomaly interval
            state["torque"] = round(min(24.5, state["torque"] + 0.35), 1)
            state["ecd"] = round(min(1.36, state["ecd"] + 0.01), 3)
            state["rop"] = max(3.5, round(state["rop"] - 0.3, 1))
        else:
            state["torque"] = max(15.0, min(18.5, round(state["torque"] + random.uniform(-0.2, 0.2), 1)))
            state["ecd"] = max(1.26, min(1.29, round(state["ecd"] + random.uniform(-0.005, 0.005), 3)))

        return self._generate_payload(well_id, state)

    def _generate_payload(self, well_id: int, state: Dict[str, Any]) -> Dict[str, Any]:
        mse = calculate_mse(state["wob"], state["torque"], state["rpm"], state["rop"], bit_diameter_in=8.5)
        now_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        telemetry = {
            "timestamp": now_str,
            "depth": state["current_depth"],
            "tvd": round(state["current_depth"] * 0.985, 2), # Trajectory ratio approx
            "rop": state["rop"],
            "wob": state["wob"],
            "rpm": state["rpm"],
            "torque": state["torque"],
            "ecd": state["ecd"],
            "mud_weight": state["mud_weight"],
            "spp": state["spp"],
            "flow_rate": state["flow_rate"],
            "hook_load": state["hook_load"],
            "mse": mse
        }

        # Simulated historical hazards nearby
        simulated_hazards = [
            {
                "offset_well_name": "OIL-DEMO-018",
                "hazard_depth_md_m": 2860.0,
                "event_type": "Mud Loss (Partial Loss of 45 bbl)",
                "historical_mitigation": "Pumped 30 bbl medium LCM pill and reduced flow rate"
            },
            {
                "offset_well_name": "OIL-DEMO-021",
                "hazard_depth_md_m": 2842.0,
                "event_type": "Torque Spike & Pack-Off",
                "historical_mitigation": "Worked string and reamed tight interval"
            }
        ]

        anomalies = RealTimeAnomalyDetector.detect_anomalies(telemetry, simulated_hazards)

        return {
            "well_id": well_id,
            "is_running": state["is_running"],
            "telemetry": telemetry,
            "anomalies": anomalies,
            "historical_proximity": {
                "active_formation": "Formation-X",
                "nearest_offset_hazard": "Mud Loss in OIL-DEMO-018 @ 2860 m",
                "delta_m": round(2860.0 - state["current_depth"], 1)
            }
        }

    async def broadcast_tick(self, well_id: int):
        if well_id in self.active_connections and self.active_connections[well_id]:
            payload = self.step_simulation(well_id)
            json_str = json.dumps(payload)
            for ws in list(self.active_connections[well_id]):
                try:
                    await ws.send_text(json_str)
                except Exception:
                    self.disconnect(ws, well_id)

ertmac_simulator = ERTMACSimulator()
