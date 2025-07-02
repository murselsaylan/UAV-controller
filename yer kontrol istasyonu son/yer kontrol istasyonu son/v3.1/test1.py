# test1.py
# -- coding: utf-8 --
import cv2
import numpy as np
from datetime import datetime

def get_limits(color_bgr):
    """
    Verilen BGR rengi için HSV uzayında alt ve üst limitleri hesaplar.
    Genişletilmiş eşikler ile daha fazla ton algılanabilir.
    """
    c = np.uint8([[color_bgr]])
    hsvC = cv2.cvtColor(c, cv2.COLOR_BGR2HSV)
    hue = int(hsvC[0][0][0])

    sat_min, val_min, val_max, delta = 150, 50, 225, 10

    if hue >= 180 - delta:
        lower = np.array([hue - delta, sat_min, val_min], dtype=np.uint8)
        upper = np.array([180,         255,     val_max], dtype=np.uint8)
    elif hue <= 0 + delta:
        lower = np.array([0,           sat_min, val_min], dtype=np.uint8)
        upper = np.array([hue + delta, 255,     val_max], dtype=np.uint8)
    else:
        lower = np.array([hue - delta, sat_min, val_min], dtype=np.uint8)
        upper = np.array([hue + delta, 255,     val_max], dtype=np.uint8)

    return lower, upper

def red_limits():
    """
    Kırmızı için iki genişletilmiş HSV aralığı.
    """
    sat_min, val_min, val_max = 150, 50, 225

    lower1 = np.array([0,   sat_min, val_min], dtype=np.uint8)
    upper1 = np.array([10,  255,     val_max], dtype=np.uint8)
    lower2 = np.array([170, sat_min, val_min], dtype=np.uint8)
    upper2 = np.array([180, 255,     val_max], dtype=np.uint8)

    return (lower1, upper1), (lower2, upper2)

def blue_limits():
    """
    Mavi için genişletilmiş HSV aralığı.
    """
    sat_min, val_min, val_max = 150, 50, 225
    lower = np.array([90,  sat_min, val_min], dtype=np.uint8)
    upper = np.array([135, 255,     val_max], dtype=np.uint8)
    return lower, upper

def is_square_like(approx, tol=0.15):
    """
    Bir konturun kareye ne kadar benzediğini kontrol eder.
    - 4 kenarlı olması
    - kenar uzunluklarının birbirine yakın olması
    - açılarının ~90° olması
    """
    if len(approx) != 4:
        return False

    pts = approx.reshape(4, 2).astype(float)
    center = pts.mean(axis=0)
    angles = np.arctan2(pts[:,1] - center[1], pts[:,0] - center[0])
    idx = np.argsort(angles)
    pts = pts[idx]

    dists = [np.linalg.norm(pts[i] - pts[(i+1) % 4]) for i in range(4)]
    mn, mx = min(dists), max(dists)
    if mx / mn > 1 + tol:
        return False

    for i in range(4):
        p0 = pts[i]
        v1 = pts[(i-1) % 4] - p0
        v2 = pts[(i+1) % 4] - p0
        cos_a = (v1 @ v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        angle = np.degrees(np.arccos(np.clip(cos_a, -1, 1)))
        if abs(angle - 90) > tol * 90:
            return False

    return True

def draw_custom_L_corners(img, x, y, w, h, color=(0,0,255), thickness=4, length=30):
    """
    Her köşede sadece L şeklinde kısa çizgi çizer.
    """
    # Sol üst
    cv2.line(img, (x, y), (x+length, y), color, thickness)
    cv2.line(img, (x, y), (x, y+length), color, thickness)
    # Sağ üst
    cv2.line(img, (x+w, y), (x+w-length, y), color, thickness)
    cv2.line(img, (x+w, y), (x+w, y+length), color, thickness)
    # Sol alt
    cv2.line(img, (x, y+h), (x+length, y+h), color, thickness)
    cv2.line(img, (x, y+h), (x, y+h-length), color, thickness)
    # Sağ alt
    cv2.line(img, (x+w, y+h), (x+w-length, y+h), color, thickness)
    cv2.line(img, (x+w, y+h), (x+w, y+h-length), color, thickness)

def drop_ball(ball_color_to_drop, detected_square_color, x, y):
    """
    Belirtilen renkteki topu bırakma eylemini simüle eder.
    """
    zaman = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if ball_color_to_drop == "blue":
        print(f"[{zaman}] 🎯🔵 Mavi top {x},{y} noktasına bırakılıyor (Tetikleyen: Kırmızı kare).", flush=True)
    else:
        print(f"[{zaman}] 🎯🔴 Kırmızı top {x},{y} noktasına bırakılıyor (Tetikleyen: Mavi kare).", flush=True)

def process_frame(frame):
    """
    Bir BGR frame alır, kırmızı ve mavi kareleri tespit edip:
      - L-corner kutular çizer
      - merkez çizgisi ve noktası ekler
      - drop_ball() ile eylemi tetikler
    Dönen değer: üzerine çizilmiş BGR frame
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    (red_l1, red_u1), (red_l2, red_u2) = red_limits()
    blue_l, blue_u = blue_limits()
    kernel = np.ones((5,5), np.uint8)

    # maskeler
    mask_red  = cv2.bitwise_or(
        cv2.inRange(hsv, red_l1, red_u1),
        cv2.inRange(hsv, red_l2, red_u2)
    )
    mask_blue = cv2.inRange(hsv, blue_l, blue_u)

    # gürültü temizleme
    mask_red  = cv2.morphologyEx(mask_red,  cv2.MORPH_OPEN, kernel)
    mask_blue = cv2.morphologyEx(mask_blue, cv2.MORPH_OPEN, kernel)

    img_center = (frame.shape[1]//2, frame.shape[0]//2)

    def _proc(mask, color_name):
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in cnts:
            if cv2.contourArea(c) < 1000:
                continue
            approx = cv2.approxPolyDP(c, 0.04 * cv2.arcLength(c, True), True)
            if not is_square_like(approx):
                continue
            x, y, w, h = cv2.boundingRect(c)
            cx, cy = x + w//2, y + h//2

            # çizim rengi
            col = (0,0,255) if color_name == 'red' else (255,0,0)
            draw_custom_L_corners(frame, x, y, w, h, color=col, thickness=4, length=35)
            cv2.circle(frame, (cx, cy), 7, (0,255,255), -1)
            cv2.line(frame, img_center, (cx, cy), (0,255,0), 3)

            # top bırakma
            ball = 'blue' if color_name == 'red' else 'red'
            drop_ball(ball, color_name, cx, cy)

    # hem kırmızı hem mavi kareleri işle
    _proc(mask_red,  'red')
    _proc(mask_blue, 'blue')

    return frame
