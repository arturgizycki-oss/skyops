/* Language switch: Polish for the Polish services this is built for,
   English for everyone else. Polish is the default - the operators we
   designed this for work in Polish, and so does the jury.

   Static text is tagged data-i18n in the HTML. Everything drawn from
   live data goes through t(). */

const I18N = {
  pl: {
    "tagline": "Dowodzenie flotą dronów",
    "p.fleet": "Flota",
    "p.mission": "Planowanie misji",
    "p.camera": "Kamera - detekcja AI",
    "p.zones": "Strefy zakazu lotów",
    "p.roads": "Przejezdność dróg",
    "p.hydro": "Wodowskazy IMGW",
    "p.swarm": "Rój przeciwpożarowy",
    "p.logs": "Dziennik lotów",
    "p.nav": "Jakość pozycji",
    "b.navok": "GNSS OK", "b.navdeg": "Zakłócenia", "b.navden": "Brak GNSS",
    "simulated": "SYMULACJA",
    "pos.degraded": "pozycja przyblizona", "pos.denied": "pozycja niepewna",
    "nav.downgraded": "Ustalenia nie zamykają drogi — spadają do „podejrzana”.",
    "nav.note": "Bez pewnej pozycji ustalenia nie zamykają drogi — spadają do „podejrzana”.",

    "b.share": "Podgląd dla sztabu", "b.plan": "Planuj misję",
    "b.launch": "Start", "b.clear": "Wyczyść", "b.hold": "Zawis",
    "b.resume": "Wznów", "b.rtl": "Powrót", "b.area": "Zaznacz obszar",
    "b.areago": "Start floty", "b.zone": "Rysuj strefę", "b.save": "Zapisz",
    "b.cancel": "Anuluj", "b.remove": "usuń", "b.search": "Ludzie", "b.fire": "Pożar",
    "b.flood": "Powódź", "b.placefire": "Wskaż pożar",
    "b.deploy": "Wyślij rój", "b.standdown": "Odwołaj",

    "tag.decision": "decyzja", "tag.public": "dane publiczne",
    "tag.concept": "koncepcja",
    "s.idle": "postój", "s.takeoff": "start", "s.enroute": "w trasie",
    "s.hold": "zawis", "s.rtl": "powrót", "s.landing": "lądowanie",
    "s.connecting": "łączenie",
    "conn.live": "na żywo", "conn.wait": "łączenie...",
    "viewonly": "Tylko podgląd",
    "hint.plan": 'Wybierz drona, naciśnij "Planuj misję", potem klikaj na mapie.',
    "hint.planning": "Klikaj na mapie, aby dodać punkty trasy, potem naciśnij Start.",
    "hint.nozones": "Brak zdefiniowanych stref.",
    "hint.nologs": "Brak lotów.",
    "hint.area": "Klikaj na mapie, aby zaznaczyć obszar.",
    "hint.nodata": "Brak danych.",
    "hint.loading": "Pobieranie danych IMGW...",
    "hint.fire": 'Naciśnij "Wskaż pożar", potem kliknij na mapie.',
    "hint.fireplaced": 'Pożar wskazany. Naciśnij "Wyślij rój".',
    "confirm": "potwierdź", "reject": "odrzuć",
    "hint.rejected": "Misja odrzucona",
    "st.confirmed": "potwierdzone", "st.rejected": "odrzucone",
    "measure": "pomiar", "ago": "temu",
    "r.impassable": "nieprzejezdnych", "r.suspect": "podejrzanych",
    "r.passable": "przejezdnych",
    "r.note": "dróg bez obserwacji — nie raportujemy ich jako przejezdne.",
    "r.none": "Brak obserwacji zalania.",
    "h.gauges": "wodowskazów", "h.alarm": "alarm", "h.warn": "ostrzegawczy",
    "h.age": "dane sprzed", "h.min": "min", "h.normal": "Wszystkie wodowskazy w normie.",
    "h.offline": "Brak połączenia z IMGW — pracujemy na danych z drona.",
    "swarm.note": "Symulacja koncepcyjna. Taka flota nigdzie dziś nie lata.",
    "roads.note": "Wodowskaz podaje POZIOM, nie ZASIĘG. Nie powie, która droga jest pod wodą — to sprawdza dron.",
  },
  en: {
    "tagline": "Drone fleet operations",
    "p.fleet": "Fleet",
    "p.mission": "Mission planning",
    "p.camera": "Camera - AI detection",
    "p.zones": "No-fly zones",
    "p.roads": "Road passability",
    "p.hydro": "IMGW river gauges",
    "p.swarm": "Firefighting swarm",
    "p.logs": "Flight log",
    "p.nav": "Position quality",
    "b.navok": "GNSS OK", "b.navdeg": "Interference", "b.navden": "No GNSS",
    "simulated": "SIMULATED",
    "pos.degraded": "position approximate", "pos.denied": "position unreliable",
    "nav.downgraded": "Findings cannot close a road - they drop to \"suspected\".",
    "nav.note": "Without a reliable position, findings cannot close a road - they drop to \"suspected\".",

    "b.share": "Share view", "b.plan": "Plan mission",
    "b.launch": "Launch", "b.clear": "Clear", "b.hold": "Hold",
    "b.resume": "Resume", "b.rtl": "Return home", "b.area": "Mark area",
    "b.areago": "Launch fleet", "b.zone": "Draw zone", "b.save": "Save",
    "b.cancel": "Cancel", "b.remove": "remove", "b.search": "People", "b.fire": "Fire",
    "b.flood": "Flood", "b.placefire": "Place fire",
    "b.deploy": "Deploy swarm", "b.standdown": "Stand down",

    "tag.decision": "decision", "tag.public": "public data",
    "tag.concept": "concept",
    "s.idle": "idle", "s.takeoff": "takeoff", "s.enroute": "en route",
    "s.hold": "hold", "s.rtl": "returning", "s.landing": "landing",
    "s.connecting": "connecting",
    "conn.live": "live", "conn.wait": "connecting...",
    "viewonly": "View only",
    "hint.plan": 'Select a drone, press "Plan mission", then click the map.',
    "hint.planning": "Click the map to add waypoints, then press Launch.",
    "hint.nozones": "No zones defined.",
    "hint.nologs": "No flights yet.",
    "hint.area": "Click the map to outline an area.",
    "hint.nodata": "No data.",
    "hint.loading": "Loading IMGW data...",
    "hint.fire": 'Press "Place fire", then click the map.',
    "hint.fireplaced": 'Fire placed. Press "Deploy swarm".',
    "confirm": "confirm", "reject": "reject",
    "hint.rejected": "Mission rejected",
    "st.confirmed": "confirmed", "st.rejected": "rejected",
    "measure": "measurement", "ago": "ago",
    "r.impassable": "impassable", "r.suspect": "suspected",
    "r.passable": "passable",
    "r.note": "roads with no observation - never reported as passable.",
    "r.none": "No flood observations.",
    "h.gauges": "gauges", "h.alarm": "alarm", "h.warn": "warning",
    "h.age": "data from", "h.min": "min ago", "h.normal": "All gauges normal.",
    "h.offline": "No connection to IMGW - working from drone data only.",
    "swarm.note": "Simulated concept. No such fleet is fielded anywhere today.",
    "roads.note": "A gauge gives the LEVEL, not the EXTENT. It cannot say which road is under water - the drone does that.",
  },
};

// ?lang=en wins, so a link can carry the language - useful at an
// international event where you hand your phone to a visitor
function initialLang() {
  const q = new URLSearchParams(location.search).get("lang");
  if (q && ["pl", "en"].includes(q.toLowerCase())) return q.toLowerCase();
  try {
    const saved = localStorage.getItem("skyops.lang");
    if (saved && ["pl", "en"].includes(saved)) return saved;
  } catch { /* private mode */ }
  return "pl";
}

let LANG = initialLang();

function t(key) {
  return (I18N[LANG] && I18N[LANG][key]) || (I18N.pl[key]) || key;
}

function applyLang() {
  document.documentElement.lang = LANG;
  document.querySelectorAll("[data-i18n]").forEach(el => {
    el.textContent = t(el.getAttribute("data-i18n"));
  });
  document.querySelectorAll("#lang-switch button").forEach(b => {
    b.classList.toggle("on", b.dataset.lang === LANG);
  });
  // panels that redraw from live data pick the new language up on their
  // next refresh; nudge the ones that only redraw on an event
  if (typeof refreshRoads === "function") refreshRoads();
  if (typeof refreshHydro === "function") refreshHydro();
  if (typeof refreshAlerts === "function") refreshAlerts();
  if (typeof renderFleet === "function") renderFleet();
  if (typeof refreshLogs === "function") refreshLogs();
}

function setLang(code) {
  if (!I18N[code]) return;
  LANG = code;
  try { localStorage.setItem("skyops.lang", code); } catch { /* private mode */ }
  applyLang();
}

document.addEventListener("DOMContentLoaded", () => {
  const sw = document.getElementById("lang-switch");
  if (sw) sw.addEventListener("click", e => {
    const b = e.target.closest("button[data-lang]");
    if (b) setLang(b.dataset.lang);
  });
  applyLang();
});
