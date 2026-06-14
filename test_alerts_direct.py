import time
import json
import urllib.request
import urllib.error
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


def send_data(data_dict):
    payload = {
        "boiler_id": BOILER_ID,
        "timestamp": datetime.now().isoformat(),
        "data": data_dict,
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        ENDPOINT,
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status
    except Exception as e:
        print(f"Error: {e}")
        return None


def run_test():
    print("Starting alert test simulator (direct urllib)...")
    print("Generating high emission values to trigger alerts...")

    alert_sequence = ["nox_high", "so2_high", "co_high", "dust_high"]

    for i in range(20):
        alert_idx = i % 4
        alert_type = alert_sequence[alert_idx]
        data = dict(BASE_VALUES)

        if alert_type == "nox_high":
            data["nox"] = 150 + random.uniform(0, 50)
        elif alert_type == "so2_high":
            data["so2"] = 80 + random.uniform(0, 40)
        elif alert_type == "co_high":
            data["co"] = 250 + random.uniform(0, 200)
        elif alert_type == "dust_high":
            data["dust"] = 18 + random.uniform(0, 15)

        for k in data:
            if k not in ["nox", "so2", "co", "dust"]:
                data[k] = BASE_VALUES[k] + random.gauss(0, abs(BASE_VALUES[k]) * 0.01)

        status = send_data(data)
        print(f"Tick {i:2d}: {alert_type:10s} - nox={data['nox']:6.1f}, so2={data['so2']:5.1f}, co={data['co']:6.0f}, dust={data['dust']:5.1f} - HTTP {status}")

        if (i + 1) % 4 == 0:
            print(f"  -> Wait 3s to let hourly buffer build...")
            time.sleep(3)
        else:
            time.sleep(1)

    print("\nTest data generation complete!")
    print("Check the dashboard for:")
    print("  1. Red alert toast cards sliding in from top-right")
    print("  2. Cards show: time, pollutant name, current value, limit, exceed %")
    print("  3. Cards auto-dismiss after ~10s")
    print("  4. Bottom '告警记录(N条)' panel - click to expand and see history")


if __name__ == "__main__":
    run_test()
