"""Windows-native Stronghold Kingdoms scouting engine.

Reuses the fork's bags and general UI templates. Never presses Go unless the
configured quantity region OCR confirms exactly one scout.
"""
from pathlib import Path
import json
import threading
import time
import cv2
import numpy as np
import pyautogui as pg

ROOT = Path(__file__).resolve().parent.parent
BAGS = ROOT / "stronghold_kingdoms_bot" / "templates" / "bags"
GENERAL = ROOT / "stronghold_kingdoms_bot" / "templates" / "general"
STATE = Path(__file__).resolve().parent / "state.json"
pg.FAILSAFE = True
pg.PAUSE = .15


def screenshot():
    return cv2.cvtColor(np.array(pg.screenshot().convert("RGB")), cv2.COLOR_RGB2BGR)


def read_state():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_state(data):
    STATE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_image(path):
    return cv2.imread(str(path), cv2.IMREAD_COLOR)


def matches(screen, template, threshold, limit=35):
    if template is None or min(template.shape[:2]) < 3:
        return []
    h, w = template.shape[:2]
    if h > screen.shape[0] or w > screen.shape[1]:
        return []
    scores = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    hits = []
    for _ in range(limit):
        _, confidence, _, (x, y) = cv2.minMaxLoc(scores)
        if confidence < threshold:
            break
        hits.append((x + w // 2, y + h // 2, float(confidence)))
        cv2.rectangle(scores, (max(0, x-w//2), max(0, y-h//2)),
                      (min(scores.shape[1]-1, x+w//2),
                       min(scores.shape[0]-1, y+h//2)), -1, -1)
    return hits


def in_polygon(x, y, polygon):
    return len(polygon) >= 3 and cv2.pointPolygonTest(
        np.asarray(polygon, dtype=np.int32), (float(x), float(y)), False
    ) >= 0


class ScoutEngine:
    def __init__(self, log=print):
        self.log = log
        self.stop = threading.Event()
        self.config = read_state()
        self.bags = [(p.stem, load_image(p)) for p in sorted(BAGS.glob("*.png"))]
        self.bags = [(n, im) for n, im in self.bags if im is not None]
        self.controls = {
            n: load_image(GENERAL / filename) for n, filename in (
                ("scout", "scout_button.png"),
                ("go", "go_button.png"),
                ("exit", "scout_exit_button.png"))
        }
        self.visited = []

    def scan(self, screen=None):
        screen = screenshot() if screen is None else screen
        polygon = self.config.get("honor_polygon", [])
        if len(polygon) < 3:
            raise RuntimeError("Rajaa ensin honor-alue.")
        candidates = []
        for name, template in self.bags:
            for x, y, score in matches(screen, template, .82):
                if not in_polygon(x, y, polygon):
                    continue
                if any((x-a)**2 + (y-b)**2 < 30**2 for a, b, *_ in candidates):
                    continue
                candidates.append((x, y, name, score))
        return sorted(candidates, key=lambda hit: -hit[3])

    def find_control(self, name, threshold=.79):
        hits = matches(screenshot(), self.controls[name], threshold, limit=1)
        if not hits:
            raise RuntimeError("Painiketta ei löytynyt: " + name)
        return hits[0]

    def click_control(self, name):
        x, y, confidence = self.find_control(name)
        self.log(f"{name}: ({x},{y}) varmuus {confidence:.2f}")
        pg.click(x, y)
        time.sleep(.8)

    def confirm_one(self):
        field = self.config.get("quantity_field")
        region = self.config.get("quantity_region")
        if not field or not region:
            raise RuntimeError("Scout-määrän kenttää ja OCR-aluetta ei ole kalibroitu.")
        pg.click(*field)
        pg.hotkey("ctrl", "a")
        pg.write("1", .15)
        pg.press("tab")
        time.sleep(.5)
        x1, y1, x2, y2 = region
        image = screenshot()
        crop = image[y1:y2, x1:x2]
        if crop.size == 0:
            raise RuntimeError("Scout-määrän OCR-alue on virheellinen.")
        try:
            import pytesseract
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
            raw = pytesseract.image_to_string(
                gray, config="--psm 7 -c tessedit_char_whitelist=0123456789"
            ).strip()
        except Exception as exc:
            raise RuntimeError("Scout-määrän OCR epäonnistui: " + str(exc))
        if raw != "1":
            raise RuntimeError(f"Scout-määrä ei ole vahvistettu yhdeksi (OCR: {raw!r}).")
        self.log("Scout-määrä vahvistettu: 1")

    def dispatch(self, x, y):
        if self.stop.is_set():
            return
        pg.click(x, y)
        time.sleep(.8)
        self.click_control("scout")
        self.confirm_one()
        if self.stop.is_set():
            return
        self.click_control("go")
        try:
            self.click_control("exit")
        except RuntimeError:
            self.log("Sulkemispainiketta ei löytynyt, jatketaan varovasti.")

    def run(self, live=False, delay=10):
        self.stop.clear()
        self.log("Aloitetaan: " + ("oikeat lähetykset" if live else "vain testitila"))
        try:
            if live and not self.config.get("quantity_region"):
                raise RuntimeError("Kalibroi scout-määrän OCR-alue ensin.")
            while not self.stop.is_set():
                targets = self.scan()
                pending = [(x, y, n, c) for x, y, n, c in targets
                           if not any((x-a)**2+(y-b)**2 < 30**2 for a,b in self.visited)]
                if not pending:
                    self.log("Ei uusia tunnistettuja kohteita.")
                    if self.stop.wait(delay):
                        break
                    continue
                for x, y, name, score in pending:
                    if self.stop.is_set():
                        break
                    self.log(f"Kohde: {name} ({x},{y}), varmuus {score:.2f}")
                    if live:
                        self.dispatch(x, y)
                    self.visited.append((x, y))
                    if self.stop.wait(delay):
                        break
                if not live:
                    break
        except Exception as exc:
            self.log("PYSÄYTETTY: " + str(exc))
        finally:
            self.log("Scouttaus päättyi.")
