import time
import random
import math
import requests
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


def generate_point(base, t, amp=0.02, noise=0.01):
    drift = math.sin(t / 200.0) * base * amp
    noise_val = random.gauss(0, base * noise)
    spike = random.gauss(0, 0) if random.random() > 0.98 else random.gauss(0, base * 0.1)
    return round(base + drift + noise_val + spike, 3)


def generate_message(tick):
    t = tick
    data = {}
    load_factor = 0.7 + 0.2 * math.sin(t / 400.0)
    data["main_steam_flow"] = round(BASE_VALUES["main_steam_flow"] * load_factor, 1)
    data["feedwater_flow"] = round(data["main_steam_flow"] * 1.02 + random.gauss(0, 2), 1)
    data["coal_feed"] = round(BASE_VALUES["coal_feed"] * load_factor + random.gauss(0, 1), 1)
    data["primary_air"] = round(BASE_VALUES["primary_air"] * (0.8 + 0.4 * load_factor) + random.gauss(0, 5), 1)
    data["induced_air"] = round(BASE_VALUES["induced_air"] * (0.8 + 0.4 * load_factor) + random.gauss(0, 5), 1)
    o2_factor = 1.0 + 0.3 * math.sin(t / 150.0)
    data["o2"] = round(BASE_VALUES["o2"] * o2_factor + random.gauss(0, 0.15), 2)
    for k in ["main_steam_temp", "main_steam_press", "feedwater_temp", "exhaust_temp",
              "furnace_press", "co", "nox", "so2", "dust",
              "sh1_out_temp", "sh2_out_temp", "sh3_out_temp", "sh4_out_temp",
              "rh1_out_temp", "rh2_out_temp", "rh3_out_temp", "rh4_out_temp",
              "drum_level", "fly_ash_carbon"]:
        data[k] = generate_point(BASE_VALUES[k], t)
    if tick % 40 == 0 and tick > 0:
        data["exhaust_temp"] = round(data["exhaust_temp"] + 15, 1)
        data["o2"] = round(data["o2"] + 1.5, 2)
    if tick % 70 == 0 and tick > 0:
        data["co"] = round(data["co"] * 3, 0)
        data["o2"] = round(max(2.0, data["o2"] - 1.2), 2)
    if tick % 100 == 0 and tick > 0:
        data["fly_ash_carbon"] = round(data["fly_ash_carbon"] + 3.5, 2)
    if random.random() < 0.03:
        data["main_steam_temp"] = None
    return data


def run():
    tick = 0
    print("Starting DCS data simulator, posting to", ENDPOINT)
    while True:
        try:
            msg = generate_message(tick)
            payload = {
                "boiler_id": BOILER_ID,
                "timestamp": datetime.now().isoformat(),
                "data": msg,
            }
            try:
                requests.post(ENDPOINT, json=payload, timeout=2)
            except Exception as e:
                print(f"Post failed: {e}")
            tick += 1
        except KeyboardInterrupt:
            print("Simulator stopped.")
            break
        time.sleep(5)


if __name__ == "__main__":
    run()
