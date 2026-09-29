# SkyOps - what it is and how it works

For Artur, and for anyone who asks you a technical question at the
summit. Read this once; keep `operator-guide.md` beside you when you
actually drive the platform.

Live at **https://getskyops.com** - landing page at the root, the
working platform at `/app`, a read-only view for guests at `/share`.

---

## 1. In one paragraph

SkyOps is a ground control platform for drone fleets in crisis
operations. One operator, one map, a whole fleet. You mark an area and
the aircraft divide it between themselves and fly it. The video is read
live by AI which marks people, fire and smoke, or flood water. Every
detection becomes an alert with a time and GPS position, and every
flight ends in a one-page Situation Report PDF that a commander can act
on. It is a web application, so anyone you give the link to opens it in
a browser with nothing to install.

**The sentence to use:** *"Aerial data already exists. The translated
answer does not. We build the layer that turns what drones see into a
decision someone can act on."*

---

## 2. What works today

Everything in this section runs and you can show it live.

| Capability | What it does |
|---|---|
| Fleet map | Live positions, altitude, speed, battery for every aircraft, updated 5 times a second |
| Mission planning | Click waypoints on the map, launch, then hold / resume / return home mid-flight |
| Area search | Draw a shape; the platform cuts it into strips and assigns each aircraft its own |
| AI detection | Three modes - Search (people, cars, boats), Fire (fire and smoke), Flood (percentage of ground under water) |
| Alerts | Every detection logged with timestamp and coordinates |
| No-fly zones | Draw a forbidden area; missions into it are refused and an aircraft entering one turns back by itself |
| Flight logs | Every flight recorded, replayable on the map at 8x speed |
| Reports | Flight report PDF, and a bilingual Situation Report with a SHA-256 hash proving it was not edited |
| Airspace awareness | Tracks cooperative aircraft and flags unknown ones inside a protected area |
| Share view | A read-only link anyone can open on a phone - they watch, they cannot touch controls |
| Safety | Automatic return home below 25% battery, with no operator input |

---

## 3. What is NOT real - say this plainly

Being exact here is what makes everything else believable.

- **The aircraft are simulated.** We run our own flight simulator, so
  the demo works indoors with no hardware. The MAVLINK connector for
  real PX4 drones is written and the same screen commands a real
  aircraft, but we have not flight-tested it against hardware yet.
- **The UTM / PansaUTM check-in is simulated** end to end so you can see
  the shape of it. Real API integration is the first roadmap item.
- **The 200-drone fire swarm is a concept.** No such fleet is fielded
  anywhere today. It exists to show that the control layer scales from
  3 aircraft to 200 without the operator's screen changing.
- **We have no customers yet.** That is why we are at the summit.

---

## 4. How it is built, in plain language

- **Backend:** Python with FastAPI. It runs the flight simulator,
  serves the map data, and pushes telemetry to the browser over a
  WebSocket five times a second.
- **AI vision:** YOLOv8 from Ultralytics - open source, no licence fee,
  no API key. Fire and smoke use weights fine-tuned on a public fire
  dataset. Flood detection uses no ML at all; it measures water by
  colour and texture, which is why it reports an honest percentage.
- **Frontend:** a plain web page with Leaflet for the map. No build
  step, no framework, nothing to install.
- **Map tiles** are cached on our own machine, so the map keeps working
  with no internet.
- **Reports** are generated with ReportLab into PDF.

**The architectural point worth making to a public or defence buyer:**
everything runs on the machine in front of you. The AI is local. The
maps are local. No video, no coordinates and no imagery leave the
building, and no foreign cloud service is involved. You can pull out
the network cable and the platform still works. That is not a technical
detail - for a sovereign buyer it is the whole argument.

---

## 5. Running it from the source code

```
cd skyops/backend
pip install -r requirements.txt
uvicorn main:app --port 8000
```

Then open http://localhost:8000

The source archive excludes three things to keep it small, and none of
them are needed to see the platform work:

- the fine-tuned fire model weights (149 MB) - the Search mode still
  works, since it downloads the standard YOLO model automatically
- the cached map tiles (29 MB) - the map fetches them from
  OpenStreetMap instead when online
- old flight logs

---

## 6. Answering the three questions you will actually get

**"Did you build this in 24 hours?"**
> "No, and we would rather tell you than have you find out. We came
> with a working platform. What we built here is [the feature added
> during the hackathon]."

**"Does it fly real drones?"**
> "The connector is built and the same screen commands a PX4 aircraft.
> What you see is our simulator because we are indoors. Flight testing
> against hardware has not happened yet."

**"Can it stop enemy drones?"**
> "We build the picture and the decision layer. We do not build
> effectors - different business, different licence."

---

## 7. Where the other documents are

- `operator-guide.md` - how to actually drive it, click by click,
  including what to do when something breaks mid-demo
- `hackathon/pitch-5min.md` - the 5-minute jury pitch, timed
- `summit-b2b.md` - the B2B meeting playbook and who to invite
- `README.md` - developer quick start
