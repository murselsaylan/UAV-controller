import os
import threading
import time
import sys
from arayuz import Arayuz
from PyQt5.QtWidgets import QApplication
import simülasyon
import local_mission_sim
import mission_planner

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OYUN_ALANI_PATH = os.path.join(BASE_DIR, "oyun_alani.json")
IHAS_PATH = os.path.join(BASE_DIR, "ihas.json")

def simulasyon_thread():
    try:
        while True:
            simülasyon.simulasyon_adimi()
            time.sleep(simülasyon.SLEEP_TIME)
    except KeyboardInterrupt:
        print("Simülasyon durduruldu.")

def yerel_gorev_thread():
    try:
        while True:
            if not mission_planner.arayuz_bagli_mi():
                local_mission_sim.yerel_gorev_adimi()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Yerel görev kontrolü durduruldu.")

if __name__ == "__main__":
    print("Başlangıç verileri oluşturuluyor...")
    try:
        simülasyon.baslangic_verisi_olustur()
    except Exception as e:
        print("Başlangıç verisi oluşturulurken hata:", e)
        sys.exit(1)

    # Oyun alanı ve ihas dosyası oluşana kadar bekle
    for _ in range(50):
        dosyalar_var = os.path.exists(OYUN_ALANI_PATH) and os.path.exists(IHAS_PATH)
        dosyalar_dolu = False
        if dosyalar_var:
            try:
                with open(OYUN_ALANI_PATH) as f:
                    if not f.read().strip():
                        raise Exception("oyun_alani.json boş")
                with open(IHAS_PATH) as f:
                    if not f.read().strip():
                        raise Exception("ihas.json boş")
                dosyalar_dolu = True
            except Exception as e:
                print("Dosya kontrol hatası:", e)
        if dosyalar_var and dosyalar_dolu:
            print("Başlangıç dosyaları hazır.")
            break
        time.sleep(0.1)
    else:
        print("Başlangıç dosyaları oluşturulamadı veya boş!")
        sys.exit(1)

    # Simülasyonu arka planda başlat
    sim_thread = threading.Thread(target=simulasyon_thread, daemon=True)
    sim_thread.start()

    # Yerel görev kontrolünü başlat
    yerel_thread = threading.Thread(target=yerel_gorev_thread, daemon=True)
    yerel_thread.start()

    # Arayüzü başlat (ana thread'de olmalı)
    app = QApplication(sys.argv)
    pencere = Arayuz()
    pencere.show()
    sys.exit(app.exec_())
