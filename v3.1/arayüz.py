import os
import sys
import json
import math
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QListWidget, QGroupBox, QFormLayout, QSpinBox, QDoubleSpinBox,
    QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsTextItem, QMessageBox
)
from PyQt5.QtCore import QTimer, Qt, QPointF
from PyQt5.QtGui import QPen, QBrush, QColor, QPainter, QFont

# Mission Planner fonksiyonlarını içe aktar
import mission_planner

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "ihas.json")
SIM_CONFIG_PATH = os.path.join(BASE_DIR, "sim_config.json")
OYUN_ALANI_PATH = os.path.join(BASE_DIR, "oyun_alani.json")
SON_WAYPOINT_PATH = os.path.join(BASE_DIR, "son_waypoint.json")

def veri_cek():
    with open(CONFIG_PATH) as f:
        data = json.load(f)
    ilger = next((i for i in data if i["id"].startswith("ilger")), None)
    hedefler = [i for i in data if i["id"].startswith("Hedef")]
    kamikler = [i for i in data if i["id"].startswith("kamik")]
    havas = [i for i in data if i["id"].startswith("hava_")]
    return ilger, hedefler, kamikler, havas

def oyun_alani_cek():
    with open(OYUN_ALANI_PATH) as f:
        data = json.load(f)
    return data["alan"]

def son_waypoint_cek():
    try:
        with open(SON_WAYPOINT_PATH) as f:
            return json.load(f)
    except Exception:
        return None

class OyunAlaniGoruntu(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setMinimumSize(420, 420)
        self.scale_factor = 1.0
        self.setStyleSheet("background-color: #181c20; border: 2px solid #263238;")

    def ciz(self, alan, ilger, hedefler, kamikler, havas, waypoint):
        self.scene.clear()
        if not alan:
            return

        poly = [QPointF(x, y) for x, y in alan]
        if poly:
            for i in range(len(poly)):
                line = QGraphicsLineItem(
                    poly[i].x(), poly[i].y(),
                    poly[(i+1)%len(poly)].x(), poly[(i+1)%len(poly)].y()
                )
                line.setPen(QPen(QColor("#4caf50"), 2))
                self.scene.addItem(line)

        for h in hedefler:
            item = QGraphicsEllipseItem(h["x"]-6, h["y"]-6, 12, 12)
            item.setBrush(QBrush(QColor("#b71c1c")))
            self.scene.addItem(item)
            text = QGraphicsTextItem(h["id"])
            text.setDefaultTextColor(QColor("#ff5252"))
            text.setFont(QFont("Consolas", 9, QFont.Bold))
            text.setPos(h["x"]+7, h["y"]-7)
            self.scene.addItem(text)

        for k in kamikler:
            item = QGraphicsEllipseItem(k["x"]-5, k["y"]-5, 10, 10)
            item.setBrush(QBrush(QColor("#8e24aa")))
            self.scene.addItem(item)
            text = QGraphicsTextItem(k["id"])
            text.setDefaultTextColor(QColor("#ce93d8"))
            text.setFont(QFont("Consolas", 9, QFont.Bold))
            text.setPos(k["x"]+6, k["y"]-6)
            self.scene.addItem(text)

        for h in havas:
            cap = h.get("cap", 40)
            item = QGraphicsEllipseItem(h["x"]-cap, h["y"]-cap, cap*2, cap*2)
            item.setPen(QPen(QColor("#1976d2"), 1, Qt.DashLine))
            self.scene.addItem(item)
            nokta = QGraphicsEllipseItem(h["x"]-3, h["y"]-3, 6, 6)
            nokta.setBrush(QBrush(QColor("#1976d2")))
            self.scene.addItem(nokta)
            text = QGraphicsTextItem(h["id"])
            text.setDefaultTextColor(QColor("#90caf9"))
            text.setFont(QFont("Consolas", 9, QFont.Bold))
            text.setPos(h["x"]+cap+2, h["y"]-8)
            self.scene.addItem(text)

        if ilger:
            item = QGraphicsEllipseItem(ilger["x"]-8, ilger["y"]-8, 16, 16)
            item.setBrush(QBrush(QColor("#aeea00")))
            self.scene.addItem(item)
            text = QGraphicsTextItem("İHA")
            text.setDefaultTextColor(QColor("#aeea00"))
            text.setFont(QFont("Consolas", 10, QFont.Bold))
            text.setPos(ilger["x"]+10, ilger["y"]-10)
            self.scene.addItem(text)
            yon = ilger.get("direction", 0)
            uzunluk = 25
            rad = math.radians(yon)
            x2 = ilger["x"] + uzunluk * math.cos(rad)
            y2 = ilger["y"] + uzunluk * math.sin(rad)
            ok = QGraphicsLineItem(ilger["x"], ilger["y"], x2, y2)
            ok.setPen(QPen(QColor("#aeea00"), 2))
            self.scene.addItem(ok)

        if waypoint:
            item = QGraphicsEllipseItem(waypoint["x"]-6, waypoint["y"]-6, 12, 12)
            item.setBrush(QBrush(QColor("#ff9800")))
            self.scene.addItem(item)
            text = QGraphicsTextItem("WP")
            text.setDefaultTextColor(QColor("#ff9800"))
            text.setFont(QFont("Consolas", 9, QFont.Bold))
            text.setPos(waypoint["x"]+7, waypoint["y"]-7)
            self.scene.addItem(text)
            if ilger:
                rota = QGraphicsLineItem(ilger["x"], ilger["y"], waypoint["x"], waypoint["y"])
                rota.setPen(QPen(QColor("#ff9800"), 1, Qt.DashLine))
                self.scene.addItem(rota)

        self.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)

class Arayuz(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("İHA Görev Kontrol Paneli")
        self.setMinimumSize(1200, 650)
        self.setStyleSheet("""
            QWidget { background-color: #181c20; color: #e0e0e0; font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; }
            QGroupBox { border: 2px solid #2e3b4e; border-radius: 8px; margin-top: 10px; background-color: #23272b; font-weight: bold; color: #aeea00; }
            QGroupBox:title { subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px; }
            QLabel { color: #aeea00; font-weight: bold; }
            QPushButton { background-color: #263238; color: #aeea00; border: 1px solid #37474f; border-radius: 6px; padding: 7px 12px; font-weight: bold; }
            QPushButton:hover { background-color: #37474f; }
            QLineEdit, QSpinBox, QDoubleSpinBox { background-color: #23272b; color: #e0e0e0; border: 1px solid #37474f; border-radius: 4px; padding: 4px; }
            QListWidget { background-color: #23272b; color: #e0e0e0; border: 1px solid #37474f; border-radius: 4px; }
        """)
        self.init_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.verileri_guncelle)
        self.timer.start(1000)
        self.puan_agirliklari = {"mesafe": 0.4, "hiz": 0.3, "aci": 0.3}

    def init_ui(self):
        ana_layout = QHBoxLayout()

        # Sol panel: Durumlar ve Mission Planner
        sol_panel = QVBoxLayout()
        self.ilger_label = QLabel("İHA Bilgisi: ")
        self.ilger_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        sol_panel.addWidget(self.ilger_label)

        self.hedef_list = QListWidget()
        sol_panel.addWidget(QLabel("Hedefler"))
        sol_panel.addWidget(self.hedef_list, 1)

        self.kamik_list = QListWidget()
        sol_panel.addWidget(QLabel("Kamikazeler"))
        sol_panel.addWidget(self.kamik_list, 1)

        self.hava_list = QListWidget()
        sol_panel.addWidget(QLabel("Hava Savunmaları"))
        sol_panel.addWidget(self.hava_list, 1)

        # Mission Planner bağlantı durumu ve butonları
        self.mp_status_label = QLabel("Mission Planner: -")
        sol_panel.addWidget(self.mp_status_label)
        self.mp_baglan_btn = QPushButton("Mission Planner'a Bağlan")
        self.mp_baglan_btn.clicked.connect(self.mp_baglan)
        sol_panel.addWidget(self.mp_baglan_btn)
        self.mp_otomatik_btn = QPushButton("Otomatik Waypoint Gönder")
        self.mp_otomatik_btn.clicked.connect(self.mp_otomatik_waypoint)
        sol_panel.addWidget(self.mp_otomatik_btn)

        self.exit_btn = QPushButton("Çıkış")
        self.exit_btn.clicked.connect(self.cikis_yap)
        sol_panel.addWidget(self.exit_btn)

        ana_layout.addLayout(sol_panel, 2)

        # Orta panel: Oyun alanı ve görsel
        orta_panel = QVBoxLayout()
        self.oyun_alani_label = QLabel("Oyun Alanı: (oyun_alani.json)")
        self.oyun_alani_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        orta_panel.addWidget(self.oyun_alani_label)
        self.oyun_alani_goruntu = OyunAlaniGoruntu()
        orta_panel.addWidget(self.oyun_alani_goruntu, 10)

        # Simülasyon parametreleri
        sim_group = QGroupBox("Simülasyon Parametreleri")
        sim_layout = QFormLayout()
        self.hedef_spin = QSpinBox()
        self.hedef_spin.setRange(1, 20)
        self.hedef_spin.setValue(3)
        self.hava_spin = QSpinBox()
        self.hava_spin.setRange(1, 10)
        self.hava_spin.setValue(2)
        self.kamik_spin = QSpinBox()
        self.kamik_spin.setRange(0, 10)
        self.kamik_spin.setValue(1)
        self.alan_spin = QSpinBox()
        self.alan_spin.setRange(100, 2000)
        self.alan_spin.setValue(250)
        self.sleep_spin = QDoubleSpinBox()
        self.sleep_spin.setRange(0.1, 10)
        self.sleep_spin.setSingleStep(0.1)
        self.sleep_spin.setValue(1.0)
        sim_layout.addRow("Hedef Sayısı:", self.hedef_spin)
        sim_layout.addRow("Hava Savunma Sayısı:", self.hava_spin)
        sim_layout.addRow("Kamikaze Sayısı:", self.kamik_spin)
        sim_layout.addRow("Oyun Alanı Yarıçapı:", self.alan_spin)
        sim_layout.addRow("Sleep Time (sn):", self.sleep_spin)
        sim_group.setLayout(sim_layout)
        orta_panel.addWidget(sim_group)

        self.sim_kaydet_btn = QPushButton("Simülasyonu Başlat / Parametreleri Kaydet")
        self.sim_kaydet_btn.clicked.connect(self.simulasyon_parametrelerini_kaydet)
        orta_panel.addWidget(self.sim_kaydet_btn)

        # Puanlama ayarları
        puan_group = QGroupBox("Puanlama Ağırlıkları")
        puan_layout = QFormLayout()
        self.mesafe_spin = QDoubleSpinBox()
        self.mesafe_spin.setRange(0, 1)
        self.mesafe_spin.setSingleStep(0.05)
        self.mesafe_spin.setValue(0.4)
        self.hiz_spin = QDoubleSpinBox()
        self.hiz_spin.setRange(0, 1)
        self.hiz_spin.setSingleStep(0.05)
        self.hiz_spin.setValue(0.3)
        self.aci_spin = QDoubleSpinBox()
        self.aci_spin.setRange(0, 1)
        self.aci_spin.setSingleStep(0.05)
        self.aci_spin.setValue(0.3)
        puan_layout.addRow("Mesafe:", self.mesafe_spin)
        puan_layout.addRow("Hız:", self.hiz_spin)
        puan_layout.addRow("Açı:", self.aci_spin)
        puan_group.setLayout(puan_layout)
        orta_panel.addWidget(puan_group)

        self.puan_kaydet_btn = QPushButton("Ağırlıkları Kaydet")
        self.puan_kaydet_btn.clicked.connect(self.puan_agirliklarini_kaydet)
        orta_panel.addWidget(self.puan_kaydet_btn)

        ana_layout.addLayout(orta_panel, 4)

        # Sağ panel: Manuel waypoint ve Mission Planner
        sag_panel = QVBoxLayout()
        sag_panel.addWidget(QLabel("Manuel Waypoint Gönder"))
        self.x_input = QLineEdit()
        self.x_input.setPlaceholderText("X")
        self.y_input = QLineEdit()
        self.y_input.setPlaceholderText("Y")
        self.z_input = QLineEdit()
        self.z_input.setPlaceholderText("Z")
        self.delay_input = QSpinBox()
        self.delay_input.setRange(0, 60)
        self.delay_input.setValue(5)
        self.waypoint_btn = QPushButton("Simülasyona Waypoint Gönder")
        self.waypoint_btn.clicked.connect(self.sim_waypoint_gonder)
        sag_panel.addWidget(self.x_input)
        sag_panel.addWidget(self.y_input)
        sag_panel.addWidget(self.z_input)
        sag_panel.addWidget(QLabel("Gecikme (sn):"))
        sag_panel.addWidget(self.delay_input)
        sag_panel.addWidget(self.waypoint_btn)

        self.mp_wp_btn = QPushButton("Mission Planner'a Waypoint Gönder")
        self.mp_wp_btn.clicked.connect(self.mp_waypoint_gonder)
        sag_panel.addWidget(self.mp_wp_btn)
        sag_panel.addStretch()
        ana_layout.addLayout(sag_panel, 2)

        self.setLayout(ana_layout)

    def verileri_guncelle(self):
        try:
            ilger, hedefler, kamikler, havas = veri_cek()
        except Exception as e:
            self.ilger_label.setText("Veri okunamadı!")
            self.hedef_list.clear()
            self.kamik_list.clear()
            self.hava_list.clear()
            self.oyun_alani_goruntu.scene.clear()
            return

        if ilger:
            self.ilger_label.setText(
                f"İHA: x={ilger['x']:.1f} y={ilger['y']:.1f} z={ilger['z']:.1f} hız={ilger['speed']:.1f} açı={ilger['direction']:.1f}"
            )
        else:
            self.ilger_label.setText("İHA verisi yok.")

        self.hedef_list.clear()
        for h in hedefler:
            self.hedef_list.addItem(f"{h['id']} x={h['x']:.1f} y={h['y']:.1f} z={h['z']:.1f} hız={h['speed']:.1f} açı={h['direction']:.1f}")

        self.kamik_list.clear()
        for k in kamikler:
            self.kamik_list.addItem(f"{k['id']} x={k['x']:.1f} y={k['y']:.1f} z={k['z']:.1f} hız={k['speed']:.1f} açı={k['direction']:.1f}")

        self.hava_list.clear()
        for h in havas:
            self.hava_list.addItem(f"{h['id']} x={h['x']:.1f} y={h['y']:.1f} yarıçap={h['cap']:.1f}")

        # Mission Planner bağlantı durumu
        try:
            durum = mission_planner.arayuz_durum()
        except Exception:
            durum = "Mission Planner: -"
        self.mp_status_label.setText(durum)

        # Oyun alanı ve waypoint görselini güncelle
        try:
            alan = oyun_alani_cek()
        except Exception:
            alan = []
        waypoint = son_waypoint_cek()
        self.oyun_alani_goruntu.ciz(alan, ilger, hedefler, kamikler, havas, waypoint)

    def puan_agirliklarini_kaydet(self):
        toplam = self.mesafe_spin.value() + self.hiz_spin.value() + self.aci_spin.value()
        if abs(toplam - 1.0) > 0.01:
            QMessageBox.warning(self, "Hata", "Ağırlıkların toplamı 1 olmalı!")
            return
        self.puan_agirliklari = {
            "mesafe": self.mesafe_spin.value(),
            "hiz": self.hiz_spin.value(),
            "aci": self.aci_spin.value()
        }
        QMessageBox.information(self, "Başarılı", "Ağırlıklar kaydedildi.")

    def simulasyon_parametrelerini_kaydet(self):
        sim_config = {
            "HEDEF_SAYISI": self.hedef_spin.value(),
            "HAVA_SAVUNMA_SAYISI": self.hava_spin.value(),
            "KAMIKAZE_SAYISI": self.kamik_spin.value(),
            "OYUN_ALANI_YARICAP": self.alan_spin.value(),
            "SLEEP_TIME": self.sleep_spin.value()
        }
        with open(SIM_CONFIG_PATH, "w") as f:
            json.dump(sim_config, f, indent=2)
        QMessageBox.information(self, "Başarılı", "Simülasyon parametreleri kaydedildi.")

    def sim_waypoint_gonder(self):
        try:
            x = float(self.x_input.text())
            y = float(self.y_input.text())
            z = float(self.z_input.text())
            delay = int(self.delay_input.value())
            wp = {"x": x, "y": y, "z": z, "delay": delay}
            with open(SON_WAYPOINT_PATH, "w") as f:
                json.dump(wp, f)
            QMessageBox.information(self, "Başarılı", f"Simülasyona waypoint gönderildi: {wp}")
        except Exception as e:
            QMessageBox.warning(self, "Hatalı giriş", str(e))

    def mp_waypoint_gonder(self):
        try:
            x = float(self.x_input.text())
            y = float(self.y_input.text())
            z = float(self.z_input.text())
            delay = int(self.delay_input.value())
            mission_planner.arayuz_rota_gonder(x, y, z, delay)
            QMessageBox.information(self, "Başarılı", f"Mission Planner'a waypoint gönderildi: x={x}, y={y}, z={z}")
        except Exception as e:
            QMessageBox.warning(self, "Hatalı giriş", str(e))

    def mp_baglan(self):
        try:
            sonuc = mission_planner.arayuz_baglan()
            if sonuc:
                QMessageBox.information(self, "Bağlantı", "Mission Planner'a başarıyla bağlanıldı.")
            else:
                QMessageBox.warning(self, "Bağlantı", "Mission Planner'a bağlanılamadı!")
        except Exception as e:
            QMessageBox.warning(self, "Bağlantı Hatası", str(e))

    def mp_otomatik_waypoint(self):
        sonuc = mission_planner.arayuz_otomatik_waypoint_gonder()
        QMessageBox.information(self, "Otomatik Waypoint", sonuc)

    def cikis_yap(self):
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    pencere = Arayuz()
    pencere.showMaximized()
    sys.exit(app.exec_())