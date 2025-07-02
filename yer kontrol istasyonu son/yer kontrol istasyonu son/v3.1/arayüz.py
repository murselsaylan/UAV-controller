import os
import sys
import json
import math
import cv2
import test1
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QListWidget, QGroupBox, QSpinBox, QDoubleSpinBox, QComboBox,
    QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsLineItem,
    QGraphicsTextItem, QMessageBox, QSizePolicy
)
from PyQt5.QtCore import QTimer, Qt, QPointF
from PyQt5.QtGui import QPen, QBrush, QColor, QPainter, QFont, QPixmap, QImage

import mission_planner
from ucus_modu_utils import ucus_modu_cek, ucus_modu_yaz

# Dosya yolları
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
    return data.get("alan", [])

def son_waypoint_cek():
    try:
        with open(SON_WAYPOINT_PATH) as f:
            return json.load(f)
    except:
        return None

class OyunAlaniGoruntu(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setMinimumSize(420, 420)
        self.setStyleSheet("background-color: #181c20; border: 2px solid #263238;")

    def ciz(self, alan, ilger, hedefler, kamikler, havas, waypoint):
        self.scene.clear()
        if not alan:
            return

        # Oyun alanı sınırları
        poly = [QPointF(x, y) for x, y in alan]
        for i in range(len(poly)):
            line = QGraphicsLineItem(
                poly[i].x(), poly[i].y(),
                poly[(i+1) % len(poly)].x(), poly[(i+1) % len(poly)].y()
            )
            line.setPen(QPen(QColor("#4caf50"), 2))
            self.scene.addItem(line)

        # Hedefler
        for h in hedefler:
            e = QGraphicsEllipseItem(h["x"]-6, h["y"]-6, 12, 12)
            e.setBrush(QBrush(QColor("#b71c1c")))
            self.scene.addItem(e)
            t = QGraphicsTextItem(h["id"])
            t.setDefaultTextColor(QColor("#ff5252"))
            t.setFont(QFont("Consolas", 9, QFont.Bold))
            t.setPos(h["x"]+7, h["y"]-7)
            self.scene.addItem(t)

        # Kamikazeler
        for k in kamikler:
            e = QGraphicsEllipseItem(k["x"]-5, k["y"]-5, 10, 10)
            e.setBrush(QBrush(QColor("#8e24aa")))
            self.scene.addItem(e)
            t = QGraphicsTextItem(k["id"])
            t.setDefaultTextColor(QColor("#ce93d8"))
            t.setFont(QFont("Consolas", 9, QFont.Bold))
            t.setPos(k["x"]+6, k["y"]-6)
            self.scene.addItem(t)

        # Hava savunmaları
        for h in havas:
            cap = h.get("cap", 40)
            c = QGraphicsEllipseItem(h["x"]-cap, h["y"]-cap, cap*2, cap*2)
            c.setPen(QPen(QColor("#1976d2"), 1, Qt.DashLine))
            self.scene.addItem(c)
            dot = QGraphicsEllipseItem(h["x"]-3, h["y"]-3, 6, 6)
            dot.setBrush(QBrush(QColor("#1976d2")))
            self.scene.addItem(dot)
            t = QGraphicsTextItem(h["id"])
            t.setDefaultTextColor(QColor("#90caf9"))
            t.setFont(QFont("Consolas", 9, QFont.Bold))
            t.setPos(h["x"]+cap+2, h["y"]-8)
            self.scene.addItem(t)

        # İHA
        if ilger:
            e = QGraphicsEllipseItem(ilger["x"]-8, ilger["y"]-8, 16, 16)
            e.setBrush(QBrush(QColor("#aeea00")))
            self.scene.addItem(e)
            t = QGraphicsTextItem("İHA")
            t.setDefaultTextColor(QColor("#aeea00"))
            t.setFont(QFont("Consolas", 10, QFont.Bold))
            t.setPos(ilger["x"]+10, ilger["y"]-10)
            self.scene.addItem(t)
            rad = math.radians(ilger.get("direction", 0))
            x2 = ilger["x"] + 25 * math.cos(rad)
            y2 = ilger["y"] + 25 * math.sin(rad)
            ok = QGraphicsLineItem(ilger["x"], ilger["y"], x2, y2)
            ok.setPen(QPen(QColor("#aeea00"), 2))
            self.scene.addItem(ok)

        # Son waypoint
        if waypoint:
            e = QGraphicsEllipseItem(waypoint["x"]-6, waypoint["y"]-6, 12, 12)
            e.setBrush(QBrush(QColor("#ff9800")))
            self.scene.addItem(e)
            t = QGraphicsTextItem("WP")
            t.setDefaultTextColor(QColor("#ff9800"))
            t.setFont(QFont("Consolas", 9, QFont.Bold))
            t.setPos(waypoint["x"]+7, waypoint["y"]-7)
            self.scene.addItem(t)
            if ilger:
                r = QGraphicsLineItem(ilger["x"], ilger["y"], waypoint["x"], waypoint["y"])
                r.setPen(QPen(QColor("#ff9800"), 1, Qt.DashLine))
                self.scene.addItem(r)

        self.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)

class Arayuz(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("İHA Görev Kontrol Paneli")
        self.setMinimumSize(1200, 650)
        self.setStyleSheet("""
            QWidget { background-color: #181c20; color: #e0e0e0; font-family: 'Segoe UI'; }
            QLabel { color: #aeea00; font-weight: bold; }
            QPushButton { background-color: #263238; color: #aeea00; border-radius: 6px; padding: 7px; }
            QPushButton:hover { background-color: #37474f; }
            QLineEdit, QSpinBox, QDoubleSpinBox { background-color: #23272b; color: #e0e0e0; border: 1px solid #37474f; }
            QListWidget { background-color: #23272b; color: #e0e0e0; border: 1px solid #37474f; }
            QGroupBox { border: 2px solid #2e3b4e; border-radius: 8px; margin-top: 10px; }
            QGroupBox:title { subcontrol-origin: margin; left: 10px; }
        """)

        self.init_ui()

        # FPV kamera
        self.cap = cv2.VideoCapture(0)
        self.fpv_timer = QTimer()
        self.fpv_timer.timeout.connect(self.guncelle_fpv)
        self.fpv_timer.start(30)

        # Veri güncelleme
        self.timer = QTimer()
        self.timer.timeout.connect(self.verileri_guncelle)
        self.timer.start(1000)

    def init_ui(self):
        ana = QHBoxLayout()

        # Sol panel
        sol = QVBoxLayout()
        self.ilger_label = QLabel("İHA Bilgisi: x= y= z= hız= açı=")
        sol.addWidget(self.ilger_label)

        sol.addWidget(QLabel("Hedefler"))
        self.hedef_list = QListWidget()
        sol.addWidget(self.hedef_list, 1)

        sol.addWidget(QLabel("Kamikazeler"))
        self.kamik_list = QListWidget()
        sol.addWidget(self.kamik_list, 1)

        sol.addWidget(QLabel("Hava Savunmaları"))
        self.hava_list = QListWidget()
        sol.addWidget(self.hava_list, 1)

        self.mp_status_label = QLabel("Mission Planner: -")
        sol.addWidget(self.mp_status_label)
        sol.addStretch()
        ana.addLayout(sol, 2)

        # Orta panel
        orta = QVBoxLayout()
        orta.addWidget(QLabel("Oyun Alanı: (oyun_alani.json)"))

        self.oyun_alani_goruntu = OyunAlaniGoruntu()
        orta.addWidget(self.oyun_alani_goruntu, 5)

        fpv_box = QGroupBox("FPV Kamera Görüntüsü")
        v = QVBoxLayout()
        v.setContentsMargins(0,0,0,0)
        self.fpv_label = QLabel("FPV Görüntüsü Buraya Gelecek")
        self.fpv_label.setStyleSheet("background-color: black;")
        self.fpv_label.setAlignment(Qt.AlignCenter)
        v.addWidget(self.fpv_label)
        fpv_box.setLayout(v)
        orta.addWidget(fpv_box, 5)

        ana.addLayout(orta, 4)

        # Sağ panel
        sag = QVBoxLayout()

        # Manuel Waypoint
        sag.addWidget(QLabel("Manuel Waypoint Gönder"))
        self.x_input = QLineEdit(); self.x_input.setPlaceholderText("X")
        self.y_input = QLineEdit(); self.y_input.setPlaceholderText("Y")
        self.z_input = QLineEdit(); self.z_input.setPlaceholderText("Z")
        self.delay_input = QSpinBox(); self.delay_input.setRange(0,60); self.delay_input.setValue(5)
        sag.addWidget(self.x_input)
        sag.addWidget(self.y_input)
        sag.addWidget(self.z_input)
        sag.addWidget(QLabel("Gecikme (sn):"))
        sag.addWidget(self.delay_input)
        btn_sim_wp = QPushButton("Simülasyona Waypoint Gönder")
        btn_sim_wp.clicked.connect(self.sim_waypoint_gonder)
        sag.addWidget(btn_sim_wp)
        btn_mp_wp = QPushButton("Mission Planner'a Waypoint Gönder")
        btn_mp_wp.clicked.connect(self.mp_wp_gonder)
        sag.addWidget(btn_mp_wp)

        # Temel Uçuş Komutları
        flight_box = QGroupBox("Temel Uçuş Komutları")
        fb = QVBoxLayout()
        btn_arm = QPushButton("ARM"); btn_arm.clicked.connect(self.cmd_arm)
        btn_disarm = QPushButton("DISARM"); btn_disarm.clicked.connect(self.cmd_disarm)
        btn_fail = QPushButton("Fail-Safe"); btn_fail.clicked.connect(self.cmd_fail_safe)
        fb.addWidget(btn_arm); fb.addWidget(btn_disarm); fb.addWidget(btn_fail)
        # TAKEOFF
        self.takeoff_spin = QDoubleSpinBox(); self.takeoff_spin.setRange(0,1000); self.takeoff_spin.setSuffix(" m")
        btn_takeoff = QPushButton("Takeoff"); btn_takeoff.clicked.connect(self.cmd_takeoff)
        fb.addWidget(self.takeoff_spin); fb.addWidget(btn_takeoff)
        # HIZLAN
        self.speed_spin = QDoubleSpinBox(); self.speed_spin.setRange(0,100); self.speed_spin.setSuffix(" m/s")
        btn_speed = QPushButton("Hızlan"); btn_speed.clicked.connect(self.cmd_speed_up)
        fb.addWidget(self.speed_spin); fb.addWidget(btn_speed)
        flight_box.setLayout(fb)
        sag.addWidget(flight_box)

        # Savaşan İHA Komutları
        sava_box = QGroupBox("Savaşan İHA Komutları")
        sb = QVBoxLayout()
        sb.addWidget(QLabel("Hedef Seç"))
        self.hedef_combo = QComboBox()
        sb.addWidget(self.hedef_combo)
        btn_follow = QPushButton("Hedefi Takip Et"); btn_follow.clicked.connect(self.cmd_follow_target)
        btn_kamikaze = QPushButton("Kamikaze"); btn_kamikaze.clicked.connect(self.cmd_kamikaze)
        btn_patrol = QPushButton("Devriyeye Dön"); btn_patrol.clicked.connect(self.cmd_return_patrol)
        btn_def = QPushButton("Savunma Modu"); btn_def.clicked.connect(self.cmd_activate_defense)
        sb.addWidget(btn_follow); sb.addWidget(btn_kamikaze)
        sb.addWidget(btn_patrol); sb.addWidget(btn_def)
        sava_box.setLayout(sb)
        sag.addWidget(sava_box)

        sag.addStretch()
        ana.addLayout(sag, 2)

        self.setLayout(ana)

    def verileri_guncelle(self):
        try:
            ilger, hedefler, kamikler, havas = veri_cek()
        except:
            return

        # İHA bilgisi
        if ilger:
            self.ilger_label.setText(
                f"İHA: x={ilger['x']:.1f} y={ilger['y']:.1f} z={ilger['z']:.1f} "
                f"hız={ilger['speed']:.1f} açı={ilger['direction']:.1f}"
            )

        # Listeleri doldur
        self.hedef_list.clear()
        for h in hedefler:
            self.hedef_list.addItem(f"{h['id']} x={h['x']:.1f} y={h['y']:.1f} z={h['z']:.1f}")

        self.kamik_list.clear()
        for k in kamikler:
            self.kamik_list.addItem(f"{k['id']} x={k['x']:.1f} y={k['y']:.1f} z={k['z']:.1f}")

        self.hava_list.clear()
        for h in havas:
            self.hava_list.addItem(f"{h['id']} x={h['x']:.1f} y={h['y']:.1f} yarıçap={h.get('cap',0):.1f}")

        # Hedef combo güncelle
        self.hedef_combo.clear()
        for h in hedefler:
            self.hedef_combo.addItem(h["id"])

        # Mission Planner durumu
        try:
            durum = mission_planner.arayuz_durum()
        except:
            durum = "Mission Planner: -"
        self.mp_status_label.setText(durum)

        # Görsel güncelle
        alan = oyun_alani_cek()
        wp = son_waypoint_cek()
        self.oyun_alani_goruntu.ciz(alan, ilger, hedefler, kamikler, havas, wp)

    def guncelle_fpv(self):
        ret, frame = self.cap.read()
        if not ret:
            return
        frame = test1.process_frame(frame)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        qimg = QImage(frame.data, w, h, ch*w, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qimg).scaled(
            self.fpv_label.width(), self.fpv_label.height(), Qt.KeepAspectRatio
        )
        self.fpv_label.setPixmap(pix)

    def sim_waypoint_gonder(self):
        try:
            x = float(self.x_input.text()); y = float(self.y_input.text())
            z = float(self.z_input.text()); delay = int(self.delay_input.value())
            wp = {"x": x, "y": y, "z": z, "delay": delay}
            with open(SON_WAYPOINT_PATH, "w") as f:
                json.dump(wp, f)
            QMessageBox.information(self, "Başarılı", f"Waypoint gönderildi: {wp}")
        except Exception as e:
            QMessageBox.warning(self, "Hatalı giriş", str(e))

    def mp_wp_gonder(self):
        try:
            x = float(self.x_input.text()); y = float(self.y_input.text())
            z = float(self.z_input.text()); delay = int(self.delay_input.value())
            mission_planner.arayuz_rota_gonder(x, y, z, delay)
            QMessageBox.information(self, "Başarılı", "Waypoin gönderildi.")
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))

    # --- Slot metodları ---
    def cmd_arm(self):
        QMessageBox.information(self, "Komut", "ARM komutu tetiklendi.")
    def cmd_disarm(self):
        QMessageBox.information(self, "Komut", "DISARM komutu tetiklendi.")
    def cmd_fail_safe(self):
        QMessageBox.information(self, "Komut", "Fail-Safe modu aktifleştirildi.")
    def cmd_takeoff(self):
        alt = self.takeoff_spin.value()
        QMessageBox.information(self, "Komut", f"Takeoff tetiklendi: {alt} m")
    def cmd_speed_up(self):
        sp = self.speed_spin.value()
        QMessageBox.information(self, "Komut", f"Hızlan tetiklendi: +{sp} m/s")

    # --- Uçuş Modu Güncelleyen Slotlar ---
    def cmd_follow_target(self):
        tgt = self.hedef_combo.currentText()
        ucus_modu_yaz(
            "takip",
            hedef_id=tgt,
            devriye_merkez=None,
            devriye_cap=None,
            inis_nokta=None,
            kalkis_yukseklik=None
        )
        QMessageBox.information(self, "Komut", f"Hedefi takip et: {tgt}")

    def cmd_kamikaze(self):
        tgt = self.hedef_combo.currentText()
        ucus_modu_yaz(
            "kamikaze",
            hedef_id=tgt,
            devriye_merkez=None,
            devriye_cap=None,
            inis_nokta=None,
            kalkis_yukseklik=None
        )
        QMessageBox.information(self, "Komut", f"Kamikaze saldırısı: {tgt}")

    def cmd_return_patrol(self):
        # Devriye merkezi ve çapı örnek olarak atanıyor, arayüzden alınabilir
        devriye_merkez = [250, 250]
        devriye_cap = 200
        ucus_modu_yaz(
            "devriye",
            hedef_id=None,
            devriye_merkez=devriye_merkez,
            devriye_cap=devriye_cap,
            inis_nokta=None,
            kalkis_yukseklik=None
        )
        QMessageBox.information(self, "Komut", "Devriyeye dön komutu tetiklendi.")

    def cmd_activate_defense(self):
        ucus_modu_yaz(
            "savunma",
            hedef_id=None,
            devriye_merkez=None,
            devriye_cap=None,
            inis_nokta=None,
            kalkis_yukseklik=None
        )
        QMessageBox.information(self, "Komut", "Savunma modu aktifleştirildi.")

    def mp_baglan(self):
        try:
            ok = mission_planner.arayuz_baglan()
            if ok:
                QMessageBox.information(self, "Bağlantı", "Mission Planner'a bağlanıldı.")
            else:
                QMessageBox.warning(self, "Bağlantı", "Bağlanılamadı!")
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))

    def mp_otomatik_waypoint(self):
        sonuc = mission_planner.arayuz_otomatik_waypoint_gonder()
        QMessageBox.information(self, "Otomatik", sonuc)

    def cikis_yap(self):
        if self.cap:
            self.cap.release()
        QApplication.quit()

    def closeEvent(self, e):
        if self.cap:
            self.cap.release()
        e.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Arayuz()
    win.showMaximized()
    sys.exit(app.exec_())