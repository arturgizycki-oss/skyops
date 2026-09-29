"""Turn an external dataset into a SkyOps Situation Report.

The point of the platform is that aerial data becomes a document a
commander can act on. That should not only work for our own flights: if
someone hands us observations from their drone, their exercise or their
archive, the same report should come out the other end.

A Situation Report renders from one plain record. This module builds a
valid record from generic inputs, writes it to the log directory, and it
then appears in the normal log list and report endpoints - no special
case anywhere else in the platform.

Usage from a format-specific loader:

    from dataimport import build_record, save_record
    rec = build_record(
        name="Powodz - Wislok",
        mode="flood",
        track=[{"lat": .., "lon": .., "alt": .., "t": ..}, ...],
        observations=[{"lat": .., "lon": .., "label": "zalanie drogi",
                       "count": 1, "conf": 0.88, "t": 12.0}, ...],
    )
    save_record(rec)
"""

import json
import time
import uuid
from pathlib import Path

from sim import meters_between

LOGS_DIR = Path(__file__).resolve().parent / "logs"


def build_record(name: str,
                 observations: list[dict],
                 track: list[dict] | None = None,
                 mode: str = "search",
                 started: float | None = None,
                 source: str | None = None) -> dict:
    """Build a Situation Report record from external data.

    `observations` is the only required input: each needs at least lat,
    lon and label. `count`, `conf`, `t` and `status` are optional.

    `track` is the flight path. If it is missing, the observation points
    are used instead, so a dataset of findings with no recorded path
    still produces a usable report and route sketch.
    """
    if not observations:
        raise ValueError("need at least one observation")

    started = started if started is not None else time.time()

    # fall back to the observation points when no path was supplied
    pts = track or [{"lat": o["lat"], "lon": o["lon"]} for o in observations]
    samples = []
    for i, p in enumerate(pts):
        samples.append({
            "t": round(float(p.get("t", i)), 1),
            "lat": float(p["lat"]),
            "lon": float(p["lon"]),
            "alt": round(float(p.get("alt", 0.0)), 1),
            "speed": round(float(p.get("speed", 0.0)), 1),
            "battery": round(float(p.get("battery", 100.0)), 1),
        })

    events = []
    for i, o in enumerate(observations):
        ev = {
            "t": round(float(o.get("t", i)), 1),
            "label": str(o["label"]),
            "count": int(o.get("count", 1)),
            "lat": float(o["lat"]),
            "lon": float(o["lon"]),
            # imported findings are unverified until a person says otherwise
            "status": o.get("status", "pending"),
        }
        if o.get("conf") is not None:
            ev["conf"] = round(float(o["conf"]), 3)
        events.append(ev)
    events.sort(key=lambda e: e["t"])

    dist = sum(meters_between((a["lat"], a["lon"]), (b["lat"], b["lon"]))
               for a, b in zip(samples, samples[1:]))

    detections: dict[str, int] = {}
    for e in events:
        detections[e["label"]] = detections.get(e["label"], 0) + e["count"]

    duration = samples[-1]["t"] - samples[0]["t"] if len(samples) > 1 else 0.0

    rec = {
        "id": uuid.uuid4().hex[:12],
        "drone": name,
        "mode": mode,
        "start": started,
        "end": started + max(duration, 1.0),
        "waypoints": [],
        "samples": samples,
        "events": events[:60],
        "summary": {
            "duration_s": round(duration, 1),
            "distance_m": round(dist, 1),
            "max_alt_m": round(max(s["alt"] for s in samples), 1),
            "battery_used_pct": round(
                samples[0]["battery"] - samples[-1]["battery"], 1),
            "detections": detections,
        },
    }
    if source:
        rec["source"] = source
    return rec


def save_record(rec: dict) -> Path:
    """Write the record so it shows up in the normal log and report views."""
    LOGS_DIR.mkdir(exist_ok=True)
    path = LOGS_DIR / f"{rec['id']}.json"
    path.write_text(json.dumps(rec), encoding="utf-8")
    return path


# --- generic loaders -------------------------------------------------

def from_csv(path: str, name: str, mode: str = "search",
             lat_col: str = "lat", lon_col: str = "lon",
             label_col: str = "label", **kw) -> dict:
    """CSV with a coordinate pair and a label per row."""
    import csv
    obs = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for i, row in enumerate(csv.DictReader(f)):
            if not row.get(lat_col) or not row.get(lon_col):
                continue
            obs.append({
                "lat": float(row[lat_col]),
                "lon": float(row[lon_col]),
                "label": row.get(label_col) or "obserwacja",
                "count": int(float(row.get("count", 1) or 1)),
                "conf": float(row["conf"]) if row.get("conf") else None,
                "t": float(row["t"]) if row.get("t") else i,
            })
    return build_record(name, obs, mode=mode, source=Path(path).name, **kw)


def from_geojson(path: str, name: str, mode: str = "flood",
                 label_prop: str = "label", **kw) -> dict:
    """GeoJSON FeatureCollection of points, or anything with coordinates."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    obs = []

    def first_point(geom):
        c = geom.get("coordinates")
        while isinstance(c, list) and c and isinstance(c[0], list):
            c = c[0]
        return c if isinstance(c, list) and len(c) >= 2 else None

    for i, feat in enumerate(data.get("features", [])):
        pt = first_point(feat.get("geometry") or {})
        if not pt:
            continue
        props = feat.get("properties") or {}
        obs.append({
            "lon": float(pt[0]), "lat": float(pt[1]),
            "label": str(props.get(label_prop) or "obserwacja"),
            "count": int(props.get("count", 1)),
            "conf": props.get("conf"),
            "t": float(props.get("t", i)),
        })
    return build_record(name, obs, mode=mode, source=Path(path).name, **kw)
