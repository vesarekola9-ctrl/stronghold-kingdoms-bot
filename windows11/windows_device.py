"""Windows device adapter for the ORIGINAL ScoutingModule.

This is an implementation of DeviceService's interface, not a new scouting algorithm.
"""
import time
import cv2
import numpy as np
import pyautogui as pg
from pathlib import Path
import pytesseract

pg.FAILSAFE = True
pg.PAUSE = .15

class WindowsDevice:
    def __init__(self, templates, log=print, stop=None, quantity=None):
        self.templates = templates
        self.log = log
        self.stop = stop
        self.quantity = quantity or {}

    def check(self):
        if self.stop is not None and self.stop.is_set():
            raise InterruptedError("Pysäytetty käyttäjän pyynnöstä")

    def take_screenshot(self):
        self.check()
        return cv2.cvtColor(np.asarray(pg.screenshot()), cv2.COLOR_RGB2BGR)

    def tap(self, x, y):
        self.check()
        pg.click(int(x), int(y))

    def click_coordinates_and_sleep(self, coords, delay=1):
        self.tap(coords["x"], coords["y"])
        self.sleep(delay)

    def sleep(self, delay):
        self.check()
        if self.stop is not None:
            if self.stop.wait(delay):
                self.check()
        else:
            time.sleep(delay)

    def match(self, name, threshold=None):
        self.check()
        template = self.templates.get_template(name)
        if not template or template["img"] is None:
            self.log(f"Kuvamalli puuttuu: {name}")
            return False
        image = self.take_screenshot()
        target = template["img"]
        if target.shape[0] > image.shape[0] or target.shape[1] > image.shape[1]:
            return False
        # Same image-template approach as original DeviceService.find_and_click.
        scores = cv2.matchTemplate(image, target, cv2.TM_CCOEFF_NORMED)
        _, score, _, (x,y) = cv2.minMaxLoc(scores)
        minimum = template["threshold"] if threshold is None else threshold
        if score < minimum:
            self.log(f"{name}: ei löytynyt ({score:.2f} < {minimum:.2f})")
            return False
        h,w = target.shape[:2]
        self.tap(x+w//2, y+h//2)
        self.log(f"{name}: klikattu ({score:.2f})")
        return True

    def find_and_click_template(self, name, threshold=None):
        return self.match(name, threshold)

    def find_and_click(self, name, threshold=None):
        # Original module calls GO_BUTTON here. Require one scout BEFORE Go.
        if name == "GO_BUTTON":
            self.verify_one_scout()
        return self.match(name, threshold)

    def verify_one_scout(self):
        # Native Windows game uses a slider, NOT a text input.
        slider_min = self.quantity.get("field")
        region = self.quantity.get("region")
        if not slider_min or not region:
            raise RuntimeError("Kalibroi liukusäätimen vasen pää ja numeron OCR-alue.")
        # Clicking the minimum position may select 1, but only OCR can approve.
        self.tap(*slider_min)
        self.sleep(.6)
        x1,y1,x2,y2 = region
        shot = self.take_screenshot()[y1:y2,x1:x2]
        if shot.size == 0:
            raise RuntimeError("Virheellinen numeron OCR-alue.")
        gray = cv2.cvtColor(shot, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
        _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        readings = []
        for sample in (gray, bw, 255-bw):
            readings.append(pytesseract.image_to_string(
                sample, config="--psm 7 -c tessedit_char_whitelist=0123456789"
            ).strip())
        if readings.count("1") < 2:
            raise RuntimeError(f"Scout-määrä ei vahvistunut yhdeksi: {readings!r}. Go estetty.")
        self.log("Scout-määrä vahvistettu OCR:llä: 1")

    def get_text_from_coords(self, a, b):
        image = self.take_screenshot()[a["y"]:b["y"],a["x"]:b["x"]]
        return pytesseract.image_to_string(image, config="--psm 6").strip()

    def click_filter_button(self, text):
        # Original filter OCR coordinate mapping; keep it in the template service.
        for i in range(1,8):
            bounds = self.templates.filter_buttons[i]
            detected = self.get_text_from_coords(bounds["top_left"],bounds["right_bottom"])
            if text.lower() in detected.lower():
                self.click_coordinates_and_sleep(bounds["top_left"])
                return True
        raise RuntimeError(f"Suodatinta {text} ei löydy. Avaa oikea näkymä ja tarkista resoluutio.")
