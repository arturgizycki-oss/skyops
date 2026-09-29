"""Which roads are still passable - turning a measurement into a decision.

The organisers' brief names "road accessibility checks" as a thing a
decision-maker needs. A duty officer does not act on "60% water
coverage"; he acts on "droga wojewodzka 878 is impassable between these
two points, so send the ambulance round".

This module does that translation, and it is deliberate about what it
does NOT know:

  nieprzejezdna  a confirmed flood observation sits on this segment
  podejrzana     an observation suggests water, nobody has confirmed it
  przejezdna     a drone looked here and saw little or no water
  nieznana       nobody has looked - most of the network, most of the time

That last state is the important one. A map that silently shows every
unchecked road as clear is worse than no map, because it invites a
commander to route an ambulance down a road nobody has seen. We say
"nieznana" instead, and say it loudly.

Road geometry: OpenStreetMap via Overpass, cached to disk so the whole
thing works with the network unplugged.
"""

import json
import math
import pathlib

from sim import EARTH_M_PER_DEG_LAT

CACHE = pathlib.Path(__file__).resolve().parent / "roads_jasionka.json"

# how close an observation must be to a road to say anything about it
NEAR_M = 70.0
# flood coverage at or above this is treated as "this is under water"
FLOODED_PCT = 45.0
# below this, the drone looked and the road appears clear
CLEAR_PCT = 15.0

IMPASSABLE, SUSPECT, PASSABLE, UNKNOWN = (
    "nieprzejezdna", "podejrzana", "przejezdna", "nieznana")


def _seg_distance_m(plat, plon, alat, alon, blat, blon) -> float:
    """Metres from point P to segment AB, in a local flat projection."""
    kx = EARTH_M_PER_DEG_LAT * math.cos(math.radians(plat))
    ky = EARTH_M_PER_DEG_LAT
    px, py = plon * kx, plat * ky
    ax, ay = alon * kx, alat * ky
    bx, by = blon * kx, blat * ky
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


class RoadNetwork:
    def __init__(self, path: pathlib.Path = CACHE):
        self.roads: list[dict] = []
        self.source = "OpenStreetMap"
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            self.roads = data.get("roads", [])
            self.source = data.get("source", self.source)

    @property
    def loaded(self) -> bool:
        return bool(self.roads)

    def assess(self, observations: list[dict]) -> dict:
        """Classify each road against flood observations.

        `observations` need lat, lon, a coverage percentage in `count`,
        and optionally a `status` of confirmed / rejected / pending.
        """
        obs = [o for o in observations if o.get("status") != "rejected"]
        out = []
        counts = {IMPASSABLE: 0, SUSPECT: 0, PASSABLE: 0, UNKNOWN: 0}

        for r in self.roads:
            pts = r["pts"]
            verdict, worst, hit = UNKNOWN, None, None

            for o in obs:
                olat, olon = o["lat"], o["lon"]
                near = any(
                    _seg_distance_m(olat, olon, a[0], a[1], b[0], b[1]) <= NEAR_M
                    for a, b in zip(pts, pts[1:]))
                if not near:
                    continue
                pct = float(o.get("count", 0))
                confirmed = o.get("status") == "confirmed"
                if pct >= FLOODED_PCT:
                    cand = IMPASSABLE if confirmed else SUSPECT
                elif pct <= CLEAR_PCT:
                    cand = PASSABLE
                else:
                    cand = SUSPECT
                # worst verdict wins: never downgrade a hazard
                rank = {IMPASSABLE: 0, SUSPECT: 1, PASSABLE: 2, UNKNOWN: 3}
                if rank[cand] < rank[verdict]:
                    verdict, worst, hit = cand, pct, o

            counts[verdict] += 1
            if verdict != UNKNOWN:
                out.append({
                    "id": r["id"],
                    "name": r.get("ref") or r.get("name"),
                    "class": r.get("class"),
                    "status": verdict,
                    "coverage_pct": worst,
                    "at": [hit["lat"], hit["lon"]] if hit else None,
                    "pts": pts,
                })

        return {
            "assessed": out,
            "counts": counts,
            "total_roads": len(self.roads),
            "source": self.source,
            "params": {"near_m": NEAR_M, "flooded_pct": FLOODED_PCT,
                       "clear_pct": CLEAR_PCT},
        }

    def impassable_summary(self, observations: list[dict]) -> list[str]:
        """Lines for the Situation Report - what a dispatcher reads.

        OpenStreetMap splits one road into many way segments, so the raw
        assessment repeats the same road number. A dispatcher wants one
        line per road: how many stretches are affected, and the worst of
        them, with a position to send somebody to.
        """
        a = self.assess(observations)
        byroad: dict[tuple, dict] = {}
        for r in a["assessed"]:
            if r["status"] not in (IMPASSABLE, SUSPECT):
                continue
            key = (r["name"] or f"droga {r['class']}", r["status"])
            g = byroad.setdefault(key, {"n": 0, "pct": 0.0, "at": None})
            g["n"] += 1
            if (r["coverage_pct"] or 0) > g["pct"]:
                g["pct"] = r["coverage_pct"] or 0
                g["at"] = r["at"]

        order = {IMPASSABLE: 0, SUSPECT: 1}
        lines = []
        for (name, status), g in sorted(
                byroad.items(), key=lambda kv: (order[kv[0][1]], -kv[1]["pct"])):
            mark = "NIEPRZEJEZDNA" if status == IMPASSABLE else "PODEJRZANA  "
            span = f"{g['n']} odc." if g["n"] > 1 else "1 odc."
            at = g["at"]
            lines.append(f"{mark} {name[:22]:<22} {span:>7}  max {g['pct']:.0f}%"
                         + (f" @ {at[0]:.5f}, {at[1]:.5f}" if at else ""))
        return lines


network = RoadNetwork()
