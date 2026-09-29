import asyncio
import json
import websockets

async def test_websocket():
    uri = "ws://127.0.0.1:8000/ws/drilling/23"
    async with websockets.connect(uri) as ws:
        init_raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
        init_data = json.loads(init_raw)
        print("Connected to eRTMAC WebSocket. Status:", init_data.get("status"))

        await ws.send("START")
        for i in range(3):
            msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
            data = json.loads(msg)
            t = data.get("telemetry", {})
            print(f"Update {i+1}: Depth={t.get('depth')}m | Torque={t.get('torque')} kN.m | ROP={t.get('rop')} m/hr | Anomalies={len(data.get('anomalies', []))}")

        await ws.send("PAUSE")
        print("[PASS] WebSocket eRTMAC live stream operational!")

if __name__ == "__main__":
    asyncio.run(test_websocket())
