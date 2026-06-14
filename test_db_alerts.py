import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database as db
from datetime import datetime, timedelta

db.init_db()

boiler_id = "Boiler-1"

print("=== Current alerts in database ===")
alerts = db.get_alert_history(boiler_id, limit=20)
print(f"Total alert count: {db.get_alert_count(boiler_id)}")
for a in alerts:
    print(f"  [{a['id']}] {a['timestamp'][:19]} {a['pollutant']} {a['level']} val={a['value']:.1f} peak={a['peak_value']:.1f} limit={a['limit_val']:.1f} status={a['status']} notified={a['notified']}")

print("\n=== Inserting test alerts ===")
now = datetime.now()

test_alerts = [
    {"pollutant": "nox", "value": 145.5, "limit_val": 100, "minutes_ago": 2},
    {"pollutant": "so2", "value": 78.3, "limit_val": 50, "minutes_ago": 1},
    {"pollutant": "co", "value": 320.0, "limit_val": 100, "minutes_ago": 0.5},
    {"pollutant": "dust", "value": 22.8, "limit_val": 10, "minutes_ago": 0.2},
]

for ta in test_alerts:
    ts = (now - timedelta(minutes=ta["minutes_ago"])).isoformat()
    db.insert_alert(boiler_id, ta["pollutant"], "hourly", "alarm", ta["value"], ta["limit_val"])
    print(f"  Inserted: {ta['pollutant']} = {ta['value']} (limit={ta['limit_val']})")

print("\n=== Alerts after insert ===")
alerts = db.get_alert_history(boiler_id, limit=20)
print(f"Total alert count: {db.get_alert_count(boiler_id)}")
unnotified = db.get_unnotified_alerts(boiler_id)
print(f"Unnotified alerts: {len(unnotified)}")
for a in alerts:
    print(f"  [{a['id']}] {a['timestamp'][:19]} {a['pollutant']} {a['level']} val={a['value']:.1f} peak={a['peak_value']:.1f} limit={a['limit_val']:.1f} status={a['status']} notified={a['notified']}")
