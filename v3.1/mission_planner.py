import os
import time
import json
from optimized_hedefv2 import hedef_sec, waypoint_olustur
from tehditler import yukseklik_kontrol, oyun_alani_kontrol, takip_ediliyor_muyuz, en_yakin_nokta_polygon, nokta_polygon_icinde

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OYUN_ALANI_PATH = os.path.join(BASE_DIR, "oyun_alani.json")
SON_WAYPOINT_PATH = os.path.join(BASE_DIR, "son_waypoint.json")

# Mission Planner bağlantı simülasyonu (gerçek bağlantı için pymavlink eklenebilir)
class MissionPlannerBaglanti:
    def __init__(self):
        self.bagli = False

    def baglan(self):
        # Gerçek bağlantı için burada pymavlink ile bağlantı kodu yazılabilir
        # Şimdilik simülasyon
        time.sleep(1)
        self.bagli = True
        print("Mission Planner'a bağlanıldı.")

    def bagli_mi(self):
        return self.bagli

    def rota_gonder(self, waypoint):
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

# Global bağlantı nesnesi
mp_baglanti = MissionPlannerBaglanti()

def arayuz_baglan():
    mp_baglanti.baglan()
    return mp_baglanti.bagli_mi()

def arayuz_bagli_mi():
    return mp_baglanti.bagli_mi()

def arayuz_rota_gonder(x, y, z, delay=0):
    wp = {"x": x, "y": y, "z": z, "delay": delay}
    mp_baglanti.rota_gonder(wp)

def arayuz_otomatik_waypoint_gonder():
    # Tüm kontrolleri arayüzden tetikleyin
    try:
        if not yukseklik_kontrol():
            return "Yükseklik sınırı dışında!"
        if not oyun_alani_kontrol():
            return "Oyun alanı dışındasınız!"
        if takip_ediliyor_muyuz():
            return "Takip ediliyorsunuz! Rota güncellenmiyor."
        hedef = hedef_sec()
        if hedef:
            wp = waypoint_olustur(hedef)
            mp_baglanti.rota_gonder(wp)
            return f"Waypoint gönderildi: {wp}"
        else:
            return "Uygun hedef bulunamadı."
    except Exception as e:
        return f"Hata: {e}"

# Arayüzde göstermek için bağlantı ve durum fonksiyonları
def arayuz_durum():
    if mp_baglanti.bagli_mi():
        return "Mission Planner'a bağlı"
    else:
        return "Mission Planner'a BAĞLI DEĞİL"

# Eski terminal fonksiyonları kaldırıldı, tüm kontrol arayüzden yapılacak

# Arayüzden örnek kullanım:
# arayuz_baglan()
# arayuz_rota_gonder(x, y, z, delay)
# arayuz_otomatik_waypoint_gonder()
# arayuz_bagli_mi() veya arayuz_durum()

if __name__ == "__main__":
    print("Bu dosya doğrudan çalıştırılmamalı. Tüm kontrol arayüzden yapılacak.")