from dronekit import connect, VehicleMode, LocationGlobalRelative, Command
import time
import json

# JSON dosyasından waypointleri oku
with open("son_waypoint.json", "r", encoding="utf-8") as f:
    waypoints = json.load(f)

# Bağlantı (ör: COM6 için)
vehicle = connect('COM6', wait_ready=True, baud=115200)

# Görevleri temizle
cmds = vehicle.commands
cmds.clear()
cmds.wait_ready()

# JSON'dan okunan waypointleri ekle
for wp in waypoints:
    cmd = Command(
        0, 0, 0,
        3,  # MAV_FRAME_GLOBAL_RELATIVE_ALT
        16, # MAV_CMD_NAV_WAYPOINT
        0, 0, 0, 0, 0, 0,
        wp["lat"], wp["lon"], wp["alt"]
    )
    cmds.add(cmd)

cmds.upload()
print("Waypointler başarıyla yüklendi.")

vehicle.close()