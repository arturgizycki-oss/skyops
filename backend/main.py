"""SkyOps API server.

Run:  uvicorn main:app --port 8000   (from the backend/ folder)
Then open http://localhost:8000
"""

import asyncio
import os
import random
import time
from contextlib import asynccontextmanager
from pathlib import Path

from airspace import airspace

from fastapi import FastAPI, HTTPException, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from detection import detector
from flight_log import recorder, render_pdf, render_sitrep
from geofence import geofences
from sim import SimEngine, Waypoint
from swarm import swarm

engine = SimEngine()
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
LANDING_DIR = Path(__file__).resolve().parent.parent / "landing"


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine.start()
    detector.start()
    swarm.attach(engine)
    mavlink_url = os.environ.get("SKYOPS_MAVLINK_URL")
    if mavlink_url:
        from mavlink_link import MavlinkDrone
        real = MavlinkDrone(mavlink_url)
        engine.drones[real.id] = real
        asyncio.create_task(real.start())

    async def record_loop():
        last = time.monotonic()
        while True:
            await asyncio.sleep(1.0)
            now = time.monotonic()
            dt, last = now - last, now
            vstat = detector.status()
            recorder.tick(engine.drones.values(), vstat["detections"],
                          vstat.get("mode", "search"))
            app.state.airspace_picture = airspace.step(dt, engine.drones.values())
            # geofence enforcement: breach -> immediate return home
            for d in engine.drones.values():
                t = d.telemetry()
                if t["state"] in ("enroute", "hold", "takeoff") and \
                        geofences.violating_zone(t["lat"], t["lon"]):
                    d.command_rtl()

    rec_task = asyncio.create_task(record_loop())
    demo_task = asyncio.create_task(_demo_loop())
    yield
    rec_task.cancel()
    demo_task.cancel()
    await engine.stop()


app = FastAPI(title="SkyOps", version="0.1.0", lifespan=lifespan)
demo_mode = {"on": False}


def _random_patrol(drone) -> list[Waypoint]:
    """3-5 waypoints within ~1.2 km of the drone's home, outside no-fly zones."""
    wps = []
    tries = 0
    while len(wps) < random.randint(3, 5) and tries < 40:
        tries += 1
        lat = drone.home_lat + random.uniform(-0.010, 0.010)
        lon = drone.home_lon + random.uniform(-0.016, 0.016)
        if geofences.violating_zone(lat, lon):
            continue
        wps.append(Waypoint(lat, lon, 50.0))
    return wps


async def _demo_loop():
    while True:
        await asyncio.sleep(5.0)
        if not demo_mode["on"]:
            continue
        for d in engine.drones.values():
            t = d.telemetry()
            if t["state"] == "idle" and t["battery"] > 40:
                wps = _random_patrol(d)
                if wps:
                    d.start_mission(wps)


class WaypointIn(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    alt: float = Field(default=50.0, ge=5, le=500)


class MissionIn(BaseModel):
    waypoints: list[WaypointIn]


class CommandIn(BaseModel):
    command: str  # rtl | hold | resume


@app.get("/api/drones")
def list_drones():
    return [d.telemetry() for d in engine.drones.values()]


@app.post("/api/drones/{drone_id}/mission")
def start_mission(drone_id: str, mission: MissionIn):
    drone = engine.drones.get(drone_id)
    if not drone:
        raise HTTPException(404, "drone not found")
    if not mission.waypoints:
        raise HTTPException(400, "mission needs at least one waypoint")
    for i, w in enumerate(mission.waypoints):
        zone = geofences.violating_zone(w.lat, w.lon)
        if zone:
            raise HTTPException(
                409, f"waypoint {i + 1} is inside no-fly zone '{zone['name']}'")
    drone.start_mission([Waypoint(w.lat, w.lon, w.alt) for w in mission.waypoints])
    return {"ok": True, "state": drone.state.value, "utm": _utm_checkin()}


@app.post("/api/drones/{drone_id}/command")
def command(drone_id: str, cmd: CommandIn):
    drone = engine.drones.get(drone_id)
    if not drone:
        raise HTTPException(404, "drone not found")
    if cmd.command == "rtl":
        drone.command_rtl()
    elif cmd.command == "hold":
        drone.command_hold()
    elif cmd.command == "resume":
        drone.command_resume()
    else:
        raise HTTPException(400, f"unknown command: {cmd.command}")
    return {"ok": True, "state": drone.state.value}


@app.websocket("/ws")
async def telemetry_ws(ws: WebSocket):
    await ws.accept()
    queue = engine.subscribe()
    try:
        while True:
            snapshot = await queue.get()
            await ws.send_json(snapshot)
    except WebSocketDisconnect:
        pass
    finally:
        engine.unsubscribe(queue)


class AreaMissionIn(BaseModel):
    points: list[WaypointIn] = Field(min_length=3)
    spacing_m: float = Field(default=80.0, ge=20, le=300)
    alt: float = Field(default=50.0, ge=5, le=500)


@app.post("/api/area_mission")
def area_mission(body: AreaMissionIn):
    from areamission import area_routes
    idle = [d for d in engine.drones.values()
            if d.telemetry()["state"] == "idle"]
    if not idle:
        raise HTTPException(409, "no idle drones available")
    routes = area_routes(
        [(p.lat, p.lon) for p in body.points],
        body.spacing_m, len(idle), body.alt)
    if not routes:
        raise HTTPException(400, "area produced no reachable waypoints")
    assigned = []
    for drone, route in zip(idle, routes):
        drone.start_mission(route)
        assigned.append({"drone": drone.name, "waypoints": len(route)})
    return {"ok": True, "assigned": assigned, "utm": _utm_checkin()}


class ZonePoint(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class ZoneIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    points: list[ZonePoint] = Field(min_length=3)


@app.get("/api/zones")
def list_zones():
    return geofences.zones


@app.post("/api/zones")
def add_zone(zone: ZoneIn):
    return geofences.add(zone.name, [p.model_dump() for p in zone.points])


@app.delete("/api/zones/{zone_id}")
def delete_zone(zone_id: str):
    if not geofences.remove(zone_id):
        raise HTTPException(404, "zone not found")
    return {"ok": True}


@app.get("/api/logs")
def list_logs():
    return recorder.list_logs()


@app.get("/api/logs/{log_id}")
def log_detail(log_id: str):
    rec = recorder.get(log_id)
    if not rec:
        raise HTTPException(404, "log not found")
    return rec


@app.get("/api/logs/{log_id}/report")
def log_report(log_id: str):
    rec = recorder.get(log_id)
    if not rec:
        raise HTTPException(404, "log not found")
    pdf = render_pdf(rec)
    return Response(
        content=pdf, media_type="application/pdf",
        headers={"Content-Disposition":
                 f'inline; filename="skyops-flight-{log_id}.pdf"'})


@app.get("/api/logs/{log_id}/sitrep")
def log_sitrep(log_id: str):
    rec = recorder.get(log_id)
    if not rec:
        raise HTTPException(404, "log not found")
    pdf = render_sitrep(rec)
    return Response(
        content=pdf, media_type="application/pdf",
        headers={"Content-Disposition":
                 f'inline; filename="skyops-sitrep-{log_id}.pdf"'})


TILES_DIR = Path(__file__).resolve().parent / "tiles"
TILES_DIR.mkdir(exist_ok=True)


@app.get("/tiles/{z}/{x}/{y}.png")
def map_tile(z: int, x: int, y: int):
    """Caching proxy for OSM tiles: serves from disk when offline."""
    if not (3 <= z <= 19 and 0 <= x < 2 ** z and 0 <= y < 2 ** z):
        raise HTTPException(400, "tile out of range")
    cached = TILES_DIR / str(z) / str(x) / f"{y}.png"
    if not cached.exists():
        import requests
        try:
            r = requests.get(
                f"https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                headers={"User-Agent": "SkyOps-demo-tile-cache/1.0"},
                timeout=10)
            r.raise_for_status()
        except Exception:
            raise HTTPException(503, "tile unavailable offline")
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_bytes(r.content)
    return FileResponse(cached, media_type="image/png",
                        headers={"Cache-Control": "public, max-age=86400"})


@app.get("/api/video/stream")
def video_stream():
    if not detector.enabled:
        raise HTTPException(503, "video source not available")
    return StreamingResponse(
        detector.mjpeg_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame")


@app.get("/api/video/status")
def video_status():
    return detector.status()


class ModeIn(BaseModel):
    mode: str


@app.post("/api/video/mode")
def set_video_mode(body: ModeIn):
    if not detector.set_mode(body.mode):
        raise HTTPException(400, f"unknown or unavailable mode: {body.mode}")
    return {"ok": True, "mode": body.mode}


@app.get("/api/alerts")
def list_alerts():
    return detector.recent_alerts()


@app.get("/api/traffic")
def traffic_picture():
    return getattr(app.state, "airspace_picture",
                   {"aircraft": [], "conflicts": []})


class SwarmIn(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    count: int = Field(default=200, ge=1, le=400)


@app.get("/api/swarm")
def swarm_status():
    return swarm.stats()


@app.post("/api/swarm")
def swarm_deploy(body: SwarmIn):
    """Deploy the concept firefighting swarm onto a fire at lat/lon."""
    return swarm.deploy(body.lat, body.lon, body.count)


@app.delete("/api/swarm")
def swarm_stand_down():
    swarm.stand_down()
    return {"ok": True, "active": False}


def _utm_checkin() -> dict:
    """Simulated UTM/U-space check-in (PansaUTM-style reference)."""
    return {"checked_in": True,
            "ref": f"UTM-SIM-{random.randint(100000, 999999)}"}


class DemoIn(BaseModel):
    on: bool


@app.get("/api/demo")
def demo_status():
    return demo_mode


@app.post("/api/demo")
def demo_toggle(body: DemoIn):
    demo_mode["on"] = body.on
    return demo_mode


@app.get("/")
def landing():
    return FileResponse(LANDING_DIR / "index.html")


@app.get("/app")
def dashboard():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/share")
def share_view():
    """Read-only observer view - same dashboard, no command controls."""
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
app.mount("/assets", StaticFiles(directory=LANDING_DIR / "assets"), name="assets")
