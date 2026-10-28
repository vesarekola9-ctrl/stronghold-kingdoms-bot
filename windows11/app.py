"""Windows UI for the original forked ScoutingModule."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import json
import threading
import tkinter as tk
from tkinter import ttk
import cv2
from PIL import Image, ImageTk
from windows_device import WindowsDevice
from stronghold_kingdoms_bot.modules.scouting_module import ScoutingModule
from stronghold_kingdoms_bot.services.template_service import TemplateService

ROOT = Path(__file__).resolve().parent.parent
SETTINGS = Path(__file__).resolve().parent / "windows_settings.json"
try:
    config = json.loads(SETTINGS.read_text(encoding="utf-8"))
except (OSError, ValueError):
    config = {}
stop_event = threading.Event()
root = tk.Tk()
root.title("SHK Scout — alkuperäinen ScoutingModule / Windows 11")
root.geometry("850x650")
mode = None
points = []
image = None
photo = None
scale = 1.0

def log(msg):
    root.after(0, lambda: (output.insert("end", str(msg)+"\n"), output.see("end")))

def save():
    SETTINGS.write_text(json.dumps(config, indent=2), encoding="utf-8")

def capture():
    global image,photo,scale
    import pyautogui as pg
    import numpy as np
    image = cv2.cvtColor(np.asarray(pg.screenshot()),cv2.COLOR_RGB2BGR)
    w,h = image.shape[1],image.shape[0]
    root.update_idletasks()
    scale = min(max(500,canvas.winfo_width())/w,max(300,canvas.winfo_height())/h)
    shown = cv2.resize(image,(round(w*scale),round(h*scale)))
    photo = ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(shown,cv2.COLOR_BGR2RGB)))
    canvas.delete("all")
    canvas.create_image(0,0,image=photo,anchor="nw")

def choose(which):
    global mode,points
    mode=which
    points=[]
    root.iconify()
    root.after(1200,finish_capture)

def finish_capture():
    root.deiconify()
    capture()
    log("Valitse pisteet kuvasta: " + str(mode))

def point(event):
    global mode
    if not mode or image is None:
        return
    x,y=round(event.x/scale),round(event.y/scale)
    if not (0<=x<image.shape[1] and 0<=y<image.shape[0]):
        return
    points.append([x,y])
    if mode=="field":
        config["field"]=points[0]
        save()
        mode=None
        log("Liukusäätimen vasen pää tallennettu.")
    elif mode=="region" and len(points)==2:
        (a,b),(c,d)=points
        config["region"]=[min(a,c),min(b,d),max(a,c),max(b,d)]
        save()
        mode=None
        log("Scout-määrän OCR-alue tallennettu.")

canvas = tk.Canvas(root,bg="#24282f")
canvas.pack(fill="both",expand=True,padx=8,pady=8)
canvas.bind("<Button-1>",point)
bar=ttk.Frame(root)
bar.pack(fill="x")
ttk.Button(bar,text="LIUKUSÄÄTIMEN VASEN PÄÄ",command=lambda:choose("field")).pack(side="left",padx=4)
ttk.Button(bar,text="NUMERON OCR-ALUE",command=lambda:choose("region")).pack(side="left",padx=4)
ttk.Button(bar,text="KUVAKAAPPAUS",command=lambda:choose("preview")).pack(side="left",padx=4)
output=tk.Text(root,height=12)
output.pack(fill="x",padx=8,pady=6)
number=ttk.Entry(root,width=4)
number.insert(0,"1")
ttk.Label(root,text="Kyliä (alkuperäinen koodi käsittelee yhden kohteen/kylä/kierros):").pack(anchor="w",padx=8)
number.pack(anchor="w",padx=8)

def run(villages):
    try:
        if not config.get("field") or not config.get("region"):
            log("Kalibroi ensin liukusäätimen vasen pää ja numeron OCR-alue.")
            return
        templates=TemplateService(str(ROOT))
        device=WindowsDevice(templates,log,stop_event,config)
        module=ScoutingModule(
            device_service=device,
            config_override={"device_address":"windows","number_of_villages":villages},
            return_home=False
        )
        # Original module owns all scouting decisions and UI flow.
        module.run()
        log("Alkuperäinen scouttausmoduuli suoritti kierroksen.")
    except Exception as exc:
        log("VIRHE: "+repr(exc))
    finally:
        log("Valmis.")

def start():
    if getattr(root,"worker",None) and root.worker.is_alive():
        log("Kierros on jo käynnissä.")
        return
    stop_event.clear()
    root.iconify()
    root.after(1000,launch)

def launch():
    root.worker=threading.Thread(target=run,args=(root.villages,),daemon=True)
    root.worker.start()

def stop():
    stop_event.set()
    log("Pysäytys pyydetty.")

ttk.Button(bar,text="KÄYNNISTÄ ALKUPERÄINEN SCOUTTAUS",command=start).pack(side="left",padx=4)
ttk.Button(bar,text="PYSÄYTÄ",command=stop).pack(side="left",padx=4)
log("Käytössä alkuperäinen ScoutingModule. WindowsDevice korvaa vain ADB-ohjauksen.")
log("HUOM: Alkuperäisen Android-näkymän koordinaatit/suodatin eivät välttämättä vastaa PC-peliä.")
log("Kalibroi määrä. Käynnistä peli oikeaan karttanäkymään ennen aloittamista.")
root.protocol("WM_DELETE_WINDOW",lambda:(stop(),root.destroy()))
root.mainloop()
