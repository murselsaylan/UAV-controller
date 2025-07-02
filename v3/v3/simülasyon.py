import os
import json
import random
import math
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SIM_CONFIG_PATH = os.path.join(BASE_DIR, "sim_config.json")

HEDEF_SAYISI = 6
HAVA_SAVUNMA_SAYISI = 2
OYUN_ALANI_YARICAP = 250
KAMIKAZE_SAYISI = 1
SLEEP_TIME = 1

if os.path.exists(SIM_CONFIG_PATH):
    with open(SIM_CONFIG_PATH) as f:
        sim_config = json.load(f)
    HEDEF_SAYISI = int(sim_config.get("HEDEF_SAYISI", HEDEF_SAYISI))
    HAVA_SAVUNMA_SAYISI = int(sim_config.get("HAVA_SAVUNMA_SAYISI", HAVA_SAVUNMA_SAYISI))
    KAMIKAZE_SAYISI = int(sim_config.get("KAMIKAZE_SAYISI", KAMIKAZE_SAYISI))
    OYUN_ALANI_YARICAP = int(sim_config.get("OYUN_ALANI_YARICAP", OYUN_ALANI_YARICAP))
    SLEEP_TIME = float(sim_config.get("SLEEP_TIME", SLEEP_TIME))

IHAS_PATH = os.path.join(BASE_DIR, "ihas.json")
OYUN_ALANI_PATH = os.path.join(BASE_DIR, "oyun_alani.json")

def oyun_alani_olustur_cember_polygon(yaricap, merkez, nokta_sayisi=36):
    aci_adim = 2 * math.pi / nokta_sayisi
    return [
        [
            merkez[0] + yaricap * math.cos(i * aci_adim),
            merkez[1] + yaricap * math.sin(i * aci_adim)
        ]
        for i in range(nokta_sayisi)
    ]

def baslangic_verisi_olustur():
    try:
        merkez = [OYUN_ALANI_YARICAP, OYUN_ALANI_YARICAP]
        polygon = oyun_alani_olustur_cember_polygon(OYUN_ALANI_YARICAP, merkez)
        with open(OYUN_ALANI_PATH, "w") as f:
            json.dump({"alan": polygon}, f, indent=2)

        hedefler = []
        for i in range(HEDEF_SAYISI):
            aci = random.uniform(0, 2 * math.pi)
            r = random.uniform(20, OYUN_ALANI_YARICAP - 20)
            hedefler.append({
                "id": f"Hedef{i+1}",
                "x": merkez[0] + r * math.cos(aci),
                "y": merkez[1] + r * math.sin(aci),
                "z": random.uniform(60, 100),
                "speed": random.uniform(5, 15),
                "direction": random.uniform(0, 360)
            })

        havas = []
        for i in range(HAVA_SAVUNMA_SAYISI):
            aci = random.uniform(0, 2 * math.pi)
            r = random.uniform(20, OYUN_ALANI_YARICAP - 20)
            havas.append({
                "id": f"hava_{i+1}",
                "x": merkez[0] + r * math.cos(aci),
                "y": merkez[1] + r * math.sin(aci),
                "cap": random.uniform(40, 80)
            })

        kamikler = []
        for i in range(KAMIKAZE_SAYISI):
            aci = random.uniform(0, 2 * math.pi)
            r = random.uniform(10, OYUN_ALANI_YARICAP - 10)
            kamikler.append({
                "id": f"kamik{i+1}",
                "x": merkez[0] + r * math.cos(aci),
                "y": merkez[1] + r * math.sin(aci),
                "z": random.uniform(0, 5),
                "speed": 0,
                "direction": 0
            })

        ilger = [{
            "id": "ilger1",
            "x": merkez[0],
            "y": merkez[1],
            "z": random.uniform(60, 100),
            "speed": random.uniform(10, 20),
            "direction": random.uniform(0, 360)
        }]

        tum_liste = hedefler + havas + kamikler + ilger
        with open(IHAS_PATH, "w") as f:
            json.dump(tum_liste, f, indent=2)
    except Exception as e:
        print("simülasyon.baslangic_verisi_olustur HATA:", e)

def yukari_asagi(z, min_z=30, max_z=120):
    z += random.uniform(-2, 2)
    return max(min_z, min(max_z, z))

def yeni_pozisyon(x, y, speed, direction):
    rad = math.radians(direction)
    x += speed * math.cos(rad) * random.uniform(0.8, 1.2)
    y += speed * math.sin(rad) * random.uniform(0.8, 1.2)
    return x, y

def yeni_acı(direction):
    direction += random.uniform(-5, 5)
    direction = direction % 360
    return direction

def simulasyon_adimi():
    try:
        with open(IHAS_PATH, "r") as f:
            data = json.load(f)
    except Exception as e:
        print("simülasyon_adimi dosya okuma HATA:", e)
        return

    yeni_data = []
    for iha in data:
        yeni_iha = dict(iha)
        if iha["id"].startswith("Hedef") or iha["id"].startswith("ilger"):
            yeni_iha["z"] = yukari_asagi(yeni_iha["z"])
            if "speed" in yeni_iha and "direction" in yeni_iha:
                yeni_iha["direction"] = yeni_acı(yeni_iha["direction"])
                yeni_iha["x"], yeni_iha["y"] = yeni_pozisyon(
                    yeni_iha["x"], yeni_iha["y"], yeni_iha["speed"], yeni_iha["direction"]
                )
        yeni_data.append(yeni_iha)

    try:
        with open(IHAS_PATH, "w") as f:
            json.dump(yeni_data, f, indent=2)
    except Exception as e:
        print("simülasyon_adimi dosya yazma HATA:", e)

if __name__ == "__main__":
    print("Simülasyon başlatıldı. Çıkmak için Ctrl+C.")
    baslangic_verisi_olustur()
    try:
        while True:
            simulasyon_adimi()
            time.sleep(SLEEP_TIME)
    except KeyboardInterrupt:
        print("Simülasyon durduruldu.")