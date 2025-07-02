import os
import json
import math
import time

SLEEP_TIME = 1  # veya istediğiniz süre (saniye cinsinden)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IHAS_PATH = os.path.join(BASE_DIR, "ihas.json")
OYUN_ALANI_PATH = os.path.join(BASE_DIR, "oyun_alani.json")

def baslangic_verisi_olustur():
    ihas = [
        {
            "id": "ilger1",
            "x": 100,
            "y": 100,
            "z": 50,
            "speed": 10,
            "direction": 0
        },
        {
            "id": "Hedef1",
            "x": 300,
            "y": 200,
            "z": 50,
            "speed": 5,
            "direction": 90
        },
        {
            "id": "hava_1",
            "x": 200,
            "y": 200,
            "z": 50,
            "cap": 50
        }
    ]
    oyun_alani = {
        "alan": [
            [50, 50],
            [350, 50],
            [350, 350],
            [50, 350]
        ]
    }
    with open(IHAS_PATH, "w") as f:
        json.dump(ihas, f, indent=2)
    with open(OYUN_ALANI_PATH, "w") as f:
        json.dump(oyun_alani, f, indent=2)
    print("Başlangıç verileri oluşturuldu.")

def mesafe_hesapla(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def aci_farki_hesapla(aci1, aci2):
    fark = abs(aci1 - aci2) % 360
    return fark if fark <= 180 else 360 - fark

def hava_savunma_kontrol(x1, y1, x2, y2, havas):
    for hava in havas:
        hx, hy, cap = hava["x"], hava["y"], hava["cap"]
        if mesafe_hesapla(x1, y1, hx, hy) < cap or mesafe_hesapla(x2, y2, hx, hy) < cap:
            return True
    return False

def hedef_puanla(ilger, hedef, havas, agirliklar):
    mesafe = mesafe_hesapla(ilger["x"], ilger["y"], hedef["x"], hedef["y"])
    hiz_farki = abs(ilger.get("speed", 0) - hedef.get("speed", 0))
    aci_farki = aci_farki_hesapla(ilger.get("direction", 0), hedef.get("direction", 0))
    hava_savunma = hava_savunma_kontrol(ilger["x"], ilger["y"], hedef["x"], hedef["y"], havas)

    puan = (
        agirliklar["mesafe"] * (1 / (mesafe + 1)) +
        agirliklar["hiz"] * (1 / (hiz_farki + 1)) +
        agirliklar["aci"] * (1 / (aci_farki + 1))
    )

    if hava_savunma:
        puan *= 0.5

    return puan

def en_iyi_hedef_bul(ilger, hedefler, havas, agirliklar):
    en_iyi_puan = -1
    en_iyi_hedef = None

    for hedef in hedefler:
        puan = hedef_puanla(ilger, hedef, havas, agirliklar)
        if puan > en_iyi_puan:
            en_iyi_puan = puan
            en_iyi_hedef = hedef

    return en_iyi_hedef

def hedef_sec():
    try:
        with open(IHAS_PATH) as f:
            data = json.load(f)
        with open(OYUN_ALANI_PATH) as f:
            oyun_alani = json.load(f)
    except Exception as e:
        print("Veri dosyaları okunamadı:", e)
        return

    ilger = next((i for i in data if i.get("id", "").lower().startswith("ilger")), None)
    hedefler = [i for i in data if i.get("id", "").lower().startswith("hedef")]
    havas = [i for i in data if i.get("id", "").lower().startswith("hava_")]

    agirliklar = {"mesafe": 0.4, "hiz": 0.3, "aci": 0.3}

    if ilger:
        en_iyi_hedef = en_iyi_hedef_bul(ilger, hedefler, havas, agirliklar)
        if en_iyi_hedef:
            print(f"En iyi hedef: {en_iyi_hedef['id']} x={en_iyi_hedef['x']} y={en_iyi_hedef['y']} z={en_iyi_hedef['z']}")
        else:
            print("Uygun hedef bulunamadı.")
    else:
        print("İlger verisi bulunamadı.")

def simulasyon_adimi():
    hedef_sec()

if __name__ == "__main__":
    if not (os.path.exists(IHAS_PATH) and os.path.exists(OYUN_ALANI_PATH)):
        baslangic_verisi_olustur()
    while True:
        simulasyon_adimi()
        time.sleep(1)