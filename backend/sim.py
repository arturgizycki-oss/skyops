"""SkyOps drone flight simulator.

Simulates a small fleet of multirotor drones with waypoint missions,
battery drain and return-to-launch. No hardware or PX4 required, so the
demo runs on any laptop. The engine ticks at 10 Hz and the API layer
broadcasts telemetry over WebSocket.
"""

import asyncio
import math
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum

EARTH_M_PER_DEG_LAT = 111_320.0

# Rzeszow-Jasionka airport area (Carpathian Drone Summit venue)
HOME_BASE = (50.1090, 22.0230)


def meters_between(a: tuple[float, float], b: tuple[float, float]) -> float:
    dlat = (b[0] - a[0]) * EARTH_M_PER_DEG_LAT
    dlon = (b[1] - a[1]) * EARTH_M_PER_DEG_LAT * math.cos(math.radians(a[0]))
    return math.hypot(dlat, dlon)


class DroneState(str, Enum):
    IDLE = "idle"
    TAKEOFF = "takeoff"
    ENROUTE = "enroute"
    HOLD = "hold"
    RTL = "rtl"
    LANDING = "landing"


@dataclass
class Waypoint:
    lat: float
    lon: float
    alt: float = 50.0


@dataclass
class Drone:
    id: str
    name: str
    lat: float
    lon: float
    home_lat: float
    home_lon: float
    alt: float = 0.0
    heading: float = 0.0
    speed: float = 0.0          # m/s ground speed
    battery: float = 100.0      # percent
    state: DroneState = DroneState.IDLE
    cruise_speed: float = 12.0
    cruise_alt: float = 50.0
    climb_rate: float = 3.0
    mission: list[Waypoint] = field(default_factory=list)
    wp_index: int = 0
    trail: list[tuple[float, float]] = field(default_factory=list)

    BATTERY_DRAIN_FLYING = 0.35   # %/s while flying
    BATTERY_DRAIN_IDLE = 0.005
    LOW_BATTERY_RTL = 25.0

    def start_mission(self, waypoints: list[Waypoint]) -> None:
        if not waypoints:
            return
        self.mission = waypoints
        self.wp_index = 0
        if self.state == DroneState.IDLE:
            self.state = DroneState.TAKEOFF

    def command_rtl(self) -> None:
        if self.state not in (DroneState.IDLE, DroneState.LANDING):
            self.state = DroneState.RTL

    def command_hold(self) -> None:
        if self.state in (DroneState.ENROUTE, DroneState.RTL):
            self.state = DroneState.HOLD

    def command_resume(self) -> None:
        if self.state == DroneState.HOLD:
            self.state = DroneState.ENROUTE if self.wp_index < len(self.mission) else DroneState.RTL

    def _move_towards(self, target: tuple[float, float], dt: float) -> float:
        """Move horizontally towards target, return remaining distance in m."""
        dist = meters_between((self.lat, self.lon), target)
        step = self.cruise_speed * dt
        if dist <= step or dist < 0.5:
            self.lat, self.lon = target
            self.speed = self.cruise_speed
            return 0.0
        frac = step / dist
        dlat = (target[0] - self.lat) * frac
        dlon = (target[1] - self.lon) * frac
        self.heading = (math.degrees(math.atan2(
            (target[1] - self.lon) * math.cos(math.radians(self.lat)),
            target[0] - self.lat)) + 360) % 360
        self.lat += dlat
        self.lon += dlon
        self.speed = self.cruise_speed
        return dist - step

    def update(self, dt: float) -> None:
        flying = self.state not in (DroneState.IDLE,)
        if flying:
            self.battery = max(0.0, self.battery - self.BATTERY_DRAIN_FLYING * dt)
        else:
            # on the ground the crew swaps/charges batteries
            self.battery = min(100.0, self.battery + 1.5 * dt)

        if flying and self.battery <= self.LOW_BATTERY_RTL and self.state not in (
                DroneState.RTL, DroneState.LANDING):
            self.state = DroneState.RTL

        if self.state == DroneState.TAKEOFF:
            self.speed = 0.0
            self.alt = min(self.cruise_alt, self.alt + self.climb_rate * dt)
            if self.alt >= self.cruise_alt:
                self.state = DroneState.ENROUTE

        elif self.state == DroneState.ENROUTE:
            if self.wp_index >= len(self.mission):
                self.state = DroneState.RTL
            else:
                wp = self.mission[self.wp_index]
                remaining = self._move_towards((wp.lat, wp.lon), dt)
                if remaining == 0.0:
                    self.wp_index += 1

        elif self.state == DroneState.HOLD:
            self.speed = 0.0

        elif self.state == DroneState.RTL:
            remaining = self._move_towards((self.home_lat, self.home_lon), dt)
            if remaining == 0.0:
                self.state = DroneState.LANDING

        elif self.state == DroneState.LANDING:
            self.speed = 0.0
            self.alt = max(0.0, self.alt - self.climb_rate * dt)
            if self.alt <= 0.0:
                self.state = DroneState.IDLE
                self.mission = []
                self.wp_index = 0

        if flying:
            if not self.trail or meters_between(self.trail[-1], (self.lat, self.lon)) > 3:
                self.trail.append((self.lat, self.lon))
                if len(self.trail) > 400:
                    self.trail.pop(0)

    def telemetry(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "lat": round(self.lat, 7),
            "lon": round(self.lon, 7),
            "alt": round(self.alt, 1),
            "heading": round(self.heading, 1),
            "speed": round(self.speed, 1),
            "battery": round(self.battery, 1),
            "state": self.state.value,
            "wp_index": self.wp_index,
            "wp_total": len(self.mission),
            "mission": [{"lat": w.lat, "lon": w.lon, "alt": w.alt} for w in self.mission],
        }


class SimEngine:
    def __init__(self) -> None:
        self.drones: dict[str, Drone] = {}
        self._task: asyncio.Task | None = None
        self.subscribers: set[asyncio.Queue] = set()
        for i, offset in enumerate([(0, 0), (0.0009, 0.0012), (-0.0011, 0.0007)]):
            d = Drone(
                id=uuid.uuid4().hex[:8],
                name=f"SKY-{i + 1:02d}",
                lat=HOME_BASE[0] + offset[0],
                lon=HOME_BASE[1] + offset[1],
                home_lat=HOME_BASE[0] + offset[0],
                home_lon=HOME_BASE[1] + offset[1],
            )
            self.drones[d.id] = d

    def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            self._task = None

    async def _run(self) -> None:
        last = time.monotonic()
        broadcast_acc = 0.0
        while True:
            await asyncio.sleep(0.1)
            now = time.monotonic()
            dt, last = now - last, now
            for d in self.drones.values():
                d.update(dt)
            broadcast_acc += dt
            if broadcast_acc >= 0.2:  # 5 Hz to clients
                broadcast_acc = 0.0
                snapshot = {"type": "telemetry",
                            "drones": [d.telemetry() for d in self.drones.values()]}
                for q in list(self.subscribers):
                    if q.full():
                        continue
                    q.put_nowait(snapshot)

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=10)
        self.subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        self.subscribers.discard(q)
