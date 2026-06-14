import sys
import os
import traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing report generation...")
try:
    import database as db
    db.init_db()
    print("DB init OK")

    boiler_id = "Boiler-1"
    from datetime import datetime, timedelta

    now = datetime.now()
    test_ts = now - timedelta(hours=2)
    test_data = {
        "main_steam_temp": 540,
        "main_steam_flow": 720,
        "exhaust_temp": 135,
        "o2": 4.0,
        "co": 80,
        "nox": 70,
        "so2": 30,
        "dust": 8,
        "coal_feed": 85,
    }
    metrics = {
        "efficiency": 91.5,
        "q2": 6.2,
        "q3": 0.8,
        "q4": 2.5,
        "q5": 1.5,
    }
    db.insert_aggregated(boiler_id, test_ts.isoformat(), test_data, metrics)
    print("Test data inserted OK")

    from emissions import EmissionMonitor
    em = EmissionMonitor(boiler_id)
    print("EmissionMonitor created OK")

    year = now.year
    month = now.month
    print(f"Calling get_monthly_report({boiler_id}, {year}, {month})...")
    report = em.get_monthly_report(boiler_id, year, month)
    print(f"get_monthly_report returned: {type(report)}")
    if report is None:
        print("WARNING: report is None")
    else:
        print(f"  keys: {list(report.keys())}")

except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()
