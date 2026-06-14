import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database as db

db.init_db()
print('=== Unnotified alerts ===')
un = db.get_unnotified_alerts('Boiler-1')
print(f'Count: {len(un)}')
for a in un:
    exceed = max(0, ((a['value'] - a['limit_val']) / max(1, a['limit_val'])) * 100)
    print(f'  [{a["id"]}] {a["pollutant"]} val={a["value"]:.1f} limit={a["limit_val"]:.1f} exceed=+{exceed:.1f}%')
print()
print('=== Recent alert history (last 10) ===')
h = db.get_alert_history('Boiler-1', limit=10)
for a in h:
    exceed = max(0, ((a['value'] - a['limit_val']) / max(1, a['limit_val'])) * 100)
    print(f'  [{a["id"]}] {a["timestamp"][:19]} {a["pollutant"]:6s} val={a["value"]:6.1f} limit={a["limit_val"]:5.1f} exceed=+{exceed:5.1f}% status={a["status"]}')
print(f'Total alerts: {db.get_alert_count("Boiler-1")}')
