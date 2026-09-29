# SkyOps - Drone Fleet Operations Platform

Web-based drone fleet dashboard: live map, telemetry, mission planning.
Ships with a built-in flight simulator, so the full demo runs on any
laptop with no drone hardware and no PX4 install.

## Quick start

```
cd skyops/backend
pip install -r requirements.txt
uvicorn main:app --port 8000
```

Open http://localhost:8000

## Demo script (for the conference)

1. Three simulated drones sit at Rzeszow-Jasionka airport.
2. Click a drone card, press "Plan mission", click waypoints on the map.
3. Press "Launch" - the drone takes off, flies the route, returns home.
4. Show Hold / Resume / Return home commands mid-flight.
5. Point out live telemetry: altitude, speed, battery with auto-RTL
   at 25% battery.

## Offline demo mode

Map tiles are served through a local caching proxy (`/tiles/...`).
The Jasionka venue area (zoom 12-16, ~840 tiles) is pre-seeded in
`backend/tiles/`, so with no internet the map, simulator and AI all
still work - only the public tunnel link needs connectivity. Browsing
new areas online caches them automatically.

## Architecture

- `backend/sim.py` - 10 Hz flight simulator (waypoints, battery, RTL)
- `backend/main.py` - FastAPI: REST commands + WebSocket telemetry (5 Hz)
- `frontend/` - Leaflet dark map dashboard, no build step

## Roadmap

- [x] Live video panel + YOLOv8 object detection overlay
- [x] MAVSDK connector to fly a real PX4 drone with the same UI

## Real drone / PX4 SITL

Set `SKYOPS_MAVLINK_URL` before starting the server and the aircraft
joins the fleet as REAL-01 next to the simulated drones:

```
# PX4 SITL (default port)
SKYOPS_MAVLINK_URL=udp://:14540 uvicorn main:app --port 8000

# Telemetry radio on serial
SKYOPS_MAVLINK_URL=serial:///dev/ttyUSB0:57600 uvicorn main:app --port 8000
```

Missions, hold/resume and return-home from the dashboard then command
the real aircraft through MAVSDK. Tested against the MAVSDK API; flight
verification against PX4 SITL still pending (SITL needs WSL2/Docker on
Windows).
- [x] Geofencing: no-fly zones drawn on the map; missions into a zone
      are rejected and a drone breaching one returns home automatically
- [x] Flight logs with one-click PDF reports (route, telemetry, AI
      detections per flight)
- [x] Fire swarm concept mode: up to 200 aircraft fighting a spreading
      wildfire (transit / drop run / refill cycle) against a cellular
      fire model, reporting live containment percentage. Clearly
      labelled a concept in the UI - no such fleet is fielded today.
      Proves the control layer scales from 3 to 200 aircraft:
      0.3% of one CPU core, 27 KB/s per viewer.
- [ ] Mission save/load templates
- [ ] Multi-user auth, cloud deploy, landing page
