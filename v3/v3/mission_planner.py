import os
import time
import json
from optimized_hedefv2 import hedef_sec, waypoint_olustur
from tehditler import yukseklik_kontrol, oyun_alani_kontrol, takip_ediliyor_muyuz, en_yakin_nokta_polygon, nokta_polygon_icinde

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OYUN_ALANI_PATH = os.path.join(BASE_DIR, "oyun_alani.json")
SON_WAYPOINT_PATH = os.path.join(BASE_DIR, "son_waypoint.json")

def rota_gonder(waypoint):
    # Oyun alanı kontrolü
    try:
        with open(OYUN_ALANI_PATH) as f:
            alan = json.load(f)["alan"]
        if not nokta_polygon_icinde(waypoint["x"], waypoint["y"], alan):
            print("Waypoint oyun alanı dışında! En yakın noktaya ayarlanıyor.")
            waypoint["x"], waypoint["y"] = en_yakin_nokta_polygon(waypoint["x"], waypoint["y"], alan)
    except Exception as e:
        print("Oyun alanı dosyası okunamadı veya bozuk:", e)
    try:
        with open(SON_WAYPOINT_PATH, "w") as f:
            json.dump(waypoint, f)
        print("Waypoint Mission Planner'a iletildi:", waypoint)
    except Exception as e:
        print("Waypoint dosyası yazılamadı:", e)

def otomatik_mod():
    while True:
        # Güvenlik kontrolleri
        try:
            if not yukseklik_kontrol():
                print("Yükseklik sınırı dışında!")
                time.sleep(1)
                continue
            if not oyun_alani_kontrol():
                print("Oyun alanı dışındasınız!")
                time.sleep(1)
                continue
            if takip_ediliyor_muyuz():
                print("Takip ediliyorsunuz! Rota güncellenmiyor.")
                time.sleep(1)
                continue
        except Exception as e:
            print("Tehdit kontrolünde hata:", e)
            time.sleep(1)
            continue

        try:
            hedef = hedef_sec()
            if hedef:
                wp = waypoint_olustur(hedef)
                rota_gonder(wp)
            else:
                print("Uygun hedef bulunamadı.")
        except Exception as e:
            print("Hedef seçimi veya waypoint oluştururken hata:", e)
        time.sleep(1)

def manuel_mod():
    while True:
        try:
            x = float(input("Manuel X koordinatı: "))
            y = float(input("Manuel Y koordinatı: "))
            z = float(input("Manuel Z koordinatı: "))
            delay = int(input("Gecikme (saniye): "))
            wp = {"x": x, "y": y, "z": z, "delay": delay}
            rota_gonder(wp)
        except Exception as e:
            print("Hatalı giriş:", e)
        time.sleep(1)

if __name__ == "__main__":
    print("Çalışma modu seçin:")
    print("1 - Otomatik (algoritmalar ile)")
    print("2 - Manuel kontrol")
    secim = input("Seçiminiz (1/2): ").strip()
    if secim == "1":
        otomatik_mod()
    elif secim == "2":
        manuel_mod()
    else:
        print("Geçersiz seçim.")