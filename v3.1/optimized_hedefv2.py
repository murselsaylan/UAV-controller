import os
import json
import time
import numpy as np

# Verileri kategorilere ayırma
def parametre_alma():
    hedefs, havas, kr, ilger = [], [], [], []
    # Dosya yolu: script hangi klasörden çalıştırılırsa çalıştırılsın doğru bulsun
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ihas_path = os.path.join(base_dir, "ihas.json")
    with open(ihas_path) as file:
        datas = json.load(file)
    for data in datas:
        ids = data["id"][:5]
        if ids == "Hedef":
            hedefs.append(data)
        elif ids == "hava_":
            havas.append(data)
        elif ids == "kamik":
            kr.append(data)
        elif ids == "ilger":
            ilger.append(data)
    return hedefs, havas, kr, ilger

# Mesafe hesaplama (3D)
def mesafe_3d(x1, y1, z1, x2, y2, z2):
    return ((x1 - x2)**2 + (y1 - y2)**2 + (z1 - z2)**2) ** 0.5

# Uzaklık listesi: her hedefe olan uzaklık
def uzakliklar(hedefs, ilger):
    ilger_pos = (ilger[0]["x"], ilger[0]["y"], ilger[0]["z"])
    return [mesafe_3d(*ilger_pos, h["x"], h["y"], h["z"]) for h in hedefs]

# Hız farkı listesi
def hiz_farklari(hedefs, ilger):
    ilger_hiz = ilger[0]["speed"]
    return [abs(ilger_hiz - h["speed"]) for h in hedefs]

# Açı farkı listesi
def aci_farklari(hedefs, ilger):
    ilger_aci = ilger[0]["direction"]
    return [abs(ilger_aci - h["direction"]) for h in hedefs]

# İki nokta arasında hava savunma engeli var mı?
def rota_hava_savunmadan_geciyor_mu(hedef, havas, ilger):
    ilger_pos = np.array([ilger[0]["x"], ilger[0]["y"]])
    hedef_pos = np.array([hedef["x"], hedef["y"]])
    for hava in havas:
        merkez = np.array([hava["x"], hava["y"]])
        yaricap = hava["cap"]
        fark = hedef_pos - ilger_pos
        norm = np.linalg.norm(fark)
        if norm == 0:
            continue  # Aynı noktadaysa kontrol etme
        t = np.clip(np.dot(merkez - ilger_pos, fark) / norm**2, 0, 1)
        en_yakin_nokta = ilger_pos + t * fark
        mesafe = np.linalg.norm(merkez - en_yakin_nokta)
        if mesafe <= yaricap:
            return True  # Hava savunma alanı kesiliyor
    return False  # Güvenli rota

# En uygun hedefi seçme
def hedef_sec():
    hedefs, havas, _, ilger = parametre_alma()
    if not hedefs or not ilger:
        return None
    uzaklik = uzakliklar(hedefs, ilger)
    hiz_fark = hiz_farklari(hedefs, ilger)
    aci_fark = aci_farklari(hedefs, ilger)
    puanlar = []
    for i, hedef in enumerate(hedefs):
        if rota_hava_savunmadan_geciyor_mu(hedef, havas, ilger):
            continue
        puan = uzaklik[i] * 0.4 + hiz_fark[i] * 0.3 + aci_fark[i] * 0.3
        puanlar.append((puan, hedef))
    if not puanlar:
        return None
    puanlar.sort(key=lambda x: x[0])
    return puanlar[0][1]

# Waypoint üretme (hedefe göre)
def waypoint_olustur(hedef, gecikme=5):
    if hedef is None:
        return None
    return {
        "x": hedef["x"],
        "y": hedef["y"],
        "z": hedef["z"],
        "delay": gecikme
    }

# Ana işlem fonksiyonu
if __name__ == "__main__":
    while True:
        hedef = hedef_sec()
        if hedef:
            wp = waypoint_olustur(hedef)
            print("Waypoint:", wp)
            # Mission Planner'a aktarım burada yapılacak
        else:
            print("Uygun hedef bulunamadı.")
        time.sleep(1)