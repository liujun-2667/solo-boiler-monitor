import math
import statistics
from datetime import datetime, timedelta

import numpy as np

import database as db
from efficiency import compute_all_metrics


DESIGN_EXHAUST_TEMP = 135.0
OPTIMAL_O2 = 4.0
CO_SPIKE_THRESHOLD = 200
FLY_ASH_HIGH_THRESHOLD = 5.0
EXHAUST_DEVIATION_MAX = 50.0
O2_DEVIATION_MAX = 4.0
CO_SPIKE_MAX_RATE = 1.0
FLY_ASH_MAX = 10.0

STEAM_TEMP_STD_MAX = 15.0
DRUM_LEVEL_STD_MAX = 30.0
FLOW_DEVIATION_MAX = 0.15
SH_TEMP_DIFF_MAX = 30.0

EFFICIENCY_MIN = 85.0
EFFICIENCY_HISTORY_HOURS = 168

SUBSYSTEM_WEIGHTS = {
    "combustion": 0.3,
    "steam_water": 0.25,
    "emission": 0.25,
    "efficiency": 0.2,
}

TREND_PARAMS = {
    "main_steam_temp": {"name": "主蒸汽温度", "unit": "℃", "alarm_high": 575, "alarm_low": 480, "flat_threshold": 0.3},
    "exhaust_temp": {"name": "排烟温度", "unit": "℃", "alarm_high": 180, "alarm_low": 80, "flat_threshold": 0.2},
    "nox": {"name": "NOx浓度", "unit": "mg/m³", "alarm_high": 100, "alarm_low": 0, "flat_threshold": 0.5},
    "efficiency": {"name": "燃烧效率", "unit": "%", "alarm_high": 100, "alarm_low": 85, "flat_threshold": 0.02},
}

PREDICTION_MINUTES = 30
HISTORY_HOURS = 2


def _linear_regression(x, y):
    n = len(x)
    if n < 2:
        return 0.0, 0.0, 0.0
    x_arr = np.array(x, dtype=float)
    y_arr = np.array(y, dtype=float)
    slope, intercept = np.polyfit(x_arr, y_arr, 1)
    y_pred = slope * x_arr + intercept
    residuals = y_arr - y_pred
    residual_std = float(np.std(residuals)) if n > 2 else 0.0
    return float(slope), float(intercept), residual_std


def _get_historical_best_efficiency(boiler_id):
    history = db.get_recent_aggregated(boiler_id, minutes=EFFICIENCY_HISTORY_HOURS * 60)
    if not history:
        return 95.0
    eff_vals = [h.get("efficiency") for h in history if h.get("efficiency") is not None]
    if not eff_vals:
        return 95.0
    return max(eff_vals)


def score_combustion(data, history_1h):
    exhaust_temp = data.get("exhaust_temp") or DESIGN_EXHAUST_TEMP
    exhaust_dev = abs(exhaust_temp - DESIGN_EXHAUST_TEMP)
    exhaust_score = max(0, 25 * (1 - exhaust_dev / EXHAUST_DEVIATION_MAX))

    o2 = data.get("o2") or OPTIMAL_O2
    o2_dev = abs(o2 - OPTIMAL_O2)
    o2_score = max(0, 25 * (1 - o2_dev / O2_DEVIATION_MAX))

    co_values = [h.get("co") for h in history_1h if h.get("co") is not None]
    spike_count = 0
    if co_values:
        co_mean = statistics.mean(co_values)
        co_std = statistics.stdev(co_values) if len(co_values) > 1 else 0
        for v in co_values:
            if v > CO_SPIKE_THRESHOLD and (co_std == 0 or abs(v - co_mean) > 2 * co_std):
                spike_count += 1
    spike_rate = spike_count / max(1, len(co_values)) if co_values else 0
    co_score = max(0, 25 * (1 - spike_rate / CO_SPIKE_MAX_RATE))

    fly_ash = data.get("fly_ash_carbon") or 0
    fly_ash_high_count = sum(
        1 for h in history_1h
        if h.get("fly_ash_carbon") is not None and h["fly_ash_carbon"] > FLY_ASH_HIGH_THRESHOLD
    )
    fly_ash_sustained_ratio = fly_ash_high_count / max(1, len(history_1h)) if history_1h else 0
    fly_ash_dev = max(0, fly_ash - 3.0)
    fly_ash_dim = max(fly_ash_sustained_ratio, min(1.0, fly_ash_dev / (FLY_ASH_MAX - 3.0)))
    fly_ash_score = max(0, 25 * (1 - fly_ash_dim))

    total = exhaust_score + o2_score + co_score + fly_ash_score
    details = {
        "排烟温度偏差": round(exhaust_score, 1),
        "O2偏差": round(o2_score, 1),
        "CO突升频率": round(co_score, 1),
        "飞灰含碳量": round(fly_ash_score, 1),
    }
    return total, details


def score_steam_water(data, history_1h):
    steam_temps = [h.get("main_steam_temp") for h in history_1h if h.get("main_steam_temp") is not None]
    steam_std = statistics.stdev(steam_temps) if len(steam_temps) > 1 else 0
    steam_score = max(0, 25 * (1 - steam_std / STEAM_TEMP_STD_MAX))

    drum_levels = [h.get("drum_level") for h in history_1h if h.get("drum_level") is not None]
    drum_std = statistics.stdev(drum_levels) if len(drum_levels) > 1 else 0
    drum_score = max(0, 25 * (1 - drum_std / DRUM_LEVEL_STD_MAX))

    feed_flow = data.get("feedwater_flow") or 0
    steam_flow = data.get("main_steam_flow") or 1
    flow_dev = abs(feed_flow - steam_flow) / max(1, steam_flow)
    flow_score = max(0, 25 * (1 - flow_dev / FLOW_DEVIATION_MAX))

    sh_temps = []
    for prefix in ["sh1_out_temp", "sh2_out_temp", "sh3_out_temp", "sh4_out_temp"]:
        v = data.get(prefix)
        if v is not None:
            sh_temps.append(v)
    if len(sh_temps) >= 2:
        sh_diff = max(sh_temps) - min(sh_temps)
        sh_score = max(0, 25 * (1 - sh_diff / SH_TEMP_DIFF_MAX))
    else:
        sh_score = 25.0

    total = steam_score + drum_score + flow_score + sh_score
    details = {
        "主汽温波动": round(steam_score, 1),
        "汽包水位波动": round(drum_score, 1),
        "给水-蒸汽偏差": round(flow_score, 1),
        "过热器温差": round(sh_score, 1),
    }
    return total, details


def score_emission(data, history_1h):
    limits = db.get_emission_limits()
    pollutants = ["nox", "so2", "co", "dust"]
    scores = []
    details = {}

    for p in pollutants:
        lim = limits.get(p, {"hourly": 100})
        hourly_limit = lim.get("hourly", 100)
        vals = [h.get(p) for h in history_1h if h.get(p) is not None]
        hourly_mean = statistics.mean(vals) if vals else 0
        ratio = hourly_mean / max(1, hourly_limit)

        if ratio >= 1.0:
            p_score = 0.0
        else:
            p_score = max(0, 25 * (1 - ratio))
        scores.append(p_score)

        p_name = lim.get("name", p)
        details[f"{p_name}占比"] = round(p_score, 1)

    total = sum(scores)
    return total, details


def score_efficiency(boiler_id, data, metrics):
    current_eff = metrics.get("efficiency", 90)
    best_eff = _get_historical_best_efficiency(boiler_id)

    if current_eff < EFFICIENCY_MIN:
        eff_score = 0.0
    else:
        ratio = current_eff / max(0.1, best_eff)
        denominator = 1 - EFFICIENCY_MIN / max(0.1, best_eff)
        if denominator <= 0:
            eff_score = 100.0
        else:
            eff_score = max(0, min(100, 100 * (1 - (1 - ratio) / denominator)))

    details = {
        "当前效率": round(current_eff, 1),
        "历史最优": round(best_eff, 1),
        "效率比值": round(current_eff / max(0.1, best_eff), 3),
    }
    return eff_score, details


def compute_health(boiler_id, data, metrics, history_1h):
    combustion_score, combustion_details = score_combustion(data, history_1h)
    steam_water_score, steam_water_details = score_steam_water(data, history_1h)
    emission_score, emission_details = score_emission(data, history_1h)
    efficiency_score, efficiency_details = score_efficiency(boiler_id, data, metrics)

    overall = (
        combustion_score * SUBSYSTEM_WEIGHTS["combustion"]
        + steam_water_score * SUBSYSTEM_WEIGHTS["steam_water"]
        + emission_score * SUBSYSTEM_WEIGHTS["emission"]
        + efficiency_score * SUBSYSTEM_WEIGHTS["efficiency"]
    )

    scores = {
        "combustion": round(combustion_score, 1),
        "steam_water": round(steam_water_score, 1),
        "emission": round(emission_score, 1),
        "efficiency": round(efficiency_score, 1),
        "overall": round(overall, 1),
    }
    details = {
        "combustion": combustion_details,
        "steam_water": steam_water_details,
        "emission": emission_details,
        "efficiency": efficiency_details,
    }
    return scores, details


def predict_trends(boiler_id, history_2h):
    results = {}
    now = datetime.now()

    for param_key, param_cfg in TREND_PARAMS.items():
        x_vals = []
        y_vals = []

        for i, h in enumerate(history_2h):
            window_start = h.get("window_start")
            if not window_start:
                continue
            try:
                ts = datetime.fromisoformat(window_start)
            except Exception:
                continue

            minutes_elapsed = (ts - now).total_seconds() / 60.0

            if param_key == "efficiency":
                d = dict(h)
                m = compute_all_metrics(d)
                val = m.get("efficiency")
            else:
                val = h.get(param_key)

            if val is not None:
                x_vals.append(minutes_elapsed)
                y_vals.append(val)

        if len(y_vals) < 3:
            results[param_key] = None
            continue

        slope, intercept, residual_std = _linear_regression(x_vals, y_vals)

        future_x = [i for i in range(1, PREDICTION_MINUTES + 1)]
        predicted = [slope * fx + intercept for fx in future_x]
        confidence_upper = [p + 1.96 * residual_std for p in predicted]
        confidence_lower = [p - 1.96 * residual_std for p in predicted]

        future_times = [(now + timedelta(minutes=i)).isoformat() for i in range(1, PREDICTION_MINUTES + 1)]

        flat_threshold = param_cfg.get("flat_threshold", 0.05)
        if abs(slope) < flat_threshold:
            trend_direction = "平稳"
        elif slope > 0:
            trend_direction = "上升"
        else:
            trend_direction = "下降"

        alarm_high = param_cfg["alarm_high"]
        alarm_low = param_cfg["alarm_low"]
        minutes_to_exceed = None
        for i, pv in enumerate(predicted):
            if pv > alarm_high or pv < alarm_low:
                minutes_to_exceed = i + 1
                break

        history_values = []
        history_times = []
        for h in history_2h:
            ws = h.get("window_start")
            if param_key == "efficiency":
                d = dict(h)
                m = compute_all_metrics(d)
                val = m.get("efficiency")
            else:
                val = h.get(param_key)
            if val is not None and ws:
                history_values.append(val)
                history_times.append(ws)

        results[param_key] = {
            "param_name": param_cfg["name"],
            "param_unit": param_cfg["unit"],
            "slope_per_min": round(slope, 4),
            "intercept": round(intercept, 2),
            "residual_std": round(residual_std, 2),
            "trend_direction": trend_direction,
            "predicted_values": [round(p, 2) for p in predicted],
            "confidence_upper": [round(p, 2) for p in confidence_upper],
            "confidence_lower": [round(p, 2) for p in confidence_lower],
            "future_times": future_times,
            "alarm_high": alarm_high,
            "alarm_low": alarm_low,
            "minutes_to_exceed": minutes_to_exceed,
            "current_value": round(y_vals[-1], 2) if y_vals else None,
            "history_values": history_values,
            "history_times": history_times,
        }

    return results


def generate_predictive_alerts(boiler_id, trend_results):
    db.expire_old_predictive_alerts(boiler_id)

    active_alerts = db.get_active_predictive_alerts(boiler_id)
    active_by_param = {}
    for a in active_alerts:
        pk = a.get("param_key")
        if pk:
            active_by_param[pk] = a

    for param_key, result in trend_results.items():
        if result is None:
            continue

        mte = result.get("minutes_to_exceed")
        if mte is None:
            continue

        now = datetime.now()
        predicted_exceed_time = (now + timedelta(minutes=mte)).isoformat()
        predicted_peak = max(result["predicted_values"]) if result["predicted_values"] else 0
        predicted_trough = min(result["predicted_values"]) if result["predicted_values"] else 0
        current_value = result.get("current_value", 0)
        alarm_high = result["alarm_high"]
        alarm_low = result["alarm_low"]

        if result["trend_direction"] == "上升":
            threshold = alarm_high
            peak_val = predicted_peak
        else:
            threshold = alarm_low
            peak_val = predicted_trough

        existing = active_by_param.get(param_key)
        if existing:
            existing_mte = existing.get("minutes_to_exceed", 0)
            if abs(existing_mte - mte) > 2:
                db.resolve_predictive_alert(existing["id"])
                db.insert_predictive_alert(
                    boiler_id,
                    param_key,
                    result["param_name"],
                    predicted_exceed_time,
                    current_value,
                    round(peak_val, 2),
                    threshold,
                    mte,
                )
            else:
                db.update_predictive_alert(
                    existing["id"],
                    predicted_exceed_time,
                    current_value,
                    round(peak_val, 2),
                    mte,
                )
        else:
            db.insert_predictive_alert(
                boiler_id,
                param_key,
                result["param_name"],
                predicted_exceed_time,
                current_value,
                round(peak_val, 2),
                threshold,
                mte,
            )


def run_health_assessment(boiler_id, data, metrics):
    history_1h = db.get_recent_aggregated(boiler_id, minutes=60)
    if not history_1h:
        history_1h = [{"window_start": datetime.now().isoformat(), **data}]

    scores, details = compute_health(boiler_id, data, metrics, history_1h)
    db.insert_health_score(boiler_id, scores, details)

    history_2h = db.get_recent_aggregated(boiler_id, minutes=HISTORY_HOURS * 60)
    if len(history_2h) >= 3:
        trend_results = predict_trends(boiler_id, history_2h)
        generate_predictive_alerts(boiler_id, trend_results)
    else:
        trend_results = {}

    return scores, details, trend_results
