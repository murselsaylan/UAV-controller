import os
import math
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IHAS_PATH = os.path.join(BASE_DIR, "ihas.json")
OYUN_ALANI_PATH = os.path.join(BASE_DIR, "oyun_alani.json")

# Yükseklik kontrolü
def yukseklik_kontrol(min_alt=30, max_alt=120):
    try:
        with open(IHAS_PATH) as file:
            data = json.load(file)
        ilger = next((iha for iha in data if iha["id"].startswith("ilger")), None)
        if ilger is None:
            return False
        return min_alt <= ilger["z"] <= max_alt
    except Exception as e:
        print("Yükseklik kontrolü hatası:", e)
        return False

# Nokta çokgen içinde mi (ray casting algoritması)
def nokta_polygon_icinde(x, y, polygon):
    inside = False
    n = len(polygon)
    p1x, p1y = polygon[0]
    for i in range(n+1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y)*(p2x - p1x)/(p2y - p1y) + p1x
                    else:
                        xinters = p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

# Oyun alanı kontrolü (nokta çokgen içinde mi)
def oyun_alani_kontrol():
    try:
        with open(IHAS_PATH) as file:
            data = json.load(file)
        ilger = next((iha for iha in data if iha["id"].startswith("ilger")), None)
        if ilger is None:
            return False
        with open(OYUN_ALANI_PATH) as file:
            alan = json.load(file)["alan"]
        return nokta_polygon_icinde(ilger["x"], ilger["y"], alan)
    except Exception as e:
        print("Oyun alanı kontrolü hatası:", e)
        return False

# Bizi takip eden uçak var mı (arkadan yaklaşan ve açısı benzer olan)
def takip_ediliyor_muyuz(acil_aci_farki=40, max_arka_mesafe=100):
    try:
        with open(IHAS_PATH) as file:
            data = json.load(file)
        ilger = next((iha for iha in data if iha["id"].startswith("ilger")), None)
        digerleri = [iha for iha in data if iha["id"].startswith("kamik")]
        if ilger is None:
            return False
        for k in digerleri:
            dx = ilger["x"] - k["x"]
            dy = ilger["y"] - k["y"]
            uzaklik = math.hypot(dx, dy)
            if uzaklik > max_arka_mesafe:
                continue
            # Açı farkını 0-180 aralığına getir
            aci_farki = abs((k["direction"] - ilger["direction"] + 180) % 360 - 180)
            if aci_farki < acil_aci_farki:
                return True  # Bize doğru benzer açıyla yaklaşıyor
        return False
    except Exception as e:
        print("Takip kontrolü hatası:", e)
        return False

# Nokta çokgenin dışındaysa, çokgenin kenarlarına olan en kısa mesafedeki noktayı bul
def en_yakin_nokta_polygon(x, y, polygon):
    min_dist = float('inf')
    closest_point = (x, y)
    n = len(polygon)
    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i+1)%n]
        dx, dy = x2-x1, y2-y1
        if dx == dy == 0:
            px, py = x1, y1
        else:
            t = max(0, min(1, ((x-x1)*dx + (y-y1)*dy)/(dx*dx+dy*dy)))
            px, py = x1 + t*dx, y1 + t*dy
        dist = math.hypot(x-px, y-py)
        if dist < min_dist:
            min_dist = dist
            closest_point = (px, py)
    return closest_point