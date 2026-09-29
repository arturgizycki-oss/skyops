# SkyOps demo video - recording script (60-90 seconds)

## Setup (before recording)
1. Start the server: `cd skyops/backend` then `uvicorn main:app --port 8000`
2. Open http://localhost:8000, wait ~15 s so YOLO loads (boxes appear in
   the camera panel).
3. Full-screen the browser (F11). Close other tabs.
4. Recorder: press Win+Alt+R (Windows Game Bar) to start/stop capture.
   Or OBS if you have it.

## Scenes

**Scene 1 (0-10 s) - Overview.** Do nothing. Let the viewer see the
dashboard: 3 drones at Jasionka airport, fleet cards, camera panel with
AI boxes appearing live.

**Scene 2 (10-30 s) - Plan a mission.** Click SKY-01's card. Press
"Plan mission". Click 3-4 waypoints on the map making a loop around the
airport. Press "Launch".

**Scene 3 (30-50 s) - Watch it fly.** The arrow takes off and follows
the green dashed route. Hover it to show the tooltip. Point the mouse at
the SKY-01 card - altitude climbs to 50 m, speed 12 m/s, battery
draining.

**Scene 4 (50-65 s) - Command mid-flight.** Press "Hold" (drone stops),
then "Resume", then "Return home" - the drone turns back and lands at
its start point.

**Scene 5 (65-80 s) - AI close-up.** Move the mouse to the camera
panel. The YOLO boxes track a person and cars, with count chips below
(person: 1, car: 2...).

**End card.** Stop recording at the landing page hero (open
landing/index.html) for 3 seconds - "Every drone. One screen."

## One-liner captions if you narrate or subtitle
- "Live fleet map - every drone, one screen"
- "Plan a mission with clicks, not code"
- "Full control mid-flight"
- "AI watches the video so you don't have to"
