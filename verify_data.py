import database as db
db.init_db()

h = db.get_recent_aggregated('Boiler-1', minutes=120)
print(f'Records: {len(h)}')
if h:
    print(f'First: {h[0]["window_start"]}')
    print(f'Last: {h[-1]["window_start"]}')
    print(f'Efficiency sample: {h[0].get("efficiency")}')

from health_engine import run_health_assessment
from efficiency import compute_all_metrics

if h:
    last_data = dict(h[-1])
    metrics = compute_all_metrics(last_data)
    scores, details, trends = run_health_assessment('Boiler-1', last_data, metrics)
    print(f'\nHealth scores:')
    for k, v in scores.items():
        print(f'  {k}: {v}')

    print(f'\nTrend results:')
    for pk, pr in trends.items():
        if pr:
            print(f'  {pk}: direction={pr["trend_direction"]}, slope={pr["slope_per_min"]}, mte={pr["minutes_to_exceed"]}')
            print(f'    predicted points: {len(pr["predicted_values"])}')
            print(f'    history points: {len(pr["history_values"])}')
        else:
            print(f'  {pk}: None')

    alerts = db.get_active_predictive_alerts('Boiler-1')
    print(f'\nActive predictive alerts: {len(alerts)}')
    for a in alerts:
        print(f'  {a["param_name"]}: {a["minutes_to_exceed"]} min to exceed')
