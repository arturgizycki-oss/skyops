"""Flood-water segmentation prototype (hackathon FLOOD mode).

Muddy flood water from the air is a distinctive low-texture brown; we
segment it with an HSV color window plus morphological cleanup, then
draw the flooded-area outline and coverage percentage. No ML needed -
fast, explainable, and always demoable.

Run:  python floodproto.py   (expects models/flood_test.mp4)
"""

import cv2
import numpy as np

# flood water comes in two color families seen from the air:
# muddy brown-yellow, and green-teal (sediment/algae or reflected sky)
BROWN_LO, BROWN_HI = np.array([8, 40, 60]), np.array([30, 200, 220])
TEAL_LO, TEAL_HI = np.array([35, 15, 90]), np.array([100, 140, 255])


def flood_mask(frame: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.bitwise_or(
        cv2.inRange(hsv, BROWN_LO, BROWN_HI),
        cv2.inRange(hsv, TEAL_LO, TEAL_HI))
    # low texture requirement: water is smooth; drop high-detail areas
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    texture = cv2.Laplacian(gray, cv2.CV_16S, ksize=3)
    smooth = (np.abs(texture) < 12).astype(np.uint8) * 255
    smooth = cv2.blur(smooth, (15, 15))
    mask = cv2.bitwise_and(mask, (smooth > 128).astype(np.uint8) * 255)
    kernel = np.ones((9, 9), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    return mask


def annotate(frame: np.ndarray) -> tuple[np.ndarray, float]:
    mask = flood_mask(frame)
    coverage = float(mask.mean() / 255)
    overlay = frame.copy()
    overlay[mask > 0] = (overlay[mask > 0] * 0.4 +
                         np.array([200, 80, 30]) * 0.6).astype(np.uint8)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
    big = [c for c in contours if cv2.contourArea(c) > 2000]
    cv2.drawContours(overlay, big, -1, (255, 120, 40), 2)
    cv2.putText(overlay, f"FLOOD COVERAGE {coverage:.0%}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
    return overlay, coverage


if __name__ == "__main__":
    cap = cv2.VideoCapture("models/flood_test.mp4")
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    coverages = []
    for i, idx in enumerate(range(0, total, max(1, total // 8))):
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if not ok:
            continue
        out, cov = annotate(frame)
        coverages.append(cov)
        if i == 2:
            cv2.imwrite("models/flood_result.jpg", out)
    print(f"frames: {len(coverages)}, "
          f"coverage min/avg/max: {min(coverages):.0%}/"
          f"{sum(coverages)/len(coverages):.0%}/{max(coverages):.0%}")
    print("annotated sample: models/flood_result.jpg")
