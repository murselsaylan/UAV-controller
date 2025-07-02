import os
import json
import math

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IHAS_PATH = os.path.join(BASE_DIR, "ihas.json")
OYUN_ALANI_PATH = os.path.join(BASE_DIR, "oyun_alani.json")

def yukseklik_kontrol(iha, min_z=30, max_z=120):
    if "z" in iha:
        if iha["z"] < min_z:
            iha["z"] = min_z
        elif iha["z"] > max_z:
            iha["z"] = max_z
    return iha

def oyun_alani_cek():
    with open(OYUN_ALANI_PATH) as f:
        data = json.load(f)
    return data["alan"]

def nokta_polygon_icinde_mi(x, y, polygon):
    n = len(polygon)
    inside = False
    p1x, p1y = polygon[0]
    for i in range(n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def oyun_alani_icinde_mi(iha):
    oyun_alani = oyun_alani_cek()
    return nokta_polygon_icinde_mi(iha["x"], iha["y"], oyun_alani)

def takip_ediliyor_mu(iha, diger_ihalar, mesafe_esik=50):
    for diger in diger_ihalar:
        if diger["id"] != iha["id"]:
            mesafe = math.sqrt((iha["x"] - diger["x"]) ** 2 + (iha["y"] - diger["y"]) ** 2)
            if mesafe < mesafe_esik:
                return True
    return False

def en_yakin_guvenli_nokta(x, y, polygon, adim=5):
    aci_adim = math.pi / 36
    min_dist = float('inf')
    en_yakin = (x, y)
    for r in range(10, 1000, adim):
        for i in range(72):
            aci = i * aci_adim
            nx = x + r * math.cos(aci)
            ny = y + r * math.sin(aci)
            if nokta_polygon_icinde_mi(nx, ny, polygon):
                dist = math.sqrt((nx - x) ** 2 + (ny - y) ** 2)
                if dist < min_dist:
                    min_dist = dist
                    en_yakin = (nx, ny)
    return en_yakin

def tehdit_kontrol():
    try:
        with open(IHAS_PATH) as f:
            ihas = json.load(f)
    except Exception as e:
        print("İHA verileri okunamadı:", e)
        return

    oyun_alani = oyun_alani_cek()
    for iha in ihas:
        iha = yukseklik_kontrol(iha)
        if not oyun_alani_icinde_mi(iha):
            iha["x"], iha["y"] = en_yakin_guvenli_nokta(iha["x"], iha["y"], oyun_alani)
        if takip_ediliyor_mu(iha, ihas):
            iha["x"], iha["y"] = en_yakin_guvenli_nokta(iha["x"], iha["y"], oyun_alani)

    try:
        with open(IHAS_PATH, "w") as f:
            json.dump(ihas, f, indent=2)
    except Exception as e:
        print("İHA verileri yazılamadı:", e)

if __name__ == "__main__":
    tehdit_kontrol()