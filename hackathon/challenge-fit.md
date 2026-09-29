# The official task vs what we have

The organisers' brief, mapped onto the platform. Use this to build the
Polish slides and to answer the jury. Where a row says GAP, that is a
candidate for the 24 hours.

**Their headline:** *"translating aerial data into actionable
information for decision-makers."*

That is our sentence. It is on our landing page and in the Situation
Report. Say it back to them in the first thirty seconds.

---

## Their words, our answer

| What the brief asks for | What we already have |
|---|---|
| "assess situations faster" | Area search - draw a shape, the fleet divides it into strips and flies it. No manual planning. |
| "evaluate threats more accurately" | AI video: people and vehicles, fire and smoke, flood water as a percentage of ground |
| "support decision-making by emergency services" | Situation Report PDF - one page, bilingual, every detection with time and GPS |
| "situational awareness" | One live map, whole fleet, plus airspace picture with unknown aircraft flagged |
| "threat assessment" | Detection alerts with coordinates, and the honest line that AI suggests, operator decides |
| "road accessibility checks" | Flood mode measures water coverage - GAP: we do not yet phrase it as "which roads are passable" |
| "operational coordination" | Fleet splitting, hold/resume/return-home, read-only share link for staff who must watch but not touch |
| "situational reporting" | The Situation Report, with a SHA-256 hash proving it was not edited afterwards |
| "floods, fires... search and rescue" | Exactly our three AI modes: Flood, Fire, Search |
| "windstorms" | GAP - no weather data yet |
| "infrastructure failures / inspection" | GAP |
| "contamination", "communication outages" | GAP - out of scope, say so honestly |

**Their permitted outputs:** "a system or service concept, an app
mockup, a dashboard, a drone data analysis algorithm, a decision-making
model, a procedure, a process simulation, or a **demonstrator**."

We are a demonstrator, and the brief explicitly says *"you do not need
to build a fully functional system."* We have one. That is not against
the rules - it is above the bar, and it is why we should score on
Realism and Feasibility.

---

## The three best things to build in the 24 hours

Ranked by how directly they hit the brief's own words.

**1. Road passability from flood data (strongest).**
The brief names "road accessibility checks" as a decision-maker need.
We already segment flood water. Turning that into "this road section is
under water, this one is clear" converts a percentage into a decision.
That is the whole point of the task in one feature.

**2. Weather and wind from IMGW (covers "windstorms").**
Poland's meteorological service publishes a free public API with live
wind speed per station - no key, tested and working. Two uses at once:
flight safety ("wind too strong, do not launch") and windstorm
situational awareness. Polish government data source, which lands well.

**3. Voice command of the fleet.**
Hands-free operation for a commander. Runs offline with Whisper - no
API key, no cloud. Note for the jury: EDTH's winning VoiceOps Map was
voice INTO the map; ours is voice OUT to the fleet. Different half of
the loop, and saying so shows we know the field.

---

## What to say about what existed before

Say it in the presentation, unprompted, on the slide:

> "The platform existed before this hackathon. What we built here in 24
> hours is [X]. We would rather tell you that than have you find out."

The rules do not forbid pre-existing work. Hiding it is the only thing
that could hurt us.

---

## Scoring, and where each point comes from

| Criterion | 20% each | Where we earn it |
|---|---|---|
| Operational usefulness | The Situation Report - a commander gets one page, not a hard drive |
| Role of drone technologies | The whole platform is drone data; three AI modes on live video |
| Innovativeness | Fleet self-dividing an area; the 24-hour feature; 200-aircraft scaling |
| **Realism and feasibility** | **It runs. Open it on your phone in the room.** This is our strongest card |
| Presentation | Polish, 10 slides max, rehearsed with a timer, live demo, printed reports |

50% of points is the minimum for any prize.
