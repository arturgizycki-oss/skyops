"""SkyOps AI video detection with crisis modes.

Loops a video file per active mode (standing in for a drone camera),
runs the mode's AI on each frame and serves annotated MJPEG:

- search: general YOLOv8 - people, vehicles (default)
- fire:   fire/smoke fine-tuned YOLOv8 (tested on real bushfire footage)
- flood:  water segmentation with coverage % (color+texture, no ML)

Falls back gracefully if OpenCV/ultralytics or a video is missing.
"""

import threading
import time
from collections import deque
from pathlib import Path

VIDEO_PATH = Path(__file__).resolve().parent / "sample_video.mp4"
HACK_MODELS = Path(__file__).resolve().parent.parent / "hackathon" / "models"

# Crisis modes: each pairs a video source with a processing profile.
MODES = {
    "search": {"video": VIDEO_PATH, "weights": "yolov8n.pt",
               "conf": 0.4, "flood": False},
    "fire": {"video": HACK_MODELS / "fire_test.mp4",
             "weights": str(HACK_MODELS / "fire_smoke_slim.pt"),
             "conf": 0.3, "flood": False},
    "flood": {"video": HACK_MODELS / "flood_test.mp4",
              "weights": None, "conf": 0.0, "flood": True},
}

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

# flood water color families seen from the air (see hackathon/floodproto.py)
FLOOD_BROWN = ((8, 40, 60), (30, 200, 220))
FLOOD_TEAL = ((35, 15, 90), (100, 140, 255))
FLOOD_ALERT_PCT = 40

BOX_COLOR = (235, 99, 37)     # BGR: SkyOps blue
LABEL_COLOR = (255, 255, 255)
TARGET_FPS = 15
INFER_WIDTH = 640


class VideoDetector:
    """Background thread: decode -> detect -> annotate -> JPEG."""

    def __init__(self) -> None:
        self.latest_jpeg: bytes | None = None
        self.detections: dict[str, int] = {}
        self.alerts: deque = deque(maxlen=100)
        self._alert_cooldown: dict[str, float] = {}
        self._alert_seq = 0
        self.mode = "search"
        self._pending_mode: str | None = None
        self.model = None
        self._models: dict[str, object] = {}
        self.enabled = cv2 is not None and VIDEO_PATH.exists()
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if not self.enabled or self._thread:
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def set_mode(self, mode: str) -> bool:
        cfg = MODES.get(mode)
        if not cfg or not Path(cfg["video"]).exists():
            return False
        with self._lock:
            self._pending_mode = mode
        return True

    def _get_model(self, weights: str):
        if weights not in self._models:
            try:
                self._models[weights] = YOLO(weights) if YOLO else None
            except Exception:
                self._models[weights] = None
        return self._models[weights]

    def _alert(self, label: str, count: int, now: float,
               conf: float | None = None) -> None:
        """Record a detection.

        `conf` is the model's own confidence (0-1) for a classification, or
        None for a measurement like flood coverage, where a percentage of
        ground covered is not the same kind of quantity as a confidence.
        Every alert starts `pending`: the operator confirms or rejects it,
        and only that decision is treated as established fact downstream.
        """
        if now - self._alert_cooldown.get(label, 0) > 10:
            self._alert_cooldown[label] = now
            self._alert_seq += 1
            self.alerts.appendleft({
                "id": self._alert_seq,
                "ts": now,
                "label": label,
                "count": count,
                "conf": round(conf, 3) if conf is not None else None,
                "status": "pending",
            })

    def set_alert_status(self, alert_id: int, status: str) -> bool:
        """Operator adjudicates one alert. Returns False if it is gone."""
        if status not in ("pending", "confirmed", "rejected"):
            return False
        with self._lock:
            for a in self.alerts:
                if a.get("id") == alert_id:
                    a["status"] = status
                    return True
        return False

    def confirmed_labels(self) -> dict[str, str]:
        """label -> worst-case status, for the flight log and the report."""
        out: dict[str, str] = {}
        with self._lock:
            for a in self.alerts:
                st = a.get("status", "pending")
                prev = out.get(a["label"])
                if prev == "confirmed":
                    continue
                if prev is None or st == "confirmed":
                    out[a["label"]] = st
        return out

    def _flood_annotate(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.bitwise_or(
            cv2.inRange(hsv, np.array(FLOOD_BROWN[0]), np.array(FLOOD_BROWN[1])),
            cv2.inRange(hsv, np.array(FLOOD_TEAL[0]), np.array(FLOOD_TEAL[1])))
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        texture = cv2.Laplacian(gray, cv2.CV_16S, ksize=3)
        smooth = (np.abs(texture) < 12).astype(np.uint8) * 255
        smooth = cv2.blur(smooth, (15, 15))
        mask = cv2.bitwise_and(mask, (smooth > 128).astype(np.uint8) * 255)
        kernel = np.ones((9, 9), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        coverage = float(mask.mean() / 255)
        frame[mask > 0] = (frame[mask > 0] * 0.4 +
                           np.array([200, 80, 30]) * 0.6).astype(np.uint8)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)
        big = [c for c in contours if cv2.contourArea(c) > 2000]
        cv2.drawContours(frame, big, -1, (255, 120, 40), 2)
        cv2.putText(frame, f"FLOOD COVERAGE {coverage:.0%}", (16, 34),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2,
                    cv2.LINE_AA)
        return frame, coverage

    def _yolo_annotate(self, frame, model, conf: float):
        """Returns (counts, best_conf_per_label)."""
        counts: dict[str, int] = {}
        best: dict[str, float] = {}
        results = model.predict(frame, imgsz=INFER_WIDTH, conf=conf,
                                verbose=False)
        for box in results[0].boxes:
            x1, y1, x2, y2 = (int(v) for v in box.xyxy[0])
            label = model.names[int(box.cls[0])]
            c = float(box.conf[0])
            counts[label] = counts.get(label, 0) + 1
            best[label] = max(best.get(label, 0.0), c)
            cv2.rectangle(frame, (x1, y1), (x2, y2), BOX_COLOR, 2)
            tag = f"{label} {c:.0%}"
            (tw, th), _ = cv2.getTextSize(tag, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(frame, (x1, y1 - th - 8), (x1 + tw + 6, y1),
                          BOX_COLOR, -1)
            cv2.putText(frame, tag, (x1 + 3, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, LABEL_COLOR, 1,
                        cv2.LINE_AA)
        return counts, best

    def _run(self) -> None:
        cap = None
        model = None
        current: str | None = None
        frame_interval = 1.0 / TARGET_FPS
        while True:
            start = time.monotonic()

            with self._lock:
                pending, self._pending_mode = self._pending_mode, None
            if cap is None or (pending and pending != current):
                current = pending or self.mode
                cfg = MODES[current]
                if cap:
                    cap.release()
                cap = cv2.VideoCapture(str(cfg["video"]))
                model = (self._get_model(cfg["weights"])
                         if cfg["weights"] else None)
                with self._lock:
                    self.mode = current
                    self.model = model
                    self.detections = {}

            cfg = MODES[current]
            ok, frame = cap.read()
            if not ok:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # loop the clip
                continue

            now = time.time()
            counts: dict[str, int] = {}
            if cfg["flood"]:
                frame, coverage = self._flood_annotate(frame)
                counts = {"water %": round(coverage * 100)}
                with self._lock:
                    if coverage * 100 >= FLOOD_ALERT_PCT:
                        self._alert("flood water", round(coverage * 100), now, None)
            elif model is not None:
                counts, best = self._yolo_annotate(frame, model, cfg["conf"])
                with self._lock:
                    prev = self.detections
                    for label, count in counts.items():
                        if count > prev.get(label, 0):
                            self._alert(label, count, now, best.get(label))

            ok, jpeg = cv2.imencode(".jpg", frame,
                                    [cv2.IMWRITE_JPEG_QUALITY, 80])
            if ok:
                with self._lock:
                    self.latest_jpeg = jpeg.tobytes()
                    self.detections = counts

            elapsed = time.monotonic() - start
            time.sleep(max(0.0, frame_interval - elapsed))

    def mjpeg_frames(self):
        """Generator yielding an MJPEG multipart stream."""
        boundary = b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
        while True:
            with self._lock:
                jpeg = self.latest_jpeg
            if jpeg:
                yield boundary + jpeg + b"\r\n"
            time.sleep(1.0 / TARGET_FPS)

    def status(self) -> dict:
        with self._lock:
            return {
                "video": self.enabled,
                "ai": self.model is not None or MODES[self.mode]["flood"],
                "mode": self.mode,
                "detections": dict(self.detections),
            }

    def recent_alerts(self) -> list[dict]:
        with self._lock:
            return list(self.alerts)


detector = VideoDetector()
