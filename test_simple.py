import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Step 1: Importing database...")
import database as db
print("OK")

print("\nStep 2: init_db...")
db.init_db()
print("OK")

print("\nStep 3: Importing efficiency...")
from efficiency import compute_all_metrics
print("OK")

print("\nStep 4: Computing metrics...")
test_data = {
    "main_steam_temp": 540.0,
    "exhaust_temp": 135.0,
    "o2": 4.0,
    "co": 80.0,
    "nox": 70.0,
    "so2": 30.0,
    "dust": 8.0,
    "fly_ash_carbon": 2.8,
    "main_steam_flow": 720.0,
    "feedwater_flow": 735.0,
    "drum_level": 0.0,
    "sh1_out_temp": 410.0,
    "sh2_out_temp": 460.0,
    "sh3_out_temp": 510.0,
    "sh4_out_temp": 538.0,
    "main_steam_press": 16.7,
    "feedwater_temp": 255.0,
    "furnace_press": -60.0,
    "coal_feed": 85.0,
    "primary_air": 450.0,
    "induced_air": 520.0,
}
metrics = compute_all_metrics(test_data)
print(f"Efficiency: {metrics.get('efficiency')}")
print("OK")

print("\nStep 5: Importing health_engine...")
from health_engine import run_health_assessment
print("OK")

print("\nStep 6: Running health assessment...")
scores, details, trends = run_health_assessment("Boiler-1", test_data, metrics)
print("Scores:", scores)
print("OK")

print("\nStep 7: Checking DB...")
latest = db.get_latest_health_score("Boiler-1")
print(f"Latest health record: {latest['id'] if latest else None}")
print("OK")

print("\nStep 8: Checking predictive alerts...")
alerts = db.get_active_predictive_alerts("Boiler-1")
print(f"Active predictive alerts: {len(alerts)}")
print("OK")

print("\n=== ALL TESTS PASSED ===")
