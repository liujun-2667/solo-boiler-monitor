import os
os.environ["NO_PROXY"] = "127.0.0.1,localhost"
os.environ["no_proxy"] = "127.0.0.1,localhost"

import requests
import time
from datetime import datetime

session = requests.Session()
session.trust_env = False

url = "http://127.0.0.1:8050/api/ingest"

for i in range(30):
    data = {
        "main_steam_temp": 540, "main_steam_press": 16.7, "main_steam_flow": 720,
        "feedwater_temp": 255, "feedwater_flow": 735, "exhaust_temp": 135,
        "furnace_press": -60, "o2": 4.0,
        "co": 150, "nox": 120, "so2": 60, "dust": 15,
        "coal_feed": 85, "primary_air": 450, "induced_air": 520,
        "sh1_out_temp": 410, "sh2_out_temp": 460, "sh3_out_temp": 510, "sh4_out_temp": 538,
        "rh1_out_temp": 360, "rh2_out_temp": 440, "rh3_out_temp": 500, "rh4_out_temp": 530,
        "drum_level": 0, "fly_ash_carbon": 2.8,
    }
    payload = {"boiler_id": "Boiler-1", "timestamp": datetime.now().isoformat(), "data": data}
    try:
        r = session.post(url, json=payload, timeout=5)
        print(f"Tick {i}: {r.status_code}", flush=True)
    except Exception as e:
        print(f"Tick {i}: {e}", flush=True)
    time.sleep(5)
