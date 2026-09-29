"""SkyOps flight logging and PDF reports.

Records every flight automatically: when a drone leaves idle a log
opens; when it lands the log is finalized to logs/<id>.json with the
route, telemetry samples and an AI-detection summary. Reports render
to PDF on demand.
"""

import hashlib
import json
import math
import time
import uuid
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas

from sim import meters_between

LOGS_DIR = Path(__file__).resolve().parent / "logs"
SAMPLE_INTERVAL = 2.0  # seconds between recorded track points

INK = colors.HexColor("#132430")
SLATE = colors.HexColor("#5b7284")
BLUE = colors.HexColor("#0f62e6")
GREEN = colors.HexColor("#148a5c")
LINE = colors.HexColor("#cfdde5")


def _nav_state() -> str:
    """Position quality when an observation was made, for the record."""
    try:
        from navquality import nav
        return nav.state
    except Exception:
        return "ok"


class FlightRecorder:
    def __init__(self) -> None:
        LOGS_DIR.mkdir(exist_ok=True)
        self.active: dict[str, dict] = {}   # drone_id -> open record
        self._last_sample: dict[str, float] = {}

    def tick(self, drones, detections: dict[str, int],
             mode: str = "search",
             statuses: dict[str, str] | None = None) -> None:
        """Call ~1x/second with current drone objects and AI counts.

        `statuses` maps a detection label to the operator's verdict
        (pending / confirmed / rejected). It is re-applied on every tick,
        because an operator usually confirms a finding some seconds after
        the system first reported it.
        """
        statuses = statuses or {}
        now = time.time()
        for d in drones:
            t = d.telemetry()
            flying = t["state"] not in ("idle", "connecting")
            rec = self.active.get(d.id)

            if flying and rec is None:
                self.active[d.id] = {
                    "id": uuid.uuid4().hex[:12],
                    "drone": t["name"],
                    "mode": mode,
                    "start": now,
                    "end": None,
                    "waypoints": t["mission"],
                    "samples": [],
                    "events": [],
                    "detections": {},
                    "_prev_counts": {},
                }
                self._last_sample[d.id] = 0.0
                rec = self.active[d.id]

            if rec is not None:
                if now - self._last_sample.get(d.id, 0) >= SAMPLE_INTERVAL:
                    self._last_sample[d.id] = now
                    rec["samples"].append({
                        "t": round(now - rec["start"], 1),
                        "lat": t["lat"], "lon": t["lon"], "alt": t["alt"],
                        "speed": t["speed"], "battery": t["battery"],
                        "state": t["state"],
                    })
                    for label, count in detections.items():
                        rec["detections"][label] = (
                            rec["detections"].get(label, 0)
                            + count * SAMPLE_INTERVAL)
                        # timeline: record when a class appears or grows
                        if count > rec["_prev_counts"].get(label, 0):
                            rec["events"].append({
                                "t": round(now - rec["start"], 1),
                                "label": label, "count": count,
                                "lat": t["lat"], "lon": t["lon"],
                                "status": statuses.get(label, "pending"),
                                "pos": _nav_state(),
                            })
                    rec["_prev_counts"] = dict(detections)

                # a verdict usually arrives after the event was logged
                for ev in rec["events"]:
                    if ev["label"] in statuses:
                        ev["status"] = statuses[ev["label"]]

                if not flying:
                    rec["end"] = now
                    self._finalize(d.id, rec)

    def _finalize(self, drone_id: str, rec: dict) -> None:
        del self.active[drone_id]
        samples = rec["samples"]
        dist = sum(
            meters_between((a["lat"], a["lon"]), (b["lat"], b["lon"]))
            for a, b in zip(samples, samples[1:]))
        rec["summary"] = {
            "duration_s": round(rec["end"] - rec["start"], 1),
            "distance_m": round(dist, 1),
            "max_alt_m": round(max((s["alt"] for s in samples), default=0), 1),
            "battery_used_pct": round(
                samples[0]["battery"] - samples[-1]["battery"], 1) if samples else 0,
            "detections": {k: round(v) for k, v in rec["detections"].items()},
        }
        del rec["detections"]
        rec.pop("_prev_counts", None)
        rec["events"] = rec["events"][:60]
        (LOGS_DIR / f"{rec['id']}.json").write_text(
            json.dumps(rec), encoding="utf-8")
        self._prune(keep=500)

    @staticmethod
    def _started(path) -> float:
        """Sortie start time from the record itself.

        File mtime is not reliable here - it has been observed to
        disagree with the recorded time by hours, which silently buried
        the newest sortie underneath older ones. The record knows when
        it started; trust that.
        """
        try:
            return float(json.loads(path.read_text(encoding="utf-8"))["start"])
        except Exception:
            return path.stat().st_mtime

    # never discard a log written within this window, whatever its
    # timestamp claims - a clock that jumps backwards must not be able to
    # delete the sortie that was just flown
    PRUNE_GRACE_S = 3600

    def _prune(self, keep: int) -> None:
        now = time.time()
        files = sorted(LOGS_DIR.glob("*.json"), key=self._started, reverse=True)
        for old in files[keep:]:
            try:
                if now - old.stat().st_mtime < self.PRUNE_GRACE_S:
                    continue          # written moments ago; keep it
            except OSError:
                continue
            old.unlink(missing_ok=True)

    # ---- queries ----

    def list_logs(self) -> list[dict]:
        out = []
        for f in sorted(LOGS_DIR.glob("*.json"),
                        key=self._started, reverse=True)[:50]:
            rec = json.loads(f.read_text(encoding="utf-8"))
            out.append({
                "id": rec["id"], "drone": rec["drone"],
                "start": rec["start"], **rec["summary"],
            })
        return out

    def get(self, log_id: str) -> dict | None:
        f = LOGS_DIR / f"{log_id}.json"
        if not f.exists() or not f.name.replace(".json", "").isalnum():
            return None
        return json.loads(f.read_text(encoding="utf-8"))


def render_pdf(rec: dict) -> bytes:
    """One-page A4 flight report."""
    buf = BytesIO()
    c = Canvas(buf, pagesize=A4)
    w, h = A4
    m = 18 * mm

    def label(x, y, text):
        c.setFont("Courier", 8)
        c.setFillColor(SLATE)
        c.drawString(x, y, text.upper())

    def value(x, y, text, size=12):
        c.setFont("Helvetica-Bold", size)
        c.setFillColor(INK)
        c.drawString(x, y, str(text))

    # header
    c.setFillColor(BLUE)
    c.rect(m, h - m - 4, 8, 14, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(INK)
    c.drawString(m + 14, h - m, "SkyOps Flight Report")
    c.setFont("Courier", 9)
    c.setFillColor(SLATE)
    started = datetime.fromtimestamp(rec["start"], tz=timezone.utc)
    c.drawRightString(w - m, h - m,
                      started.strftime("%Y-%m-%d %H:%M UTC"))
    c.setStrokeColor(LINE)
    c.line(m, h - m - 14, w - m, h - m - 14)

    # summary row
    s = rec["summary"]
    y = h - m - 40
    cols = [
        ("Aircraft", rec["drone"]),
        ("Duration", f"{s['duration_s']:.0f} s"),
        ("Distance", f"{s['distance_m']:.0f} m"),
        ("Max altitude", f"{s['max_alt_m']:.0f} m"),
        ("Battery used", f"{s['battery_used_pct']:.0f}%"),
    ]
    step = (w - 2 * m) / len(cols)
    for i, (k, v) in enumerate(cols):
        label(m + i * step, y, k)
        value(m + i * step, y - 16, v, 14)

    # route sketch
    y_top = y - 44
    box_h = 95 * mm
    c.setStrokeColor(LINE)
    c.setFillColor(colors.HexColor("#f3f7f9"))
    c.rect(m, y_top - box_h, w - 2 * m, box_h, fill=1)
    pts = [(p["lon"], p["lat"]) for p in rec["samples"]]
    if len(pts) > 1:
        lons, lats = zip(*pts)
        lo_x, hi_x = min(lons), max(lons)
        lo_y, hi_y = min(lats), max(lats)
        span_x = max(hi_x - lo_x, 1e-6)
        span_y = max(hi_y - lo_y, 1e-6)
        pad = 12 * mm
        bw, bh = w - 2 * m - 2 * pad, box_h - 2 * pad

        def to_xy(lon, lat):
            return (m + pad + (lon - lo_x) / span_x * bw,
                    y_top - box_h + pad + (lat - lo_y) / span_y * bh)

        c.setStrokeColor(BLUE)
        c.setLineWidth(1.6)
        path = c.beginPath()
        path.moveTo(*to_xy(*pts[0]))
        for p in pts[1:]:
            path.lineTo(*to_xy(*p))
        c.drawPath(path)
        for wp in rec.get("waypoints", []):
            x, yy = to_xy(wp["lon"], wp["lat"])
            c.setFillColor(GREEN)
            c.circle(x, yy, 3, fill=1, stroke=0)
        x0, y0 = to_xy(*pts[0])
        c.setFillColor(INK)
        c.circle(x0, y0, 3, fill=1, stroke=0)
    label(m + 4, y_top - 10, "flight track (blue) / waypoints (green)")

    # detections
    y2 = y_top - box_h - 22
    label(m, y2, "AI detections (object-seconds)")
    dets = s.get("detections", {})
    c.setFont("Helvetica", 11)
    c.setFillColor(INK)
    text = "  |  ".join(f"{k}: {v}" for k, v in
                        sorted(dets.items(), key=lambda kv: -kv[1])) or "none"
    c.drawString(m, y2 - 16, text)

    # footer
    c.setFont("Courier", 8)
    c.setFillColor(SLATE)
    c.drawString(m, m, f"LOG {rec['id']}  -  generated by SkyOps")
    c.showPage()
    c.save()
    return buf.getvalue()


MODE_TITLES = {
    "search": ("SEARCH & RESCUE", "Poszukiwanie osob"),
    "fire": ("WILDFIRE WATCH", "Monitoring pozaru"),
    "flood": ("FLOOD MAPPING", "Mapowanie powodzi"),
}


def render_sitrep(rec: dict) -> bytes:
    """Situation report: what a commander receives after the sortie."""
    buf = BytesIO()
    c = Canvas(buf, pagesize=A4)
    w, h = A4
    m = 18 * mm
    mode = rec.get("mode", "search")
    title_en, title_pl = MODE_TITLES.get(mode, MODE_TITLES["search"])
    s = rec["summary"]
    started = datetime.fromtimestamp(rec["start"], tz=timezone.utc)

    def label(x, y, text):
        c.setFont("Courier", 8)
        c.setFillColor(SLATE)
        c.drawString(x, y, text.upper())

    def value(x, y, text, size=12):
        c.setFont("Helvetica-Bold", size)
        c.setFillColor(INK)
        c.drawString(x, y, str(text))

    # header band
    c.setFillColor(INK)
    c.rect(0, h - 26 * mm, w, 26 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(m, h - 13 * mm, "SITUATION REPORT / RAPORT SYTUACYJNY")
    c.setFont("Courier", 9)
    c.setFillColor(colors.HexColor("#8db8ff"))
    c.drawString(m, h - 19 * mm,
                 f"SKYOPS CRISIS - {title_en} / {title_pl}")
    c.setFillColor(colors.HexColor("#b6c8d6"))
    c.drawRightString(w - m, h - 13 * mm,
                      started.strftime("%Y-%m-%d %H:%M UTC"))
    c.drawRightString(w - m, h - 19 * mm, f"SORTIE {rec['id'].upper()}")

    # key facts
    y = h - 36 * mm
    cols = [
        ("Aircraft", rec["drone"]),
        ("Mode", title_en.title()),
        ("Duration", f"{s['duration_s']:.0f} s"),
        ("Track", f"{s['distance_m']:.0f} m"),
        ("Battery used", f"{s['battery_used_pct']:.0f}%"),
    ]
    step = (w - 2 * m) / len(cols)
    for i, (k, v) in enumerate(cols):
        label(m + i * step, y, k)
        value(m + i * step, y - 14, v, 12)

    # findings summary sentence (from data, no invention)
    y2 = y - 34
    label(m, y2, "Findings / Ustalenia")
    dets = s.get("detections", {})
    c.setFont("Helvetica", 11)
    c.setFillColor(INK)
    from detection import FLOOD_LABEL
    if mode == "flood" and FLOOD_LABEL in dets:
        floods = [e["count"] for e in rec.get("events", [])
                  if e.get("label") == FLOOD_LABEL]
        peak = max(floods) if floods else dets[FLOOD_LABEL]
        conf = any(e.get("status") == "confirmed" for e in rec.get("events", [])
                   if e.get("label") == FLOOD_LABEL)
        text = (f"Flood water observed; peak measured coverage in frame {peak}%. "
                + ("Operator-confirmed." if conf
                   else "Not yet confirmed by the operator."))
    elif dets:
        ev = rec.get("events", [])
        ok = sorted({e["label"] for e in ev
                     if e.get("status") == "confirmed"})
        na = sorted({e["label"] for e in ev
                     if e.get("status", "pending") == "pending"})
        bits = []
        if ok:
            bits.append("Operator-confirmed: " + ", ".join(ok))
        if na:
            bits.append("reported by AI, not yet confirmed: " + ", ".join(na))
        text = ("; ".join(bits) + "." if bits else
                "Detections recorded; none adjudicated by the operator.")
    else:
        text = "No AI detections during this sortie."
    import textwrap
    lines = textwrap.wrap(text, 96)[:2]
    for i, ln in enumerate(lines):
        c.drawString(m, y2 - 16 - i * 14, ln)

    # road passability - the actual decision, for flood sorties
    road_lines = []
    if mode == "flood":
        try:
            from roads import network as _rn
            from detection import FLOOD_LABEL
            if _rn.loaded:
                obs = [e for e in rec.get("events", [])
                       if e.get("label") == FLOOD_LABEL]
                road_lines = _rn.impassable_summary(obs)[:5]
        except Exception:
            road_lines = []

    y_roads = y2 - 44 - (14 if len(lines) > 1 else 0)
    if road_lines:
        label(m, y_roads, "Przejezdnosc drog / Road passability")
        c.setFont("Courier", 8.5)
        yy = y_roads - 13
        for ln in road_lines:
            c.setFillColor(colors.HexColor("#c0392b")
                           if ln.startswith("NIEPRZEJEZDNA") else INK)
            c.drawString(m, yy, ln[:104])
            yy -= 11
        c.setFillColor(SLATE)
        c.setFont("Courier", 7.5)
        c.drawString(m, yy - 1,
                     "Drogi bez obserwacji sa oznaczone NIEZNANA - nie sa "
                     "raportowane jako przejezdne.")
        y2 = yy - 14

    # detection timeline
    y3 = y2 - 44 - (14 if len(lines) > 1 else 0)
    label(m, y3, "Detection timeline / Os czasu wykryc")
    _rank = {"confirmed": 0, "pending": 1, "rejected": 2}
    events = sorted(rec.get("events", []),
                    key=lambda e: _rank.get(e.get("status", "pending"), 1)
                    )[:14]
    c.setFont("Courier", 9)
    yy = y3 - 14
    if not events:
        c.setFillColor(SLATE)
        c.drawString(m, yy, "(no events)")
        yy -= 12
    _mark = {"confirmed": "[POTWIERDZONE]", "rejected": "[ODRZUCONE]  ",
             "pending": "[NIEPOTW. AI] "}
    for e in events:
        st = e.get("status", "pending")
        c.setFillColor(colors.HexColor("#148a5c") if st == "confirmed"
                       else SLATE if st == "rejected" else INK)
        line = (f"{_mark.get(st, _mark['pending'])} T+{e['t']:>6.1f}s  "
                f"{e['label']:<13} x{e['count']:<3} "
                f"@ {e['lat']:.5f}, {e['lon']:.5f}")
        c.drawString(m, yy, line)
        yy -= 12
    c.setFillColor(SLATE)
    c.setFont("Courier", 7.5)
    c.drawString(m, yy - 2,
                 "POTWIERDZONE = operator potwierdzil / operator confirmed."
                 "  NIEPOTW. AI = tylko wskazanie AI / AI only.")
    yy -= 14

    # observations made without a reliable position cannot be acted on the
    # way located ones can - the report has to say so
    bad_pos = [e for e in rec.get("events", []) if e.get("pos", "ok") != "ok"]
    if bad_pos:
        c.setFillColor(colors.HexColor("#c0392b"))
        c.setFont("Courier", 8)
        c.drawString(m, yy - 2,
                     f"UWAGA: {len(bad_pos)} obserwacji zapisano przy "
                     "niepewnej pozycji - wspolrzedne orientacyjne, "
                     "nie zamykaja drogi.")
        yy -= 13

    # route sketch (compact)
    box_h = 55 * mm
    y4 = yy - 10
    c.setStrokeColor(LINE)
    c.setFillColor(colors.HexColor("#f3f7f9"))
    c.rect(m, y4 - box_h, w - 2 * m, box_h, fill=1)
    pts = [(p["lon"], p["lat"]) for p in rec["samples"]]
    if len(pts) > 1:
        lons, lats = zip(*pts)
        lo_x, hi_x, lo_y, hi_y = min(lons), max(lons), min(lats), max(lats)
        span_x, span_y = max(hi_x - lo_x, 1e-6), max(hi_y - lo_y, 1e-6)
        pad = 8 * mm
        bw, bh = w - 2 * m - 2 * pad, box_h - 2 * pad

        def to_xy(lon, lat):
            return (m + pad + (lon - lo_x) / span_x * bw,
                    y4 - box_h + pad + (lat - lo_y) / span_y * bh)

        c.setStrokeColor(BLUE)
        c.setLineWidth(1.4)
        path = c.beginPath()
        path.moveTo(*to_xy(*pts[0]))
        for p in pts[1:]:
            path.lineTo(*to_xy(*p))
        c.drawPath(path)
        c.setFillColor(colors.HexColor("#dc2626"))
        for e in events:
            x, ey = to_xy(e["lon"], e["lat"])
            c.circle(x, ey, 2.6, fill=1, stroke=0)
    label(m + 4, y4 - 10, "track (blue) / detection events (red)")

    # evidence integrity footer
    digest = hashlib.sha256(
        json.dumps(rec, sort_keys=True).encode()).hexdigest()
    c.setFont("Courier", 7.5)
    c.setFillColor(SLATE)
    c.drawString(m, m + 10,
                 f"EVIDENCE INTEGRITY SHA-256: {digest}")
    c.drawString(m, m,
                 "Generated automatically by SkyOps Crisis from the "
                 "flight log. Detections are AI-assisted and require "
                 "operator confirmation.")
    c.showPage()
    c.save()
    return buf.getvalue()


recorder = FlightRecorder()
