import sys
import os
import traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing full report generation flow...")
try:
    import database as db
    db.init_db()
    print("1. DB init OK")

    from datetime import datetime, timedelta
    boiler_id = "Boiler-1"

    now = datetime.now()
    for i in range(10):
        ts = now - timedelta(hours=1) + timedelta(minutes=6 * i)
        test_data = {
            "main_steam_temp": 540 + i,
            "main_steam_flow": 720 + i * 10,
            "exhaust_temp": 135 + i * 0.5,
            "o2": 4.0 + i * 0.1,
            "co": 80 + i * 5,
            "nox": 70 + i * 3,
            "so2": 30 + i * 2,
            "dust": 8 + i * 0.5,
            "coal_feed": 85 + i,
        }
        metrics = {
            "efficiency": 91.5 - i * 0.1,
            "q2": 6.2 + i * 0.05,
            "q3": 0.8,
            "q4": 2.5,
            "q5": 1.5,
            "o2_dev": 0.5,
            "nox_intensity": 1.2,
        }
        db.insert_aggregated(boiler_id, ts.isoformat(), test_data, metrics)
    print("2. Test data inserted OK (10 points)")

    from emissions import EmissionMonitor
    em = EmissionMonitor(boiler_id)
    year = now.year
    month = now.month
    report = em.get_monthly_report(boiler_id, year, month)
    print(f"3. EmissionMonitor.get_monthly_report OK, keys: {list(report.keys())}")

    import statistics
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, month + 1, 1)
    data = db.get_aggregated_range(boiler_id, start.isoformat(), end.isoformat())
    eff_vals = [d.get("efficiency") for d in data if d.get("efficiency") is not None]
    q2_vals = [d.get("q2") for d in data if d.get("q2") is not None]
    report["avg_efficiency"] = statistics.mean(eff_vals) if eff_vals else 0
    report["avg_q2"] = statistics.mean(q2_vals) if q2_vals else 0
    report["data_points"] = len(data)
    limits = db.get_emission_limits()
    report["limits"] = limits
    alerts = db.get_recent_alerts(boiler_id, minutes=60 * 24 * 31)
    report["alert_list"] = alerts[:20]
    print(f"4. Report data enriched OK, data_points={report['data_points']}")

    from dash import html
    import dash_bootstrap_components as dbc

    DARK_BG_CARD = "#112240"
    BORDER_COLOR = "#1E3A5F"
    ACCENT_CYAN = "#00D4FF"
    ACCENT_GREEN = "#00FF88"
    ACCENT_ORANGE = "#FFB800"
    ACCENT_RED = "#FF4D6D"
    TEXT_PRIMARY = "#E6F1FF"
    TEXT_SECONDARY = "#88A0C0"

    CARD = {
        "backgroundColor": DARK_BG_CARD,
        "border": f"1px solid {BORDER_COLOR}",
        "borderRadius": "8px",
        "padding": "16px",
        "marginBottom": "16px",
    }
    poll_labels = {"nox": "NOx", "so2": "SO₂", "co": "CO", "dust": "粉尘"}
    r = report

    daily_rows = []
    for day in sorted(r.get("daily_stats", {}).keys()):
        ds = r["daily_stats"][day]
        cells = [html.Td(day, style={"color": TEXT_SECONDARY, "padding": "6px 10px", "borderBottom": f"1px solid {BORDER_COLOR}"})]
        for p in ["nox", "so2", "co", "dust"]:
            v = ds.get(p, {})
            mean_v = v.get("mean", 0)
            max_v = v.get("max", 0)
            cells.append(html.Td(f"{mean_v:.1f} / {max_v:.1f}", style={"color": TEXT_PRIMARY, "padding": "6px 10px", "borderBottom": f"1px solid {BORDER_COLOR}", "textAlign": "center"}))
        daily_rows.append(html.Tr(cells))
    print(f"5. Daily rows built OK, {len(daily_rows)} rows")

    alert_rows = []
    for a in r.get("alert_list", []):
        alert_rows.append(html.Tr([
            html.Td(a.get("timestamp", "")[:19], style={"color": TEXT_SECONDARY, "padding": "6px 10px"}),
            html.Td(a.get("pollutant", ""), style={"color": ACCENT_ORANGE if a.get("level") == "warning" else ACCENT_RED, "padding": "6px 10px"}),
            html.Td(a.get("level", ""), style={"color": ACCENT_RED if a.get("level") == "alarm" else ACCENT_ORANGE, "padding": "6px 10px"}),
            html.Td(f"{a.get('value', 0):.1f}", style={"color": TEXT_PRIMARY, "padding": "6px 10px"}),
            html.Td(f"{a.get('limit_val', 0):.1f}", style={"color": TEXT_PRIMARY, "padding": "6px 10px"}),
        ]))
    print(f"6. Alert rows built OK, {len(alert_rows)} rows")

    children = [
        html.Div([
            html.Div(f"锅炉编号: {boiler_id}", style={"color": TEXT_SECONDARY, "fontSize": "14px", "marginRight": "24px"}),
            html.Div(f"报告周期: {year}年{month}月", style={"color": TEXT_SECONDARY, "fontSize": "14px", "marginRight": "24px"}),
            html.Div(f"数据点数: {r.get('data_points', 0)}", style={"color": TEXT_SECONDARY, "fontSize": "14px"}),
        ], style={"marginBottom": "16px", "display": "flex"}),
    ]
    print("7. Header children OK")

    cr = r.get('compliance_rate', 0)
    print(f"8. compliance_rate = {cr}")
    color = ACCENT_GREEN if cr >= 90 else ACCENT_RED
    print(f"   color = {color}")

    compliance_div = html.Div(f"{cr:.1f}%", style={"color": color, "fontSize": "36px", "fontWeight": "700", "fontFamily": "Consolas, monospace"})
    print("9. Compliance div OK")

    print("\n*** ALL TESTS PASSED ***")

except Exception as e:
    print(f"\n*** ERROR: {e} ***")
    traceback.print_exc()
