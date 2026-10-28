"""Detect resource icons using the repository's existing templates/bags PNGs.

The source artwork may not match the small in-game world-map sprites.
Review hits visually before enabling any automation.
"""
from pathlib import Path
import cv2

ROOT = Path(__file__).resolve().parent.parent
RESOURCE_DIR = ROOT / "stronghold_kingdoms_bot" / "templates" / "bags"

def load_templates():
    result = {}
    for path in sorted(RESOURCE_DIR.glob("*.png")):
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is not None and image.size:
            result[path.stem] = image
    return result

def detect(image, threshold=0.84):
    found = []
    for name, template in load_templates().items():
        h, w = template.shape[:2]
        if h > image.shape[0] or w > image.shape[1]:
            continue
        scores = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
        for _ in range(80):
            _, score, _, position = cv2.minMaxLoc(scores)
            if score < threshold:
                break
            x, y = position
            found.append((name, x + w // 2, y + h // 2, round(score, 3)))
            cv2.rectangle(scores, (max(0, x-w//2), max(0, y-h//2)),
                          (min(scores.shape[1]-1, x+w//2),
                           min(scores.shape[0]-1, y+h//2)), -1, -1)
    return found
