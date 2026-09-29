# Connecting a real drone to SkyOps

Honest starting point: the connector is written and complete - it
implements every command the platform uses - but it has **never been
run against an actual aircraft**. Everything below is the correct
procedure; none of it is yet proven in the air. Say that plainly to
anyone who asks.

---

## 1. What the platform speaks

SkyOps talks **MAVLink**, through the MAVSDK library. MAVLink is the
open standard used by PX4 and ArduPilot - the two flight-control
systems behind most professional, industrial and DIY drones.

You point the platform at an aircraft with one environment variable:

```
SKYOPS_MAVLINK_URL=<address>  uvicorn main:app --port 8000
```

The aircraft then appears in the fleet as **REAL-01**, next to the
simulated ones, and the same buttons command it: plan a mission,
hold, resume, return home.

---

## 2. Which drones work - ask this FIRST

This is the question that decides everything, and it is the one to ask
any mentor offering hardware:

> **"Does it run PX4 or ArduPilot?"**

| Works | Does not work |
|---|---|
| Pixhawk / Cube / Holybro flight controllers | **DJI** (Mavic, Mini, Air, Matrice) |
| Anything running PX4 | Autel |
| Anything running ArduPilot | Most Parrot |
| Most industrial and DIY platforms | Any drone with a closed proprietary link |

**DJI is the important one.** DJI drones are the most common ones
anybody will have, and they do *not* speak MAVLink - they use DJI's own
closed SDK. If a mentor offers a Mavic, our connector cannot fly it,
and you should say so rather than fail in front of them. Supporting DJI
would be a separate piece of work against a different SDK.

---

## 3. The four ways to connect, easiest first

### A. USB cable - best for a demonstration
Plug the flight controller straight into the laptop with USB. No radio,
no range, but it works on a table in five minutes and proves the whole
chain.

```
# Windows
SKYOPS_MAVLINK_URL=serial:///COM3:57600  uvicorn main:app --port 8000

# Linux / Mac
SKYOPS_MAVLINK_URL=serial:///dev/ttyACM0:57600  uvicorn main:app --port 8000
```

Find the port in Windows Device Manager under "Ports (COM & LPT)".
Common baud rates: 57600 for a radio, 115200 over USB.

### B. Telemetry radio - the normal way to fly
A SiK radio pair (433 MHz in Europe, 915 MHz in the US): one module on
the aircraft, one USB dongle on the laptop. Range roughly 1-2 km. The
laptop sees it as another serial port, so the command is identical to A.

### C. WiFi / UDP - if the drone has a companion computer
Some aircraft broadcast MAVLink over the network.

```
SKYOPS_MAVLINK_URL=udp://:14550  uvicorn main:app --port 8000
```

### D. PX4 SITL - no hardware at all
The PX4 software simulator behaves exactly like a real aircraft over
MAVLink. This is how you prove the connector works before touching
anything that flies.

```
SKYOPS_MAVLINK_URL=udp://:14540  uvicorn main:app --port 8000
```

SITL needs Linux, so on Windows it needs WSL2 or Docker. **Neither is
installed on our machine** - that is why this has never been tested.
Installing WSL2 takes about 20 minutes plus a reboot.

---

## 4. The realistic recommendation

**For proving it works:** PX4 SITL. No hardware, no risk, no flying
licence, and it exercises exactly the same code path as a real drone.
This is the sensible first step and we should do it.

**For a demonstration in a room:** USB cable to a Pixhawk. Five minutes,
nothing flies, and you can show real telemetry arriving on the map.

**For actual flight:** telemetry radio pair. This is what every PX4
operator uses.

---

## 5. If a mentor at the hackathon has hardware

This would be the single best outcome of the 24 hours - far better than
any feature. Ask, in this order:

1. "Does it run PX4 or ArduPilot?" (If DJI - thank them, move on.)
2. "Can we connect it by USB, just on the table? Nothing needs to fly."
3. If yes: find the COM port, set `SKYOPS_MAVLINK_URL`, restart.

If telemetry appears on the map, a two-person team that arrived with a
simulator has left having driven real hardware. That is a completely
different story to tell the jury, and it costs nothing but asking.

**Safety:** never arm or fly indoors, and never move propellers with a
battery connected. Everything above works with props removed - position,
battery and mode telemetry all flow without the aircraft ever spinning up.
