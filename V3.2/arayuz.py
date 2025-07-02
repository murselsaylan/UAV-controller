import math
import os
import sys
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QGraphicsView, QGraphicsScene, QGraphicsEllipseItem,
    QGraphicsLineItem, QGraphicsTextItem, QFrame, QSplitter, QSizePolicy
)
from PyQt5.QtCore import QTimer, Qt, QPointF
from PyQt5.QtGui import QPen, QBrush, QColor, QFont, QIcon

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "ihas.json")
OYUN_ALANI_PATH = os.path.join(BASE_DIR, "oyun_alani.json")
SON_WAYPOINT_PATH = os.path.join(BASE_DIR, "son_waypoint.json")

def veri_cek():
    try:
        with open(CONFIG_PATH) as f:
            data = json.load(f)
        ilger = next((i for i in data if i["id"].lower().startswith("ilger")), None)
        hedefler = [i for i in data if i["id"].lower().startswith("hedef")]
        kamikler = [i for i in data if i["id"].lower().startswith("kamik")]
        havas = [i for i in data if i["id"].lower().startswith("hava_")]
        return ilger, hedefler, kamikler, havas
    except Exception as e:
        print("veri_cek hata:", e)
        return None, [], [], []

def oyun_alani_cek():
    try:
        with open(OYUN_ALANI_PATH) as f:
            data = json.load(f)
        return data["alan"]
    except Exception as e:
        print("oyun_alani_cek hata:", e)
        return []

def son_waypoint_cek():
    try:
        with open(SON_WAYPOINT_PATH) as f:
            return json.load(f)
    except Exception:
        return None

class Arayuz(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modern İHA Kontrol İstasyonu")
        self.setWindowIcon(QIcon())  # İsterseniz özel bir ikon ekleyin
        self.setStyleSheet("""
            QWidget {
                background-color: #181c20;
                color: #e0e0e0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                font-size: 15px;
                font-weight: 600;
            }
            QPushButton {
                background-color: #263238;
                color: #e0e0e0;
                border-radius: 10px;
                padding: 8px 18px;
                font-size: 14px;
                margin: 4px;
                border: 1px solid #37474f;
            }
            QPushButton:hover {
                background-color: #37474f;
            }
            QListWidget {
                background: #232b2f;
                border-radius: 8px;
                font-size: 13px;
                color: #f1c40f;
            }
            QFrame#statusBar {
                background: #232b2f;
                border-radius: 8px;
                padding: 8px;
                margin-bottom: 8px;
            }
        """)

        ana_layout = QVBoxLayout(self)
        # Üst panel: Durumlar
        self.status_bar = QFrame()
        self.status_bar.setObjectName("statusBar")
        status_layout = QHBoxLayout()
        self.ilger_label = QLabel("İlger: -")
        self.hedef_label = QLabel("Hedefler: -")
        self.kamik_label = QLabel("Kamikazeler: -")
        self.hava_label = QLabel("Hava Savunmalar: -")
        for l in [self.ilger_label, self.hedef_label, self.kamik_label, self.hava_label]:
            l.setStyleSheet("font-size: 15px;")
            status_layout.addWidget(l)
        self.status_bar.setLayout(status_layout)
        ana_layout.addWidget(self.status_bar)

        # Orta panel: Harita ve Kontroller
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background: #263238; }")

        # Harita
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setStyleSheet("background: #1a2327; border: 2px solid #00bfae; border-radius: 10px;")
        self.view.setFixedSize(500, 500)
        self.view.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        splitter.addWidget(self.view)

        # Sağ panel: Kontroller ve Waypointler
        sag_panel = QFrame()
        sag_panel.setStyleSheet("background: #232b2f; border-radius: 10px;")
        sag_layout = QVBoxLayout()
        self.start_btn = QPushButton("Simülasyonu Başlat")
        self.start_btn.clicked.connect(self.simulasyonu_baslat)
        self.stop_btn = QPushButton("Simülasyonu Durdur")
        self.stop_btn.clicked.connect(self.simulasyonu_durdur)
        self.stop_btn.setEnabled(False)
        sag_layout.addWidget(self.start_btn)
        sag_layout.addWidget(self.stop_btn)

        self.wpList = QListWidget()
        sag_layout.addWidget(QLabel("Waypoint Listesi:"))
        sag_layout.addWidget(self.wpList)
        sag_panel.setLayout(sag_layout)
        splitter.addWidget(sag_panel)
        splitter.setSizes([600, 200])
        ana_layout.addWidget(splitter)

        # Alt panel: Bilgi
        self.info_label = QLabel("Modern İHA Kontrol İstasyonu - Durum: Hazır")
        self.info_label.setStyleSheet("font-size: 13px; color: #00bfae; margin-top: 8px;")
        ana_layout.addWidget(self.info_label)

        self.timer = QTimer()
        self.timer.timeout.connect(self.verileri_guncelle)
        self.simulation_running = False

        self.verileri_guncelle()
        self.show()

    def simulasyonu_baslat(self):
        self.simulation_running = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.timer.start(1000)
        self.info_label.setText("Simülasyon çalışıyor...")

    def simulasyonu_durdur(self):
        self.simulation_running = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.timer.stop()
        self.info_label.setText("Simülasyon durduruldu.")

    def verileri_guncelle(self):
        ilger, hedefler, kamikler, havas = veri_cek()
        alan = oyun_alani_cek()
        waypoint = son_waypoint_cek()

        self.ilger_label.setText(f"İlger: {ilger['id'] if ilger else '-'}")
        self.hedef_label.setText(f"Hedefler: {len(hedefler)}")
        self.kamik_label.setText(f"Kamikazeler: {len(kamikler)}")
        self.hava_label.setText(f"Hava Savunmalar: {len(havas)}")

        # Grafik alanı temizle
        self.scene.clear()
        # Oyun alanı çiz
        if alan and isinstance(alan, list):
            polygon = [QPointF(pt[0], pt[1]) for pt in alan]
            for i in range(len(polygon)):
                line = QGraphicsLineItem(
                    polygon[i].x(), polygon[i].y(),
                    polygon[(i+1)%len(polygon)].x(), polygon[(i+1)%len(polygon)].y()
                )
                line.setPen(QPen(QColor("#00bfae"), 3))
                self.scene.addItem(line)
        # Hedefleri çiz
        for hedef in hedefler:
            item = QGraphicsEllipseItem(hedef["x"]-8, hedef["y"]-8, 16, 16)
            item.setBrush(QBrush(QColor("#ff5252")))
            item.setPen(QPen(QColor("#b71c1c"), 2))
            self.scene.addItem(item)
            text = QGraphicsTextItem("H")
            text.setDefaultTextColor(QColor("#ff5252"))
            text.setFont(QFont("Segoe UI", 11, QFont.Bold))
            text.setPos(hedef["x"]-6, hedef["y"]-25)
            self.scene.addItem(text)
        # Kamikazeleri çiz
        for kamik in kamikler:
            item = QGraphicsEllipseItem(kamik["x"]-6, kamik["y"]-6, 12, 12)
            item.setBrush(QBrush(QColor("#f39c12")))
            item.setPen(QPen(QColor("#e67e22"), 2))
            self.scene.addItem(item)
            text = QGraphicsTextItem("K")
            text.setDefaultTextColor(QColor("#f39c12"))
            text.setFont(QFont("Segoe UI", 10, QFont.Bold))
            text.setPos(kamik["x"]-5, kamik["y"]-20)
            self.scene.addItem(text)
        # Hava savunma
        for hava in havas:
            item = QGraphicsEllipseItem(hava["x"]-hava["cap"], hava["y"]-hava["cap"], hava["cap"]*2, hava["cap"]*2)
            item.setBrush(QBrush(QColor(255,255,255,30)))
            item.setPen(QPen(QColor("#00bfae"), 2, Qt.DashLine))
            self.scene.addItem(item)
            nokta = QGraphicsEllipseItem(hava["x"]-3, hava["y"]-3, 6, 6)
            nokta.setBrush(QBrush(QColor("#00bfae")))
            self.scene.addItem(nokta)
            text = QGraphicsTextItem("HV")
            text.setDefaultTextColor(QColor("#00bfae"))
            text.setFont(QFont("Segoe UI", 9, QFont.Bold))
            text.setPos(hava["x"]+hava["cap"]+2, hava["y"]-8)
            self.scene.addItem(text)
        # İlger
        if ilger:
            item = QGraphicsEllipseItem(ilger["x"]-11, ilger["y"]-11, 22, 22)
            item.setBrush(QBrush(QColor("#00e676")))
            item.setPen(QPen(QColor("#00bfae"), 3))
            self.scene.addItem(item)
            text = QGraphicsTextItem("İ")
            text.setDefaultTextColor(QColor("#00e676"))
            text.setFont(QFont("Segoe UI", 13, QFont.Bold))
            text.setPos(ilger["x"]-7, ilger["y"]-28)
            self.scene.addItem(text)
            # Yön oku
            yon = ilger.get("direction", 0)
            uzunluk = 30
            rad = math.radians(yon)
            x2 = ilger["x"] + uzunluk * math.cos(rad)
            y2 = ilger["y"] + uzunluk * math.sin(rad)
            ok = QGraphicsLineItem(ilger["x"], ilger["y"], x2, y2)
            ok.setPen(QPen(QColor("#00e676"), 3))
            self.scene.addItem(ok)

        # Waypointleri göster
        self.wpList.clear()
        if waypoint:
            if isinstance(waypoint, list):
                for wp in waypoint:
                    if isinstance(wp, dict) and "x" in wp and "y" in wp:
                        self.wpList.addItem(f"WP: ({wp['x']}, {wp['y']}, {wp.get('z','-')})")
                        wp_item = QGraphicsEllipseItem(wp["x"]-6, wp["y"]-6, 12, 12)
                        wp_item.setBrush(QBrush(QColor("#f1c40f")))
                        self.scene.addItem(wp_item)
            elif isinstance(waypoint, dict) and "x" in waypoint and "y" in waypoint:
                self.wpList.addItem(f"WP: ({waypoint['x']}, {waypoint['y']}, {waypoint.get('z','-')})")
                wp_item = QGraphicsEllipseItem(waypoint["x"]-6, waypoint["y"]-6, 12, 12)
                wp_item.setBrush(QBrush(QColor("#f1c40f")))
                self.scene.addItem(wp_item)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Arayuz()
    sys.exit(app.exec_())