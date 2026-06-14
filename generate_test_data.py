import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
import json
import math
import random

import database as db
from efficiency import compute_all_metrics

db.init_db()

boiler_id = "Boiler-1"

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


def generate_point(base, tick, amp=0.02, noise=0.01):
    drift = math.sin(tick / 20.0) * base * amp
    noise_val = random.gauss(0, base * noise)
    return round(base + drift + noise_val, 3)


def generate_data(tick):
    data = {}
    load_factor = 0.7 + 0.2 * math.sin(tick / 40.0)
    data["main_steam_flow"] = round(BASE_VALUES["main_steam_flow"] * load_factor, 1)
    data["feedwater_flow"] = round(data["main_steam_flow"] * 1.02 + random.gauss(0, 2), 1)
    data["coal_feed"] = round(BASE_VALUES["coal_feed"] * load_factor + random.gauss(0, 1), 1)
    data["primary_air"] = round(BASE_VALUES["primary_air"] * (0.8 + 0.4 * load_factor) + random.gauss(0, 5), 1)
    data["induced_air"] = round(BASE_VALUES["induced_air"] * (0.8 + 0.4 * load_factor) + random.gauss(0, 5), 1)
    o2_factor = 1.0 + 0.3 * math.sin(tick / 15.0)
    data["o2"] = round(BASE_VALUES["o2"] * o2_factor + random.gauss(0, 0.15), 2)
    for k in ["main_steam_temp", "main_steam_press", "feedwater_temp", "exhaust_temp",
              "furnace_press", "co", "nox", "so2", "dust",
              "sh1_out_temp", "sh2_out_temp", "sh3_out_temp", "sh4_out_temp",
              "rh1_out_temp", "rh2_out_temp", "rh3_out_temp", "rh4_out_temp",
              "drum_level", "fly_ash_carbon"]:
        data[k] = generate_point(BASE_VALUES[k], tick)
    return data


print("Generating 2 hours of historical data...")
print("(30-second intervals, 240 data points)")

now = datetime.now()
start_time = now - timedelta(hours=2)

count = 0
for i in range(240):
    ts = start_time + timedelta(seconds=i * 30)
    data = generate_data(i)
    metrics = compute_all_metrics(data)

    db.insert_raw(boiler_id, ts.isoformat(), data)
    db.insert_aggregated(boiler_id, ts.isoformat(), data, metrics)

    count += 1
    if count % 60 == 0:
        print(f"  Generated {count} points...")

print(f"\nDone! Generated {count} data points.")

history_2h = db.get_recent_aggregated(boiler_id, minutes=120)
print(f"Verified: {len(history_2h)} aggregated records in last 2 hours")

if history_2h:
    latest = history_2h[-1]
    print(f"Latest data: main_steam_temp={latest.get('main_steam_temp'):.1f}, "
          f"efficiency={latest.get('efficiency', 0):.2f}%")

print("\nData generation complete.")
