"""SkyOps fire-swarm concept simulator.

A forward-deployed swarm (up to 200 aircraft) fighting a spreading
wildfire from the air: transit to the fire front, water drop run,
return to the forward base, refill, repeat.

This is a CONCEPT simulation and is labelled as such in the UI. No such
fleet is fielded today; the point is to show what the control layer
looks like when it is, and that our architecture scales from three
aircraft to two hundred without changing the operator's screen.

Runs independently of SimEngine: the named fleet, the flight logs and
geofencing are untouched by anything in this module.
"""

import asyncio
import math
import random
import time

from sim import EARTH_M_PER_DEG_LAT

CELL_M = 50.0              # fire grid resolution
FIRE_MAX_RADIUS_M = 420.0  # fire cannot grow past this (keeps the demo bounded)
SPREAD_PER_SEC = 0.060     # chance a burning cell ignites a given neighbour
DROP_RUN_M = 140.0         # length of one water drop run
DROP_SWATH_M = 90.0        # effective width of a drop
REFILL_SEC = 6.0
LAUNCH_SPREAD_SEC = 50.0   # departures spread over this window at deploy
BASE_OFFSET_M = 550.0      # forward base distance from the fire origin
LITRES_PER_CELL = 200      # water credited per cell knocked down

TRANSIT, DROP, RETURN, REFILL = 0, 1, 2, 3
BURNING, OUT = 1, 2


def _offset(origin, north_m, east_m):
    lat = origin[0] + north_m / EARTH_M_PER_DEG_LAT
    lon = origin[1] + east_m / (EARTH_M_PER_DEG_LAT *
                                math.cos(math.radians(origin[0])))
    return lat, lon


class FireGrid:
    """Cellular wildfire: burning cells ignite their neighbours."""

    def __init__(self, origin):
        self.origin = origin
        self.cells: dict[tuple[int, int], int] = {}
        for cell in ((0, 0), (1, 0), (0, 1), (-1, 0), (0, -1)):
            self.cells[cell] = BURNING
        self._acc = 0.0

    def step(self, dt):
        # spread on a 1 Hz cadence; cheap, and smooth enough to watch
        self._acc += dt
        if self._acc < 1.0:
            return
        self._acc = 0.0
        max_cells = (FIRE_MAX_RADIUS_M / CELL_M) ** 2
        new = []
        for (i, j), st in self.cells.items():
            if st != BURNING:
                continue
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (i + di, j + dj)
                if n in self.cells or (n[0] ** 2 + n[1] ** 2) > max_cells:
                    continue
                if random.random() < SPREAD_PER_SEC:
                    new.append(n)
        for n in new:
            self.cells[n] = BURNING

    def extinguish(self, lat, lon, radius_m):
        """Put out burning cells within radius_m of a point; returns count."""
        ci = int(round((lat - self.origin[0]) * EARTH_M_PER_DEG_LAT / CELL_M))
        cj = int(round((lon - self.origin[1]) * EARTH_M_PER_DEG_LAT *
                       math.cos(math.radians(self.origin[0])) / CELL_M))
        span = int(radius_m / CELL_M) + 1
        hit = 0
        for i in range(ci - span, ci + span + 1):
            for j in range(cj - span, cj + span + 1):
                if self.cells.get((i, j)) != BURNING:
                    continue
                if math.hypot((i - ci) * CELL_M, (j - cj) * CELL_M) <= radius_m:
                    self.cells[(i, j)] = OUT
                    hit += 1
        return hit

    def burning(self):
        return [c for c, st in self.cells.items() if st == BURNING]

    def containment(self):
        out = sum(1 for st in self.cells.values() if st == OUT)
        total = len(self.cells)
        return 100.0 * out / total if total else 0.0

    def snapshot(self):
        """Compact: [i, j, state] per touched cell."""
        return [[i, j, st] for (i, j), st in self.cells.items()]


class SwarmDrone:
    __slots__ = ("lat", "lon", "heading", "state", "timer",
                 "tlat", "tlon", "run_left", "drops")

    def __init__(self, lat, lon):
        self.lat, self.lon = lat, lon
        self.heading = 0.0
        self.state = REFILL
        self.timer = 0.0   # set by deploy(): staggered so they fly as a stream
        self.tlat = self.tlon = 0.0
        self.run_left = 0.0
        self.drops = 0


class FireSwarm:
    """Manages the concept swarm and the fire it is fighting."""

    SPEED = 20.0  # m/s

    def __init__(self):
        self.active = False
        self.drones: list[SwarmDrone] = []
        self.fire: FireGrid | None = None
        self.base = (0.0, 0.0)
        self.started_at = 0.0
        self.water_l = 0
        self._task = None
        self._acc = 0.0

    # --- control ---

    def deploy(self, lat, lon, count):
        self.fire = FireGrid((lat, lon))
        self.base = _offset((lat, lon), -BASE_OFFSET_M, -BASE_OFFSET_M)
        self.drones = [SwarmDrone(*_offset(self.base, (k % 20) * 12.0,
                                           (k // 20) * 12.0))
                       for k in range(count)]
        # stagger departures across a full sortie cycle so the swarm forms a
        # continuous conveyor between base and fire instead of one clump
        for k, d in enumerate(self.drones):
            d.timer = LAUNCH_SPREAD_SEC * k / max(1, count)
        self.water_l = 0
        self.started_at = time.monotonic()
        self.active = True
        return self.stats()

    def stand_down(self):
        self.active = False
        self.drones = []
        self.fire = None

    def stats(self):
        if not self.active or self.fire is None:
            return {"active": False}
        return {
            "active": True,
            "count": len(self.drones),
            "airborne": sum(1 for d in self.drones if d.state != REFILL),
            "containment": round(self.fire.containment(), 1),
            "burning_cells": len(self.fire.burning()),
            "area_burning_ha": round(
                len(self.fire.burning()) * CELL_M ** 2 / 10000, 1),
            "drops": sum(d.drops for d in self.drones),
            "water_l": self.water_l,
            "elapsed_s": int(time.monotonic() - self.started_at),
        }

    # --- physics ---

    def _pick_target(self, d):
        burning = self.fire.burning()
        if not burning:
            return False
        i, j = random.choice(burning)
        d.tlat, d.tlon = _offset(self.fire.origin, i * CELL_M, j * CELL_M)
        return True

    def _fly_to(self, d, dt):
        """Move toward (tlat, tlon); True once arrived."""
        dlat = (d.tlat - d.lat) * EARTH_M_PER_DEG_LAT
        dlon = (d.tlon - d.lon) * EARTH_M_PER_DEG_LAT * \
            math.cos(math.radians(d.lat))
        dist = math.hypot(dlat, dlon)
        if dist < 1.0:
            return True
        d.heading = math.degrees(math.atan2(dlon, dlat)) % 360
        step = min(self.SPEED * dt, dist)
        d.lat += (dlat / dist) * step / EARTH_M_PER_DEG_LAT
        d.lon += (dlon / dist) * step / (EARTH_M_PER_DEG_LAT *
                                         math.cos(math.radians(d.lat)))
        return False

    def step(self, dt):
        if not self.active or self.fire is None:
            return
        self.fire.step(dt)
        for d in self.drones:
            if d.state == REFILL:
                d.timer -= dt
                if d.timer <= 0:
                    if self._pick_target(d):
                        d.state = TRANSIT
                    else:
                        d.timer = 2.0   # fire is out; hold at base
            elif d.state == TRANSIT:
                if self._fly_to(d, dt):
                    d.state = DROP
                    d.run_left = DROP_RUN_M
            elif d.state == DROP:
                step = min(self.SPEED * dt, d.run_left)
                rad = math.radians(d.heading)
                d.lat += (step * math.cos(rad)) / EARTH_M_PER_DEG_LAT
                d.lon += (step * math.sin(rad)) / (
                    EARTH_M_PER_DEG_LAT * math.cos(math.radians(d.lat)))
                self.water_l += self.fire.extinguish(
                    d.lat, d.lon, DROP_SWATH_M / 2) * LITRES_PER_CELL
                d.run_left -= step
                if d.run_left <= 0:
                    d.drops += 1
                    d.tlat, d.tlon = self.base
                    d.state = RETURN
            elif d.state == RETURN:
                if self._fly_to(d, dt):
                    d.state = REFILL
                    d.timer = REFILL_SEC

    # --- broadcast ---

    def snapshot(self):
        """Compact payload: each drone is [lat, lon, heading, state]."""
        return {
            "type": "swarm",
            "origin": list(self.fire.origin),
            "base": list(self.base),
            "cell_m": CELL_M,
            "drones": [[round(d.lat, 5), round(d.lon, 5),
                        int(d.heading), d.state] for d in self.drones],
            "fire": self.fire.snapshot(),
            "stats": self.stats(),
        }

    def attach(self, engine):
        """Publish swarm frames through the existing telemetry subscribers."""
        async def loop():
            last = time.monotonic()
            while True:
                await asyncio.sleep(0.1)
                now = time.monotonic()
                dt, last = now - last, now
                if not self.active:
                    continue
                self.step(dt)
                self._acc += dt
                if self._acc < 0.5:      # 2 Hz to clients
                    continue
                self._acc = 0.0
                frame = self.snapshot()
                for q in list(engine.subscribers):
                    if not q.full():
                        q.put_nowait(frame)

        self._task = asyncio.create_task(loop())


swarm = FireSwarm()
