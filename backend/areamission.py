"""Objective-based mission generation: draw an area, get a fleet plan.

The operator draws a polygon; the platform computes serpentine
(lawnmower) coverage passes and splits them between available drones.
Geometry proven in skyops/hackathon/gridgen.py.
"""

import math

from geofence import geofences
from sim import Waypoint

M_PER_DEG_LAT = 111_320.0


def _point_in_polygon(lat: float, lon: float, poly: list[tuple[float, float]]) -> bool:
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        yi, xi = poly[i]
        yj, xj = poly[j]
        if ((xi > lon) != (xj > lon)) and (
                lat < (yj - yi) * (lon - xi) / (xj - xi + 1e-12) + yi):
            inside = not inside
        j = i
    return inside


def area_routes(polygon: list[tuple[float, float]], spacing_m: float,
                n_routes: int, alt: float = 50.0) -> list[list[Waypoint]]:
    """Serpentine coverage of `polygon`, split into `n_routes` chunks.

    Waypoints inside no-fly zones are dropped (the fleet skips over them
    on the connecting leg).
    """
    lats = [p[0] for p in polygon]
    lons = [p[1] for p in polygon]
    mean_lat = sum(lats) / len(lats)
    m_per_deg_lon = M_PER_DEG_LAT * math.cos(math.radians(mean_lat))
    dlat = spacing_m / M_PER_DEG_LAT
    sample_dlon = 10.0 / m_per_deg_lon

    passes = []
    lat = min(lats) + dlat / 2
    while lat < max(lats):
        lon, run = min(lons), []
        while lon <= max(lons):
            if _point_in_polygon(lat, lon, polygon):
                run.append(lon)
            lon += sample_dlon
        if run:
            passes.append((lat, run[0], run[-1]))
        lat += dlat

    waypoints: list[Waypoint] = []
    for i, (plat, lo, hi) in enumerate(passes):
        a, b = (lo, hi) if i % 2 == 0 else (hi, lo)
        for wlon in (a, b):
            if not geofences.violating_zone(plat, wlon):
                waypoints.append(Waypoint(plat, wlon, alt))

    if not waypoints:
        return []
    n_routes = max(1, min(n_routes, len(waypoints) // 2 or 1))
    chunk = math.ceil(len(waypoints) / n_routes)
    return [waypoints[i:i + chunk] for i in range(0, len(waypoints), chunk)]
