"""SHK Scout Windows 11 — native GUI, calibration, preview and guarded automation."""
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
from scout_engine import ScoutEngine, screenshot, save_state

root = tk.Tk()
root.title("SHK Scout — Windows 11")
root.geometry("1000x780")
engine = ScoutEngine()
status = tk.StringVar(value="Valmis")
live = tk.BooleanVar(value=False)
mode = None
screen = None
scale = 1.0
points = []
photo = None

frame = ttk.Frame(root, padding=8)
frame.pack(fill="x")
ttk.Label(frame, text="SHK Scout — Windows 11", font=("Segoe UI", 16, "bold")).pack(anchor="w")
ttk.Label(frame, text="Rajaa honor-alue ja scout-määrä. Testaa ensin ilman oikeita lähetyksiä.").pack(anchor="w")
bar = ttk.Frame(frame)
bar.pack(fill="x", pady=6)
canvas = tk.Canvas(root, bg="#20242b", height=490, highlightthickness=0)
canvas.pack(fill="both", expand=True, padx=8)
log = tk.Text(root, height=10, state="disabled")
log.pack(fill="x", padx=8, pady=5)

def say(message):
    def append():
        log.config(state="normal")
        log.insert("end", str(message) + "\n")
        log.see("end")
        log.config(state="disabled")
    root.after(0, append)

engine.log = say

def render(image, selection=None):
    global screen, photo, scale, mode
    screen = image.copy()
    h, w = image.shape[:2]
    root.update_idletasks()
    cw, ch = max(450, canvas.winfo_width()), max(350, canvas.winfo_height())
    scale = min(cw/w, ch/h)
    output = cv2.resize(image, (round(w*scale), round(h*scale)))
    if selection and len(selection) > 1:
        ps = [(round(x*scale), round(y*scale)) for x,y in selection]
        cv2.polylines(output, [__import__("numpy").array(ps)], False, (0,255,255), 2)
    photo = ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(output, cv2.COLOR_BGR2RGB)))
    canvas.delete("all")
    canvas.create_image(0, 0, image=photo, anchor="nw")

def begin(which):
    global mode, points
    engine.stop.set()
    points = []
    mode = which
    render(screenshot())
    if which == "honor":
        say("Klikkaa honor-alueen rajapisteet karttakuvasta. Päätä oikealla hiiren painikkeella.")
    elif which == "field":
        say("Klikkaa scout-määrän syöttökentän keskustaa kuvassa.")
    else:
        say("Klikkaa scout-määrän tekstialueen vasen yläkulma ja oikea alakulma.")

def clicked(event):
    global mode
    if mode is None or screen is None:
        return
    x, y = round(event.x/scale), round(event.y/scale)
    if x >= screen.shape[1] or y >= screen.shape[0]:
        return
    points.append([x, y])
    if mode == "field":
        engine.config["quantity_field"] = [x, y]
        save_state(engine.config)
        say(f"Scout-määrän kenttä: ({x},{y})")
        mode = None
    elif mode == "region" and len(points) == 2:
        (a,b),(c,d) = points
        if abs(c-a)<8 or abs(d-b)<8:
            say("OCR-alue on liian pieni.")
        else:
            engine.config["quantity_region"] = [min(a,c),min(b,d),max(a,c),max(b,d)]
            save_state(engine.config)
            say("Scout-määrän OCR-alue tallennettu.")
        mode = None
    else:
        render(screen, points)

def finish(event=None):
    global mode
    if mode != "honor":
        return
    if len(points) < 3:
        say("Honor-alue vaatii vähintään kolme pistettä.")
        return
    engine.config["honor_polygon"] = points.copy()
    save_state(engine.config)
    mode = None
    say(f"Honor-alue tallennettu: {len(points)} pistettä. Älä siirrä tai zoomaa karttaa.")

canvas.bind("<Button-1>", clicked)
canvas.bind("<Button-3>", finish)

def scan():
    global mode
    mode = None
    try:
        shot = screenshot()
        hits = engine.scan(shot)
        for x,y,name,confidence in hits:
            cv2.circle(shot, (x,y), 18, (0,255,0), 2)
            cv2.putText(shot, name, (x+12,y), cv2.FONT_HERSHEY_SIMPLEX, .45, (0,255,0), 1)
        render(shot)
        say(f"Skannaus: {len(hits)} ehdokasta. Tarkista merkinnät ennen lähetystä.")
    except Exception as exc:
        say("Skannausvirhe: " + str(exc))

def start():
    if getattr(engine, "thread", None) and engine.thread.is_alive():
        say("Scouttaus on jo käynnissä.")
        return
    if live.get() and not messagebox.askyesno("Oikeat lähetykset", "Lähetetään oikeita scoutteja?\nOhjelma pysähtyy, jos määrää 1 ei voida vahvistaa."):
        return
    engine.visited.clear()
    engine.thread = threading.Thread(target=engine.run, kwargs={"live": live.get(), "delay": 10}, daemon=True)
    engine.thread.start()

def stop():
    engine.stop.set()
    say("Pysäytys pyydetty. Hiiri vasempaan yläkulmaan = hätäpysäytys.")

for title,callback in [
    ("1. RAJAA HONOR",lambda:begin("honor")),
    ("2. SCOUT-MÄÄRÄN KENTTÄ",lambda:begin("field")),
    ("3. SCOUT-MÄÄRÄN OCR",lambda:begin("region")),
    ("SKANNAA",scan),
    ("ALOITA",start),
    ("PYSÄYTÄ",stop),
]:
    ttk.Button(bar, text=title, command=callback).pack(side="left", padx=2)
ttk.Checkbutton(frame, text="Salli oikeat lähetykset (oletus: EI)", variable=live).pack(anchor="w")
ttk.Label(frame, textvariable=status).pack(anchor="w")
say(f"Ladattu {len(engine.bags)} resurssimallia. Scout/Go-kuvat: {sum(v is not None for v in engine.controls.values())}/3.")
say("Alkuperäisen projektin kuvamallit ovat käytössä. Peli-ikkunan täytyy pysyä samassa paikassa ja zoomissa.")
root.protocol("WM_DELETE_WINDOW", lambda: (stop(), root.destroy()))
root.mainloop()
