"""Search-grid generator prototype (hackathon SEARCH mode).

Given a polygon search area, produce lawnmower-pattern waypoints with a
given track spacing, and split the passes between N drones. Pure
geometry - proven here so the hackathon build is just wiring it to the
API and map UI.

Run:  python gridgen.py
"""

import math

M_PER_DEG_LAT = 111_320.0


def _point_in_polygon(lat, lon, poly):
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


def search_grid(polygon, spacing_m=60.0, n_drones=1):
    """polygon: [(lat, lon), ...]. Returns list of per-drone waypoint lists.

    Lawnmower: horizontal passes south->north, alternating direction,
    clipped to the polygon by sampling along each pass.
    """
    lats = [p[0] for p in polygon]
    lons = [p[1] for p in polygon]
    lat0 = min(lats)
    m_per_deg_lon = M_PER_DEG_LAT * math.cos(math.radians(sum(lats) / len(lats)))
    dlat = spacing_m / M_PER_DEG_LAT
    sample_dlon = 10.0 / m_per_deg_lon  # sample every 10 m along a pass

    passes = []
    lat = lat0 + dlat / 2
    while lat < max(lats):
        # find polygon coverage on this latitude by sampling
        lon = min(lons)
        run = []
        while lon <= max(lons):
            if _point_in_polygon(lat, lon, polygon):
                run.append(lon)
            lon += sample_dlon
        if run:
            passes.append((lat, run[0], run[-1]))
        lat += dlat

    # serpentine: alternate pass direction, then chunk between drones
    waypoints = []
    for i, (plat, lo, hi) in enumerate(passes):
        a, b = (lo, hi) if i % 2 == 0 else (hi, lo)
        waypoints.append((plat, a))
        waypoints.append((plat, b))

    if n_drones <= 1:
        return [waypoints]
    chunk = math.ceil(len(waypoints) / n_drones)
    return [waypoints[i:i + chunk] for i in range(0, len(waypoints), chunk)]


if __name__ == "__main__":
    # irregular pentagon over Jasionka, ~1.2 x 0.9 km
    area = [
        (50.105, 22.015), (50.107, 22.030), (50.113, 22.032),
        (50.116, 22.020), (50.110, 22.012),
    ]
    for n in (1, 3):
        plans = search_grid(area, spacing_m=80, n_drones=n)
        total = sum(len(p) for p in plans)
        print(f"{n} drone(s): {len(plans)} route(s), {total} waypoints, "
              f"per-route {[len(p) for p in plans]}")
    plan = search_grid(area, spacing_m=80)[0]
    # sanity: every waypoint inside or on the sampled polygon rows
    inside = sum(_point_in_polygon(la, lo, area) for la, lo in plan)
    print(f"waypoints inside polygon: {inside}/{len(plan)}")
    # route length estimate
    dist = 0.0
    for (a_lat, a_lon), (b_lat, b_lon) in zip(plan, plan[1:]):
        dy = (b_lat - a_lat) * M_PER_DEG_LAT
        dx = (b_lon - a_lon) * M_PER_DEG_LAT * math.cos(math.radians(a_lat))
        dist += math.hypot(dx, dy)
    print(f"single-drone route length: {dist/1000:.1f} km "
          f"(~{dist/12/60:.0f} min at 12 m/s)")
