import os
import json
import math
import time

# BASE_DIR'i güvenli şekilde ayarla
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IHAS_PATH = os.path.join(BASE_DIR, "ihas.json")
WAYPOINT_PATH = os.path.join(BASE_DIR, "son_waypoint.json")

def waypointe_git(iha, hedef, step=5):
    dx = hedef["x"] - iha["x"]
    dy = hedef["y"] - iha["y"]
    dz = hedef["z"] - iha["z"]
    mesafe = math.sqrt(dx**2 + dy**2 + dz**2)
    if mesafe < step:
        iha["x"], iha["y"], iha["z"] = hedef["x"], hedef["y"], hedef["z"]
    else:
        iha["x"] += dx / mesafe * step
        iha["y"] += dy / mesafe * step
        iha["z"] += dz / mesafe * step
    iha["direction"] = math.degrees(math.atan2(dy, dx)) % 360
    return iha

def yerel_gorev_adimi():
    try:
        with open(IHAS_PATH) as f:
            data = json.load(f)
        with open(WAYPOINT_PATH) as f:
            hedef = json.load(f)
    except Exception as e:
        print("Yerel görev verileri okunamadı:", e)
        return

    # Listenin elemanlarını güncellemek için indeks kullan
    for idx, iha in enumerate(data):
        if iha.get("id", "").startswith("ilger"):
            data[idx] = waypointe_git(iha, hedef)

    try:
        with open(IHAS_PATH, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print("Yerel görev verisi yazılamadı:", e)

def yerel_gorev_dongusu():
    print("Yerel görev kontrolü başlatıldı.")
    while True:
        yerel_gorev_adimi()
        time.sleep(1)