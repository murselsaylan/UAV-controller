import os
import json
import random
import math
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SIM_CONFIG_PATH = os.path.join(BASE_DIR, "sim_config.json")

HEDEF_SAYISI = 6
HAVA_SAVUNMA_SAYISI = 2
OYUN_ALANI_YARICAP = 400
KAMIKAZE_SAYISI = 1
SLEEP_TIME = 0.4

WAYPOINTS_DIR = os.path.join(BASE_DIR, "waypoints")
os.makedirs(WAYPOINTS_DIR, exist_ok=True)

IHAS_PATH = os.path.join(BASE_DIR, "ihas.json")
OYUN_ALANI_PATH = os.path.join(BASE_DIR, "oyun_alani.json")

def sim_config_yukle():
    global HEDEF_SAYISI, HAVA_SAVUNMA_SAYISI, KAMIKAZE_SAYISI, OYUN_ALANI_YARICAP, SLEEP_TIME
    if os.path.exists(SIM_CONFIG_PATH):
        with open(SIM_CONFIG_PATH) as f:
            sim_config = json.load(f)
        HEDEF_SAYISI = int(sim_config.get("HEDEF_SAYISI", HEDEF_SAYISI))
        HAVA_SAVUNMA_SAYISI = int(sim_config.get("HAVA_SAVUNMA_SAYISI", HAVA_SAVUNMA_SAYISI))
        KAMIKAZE_SAYISI = int(sim_config.get("KAMIKAZE_SAYISI", KAMIKAZE_SAYISI))
        OYUN_ALANI_YARICAP = int(sim_config.get("OYUN_ALANI_YARICAP", OYUN_ALANI_YARICAP))
        SLEEP_TIME = float(sim_config.get("SLEEP_TIME", SLEEP_TIME))

sim_config_yukle()

def oyun_alani_olustur_cember_polygon(yaricap, merkez, nokta_sayisi=36):
    aci_adim = 2 * math.pi / nokta_sayisi
    return [
        [
            merkez[0] + yaricap * math.cos(i * aci_adim),
            merkez[1] + yaricap * math.sin(i * aci_adim)
        ]
        for i in range(nokta_sayisi)
    ]

def alan_disinda_mi(x, y, havas, min_mesafe):
    for hava in havas:
        hx, hy, cap = hava["x"], hava["y"], hava["cap"]
        if math.sqrt((x - hx)**2 + (y - hy)**2) < cap + min_mesafe:
            return False
    return True

def en_yakin_nokta_hava_disinda(x, y, havas, merkez):
    aci_adim = math.pi / 36
    min_dist = float('inf')
    en_yakin = (x, y)
    for r in range(10, OYUN_ALANI_YARICAP, 5):
        for i in range(72):
            aci = i * aci_adim
            nx = merkez[0] + r * math.cos(aci)
            ny = merkez[1] + r * math.sin(aci)
            if alan_disinda_mi(nx, ny, havas, 5):
                dist = math.sqrt((nx - x)**2 + (ny - y)**2)
                if dist < min_dist:
                    min_dist = dist
                    en_yakin = (nx, ny)
    return en_yakin

def yukari_asagi(z, min_z=30, max_z=120):
    z += random.uniform(-2, 2)
    return max(min_z, min(max_z, z))

def hedefe_ulaştı_mı(iha, hedef, eşik=5):
    dx = hedef["x"] - iha["x"]
    dy = hedef["y"] - iha["y"]
    dz = hedef["z"] - iha["z"]
    mesafe = math.sqrt(dx**2 + dy**2 + dz**2)
    return mesafe < eşik

def waypointe_git(iha, step, hedef, havas):
    dx = hedef["x"] - iha["x"]
    dy = hedef["y"] - iha["y"]
    dz = hedef["z"] - iha["z"]
    mesafe = math.sqrt(dx**2 + dy**2 + dz**2)
    if mesafe == 0:
        return iha
    if mesafe < step:
        iha["x"], iha["y"], iha["z"] = hedef["x"], hedef["y"], hedef["z"]
    else:
        iha["x"] += dx / mesafe * step
        iha["y"] += dy / mesafe * step
        iha["z"] += dz / mesafe * step
    iha["direction"] = math.degrees(math.atan2(dy, dx)) % 360
    # Hava savunma içine girdiyse, güvenli noktaya yeni hedef ata
    if havas:
        for hava in havas:
            hx, hy, cap = hava["x"], hava["y"], hava["cap"]
            if math.sqrt((iha["x"] - hx)**2 + (iha["y"] - hy)**2) < cap:
                safe_x, safe_y = en_yakin_nokta_hava_disinda(iha["x"], iha["y"], havas, (OYUN_ALANI_YARICAP, OYUN_ALANI_YARICAP))
                iha["x"], iha["y"] = safe_x, safe_y
                # Waypoint listesi varsa, bir sonraki waypoint'e geç
                if "wp_index" in iha and "waypoints" in iha:
                    iha["wp_index"] = (iha["wp_index"] + 1) % len(iha["waypoints"])
                break
    return iha

def iha_waypoint_list_gotur(iha, step=5, havas=None):
    wp_path = os.path.join(WAYPOINTS_DIR, f"waypoints_{iha['id']}.json")
    if not os.path.exists(wp_path):
        return iha
    try:
        with open(wp_path) as f:
            wp_list = json.load(f)
        if not wp_list:
            return iha
        if "wp_index" not in iha or not isinstance(iha["wp_index"], int):
            iha["wp_index"] = 0
        hedef = wp_list[iha["wp_index"]]
        # Hedefe ulaştıysa bir sonrakine geç
        if hedefe_ulaştı_mı(iha, hedef):
            iha["wp_index"] += 1
            if iha["wp_index"] >= len(wp_list):
                iha["wp_index"] = 0
            hedef = wp_list[iha["wp_index"]]
        # Waypoint listesi iha'nın içinde tutulursa, güvenli noktaya geçişte kullanılabilir
        iha["waypoints"] = wp_list
        return waypointe_git(iha, step, hedef, havas)
    except Exception as e:
        print(f"{iha['id']} waypoint listesi hatası:", e)
        return iha

def simulasyon_adimi():
    sim_config_yukle()  # Her adımda güncel ayarları yükle
    try:
        with open(IHAS_PATH, "r") as f:
            data = json.load(f)
    except Exception as e:
        print("simülasyon_adimi dosya okuma HATA:", e)
        return

    havas = [iha for iha in data if iha["id"].startswith("hava_")]
    yeni_data = []
    for iha in data:
        yeni_iha = dict(iha)
        # Sadece ilger1 waypoint takip eder
        if iha["id"] == "ilger1":
            yeni_iha = iha_waypoint_list_gotur(yeni_iha, step=5, havas=havas)
            if "z" in yeni_iha:
                yeni_iha["z"] = yukari_asagi(yeni_iha["z"])
        # Hedefler de waypoint takip edebilir
        elif iha["id"].startswith("Hedef"):
            yeni_iha = iha_waypoint_list_gotur(yeni_iha, step=5, havas=havas)
            if "z" in yeni_iha:
                yeni_iha["z"] = yukari_asagi(yeni_iha["z"])
        # Kamikazeler sadece ilk pozisyonunda kalır
        elif iha["id"].startswith("kamik"):
            if "z" in yeni_iha:
                yeni_iha["z"] = yukari_asagi(yeni_iha["z"])
        elif iha["id"].startswith("hava_"):
            pass
        yeni_data.append(yeni_iha)

    try:
        with open(IHAS_PATH, "w") as f:
            json.dump(yeni_data, f, indent=2)
    except Exception as e:
        print("simülasyon_adimi dosya yazma HATA:", e)

def baslangic_verisi_olustur():
    sim_config_yukle()
    merkez = [OYUN_ALANI_YARICAP, OYUN_ALANI_YARICAP]
    polygon = oyun_alani_olustur_cember_polygon(OYUN_ALANI_YARICAP, merkez)
    with open(OYUN_ALANI_PATH, "w") as f:
        json.dump({"alan": polygon}, f, indent=2)

    havas = []
    for i in range(HAVA_SAVUNMA_SAYISI):
        aci = random.uniform(0, 2 * math.pi)
        r = random.uniform(20, OYUN_ALANI_YARICAP - 40)
        havas.append({
            "id": f"hava_{i+1}",
            "x": merkez[0] + r * math.cos(aci),
            "y": merkez[1] + r * math.sin(aci),
            "cap": random.uniform(40, 80)
        })

    hedefler = []
    for i in range(HEDEF_SAYISI):
        while True:
            aci = random.uniform(0, 2 * math.pi)
            r = random.uniform(20, OYUN_ALANI_YARICAP - 20)
            x = merkez[0] + r * math.cos(aci)
            y = merkez[1] + r * math.sin(aci)
            if alan_disinda_mi(x, y, havas, 10):
                break
        hedefler.append({
            "id": f"Hedef{i+1}",
            "x": x,
            "y": y,
            "z": random.uniform(60, 100),
            "speed": random.uniform(5, 15),
            "direction": random.uniform(0, 360)
        })

    kamikler = []
    for i in range(KAMIKAZE_SAYISI):
        while True:
            aci = random.uniform(0, 2 * math.pi)
            r = random.uniform(10, OYUN_ALANI_YARICAP - 10)
            x = merkez[0] + r * math.cos(aci)
            y = merkez[1] + r * math.sin(aci)
            if alan_disinda_mi(x, y, havas, 10):
                break
        kamikler.append({
            "id": f"kamik{i+1}",
            "x": x,
            "y": y,
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

    # Her uçak için otomatik waypoint dosyası oluştur
    for iha in hedefler + ilger:
        waypoints = []
        # 4 köşe ve merkeze giden bir rota örneği
        for j in range(4):
            aci = (j * math.pi / 2)
            r = OYUN_ALANI_YARICAP - 50
            x = merkez[0] + r * math.cos(aci)
            y = merkez[1] + r * math.sin(aci)
            z = iha["z"] if "z" in iha else 50
            waypoints.append({"x": x, "y": y, "z": z})
        waypoints.append({"x": merkez[0], "y": merkez[1], "z": iha["z"] if "z" in iha else 50})
        wp_path = os.path.join(WAYPOINTS_DIR, f"waypoints_{iha['id']}.json")
        with open(wp_path, "w") as f:
            json.dump(waypoints, f, indent=2)
    # Kamikaze için sadece ilk pozisyonunu içeren waypoint dosyası oluştur
    for iha in kamikler:
        waypoints = [{
            "x": iha["x"],
            "y": iha["y"],
            "z": iha["z"]
        }]
        wp_path = os.path.join(WAYPOINTS_DIR, f"waypoints_{iha['id']}.json")
        with open(wp_path, "w") as f:
            json.dump(waypoints, f, indent=2)

def hiz_ayarla(yeni_hiz):
    global SLEEP_TIME
    SLEEP_TIME = max(0.01, float(yeni_hiz))
    # Ayrıca sim_config dosyasını da güncelle
    if os.path.exists(SIM_CONFIG_PATH):
        with open(SIM_CONFIG_PATH) as f:
            sim_config = json.load(f)
    else:
        sim_config = {}
    sim_config["SLEEP_TIME"] = SLEEP_TIME
    with open(SIM_CONFIG_PATH, "w") as f:
        json.dump(sim_config, f, indent=2)

if __name__ == "__main__":
    print("Simülasyon başlatıldı. Çıkmak için Ctrl+C.")
    # baslangic_verisi_olustur() # Sadece ilk başlatmada çağır
    try:
        while True:
            simulasyon_adimi()
            time.sleep(SLEEP_TIME)
    except KeyboardInterrupt:
        print("Simülasyon durduruldu.")