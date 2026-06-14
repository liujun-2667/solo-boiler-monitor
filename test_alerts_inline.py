import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import time
import random
from datetime import datetime
import database as db
from engine import engine

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


def run_test():
    db.init_db()
    print("Starting alert test simulator (direct engine ingest)...")
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

        timestamp = datetime.now().isoformat()
        engine.ingest(BOILER_ID, timestamp, data)

        print(f"Tick {i:2d}: {alert_type:10s} - nox={data['nox']:6.1f}, so2={data['so2']:5.1f}, co={data['co']:6.0f}, dust={data['dust']:5.1f}")

        if (i + 1) % 4 == 0:
            print(f"  -> Wait 3s to let hourly buffer build...")
            time.sleep(3)
        else:
            time.sleep(1)

    print("\n=== Checking generated alerts in database ===")
    unnotified = db.get_unnotified_alerts(BOILER_ID)
    print(f"Unnotified alerts: {len(unnotified)}")
    for a in unnotified:
        print(f"  [{a['id']}] {a['pollutant']} {a['type']} {a['level']} val={a['value']:.1f} limit={a['limit_val']:.1f}")

    history = db.get_alert_history(BOILER_ID, limit=10)
    print(f"\nRecent alert history (last 10):")
    for a in history:
        exceed_pct = max(0, ((a['value'] - a['limit_val']) / max(1, a['limit_val'])) * 100)
        print(f"  [{a['id']}] {a['timestamp'][:19]} {a['pollutant']} val={a['value']:.1f} limit={a['limit_val']:.1f} exceed=+{exceed_pct:.1f}% status={a['status']}")

    print(f"\nTotal alert count: {db.get_alert_count(BOILER_ID)}")
    print("\nTest complete! Refresh the dashboard to see alerts.")


if __name__ == "__main__":
    run_test()
