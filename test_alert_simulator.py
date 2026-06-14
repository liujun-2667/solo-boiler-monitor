import time
import requests
import random
from datetime import datetime

ENDPOINT = "http://127.0.0.1:8050/api/ingest"
BOILER_ID = "Boiler-1"

BASE_VALUES = {
    "main_steam_temp": 540,
    "main_steam_press": 16.7,
    "main_steam_flow": 720,
    "feedwater_temp": 255,
    "feedwater_flow": 735,
    "exhaust_temp": 135,
    "furnace_press": -60,
    "o2": 4.0,
    "co": 80,
    "nox": 70,
    "so2": 30,
    "dust": 8,
    "coal_feed": 85,
    "primary_air": 450,
    "induced_air": 520,
    "sh1_out_temp": 410,
    "sh2_out_temp": 460,
    "sh3_out_temp": 510,
    "sh4_out_temp": 538,
    "rh1_out_temp": 360,
    "rh2_out_temp": 440,
    "rh3_out_temp": 500,
    "rh4_out_temp": 530,
    "drum_level": 0,
    "fly_ash_carbon": 2.8,
}


def generate_alert_message(tick, alert_type):
    data = dict(BASE_VALUES)
    if alert_type == "nox_high":
        data["nox"] = 150 + random.uniform(0, 50)
    elif alert_type == "so2_high":
        data["so2"] = 80 + random.uniform(0, 40)
    elif alert_type == "co_high":
        data["co"] = 250 + random.uniform(0, 200)
    elif alert_type == "dust_high":
        data["dust"] = 18 + random.uniform(0, 15)
    return data


def run():
    print("Starting alert test simulator...")
    print("Generating high emission values to trigger alerts...")

    alert_sequence = ["nox_high", "so2_high", "co_high", "dust_high"]
    tick = 0

    for i in range(15):
        alert_idx = i % 4
        alert_type = alert_sequence[alert_idx]
        msg = generate_alert_message(tick, alert_type)
        payload = {
            "boiler_id": BOILER_ID,
            "timestamp": datetime.now().isoformat(),
            "data": msg,
        }
        try:
            resp = requests.post(ENDPOINT, json=payload, timeout=2)
            print(f"Tick {i}: {alert_type} - nox={msg['nox']:.1f}, so2={msg['so2']:.1f}, co={msg['co']:.1f}, dust={msg['dust']:.1f} - status={resp.status_code}")
        except Exception as e:
            print(f"Post failed: {e}")
        tick += 1
        time.sleep(3)

    print("\nTest data generation complete. Check the dashboard for alerts!")
    print("The bottom panel should show alert history.")


if __name__ == "__main__":
    run()
