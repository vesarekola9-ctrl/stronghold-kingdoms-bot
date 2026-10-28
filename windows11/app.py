"""Windows 11 scouting port — screenshot capture; no Android ADB."""
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import time
import cv2
import numpy as np
import pyautogui as pg

OUT = Path(__file__).resolve().parent / "captures"
OUT.mkdir(exist_ok=True)
pg.FAILSAFE = True

def capture():
    shot = np.array(pg.screenshot().convert("RGB"))
    name = OUT / f"kartta_{time.strftime('%Y%m%d_%H%M%S')}.png"
    cv2.imwrite(str(name), cv2.cvtColor(shot, cv2.COLOR_RGB2BGR))
    messagebox.showinfo("Kartta tallennettu", str(name))

root = tk.Tk()
root.title("Stronghold Kingdoms — Windows 11 (kehitysversio)")
root.geometry("570x240")
ttk.Label(root,text="Stronghold Kingdoms — Windows 11",font=("Segoe UI",16,"bold")).pack(pady=18)
ttk.Label(root,text="Windows-kuvakaappaus ilman Androidia tai ADB:tä.").pack(pady=6)
ttk.Button(root,text="TALLENNA KARTTAKUVAKAAPPAUS",command=capture).pack(pady=12)
ttk.Label(root,text="Automaattinen scouttaus ei vielä sisälly tähän kehitysversioon.").pack(pady=6)
root.mainloop()
