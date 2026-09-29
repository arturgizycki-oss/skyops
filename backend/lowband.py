"""Pack a sortie's findings small enough to survive losing every mast.

The platform's argument is that we do not move footage, we move the
answer. That has a practical consequence worth proving rather than
asserting: an answer is small.

Video cannot cross a LoRa link at 0.3-22 kbps. A confirmed finding with
coordinates is a few dozen bytes, so it can - along with anything else
narrow and slow, a satellite messenger, SMS, or a voice reading it out.

Format is deliberately plain text so an operator can read it off a
screen and re-key it by hand if the radio dies too:

    SKYOPS|cb62|1432
    R|869|N|71|50.1171|22.0286
    R|res|S|62|50.1160|22.0217
    G|Gorlice|A|485

    R  road       N nieprzejezdna / S podejrzana / P przejezdna
    G  gauge      A alarm / O ostrzegawczy
"""

from roads import IMPASSABLE, SUSPECT, PASSABLE

_ROAD_CODE = {IMPASSABLE: "N", SUSPECT: "S", PASSABLE: "P"}


def _short(name: str, n: int = 8) -> str:
    """Road numbers survive intact; long street names get truncated."""
    if not name:
        return "?"
    name = name.replace("droga ", "")
    return name[:n]


def pack(rec: dict, roads: dict | None = None,
         gauges: list[dict] | None = None) -> str:
    """Build the smallest message that still supports a decision."""
    import time
    t = time.strftime("%H%M", time.localtime(rec.get("start", 0)))
    lines = [f"SKYOPS|{rec.get('id', '?')[:4]}|{t}"]

    seen = set()
    for r in (roads or {}).get("assessed", []):
        code = _ROAD_CODE.get(r.get("status"))
        if code is None or code == "P":
            continue                      # only hazards are worth the airtime
        key = (_short(r.get("name") or r.get("class")), code)
        if key in seen:
            continue                      # one line per road, not per segment
        seen.add(key)
        at = r.get("at") or [0, 0]
        lines.append(f"R|{key[0]}|{code}|{r.get('coverage_pct') or 0:.0f}"
                     f"|{at[0]:.4f}|{at[1]:.4f}")

    for g in (gauges or []):
        if g.get("status") == "alarmowy":
            lines.append(f"G|{_short(g.get('name'), 8)}|A|{g.get('level_cm')}")
        elif g.get("status") == "ostrzegawczy":
            lines.append(f"G|{_short(g.get('name'), 8)}|O|{g.get('level_cm')}")

    if len(lines) == 1:
        lines.append("OK|brak zagrozen")
    return "\n".join(lines)


def report(rec: dict, roads=None, gauges=None) -> dict:
    msg = pack(rec, roads, gauges)
    size = len(msg.encode("utf-8"))
    # slowest LoRa setting, EU 868 MHz, 1% duty cycle: ~1.5 s airtime per
    # ~50 byte frame, so ~24 frames an hour at worst-case range
    frames = max(1, -(-size // 50))
    return {
        "message": msg,
        "bytes": size,
        "lines": len(msg.splitlines()),
        "lora_frames": frames,
        "lora_note": ("Przy najwolniejszym ustawieniu LoRa 868 MHz i limicie "
                      "1% czasu nadawania miesci sie okolo 24 ramek na "
                      "godzine. Wideo nie przejdzie nigdy."),
    }
