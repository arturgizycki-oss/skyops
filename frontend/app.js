/* SkyOps dashboard */

// /share serves the same page as a read-only observer view for
// crisis staff, stakeholders or press - watch everything, command nothing.
const VIEWER = location.pathname.replace(/\/$/, "").endsWith("/share");
if (VIEWER) document.body.classList.add("viewer");

window.addEventListener("DOMContentLoaded", () => {
  if (VIEWER) {
    const badge = document.createElement("span");
    badge.className = "viewer-badge";
    badge.textContent = t("viewonly");
    document.querySelector(".head-right").prepend(badge);
    return;
  }
  const shareBtn = document.getElementById("btn-share");
  shareBtn.onclick = async () => {
    const url = `${location.origin}/share`;
    try {
      await navigator.clipboard.writeText(url);
      shareBtn.textContent = t("b.share") + " OK";
    } catch {
      prompt(t("b.share") + ":", url);
      shareBtn.textContent = t("b.share");
      return;
    }
    setTimeout(() => { shareBtn.textContent = t("b.share"); }, 2000);
  };
});

const HOME = [50.1090, 22.0230]; // Rzeszow-Jasionka

const map = L.map("map", { zoomControl: true }).setView(HOME, 15);
// served through our caching proxy so the demo survives dead wifi
L.tileLayer("/tiles/{z}/{x}/{y}.png", {
  attribution: "&copy; OpenStreetMap contributors",
  maxZoom: 19,
}).addTo(map);

const state = {
  drones: {},          // id -> telemetry
  markers: {},         // id -> L.Marker
  trails: {},          // id -> L.Polyline
  missionLines: {},    // id -> L.Polyline
  selected: null,
  planning: false,
  plannedWps: [],
  plannedMarkers: [],
  plannedLine: null,
};

const els = {
  fleet: document.getElementById("fleet"),
  conn: document.getElementById("conn-status"),
  hint: document.getElementById("plan-hint"),
  plan: document.getElementById("btn-plan"),
  launch: document.getElementById("btn-launch"),
  clear: document.getElementById("btn-clear"),
  hold: document.getElementById("btn-hold"),
  resume: document.getElementById("btn-resume"),
  rtl: document.getElementById("btn-rtl"),
};

function droneIcon(heading, selected) {
  const color = selected ? "#0f62e6" : "#132430";
  return L.divIcon({
    className: "drone-icon",
    html: `<svg width="30" height="30" viewBox="0 0 30 30"
             style="transform: rotate(${heading}deg)">
             <polygon points="15,3 24,26 15,20 6,26" fill="${color}"
               stroke="#ffffff" stroke-width="1.5"/>
           </svg>`,
    iconSize: [30, 30],
    iconAnchor: [15, 15],
  });
}

// flight states, shown on the drone cards - the jury reads these
function batteryClass(pct) {
  if (pct <= 25) return "critical";
  if (pct <= 45) return "low";
  return "";
}

function renderFleet() {
  els.fleet.innerHTML = "";
  for (const d of Object.values(state.drones)) {
    const card = document.createElement("div");
    card.className = "drone-card" + (d.id === state.selected ? " selected" : "");
    card.innerHTML = `
      <div class="row1">
        <span class="name">${d.name}</span>
        <span class="state-badge ${d.state}">${t("s." + d.state)}</span>
      </div>
      <div class="stats">
        <span>ALT <b>${d.alt} m</b></span>
        <span>SPD <b>${d.speed} m/s</b></span>
        <span>BAT <b>${d.battery}%</b></span>
      </div>
      <div class="battery-bar">
        <div class="${batteryClass(d.battery)}" style="width:${d.battery}%"></div>
      </div>`;
    card.onclick = () => selectDrone(d.id);
    els.fleet.appendChild(card);
  }
}

function selectDrone(id) {
  state.selected = id;
  renderFleet();
  updateButtons();
  const d = state.drones[id];
  if (d) map.panTo([d.lat, d.lon]);
}

function updateButtons() {
  const d = state.drones[state.selected];
  const has = !!d;
  els.plan.disabled = !has;
  els.launch.disabled = !(has && state.plannedWps.length > 0);
  els.clear.disabled = state.plannedWps.length === 0;
  els.hold.disabled = !(has && ["enroute", "rtl"].includes(d?.state));
  els.resume.disabled = !(has && d?.state === "hold");
  els.rtl.disabled = !(has && d?.state !== "idle");
}

function updateMap() {
  for (const d of Object.values(state.drones)) {
    const pos = [d.lat, d.lon];
    if (!state.markers[d.id]) {
      state.markers[d.id] = L.marker(pos, {
        icon: droneIcon(d.heading, d.id === state.selected),
      }).addTo(map).on("click", () => selectDrone(d.id));
      state.trails[d.id] = L.polyline([], {
        color: "#0f62e6", weight: 3, opacity: 0.45,
      }).addTo(map);
      state.missionLines[d.id] = L.polyline([], {
        color: "#148a5c", weight: 3, dashArray: "6 6", opacity: 0.85,
      }).addTo(map);
    }
    const m = state.markers[d.id];
    m.setLatLng(pos);
    m.setIcon(droneIcon(d.heading, d.id === state.selected));
    m.bindTooltip(`${d.name} | ${d.alt}m | ${d.battery}%`, { direction: "top" });

    const remaining = d.mission.slice(d.wp_index).map(w => [w.lat, w.lon]);
    state.missionLines[d.id].setLatLngs(
      remaining.length ? [pos, ...remaining] : []);
  }
}

/* --- Mission planning --- */

els.plan.onclick = () => {
  state.planning = !state.planning;
  els.plan.classList.toggle("active", state.planning);
  els.hint.textContent = state.planning
    ? t("hint.planning")
    : t("hint.plan");
};

map.on("click", (e) => {
  if (!state.planning || !state.selected || zoneState.drawing
      || areaState.drawing || swarmState.placing) return;
  const wp = { lat: e.latlng.lat, lon: e.latlng.lng, alt: 50 };
  state.plannedWps.push(wp);
  const idx = state.plannedWps.length;
  state.plannedMarkers.push(
    L.circleMarker(e.latlng, {
      radius: 9, color: "#ffffff", fillColor: "#148a5c", fillOpacity: 1, weight: 2,
    }).addTo(map).bindTooltip(String(idx), {
      permanent: true, direction: "center", className: "wp-label",
    })
  );
  if (!state.plannedLine) {
    state.plannedLine = L.polyline([], { color: "#148a5c", weight: 3 }).addTo(map);
  }
  state.plannedLine.setLatLngs(state.plannedWps.map(w => [w.lat, w.lon]));
  updateButtons();
});

function clearPlan() {
  state.plannedWps = [];
  state.plannedMarkers.forEach(m => map.removeLayer(m));
  state.plannedMarkers = [];
  if (state.plannedLine) { map.removeLayer(state.plannedLine); state.plannedLine = null; }
  state.planning = false;
  els.plan.classList.remove("active");
  updateButtons();
}

els.clear.onclick = clearPlan;

els.launch.onclick = async () => {
  if (!state.selected || !state.plannedWps.length) return;
  const res = await api(`/api/drones/${state.selected}/mission`, {
    waypoints: state.plannedWps,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    alert(err.detail || t("hint.rejected"));
    return;
  }
  showUtmToast((await res.json().catch(() => ({}))).utm);
  clearPlan();
};

els.hold.onclick = () => sendCommand("hold");
els.resume.onclick = () => sendCommand("resume");
els.rtl.onclick = () => sendCommand("rtl");

async function sendCommand(command) {
  if (!state.selected) return;
  await api(`/api/drones/${state.selected}/command`, { command });
}

async function api(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) console.error("API error", path, res.status);
  return res;
}

/* --- Telemetry stream --- */

function connect() {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${location.host}/ws`);
  ws.onopen = () => {
    els.conn.textContent = t("conn.live");
    els.conn.className = "conn ok";
  };
  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.type === "swarm") { renderSwarm(msg); return; }
    if (msg.type !== "telemetry") return;
    for (const d of msg.drones) {
      state.drones[d.id] = d;
      if (state.trails[d.id] && ["enroute", "rtl", "takeoff"].includes(d.state)) {
        state.trails[d.id].addLatLng([d.lat, d.lon]);
      }
      if (d.state === "idle" && state.trails[d.id]) {
        state.trails[d.id].setLatLngs([]);
      }
    }
    if (!state.selected) selectDrone(msg.drones[0]?.id);
    renderFleet();
    updateMap();
    updateButtons();
  };
  ws.onclose = () => {
    els.conn.textContent = t("conn.wait");
    els.conn.className = "conn err";
    setTimeout(connect, 1500);
  };
}

connect();

/* Initial render from REST so the fleet shows even before the
   WebSocket delivers its first snapshot. */
(async () => {
  try {
    const drones = await (await fetch("/api/drones")).json();
    if (Object.keys(state.drones).length) return; // WS beat us to it
    for (const d of drones) state.drones[d.id] = d;
    if (!state.selected) selectDrone(drones[0]?.id);
    renderFleet();
    updateMap();
    updateButtons();
  } catch { /* WS will populate when it connects */ }
})();

/* --- Search area (objective-based mission) --- */

const areaState = { drawing: false, points: [], markers: [], poly: null };
const aEls = {
  draw: document.getElementById("btn-area"),
  go: document.getElementById("btn-area-go"),
  clear: document.getElementById("btn-area-clear"),
  hint: document.getElementById("area-hint"),
};

function resetArea() {
  areaState.drawing = false;
  areaState.points = [];
  areaState.markers.forEach(m => map.removeLayer(m));
  areaState.markers = [];
  if (areaState.poly) { map.removeLayer(areaState.poly); areaState.poly = null; }
  aEls.draw.classList.remove("active");
  aEls.go.disabled = true;
  aEls.clear.disabled = true;
  aEls.hint.hidden = true;
}

aEls.draw.onclick = () => {
  areaState.drawing = !areaState.drawing;
  aEls.draw.classList.toggle("active", areaState.drawing);
  aEls.hint.hidden = !areaState.drawing;
  aEls.clear.disabled = !areaState.drawing;
};

aEls.clear.onclick = resetArea;

aEls.go.onclick = async () => {
  const res = await api("/api/area_mission", {
    points: areaState.points.map(p => ({ lat: p[0], lon: p[1] })),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    alert(err.detail || "Area mission rejected");
    return;
  }
  const out = await res.json();
  console.log("fleet assigned:", out.assigned);
  showUtmToast(out.utm);
  resetArea();
};

map.on("click", (e) => {
  if (!areaState.drawing) return;
  areaState.points.push([e.latlng.lat, e.latlng.lng]);
  areaState.markers.push(L.circleMarker(e.latlng, {
    radius: 5, color: "#2563eb", fillColor: "#fff", fillOpacity: 1, weight: 2,
  }).addTo(map));
  if (!areaState.poly) {
    areaState.poly = L.polygon([], {
      color: "#2563eb", weight: 2, dashArray: "4 4", fillOpacity: 0.08,
    }).addTo(map);
  }
  areaState.poly.setLatLngs(areaState.points);
  aEls.go.disabled = areaState.points.length < 3;
});

/* --- No-fly zones --- */

const zoneState = { drawing: false, points: [], markers: [], poly: null, layers: {} };
const zEls = {
  draw: document.getElementById("btn-zone"),
  save: document.getElementById("btn-zone-save"),
  cancel: document.getElementById("btn-zone-cancel"),
  list: document.getElementById("zones"),
};

async function refreshZones() {
  try {
    const zones = await (await fetch("/api/zones")).json();
    for (const id of Object.keys(zoneState.layers)) {
      if (!zones.find(z => z.id === id)) {
        map.removeLayer(zoneState.layers[id]);
        delete zoneState.layers[id];
      }
    }
    for (const z of zones) {
      if (!zoneState.layers[z.id]) {
        zoneState.layers[z.id] = L.polygon(
          z.points.map(p => [p.lat, p.lon]),
          { color: "#dc2626", weight: 2, fillOpacity: 0.15 }
        ).addTo(map).bindTooltip(`NO-FLY: ${z.name}`);
      }
    }
    zEls.list.innerHTML = zones.map(z =>
      `<div class="log-row"><span><b>${z.name}</b>
         <span class="meta">${z.points.length} pts</span></span>
       <a href="#" data-zone="${z.id}">${t("b.remove")}</a></div>`).join("")
      || `<span class="hint">${t("hint.nozones")}</span>`;
    zEls.list.querySelectorAll("a[data-zone]").forEach(a => {
      a.onclick = async (e) => {
        e.preventDefault();
        await fetch(`/api/zones/${a.dataset.zone}`, { method: "DELETE" });
        refreshZones();
      };
    });
  } catch { /* backend not ready */ }
}
refreshZones();

function resetZoneDraw() {
  zoneState.drawing = false;
  zoneState.points = [];
  zoneState.markers.forEach(m => map.removeLayer(m));
  zoneState.markers = [];
  if (zoneState.poly) { map.removeLayer(zoneState.poly); zoneState.poly = null; }
  zEls.draw.classList.remove("active");
  zEls.save.disabled = true;
  zEls.cancel.disabled = true;
}

zEls.draw.onclick = () => {
  zoneState.drawing = !zoneState.drawing;
  zEls.draw.classList.toggle("active", zoneState.drawing);
  zEls.cancel.disabled = !zoneState.drawing;
};

zEls.cancel.onclick = resetZoneDraw;

zEls.save.onclick = async () => {
  const name = prompt("Zone name:", "Restricted area") || "Restricted area";
  await api("/api/zones", {
    name,
    points: zoneState.points.map(p => ({ lat: p[0], lon: p[1] })),
  });
  resetZoneDraw();
  refreshZones();
};

map.on("click", (e) => {
  if (!zoneState.drawing) return;
  zoneState.points.push([e.latlng.lat, e.latlng.lng]);
  zoneState.markers.push(L.circleMarker(e.latlng, {
    radius: 5, color: "#dc2626", fillColor: "#fff", fillOpacity: 1, weight: 2,
  }).addTo(map));
  if (!zoneState.poly) {
    zoneState.poly = L.polygon([], {
      color: "#dc2626", weight: 2, dashArray: "4 4", fillOpacity: 0.1,
    }).addTo(map);
  }
  zoneState.poly.setLatLngs(zoneState.points);
  zEls.save.disabled = zoneState.points.length < 3;
});

/* --- Flight logs panel --- */

async function refreshLogs() {
  try {
    const logs = await (await fetch("/api/logs")).json();
    const el = document.getElementById("logs");
    if (!logs.length) return;
    el.innerHTML = logs.slice(0, 8).map(l => {
      const when = new Date(l.start * 1000).toLocaleTimeString();
      return `<div class="log-row">
        <span><b>${l.drone}</b>
          <span class="meta">${when} - ${Math.round(l.duration_s)}s,
          ${Math.round(l.distance_m)}m</span></span>
        <span class="log-actions">
          <a href="#" data-replay="${l.id}">Replay</a>
          <a href="/api/logs/${l.id}/report" target="_blank">PDF</a>
          <a href="/api/logs/${l.id}/sitrep" target="_blank">Sitrep</a>
        </span>
      </div>`;
    }).join("");
    el.querySelectorAll("a[data-replay]").forEach(a => {
      a.onclick = (e) => { e.preventDefault(); startReplay(a.dataset.replay); };
    });
  } catch { /* backend not ready */ }
}
refreshLogs();
setInterval(refreshLogs, 5000);

/* --- Airspace awareness --- */

const air = { markers: {}, banner: null };

function trafficIcon(t) {
  const color = t.kind === "adsb" ? "#3c5364"
    : t.kind === "rid" ? "#6d28d9" : "#bb2124";
  const shape = t.kind === "adsb"
    ? `<path d="M15 4 L18 13 L27 15 L18 17 L15 26 L12 17 L3 15 L12 13 Z"
         fill="${color}" stroke="#fff" stroke-width="1.2"
         transform="rotate(${t.heading} 15 15)"/>`
    : `<rect x="9" y="9" width="12" height="12" fill="${color}"
         stroke="#fff" stroke-width="1.5"
         transform="rotate(45 15 15)"/>`;
  return L.divIcon({
    className: "traffic-icon",
    html: `<svg width="30" height="30" viewBox="0 0 30 30">${shape}</svg>`,
    iconSize: [30, 30], iconAnchor: [15, 15],
  });
}

async function refreshTraffic() {
  try {
    const pic = await (await fetch("/api/traffic")).json();
    const seen = new Set();
    for (const t of pic.aircraft) {
      seen.add(t.id);
      const label = `${t.callsign} | ${t.kind.toUpperCase()} | ${t.alt} m`;
      if (!air.markers[t.id]) {
        air.markers[t.id] = L.marker([t.lat, t.lon], { icon: trafficIcon(t) })
          .addTo(map).bindTooltip(label, { direction: "top" });
      } else {
        air.markers[t.id].setLatLng([t.lat, t.lon]);
        air.markers[t.id].setIcon(trafficIcon(t));
        air.markers[t.id].setTooltipContent(label);
      }
    }
    for (const id of Object.keys(air.markers)) {
      if (!seen.has(id)) { map.removeLayer(air.markers[id]); delete air.markers[id]; }
    }
    if (pic.conflicts.length) {
      if (!air.banner) {
        air.banner = document.createElement("div");
        air.banner.className = "conflict-banner";
        document.getElementById("map").appendChild(air.banner);
      }
      const c = pic.conflicts[0];
      air.banner.textContent =
        `AIRSPACE CONFLICT: ${c.traffic} within ${c.dist_m} m of ${c.drone}`;
    } else if (air.banner) {
      air.banner.remove();
      air.banner = null;
    }
  } catch { /* backend not ready */ }
}
refreshTraffic();
setInterval(refreshTraffic, 2000);

function showUtmToast(utm) {
  if (!utm || !utm.checked_in) return;
  const el = document.createElement("div");
  el.className = "utm-toast";
  el.textContent = `UTM check-in accepted - ref ${utm.ref} (simulated)`;
  document.getElementById("map").appendChild(el);
  setTimeout(() => el.remove(), 6000);
}

/* --- Flight replay --- */

const replay = { timer: null, track: null, marker: null, banner: null };

function stopReplay() {
  if (replay.timer) clearInterval(replay.timer);
  [replay.track, replay.marker].forEach(l => l && map.removeLayer(l));
  if (replay.banner) replay.banner.remove();
  replay.timer = replay.track = replay.marker = replay.banner = null;
}

async function startReplay(logId) {
  stopReplay();
  const rec = await (await fetch(`/api/logs/${logId}`)).json();
  const pts = rec.samples.map(s => [s.lat, s.lon]);
  if (pts.length < 2) return;

  replay.track = L.polyline(pts, {
    color: "#94a3b8", weight: 3, opacity: 0.8, dashArray: "2 6",
  }).addTo(map);
  map.fitBounds(replay.track.getBounds(), { padding: [60, 60] });
  replay.marker = L.circleMarker(pts[0], {
    radius: 8, color: "#fff", weight: 2, fillColor: "#2563eb", fillOpacity: 1,
  }).addTo(map);

  replay.banner = document.createElement("div");
  replay.banner.className = "replay-banner";
  document.getElementById("map").appendChild(replay.banner);

  let i = 0;
  const SPEED = 8; // 8x real time; samples are 2s apart
  replay.timer = setInterval(() => {
    if (i >= rec.samples.length) { stopReplay(); return; }
    const s = rec.samples[i++];
    replay.marker.setLatLng([s.lat, s.lon]);
    replay.banner.innerHTML =
      `REPLAY ${rec.drone} - t+${Math.round(s.t)}s - ` +
      `${s.alt} m - ${s.battery}% - ${s.state}` +
      ` <button id="replay-stop">stop</button>`;
    document.getElementById("replay-stop").onclick = stopReplay;
  }, 2000 / SPEED);
}

/* --- Auto demo toggle --- */

const demoBtn = document.getElementById("btn-demo");
function renderDemoBtn(on) {
  demoBtn.textContent = `Auto demo: ${on ? "wl." : "wyl."}`;
  demoBtn.classList.toggle("on", on);
  demoBtn.dataset.on = on ? "1" : "";
}
(async () => {
  try {
    renderDemoBtn((await (await fetch("/api/demo")).json()).on);
  } catch { /* default off */ }
})();
demoBtn.onclick = async () => {
  const next = !demoBtn.dataset.on;
  const res = await api("/api/demo", { on: next });
  if (res.ok) renderDemoBtn((await res.json()).on);
};

/* --- Crisis mode switch --- */

document.querySelectorAll(".mode-btn").forEach(btn => {
  btn.onclick = async () => {
    const res = await api("/api/video/mode", { mode: btn.dataset.mode });
    if (!res.ok) return;
    document.querySelectorAll(".mode-btn").forEach(b =>
      b.classList.toggle("active", b === btn));
  };
});
(async () => {
  try {
    const st = await (await fetch("/api/video/status")).json();
    if (st.mode) document.querySelectorAll(".mode-btn").forEach(b =>
      b.classList.toggle("active", b.dataset.mode === st.mode));
  } catch { /* default highlight stays */ }
})();

/* --- AI alerts feed --- */

// An alert is a proposal, not a fact. The operator adjudicates it, and
// only that verdict is carried into the Situation Report.
async function setAlertStatus(id, status) {
  await api(`/api/alerts/${id}/status`, { status });
  refreshAlerts();
}

function alertAge(ts) {
  const s = Math.max(0, Math.round(Date.now() / 1000 - ts));
  if (s < 60) return `${s} s ${t("ago")}`;
  return `${Math.round(s / 60)} min ${t("ago")}`;
}

async function refreshAlerts() {
  try {
    const alerts = await (await fetch("/api/alerts")).json();
    const el = document.getElementById("alerts");
    el.innerHTML = alerts.slice(0, 12).map(a => {
      const t = new Date(a.ts * 1000).toLocaleTimeString();
      const st = a.status || "pending";
      // a confidence is a classifier's own certainty; flood coverage is a
      // measurement, so it is labelled as one instead of faking a score
      const conf = a.conf == null
        ? `<span class="conf meas">${t("measure")}</span>`
        : `<span class="conf">${Math.round(a.conf * 100)}%</span>`;
      const controls = (VIEWER || st !== "pending") ? "" : `
        <span class="adj">
          <button class="ok" onclick="setAlertStatus(${a.id},'confirmed')">${t('confirm')}</button>
          <button class="no" onclick="setAlertStatus(${a.id},'rejected')">${t('reject')}</button>
        </span>`;
      const verdict = st === "confirmed"
        ? `<span class="verdict ok">${t("st.confirmed")}</span>`
        : st === "rejected" ? `<span class="verdict no">${t("st.rejected")}</span>` : "";
      return `<div class="alert-row st-${st}">
        <div class="ar-main"><span class="t">${t}</span>
          <span class="lab">${a.label} (x${a.count})</span> ${conf}</div>
        <div class="ar-sub"><span class="age">${alertAge(a.ts)}</span>
          ${verdict}${controls}</div>
      </div>`;
    }).join("");
  } catch { /* backend not ready */ }
}
refreshAlerts();
setInterval(refreshAlerts, 2000);

/* --- AI video panel --- */

async function initVideo(attempt = 0) {
  const feed = document.getElementById("video-feed");
  const offline = document.getElementById("video-offline");
  const dets = document.getElementById("detections");
  try {
    const res = await fetch("/api/video/status");
    const st = await res.json();
    if (!st.video) throw new Error("video not ready");
    feed.src = "/api/video/stream";
    feed.hidden = false;
    offline.hidden = true;
    setInterval(async () => {
      try {
        const s = await (await fetch("/api/video/status")).json();
        dets.innerHTML = Object.entries(s.detections)
          .map(([k, v]) => `<span class="det-chip">${k}: ${v}</span>`)
          .join("") || '<span class="det-chip">no objects</span>';
      } catch { /* keep last chips */ }
    }, 1000);
  } catch {
    // server may still be loading the AI model right after startup
    if (attempt < 30) setTimeout(() => initVideo(attempt + 1), 2000);
  }
}

initVideo();

/* --- Fire swarm (concept): 200-aircraft firefighting demonstration --- */

const swarmState = {
  placing: false,
  fire: null,          // L.Marker for the fire seed
  origin: null,
  cellM: 50,
  cells: new Map(),    // "i,j" -> L.Rectangle
  dots: [],            // L.CircleMarker per aircraft
  base: null,
};

// one shared canvas keeps 200 aircraft + the fire grid cheap to draw
const swarmCanvas = L.canvas({ padding: 0.4 });

const sEls = {
  place: document.getElementById("btn-swarm-place"),
  count: document.getElementById("swarm-count"),
  go: document.getElementById("btn-swarm-go"),
  stop: document.getElementById("btn-swarm-stop"),
  hint: document.getElementById("swarm-hint"),
  stats: document.getElementById("swarm-stats"),
};

const DOT_COLOR = ["#0f62e6", "#c22e6f", "#43606f", "#43606f"]; // transit/drop/return/refill
const CELL_FILL = { burning: "#e8442a", out: "#a9c2cf" };

function cellBounds(origin, i, j, cellM) {
  const mLat = 111320;
  const mLon = 111320 * Math.cos(origin[0] * Math.PI / 180);
  return [
    [origin[0] + (i * cellM - cellM / 2) / mLat,
     origin[1] + (j * cellM - cellM / 2) / mLon],
    [origin[0] + (i * cellM + cellM / 2) / mLat,
     origin[1] + (j * cellM + cellM / 2) / mLon],
  ];
}

function clearSwarmLayers() {
  swarmState.cells.forEach(r => map.removeLayer(r));
  swarmState.cells.clear();
  swarmState.dots.forEach(d => map.removeLayer(d));
  swarmState.dots = [];
  if (swarmState.base) { map.removeLayer(swarmState.base); swarmState.base = null; }
  if (swarmState.fire) { map.removeLayer(swarmState.fire); swarmState.fire = null; }
}

function renderSwarm(msg) {
  swarmState.origin = msg.origin;
  swarmState.cellM = msg.cell_m;

  // forward operating base
  if (!swarmState.base) {
    swarmState.base = L.circleMarker(msg.base, {
      renderer: swarmCanvas, radius: 7, color: "#132430",
      fillColor: "#f3f7f9", fillOpacity: 1, weight: 2,
    }).addTo(map).bindTooltip("Baza wysunieta - tankowanie", { direction: "top" });
  }

  // fire grid: create each cell once, then only recolour
  for (const [i, j, st] of msg.fire) {
    const key = i + "," + j;
    const burning = st === 1;
    let rect = swarmState.cells.get(key);
    if (!rect) {
      rect = L.rectangle(cellBounds(msg.origin, i, j, msg.cell_m), {
        renderer: swarmCanvas, stroke: false,
        fillColor: burning ? CELL_FILL.burning : CELL_FILL.out,
        fillOpacity: burning ? 0.55 : 0.4,
      }).addTo(map);
      swarmState.cells.set(key, rect);
      rect._burning = burning;
    } else if (rect._burning !== burning) {
      rect.setStyle({
        fillColor: burning ? CELL_FILL.burning : CELL_FILL.out,
        fillOpacity: burning ? 0.55 : 0.4,
      });
      rect._burning = burning;
    }
  }

  // aircraft
  const dots = swarmState.dots;
  for (let k = 0; k < msg.drones.length; k++) {
    const [lat, lon, , st] = msg.drones[k];
    if (!dots[k]) {
      dots[k] = L.circleMarker([lat, lon], {
        renderer: swarmCanvas, radius: 3.5, weight: 0,
        fillColor: DOT_COLOR[st], fillOpacity: 0.95,
      }).addTo(map);
      dots[k]._st = st;
    } else {
      dots[k].setLatLng([lat, lon]);
      if (dots[k]._st !== st) {
        dots[k].setStyle({ fillColor: DOT_COLOR[st] });
        dots[k]._st = st;
      }
    }
  }

  renderSwarmStats(msg.stats);
}

function renderSwarmStats(s) {
  if (!s || !s.active) { sEls.stats.hidden = true; return; }
  sEls.stats.hidden = false;
  const mins = String(Math.floor(s.elapsed_s / 60)).padStart(2, "0");
  const secs = String(s.elapsed_s % 60).padStart(2, "0");
  sEls.stats.innerHTML = `
    <div class="contain-row">
      <span class="contain-val">${s.containment}%</span>
      <span class="contain-lbl">contained</span>
    </div>
    <div class="contain-bar"><i style="width:${s.containment}%"></i></div>
    <dl class="swarm-grid">
      <dt>airborne</dt><dd>${s.airborne} / ${s.count}</dd>
      <dt>fire area</dt><dd>${s.area_burning_ha} ha</dd>
      <dt>drops</dt><dd>${s.drops}</dd>
      <dt>water</dt><dd>${(s.water_l / 1000).toFixed(1)} t</dd>
      <dt>elapsed</dt><dd>${mins}:${secs}</dd>
    </dl>`;
}

sEls.place.onclick = () => {
  swarmState.placing = !swarmState.placing;
  sEls.place.classList.toggle("active", swarmState.placing);
  sEls.hint.textContent = swarmState.placing
    ? t("hint.fire")
    : t("hint.fire");
};

map.on("click", (e) => {
  if (!swarmState.placing || zoneState.drawing || areaState.drawing) return;
  if (swarmState.fire) map.removeLayer(swarmState.fire);
  swarmState.fire = L.circleMarker(e.latlng, {
    radius: 9, color: "#e8442a", fillColor: "#e8442a",
    fillOpacity: 0.5, weight: 2,
  }).addTo(map).bindTooltip("Fire origin", { direction: "top" });
  swarmState.placing = false;
  sEls.place.classList.remove("active");
  sEls.go.disabled = false;
  sEls.hint.textContent = t("hint.fireplaced");
});

sEls.go.onclick = async () => {
  if (!swarmState.fire) return;
  const ll = swarmState.fire.getLatLng();
  sEls.go.disabled = true;
  const res = await api("/api/swarm", {
    lat: ll.lat, lon: ll.lng, count: Number(sEls.count.value),
  });
  if (res.ok) {
    sEls.stop.disabled = false;
    sEls.hint.textContent = "Roj wyslany. Maszyny startuja falami.";
    map.setView(ll, 14);
  } else {
    sEls.go.disabled = false;
  }
};

sEls.stop.onclick = async () => {
  await fetch("/api/swarm", { method: "DELETE" });
  clearSwarmLayers();
  sEls.stats.hidden = true;
  sEls.stop.disabled = true;
  sEls.go.disabled = true;
  sEls.hint.textContent = t("hint.fire");
};

// a reload mid-demo must not strand the operator: recover the swarm's
// state from the server so "Stand down" stays reachable
async function initSwarm() {
  try {
    const s = await (await fetch("/api/swarm")).json();
    if (s.active) {
      sEls.stop.disabled = false;
      sEls.hint.textContent = "Roj juz dziala przy pozarze.";
    }
  } catch { /* server not reachable yet; the websocket will catch up */ }
}

initSwarm();

/* --- IMGW river gauges: the trigger, and the other half of the uncertainty ---
   A gauge is authoritative about water level and blind about extent. It is
   what starts a sortie; the drone answers the question it raises. */

const hydroState = { markers: {}, seen: false };
const HYDRO_COLOR = {
  "alarmowy": "#c0392b",
  "ostrzegawczy": "#9a6200",
  "norma": "#148a5c",
  "brak progow": "#8ba0ac",
};

function hydroIcon(st, simulated) {
  const c = HYDRO_COLOR[st] || HYDRO_COLOR["brak progow"];
  return L.divIcon({
    className: "hydro-icon",
    html: `<svg width="18" height="18" viewBox="0 0 18 18">
      <rect x="2" y="2" width="14" height="14" rx="2"
        fill="${c}" stroke="${simulated ? '#132430' : '#ffffff'}"
        stroke-width="${simulated ? 2.5 : 1.5}"
        stroke-dasharray="${simulated ? '3 2' : ''}"/>
      <path d="M5 11 q4 -4 8 0" stroke="#fff" stroke-width="1.6" fill="none"/>
    </svg>`,
    iconSize: [18, 18], iconAnchor: [9, 9],
  });
}

async function refreshHydro() {
  try {
    const p = await (await fetch("/api/hydro")).json();
    const sum = document.getElementById("hydro-summary");
    const list = document.getElementById("hydro-list");
    if (!sum || !list) return;

    if (p.error && !p.stations.length) {
      sum.textContent = t("h.offline");
      return;
    }

    const c = p.counts || {};
    const alarm = c["alarmowy"] || 0, warn = c["ostrzegawczy"] || 0;
    sum.innerHTML = `${p.stations.length} ${t("h.gauges")} &middot; `
      + `<b style="color:${HYDRO_COLOR['alarmowy']}">${alarm} ${t("h.alarm")}</b> &middot; `
      + `<b style="color:${HYDRO_COLOR['ostrzegawczy']}">${warn} ${t("h.warn")}</b>`
      + (p.age_s != null ? ` &middot; ${t("h.age")} ${Math.round(p.age_s / 60)} ${t("h.min")}` : "");

    // only the ones an officer would act on
    const hot = p.stations.filter(s => s.status === "alarmowy" || s.status === "ostrzegawczy");
    list.innerHTML = hot.length ? hot.map(s => `
      <div class="hydro-row ${s.status}">
        <b>${s.name}</b> <span class="river">${s.river || ""}</span>
        <span class="lvl">${s.level_cm} cm</span>
        <span class="thr">alarm ${s.alarm_cm}</span>
        ${s.simulated ? '<span class="sim">SYMULACJA</span>' : ""}
      </div>`).join("")
      : `<span class="hint">${t("h.normal")}</span>`;

    for (const s of p.stations) {
      const key = String(s.id);
      const tip = `${s.name} (${s.river || "-"})<br>stan ${s.level_cm} cm`
        + `<br>ostrzegawczy ${s.warn_cm} / alarmowy ${s.alarm_cm}`
        + (s.simulated ? "<br><b>SYMULACJA</b>" : "")
        + `<br><span style="opacity:.7">IMGW ${s.measured_at || ""}</span>`;
      if (!hydroState.markers[key]) {
        hydroState.markers[key] = L.marker([s.lat, s.lon], {
          icon: hydroIcon(s.status, s.simulated),
        }).addTo(map).bindTooltip(tip, { direction: "top" });
      } else {
        hydroState.markers[key].setIcon(hydroIcon(s.status, s.simulated));
        hydroState.markers[key].setTooltipContent(tip);
      }
    }
  } catch { /* backend not ready */ }
}

refreshHydro();
setInterval(refreshHydro, 30000);

/* --- Road passability: the decision, drawn on the map ---
   Roads nobody flew over stay unmarked. An unchecked road must never
   look clear, so we draw only what we actually observed. */

const roadState = { layer: null };
const ROAD_COLOR = {
  "nieprzejezdna": "#c0392b",
  "podejrzana": "#9a6200",
  "przejezdna": "#148a5c",
};

async function refreshRoads() {
  try {
    const d = await (await fetch("/api/roads")).json();
    if (!d.assessed) return;
    if (roadState.layer) map.removeLayer(roadState.layer);
    roadState.layer = L.layerGroup();
    for (const r of d.assessed) {
      const col = ROAD_COLOR[r.status];
      if (!col) continue;
      L.polyline(r.pts, {
        color: col, weight: 6, opacity: 0.85,
        dashArray: r.status === "podejrzana" ? "10 6" : null,
      }).bindTooltip(
        `${r.name || r.class}<br><b>${r.status.toUpperCase()}</b>`
        + (r.coverage_pct != null ? `<br>zalanie ${Math.round(r.coverage_pct)}%` : ""),
        { direction: "top" }
      ).addTo(roadState.layer);
    }
    roadState.layer.addTo(map);

    const el = document.getElementById("roads-summary");
    if (el) {
      const c = d.counts || {};
      el.innerHTML =
        `<b style="color:${ROAD_COLOR['nieprzejezdna']}">${c["nieprzejezdna"] || 0}</b> ${t("r.impassable")} &middot; `
        + `<b style="color:${ROAD_COLOR['podejrzana']}">${c["podejrzana"] || 0}</b> ${t("r.suspect")} &middot; `
        + `<b style="color:${ROAD_COLOR['przejezdna']}">${c["przejezdna"] || 0}</b> ${t("r.passable")}<br>`
        + `<span class="hint">${c["nieznana"] || 0} ${t("r.note")}</span>`;
    }
    const list = document.getElementById("roads-list");
    if (list) {
      list.innerHTML = (d.summary || []).slice(0, 6).map(s =>
        `<div class="road-row ${s.startsWith("NIEPRZEJEZDNA") ? "bad" : "warn"}">${s}</div>`
      ).join("") || `<span class="hint">${t("r.none")}</span>`;
    }
  } catch { /* backend not ready */ }
}

refreshRoads();
setInterval(refreshRoads, 15000);
