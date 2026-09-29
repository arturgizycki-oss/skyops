"""SkyOps geofencing - no-fly zones.

Zones are polygons stored in zones.json. Enforcement is two-layer:
mission waypoints inside a zone are rejected at planning time, and a
drone that strays into a zone mid-flight is sent home automatically.
"""

import json
import uuid
from pathlib import Path

ZONES_FILE = Path(__file__).resolve().parent / "zones.json"


def _point_in_polygon(lat: float, lon: float, points: list[dict]) -> bool:
    """Ray casting; points are [{lat, lon}, ...]."""
    inside = False
    n = len(points)
    j = n - 1
    for i in range(n):
        yi, xi = points[i]["lat"], points[i]["lon"]
        yj, xj = points[j]["lat"], points[j]["lon"]
        if ((xi > lon) != (xj > lon)) and (
                lat < (yj - yi) * (lon - xi) / (xj - xi + 1e-12) + yi):
            inside = not inside
        j = i
    return inside


class GeofenceStore:
    def __init__(self) -> None:
        self.zones: list[dict] = []
        if ZONES_FILE.exists():
            try:
                self.zones = json.loads(ZONES_FILE.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                self.zones = []

    def _save(self) -> None:
        ZONES_FILE.write_text(json.dumps(self.zones), encoding="utf-8")

    def add(self, name: str, points: list[dict]) -> dict:
        zone = {"id": uuid.uuid4().hex[:8], "name": name, "points": points}
        self.zones.append(zone)
        self._save()
        return zone

    def remove(self, zone_id: str) -> bool:
        before = len(self.zones)
        self.zones = [z for z in self.zones if z["id"] != zone_id]
        if len(self.zones) != before:
            self._save()
            return True
        return False

    def violating_zone(self, lat: float, lon: float) -> dict | None:
        for z in self.zones:
            if len(z["points"]) >= 3 and _point_in_polygon(lat, lon, z["points"]):
                return z
        return None


geofences = GeofenceStore()
