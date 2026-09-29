"""SkyOps airspace awareness (simulated traffic).

Simulates the surrounding-traffic picture a UTM/U-space feed would
provide: a manned light aircraft on ADS-B, a third-party UAS
broadcasting Remote ID, and an occasional non-cooperative drone.
Conflicts are flagged when traffic comes near our flying aircraft.
All simulated - the real feed plugs into the same shape later.
"""

import math
import random
import time

from sim import HOME_BASE, meters_between

CONFLICT_RADIUS_M = 300.0


class Traffic:
    def __init__(self, tid: str, callsign: str, kind: str,
                 lat: float, lon: float, alt: float,
                 speed: float, heading: float) -> None:
        self.id = tid
        self.callsign = callsign
        self.kind = kind          # adsb | rid | unknown
        self.lat, self.lon = lat, lon
        self.alt = alt
        self.speed = speed        # m/s
        self.heading = heading    # deg
        self.expires: float | None = None

    def step(self, dt: float) -> None:
        dist = self.speed * dt
        dlat = dist * math.cos(math.radians(self.heading)) / 111_320.0
        dlon = dist * math.sin(math.radians(self.heading)) / (
            111_320.0 * math.cos(math.radians(self.lat)))
        self.lat += dlat
        self.lon += dlon

    def as_dict(self) -> dict:
        return {
            "id": self.id, "callsign": self.callsign, "kind": self.kind,
            "lat": round(self.lat, 7), "lon": round(self.lon, 7),
            "alt": round(self.alt), "speed": round(self.speed, 1),
            "heading": round(self.heading, 1),
        }


class AirspaceSim:
    def __init__(self) -> None:
        self.traffic: dict[str, Traffic] = {}
        self._next_unknown = time.time() + random.uniform(40, 90)
        self._spawn_adsb()
        self._spawn_rid()

    def _spawn_adsb(self) -> None:
        heading = random.choice([80.0, 100.0, 260.0, 280.0])
        south = heading < 180
        self.traffic["adsb1"] = Traffic(
            "adsb1", "SP-KYR", "adsb",
            HOME_BASE[0] + random.uniform(-0.004, 0.008),
            HOME_BASE[1] + (-0.05 if south else 0.05),
            random.uniform(300, 500), 45.0, heading)

    def _spawn_rid(self) -> None:
        self.traffic["rid1"] = Traffic(
            "rid1", "RID-4F2A", "rid",
            HOME_BASE[0] + 0.006, HOME_BASE[1] + 0.010,
            80.0, 6.0, 0.0)

    def step(self, dt: float, drones) -> dict:
        now = time.time()

        # circle the RID drone around its area
        rid = self.traffic.get("rid1")
        if rid:
            rid.heading = (rid.heading + 18.0 * dt) % 360

        for t in list(self.traffic.values()):
            t.step(dt)
            gone = t.expires and now > t.expires
            far = meters_between(HOME_BASE, (t.lat, t.lon)) > 6000
            if gone or far:
                del self.traffic[t.id]

        if "adsb1" not in self.traffic:
            self._spawn_adsb()
        if "rid1" not in self.traffic:
            self._spawn_rid()
        if now >= self._next_unknown:
            self._next_unknown = now + random.uniform(120, 240)
            u = Traffic(
                f"unk{int(now)}", "UNKNOWN", "unknown",
                HOME_BASE[0] + random.uniform(-0.008, 0.008),
                HOME_BASE[1] + random.uniform(-0.012, 0.012),
                random.uniform(40, 120), 8.0, random.uniform(0, 360))
            u.expires = now + 60
            self.traffic[u.id] = u

        conflicts = []
        for d in drones:
            td = d.telemetry()
            if td["state"] in ("idle", "connecting"):
                continue
            for t in self.traffic.values():
                dist = meters_between((td["lat"], td["lon"]), (t.lat, t.lon))
                if dist < CONFLICT_RADIUS_M:
                    conflicts.append({
                        "drone": td["name"], "traffic": t.callsign,
                        "kind": t.kind, "dist_m": round(dist),
                    })

        return {
            "aircraft": [t.as_dict() for t in self.traffic.values()],
            "conflicts": conflicts,
        }


airspace = AirspaceSim()
