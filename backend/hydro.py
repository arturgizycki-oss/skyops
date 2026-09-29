"""Official Polish river gauges (IMGW-PIB) as the trigger for a sortie.

Why this sits in a drone platform:

A river gauge is authoritative but it is a *point*. IMGW tells you the
Wislok is 40 cm over its warning level at one bridge. It cannot tell you
which road three kilometres downstream is still passable - that is the
question the duty officer actually has to answer.

So the gauge and the drone carry different kinds of uncertainty, and
they correct each other:

  gauge      certain about level, uncertain about extent  (spatial)
  drone + AI certain about extent, uncertain about meaning (perceptual)
  operator   adjudicates both, and owns the decision

The gauge crossing a threshold is what starts the process: it is the
"operational need" in the organisers' own flow. The drone answers the
question the gauge raised.

Source: https://danepubliczne.imgw.pl/api/data/hydro - public, no key.
"""

import json
import logging
import threading
import time
import urllib.request

log = logging.getLogger("skyops.hydro")

HYDRO_URL = "https://danepubliczne.imgw.pl/api/data/hydro"
REFRESH_S = 600            # IMGW publishes roughly hourly; 10 min is ample
TIMEOUT_S = 20

# Podkarpackie and the area around Rzeszow-Jasionka
DEFAULT_BBOX = (49.0, 21.0, 50.9, 23.2)   # lat_min, lon_min, lat_max, lon_max

NORMA, OSTRZEGAWCZY, ALARMOWY = "norma", "ostrzegawczy", "alarmowy"


def _num(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def classify(level, warn, alarm) -> str:
    """Official three-state classification used by Polish crisis services."""
    if level is None or alarm is None or warn is None:
        return "brak progow"
    if level >= alarm:
        return ALARMOWY
    if level >= warn:
        return OSTRZEGAWCZY
    return NORMA


class HydroFeed:
    """Cached view of the national gauge network, filtered to a region."""

    def __init__(self, bbox=DEFAULT_BBOX):
        self.bbox = bbox
        self.stations: list[dict] = []
        self.fetched_at: float = 0.0
        self.error: str | None = None
        self._lock = threading.Lock()

    def _in_bbox(self, lat, lon) -> bool:
        la0, lo0, la1, lo1 = self.bbox
        return lat is not None and lon is not None and \
            la0 <= lat <= la1 and lo0 <= lon <= lo1

    def refresh(self, force: bool = False) -> bool:
        if not force and time.time() - self.fetched_at < REFRESH_S:
            return True
        try:
            raw = json.load(urllib.request.urlopen(HYDRO_URL, timeout=TIMEOUT_S))
        except Exception as exc:                       # offline at the venue
            self.error = str(exc)
            log.warning("IMGW hydro unavailable: %s", exc)
            return False

        out = []
        for s in raw:
            try:
                lat, lon = float(s["lat"]), float(s["lon"])
            except (TypeError, ValueError, KeyError):
                continue
            if not self._in_bbox(lat, lon):
                continue
            level = _num(s.get("stan_wody"))
            warn = _num(s.get("stan_ostrzegawczy"))
            alarm = _num(s.get("stan_alarmowy"))
            out.append({
                "id": s.get("id_stacji"),
                "name": s.get("stacja"),
                "river": s.get("rzeka"),
                "lat": lat, "lon": lon,
                "level_cm": level,
                "warn_cm": warn,
                "alarm_cm": alarm,
                "status": classify(level, warn, alarm),
                # how far below the alarm threshold, in cm - what an officer reads
                "margin_cm": (alarm - level) if (alarm and level is not None) else None,
                "measured_at": s.get("stan_wody_data_pomiaru"),
            })
        with self._lock:
            self.stations = sorted(
                out, key=lambda x: (x["margin_cm"] is None, x["margin_cm"]))
            self.fetched_at = time.time()
            self.error = None
        log.info("IMGW hydro: %d stations in region", len(out))
        return True

    def picture(self) -> dict:
        with self._lock:
            counts: dict[str, int] = {}
            for s in self.stations:
                counts[s["status"]] = counts.get(s["status"], 0) + 1
            return {
                "stations": self.stations,
                "counts": counts,
                "fetched_at": self.fetched_at,
                "age_s": round(time.time() - self.fetched_at) if self.fetched_at else None,
                "error": self.error,
                "source": "IMGW-PIB (dane publiczne)",
            }

    def simulate(self, station_id: str | None, over_alarm_cm: int = 25) -> dict | None:
        """Push one gauge above its alarm level, for demonstration only.

        Poland is not flooding today, so a live feed shows nothing but
        `norma` and the trigger never fires. This raises a single station
        so the process can be shown end to end. Every station touched
        this way is flagged `simulated`, the flag travels with the data
        into the API and the UI, and a refresh from IMGW wipes it.
        """
        with self._lock:
            target = None
            for st in self.stations:
                if station_id in (None, st["id"]) or station_id == st["name"]:
                    target = st
                    break
            if not target or not target["alarm_cm"]:
                return None
            target["level_cm"] = target["alarm_cm"] + int(over_alarm_cm)
            target["margin_cm"] = -int(over_alarm_cm)
            target["status"] = ALARMOWY
            target["simulated"] = True
            self.stations.sort(
                key=lambda x: (x["margin_cm"] is None, x["margin_cm"]))
            return dict(target)

    def clear_simulation(self) -> None:
        self.fetched_at = 0.0          # force a clean pull from IMGW
        self.refresh(force=True)

    def triggered(self) -> list[dict]:
        """Gauges at or above the warning level - a reason to fly."""
        with self._lock:
            return [s for s in self.stations
                    if s["status"] in (OSTRZEGAWCZY, ALARMOWY)]


hydro = HydroFeed()
