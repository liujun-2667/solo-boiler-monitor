import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database as db

db.init_db()

print('=== Resetting all alerts to notified=0 for testing ===')
import sqlite3
with db.get_db() as conn:
    conn.execute("UPDATE alerts SET notified=0 WHERE status='active'")
    conn.execute("UPDATE alerts SET status='resolved' WHERE status='active'")

print('=== Inserting fresh test alerts ===')
from datetime import datetime, timedelta
boiler_id = "Boiler-1"

test_data = [
    {"pollutant": "nox", "value": 145.5, "limit_val": 100, "minutes_ago": 0.2},
    {"pollutant": "so2", "value": 78.3, "limit_val": 50, "minutes_ago": 0.15},
    {"pollutant": "co", "value": 320.0, "limit_val": 100, "minutes_ago": 0.1},
    {"pollutant": "dust", "value": 22.8, "limit_val": 10, "minutes_ago": 0.05},
]

for ta in test_data:
    db.insert_alert(boiler_id, ta["pollutant"], "hourly", "alarm", ta["value"], ta["limit_val"])
    print(f"  Inserted: {ta['pollutant']} = {ta['value']} (limit={ta['limit_val']})")

print()
print('=== Current unnotified alerts ===')
un = db.get_unnotified_alerts('Boiler-1')
print(f'Count: {len(un)}')
for a in un:
    exceed = max(0, ((a['value'] - a['limit_val']) / max(1, a['limit_val'])) * 100)
    print(f'  [{a["id"]}] {a["pollutant"]:6s} val={a["value"]:6.1f} limit={a["limit_val"]:5.1f} exceed=+{exceed:5.1f}% status={a["status"]} notified={a["notified"]}')
print(f'\nTotal alerts now: {db.get_alert_count("Boiler-1")}')
