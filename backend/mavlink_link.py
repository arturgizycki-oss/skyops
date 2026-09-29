"""SkyOps real-drone connector (MAVLink via MAVSDK).

Bridges a physical PX4/ArduPilot aircraft (or PX4 SITL) into the same
fleet API the simulator uses, so the dashboard needs no changes to
control real hardware.

Enable by setting the environment variable before starting the server:

    SKYOPS_MAVLINK_URL=udp://:14540        (PX4 SITL default)
    SKYOPS_MAVLINK_URL=serial:///dev/ttyUSB0:57600   (telemetry radio)

The aircraft appears in the fleet as REAL-01 once MAVSDK connects.
"""

import asyncio
import logging
import uuid

from mavsdk import System
from mavsdk.mission import MissionItem, MissionPlan

from sim import Waypoint

log = logging.getLogger("skyops.mavlink")

# Map PX4 flight modes onto the dashboard's state vocabulary.
_MODE_TO_STATE = {
    "READY": "idle",
    "TAKEOFF": "takeoff",
    "MISSION": "enroute",
    "HOLD": "hold",
    "RETURN_TO_LAUNCH": "rtl",
    "LAND": "landing",
}


class MavlinkDrone:
    """Adapter exposing the same interface as sim.Drone."""

    def __init__(self, url: str, name: str = "REAL-01") -> None:
        self.id = uuid.uuid4().hex[:8]
        self.name = name
        self.url = url
        self.system = System()
        self.connected = False
        self._telemetry = {
            "lat": 0.0, "lon": 0.0, "alt": 0.0, "heading": 0.0,
            "speed": 0.0, "battery": 0.0, "state": "connecting",
        }
        self.mission: list[Waypoint] = []
        self.wp_index = 0

    async def start(self) -> None:
        await self.system.connect(system_address=self.url)
        async for cs in self.system.core.connection_state():
            if cs.is_connected:
                break
        self.connected = True
        self._telemetry["state"] = "idle"
        log.info("MAVLink aircraft connected on %s", self.url)
        for coro in (self._track_position(), self._track_velocity(),
                     self._track_battery(), self._track_mode(),
                     self._track_mission_progress()):
            asyncio.create_task(coro)

    async def _track_position(self) -> None:
        async for pos in self.system.telemetry.position():
            self._telemetry["lat"] = pos.latitude_deg
            self._telemetry["lon"] = pos.longitude_deg
            self._telemetry["alt"] = pos.relative_altitude_m

    async def _track_velocity(self) -> None:
        async for v in self.system.telemetry.velocity_ned():
            self._telemetry["speed"] = (v.north_m_s ** 2 + v.east_m_s ** 2) ** 0.5

    async def _track_battery(self) -> None:
        async for b in self.system.telemetry.battery():
            self._telemetry["battery"] = b.remaining_percent * 100

    async def _track_mode(self) -> None:
        async for mode in self.system.telemetry.flight_mode():
            self._telemetry["state"] = _MODE_TO_STATE.get(mode.name, "enroute")

    async def _track_mission_progress(self) -> None:
        async for mp in self.system.mission.mission_progress():
            self.wp_index = mp.current

    # ---- fleet API (same shape as sim.Drone) ----

    def start_mission(self, waypoints: list[Waypoint]) -> None:
        self.mission = waypoints
        self.wp_index = 0
        asyncio.create_task(self._fly_mission(waypoints))

    async def _fly_mission(self, waypoints: list[Waypoint]) -> None:
        items = [
            MissionItem(
                w.lat, w.lon, w.alt, 10.0, True,
                float("nan"), float("nan"),
                MissionItem.CameraAction.NONE,
                float("nan"), float("nan"), float("nan"),
                float("nan"), float("nan"),
                MissionItem.VehicleAction.NONE)
            for w in waypoints
        ]
        await self.system.mission.set_return_to_launch_after_mission(True)
        await self.system.mission.upload_mission(MissionPlan(items))
        await self.system.action.arm()
        await self.system.mission.start_mission()

    def command_rtl(self) -> None:
        asyncio.create_task(self.system.action.return_to_launch())

    def command_hold(self) -> None:
        asyncio.create_task(self.system.action.hold())

    def command_resume(self) -> None:
        asyncio.create_task(self.system.mission.start_mission())

    def update(self, dt: float) -> None:
        pass  # telemetry is pushed by MAVSDK subscriptions

    def telemetry(self) -> dict:
        t = self._telemetry
        return {
            "id": self.id,
            "name": self.name,
            "lat": round(t["lat"], 7),
            "lon": round(t["lon"], 7),
            "alt": round(t["alt"], 1),
            "heading": round(t["heading"], 1),
            "speed": round(t["speed"], 1),
            "battery": round(t["battery"], 1),
            "state": t["state"],
            "wp_index": self.wp_index,
            "wp_total": len(self.mission),
            "mission": [{"lat": w.lat, "lon": w.lon, "alt": w.alt}
                        for w in self.mission],
        }
