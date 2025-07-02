import os
import json

# BASE_DIR'i güvenli şekilde ayarla
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WAYPOINTS_DIR = os.path.join(BASE_DIR, "waypoints")
os.makedirs(WAYPOINTS_DIR, exist_ok=True)

def arayuz_baglan():
    # Simulate connecting to Mission Planner
    print("Mission Planner'a bağlanılıyor...")
    return True

def arayuz_bagli_mi():
    # Simulate checking connection status
    return True

def arayuz_durum():
    # Simulate getting connection status
    return "Mission Planner: Bağlı"

def arayuz_rota_gonder(x, y, z, delay):
    # Simulate sending a waypoint to Mission Planner
    print(f"Mission Planner'a waypoint gönderiliyor: x={x}, y={y}, z={z}, delay={delay}")
    return True

def arayuz_otomatik_waypoint_gonder():
    # Simulate sending automatic waypoints to Mission Planner
    print("Mission Planner'a otomatik waypoint gönderiliyor...")
    return "Otomatik waypoint gönderildi."

def waypoint_kaydet(iha_id, x, y, z):
    wp_path = os.path.join(WAYPOINTS_DIR, f"waypoints_{iha_id}.json")
    waypoints = []
    if os.path.exists(wp_path):
        with open(wp_path) as f:
            waypoints = json.load(f)
    waypoints.append({"x": x, "y": y, "z": z})
    with open(wp_path, "w") as f:
        json.dump(waypoints, f, indent=2)
    print(f"Yerel waypoint kaydedildi: {iha_id} -> x={x}, y={y}, z={z}")

def waypoint_gonder(iha_id, x, y, z):
    if arayuz_bagli_mi():
        arayuz_rota_gonder(x, y, z, 0)
    else:
        waypoint_kaydet(iha_id, x, y, z)

if __name__ == "__main__":
    # Test the functions
    arayuz_baglan()
    print(arayuz_durum())
    waypoint_gonder("ilger1", 100, 200, 50)