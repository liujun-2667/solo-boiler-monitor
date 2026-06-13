import database as db


URGENCY_SCORE = {"高": 3, "中": 2, "低": 1}


def diagnose(data, metrics):
    thresholds = db.get_diag_thresholds()
    suggestions = []

    exhaust_temp_high = thresholds.get("exhaust_temp_high", 145)
    co_spike = thresholds.get("co_spike", 200)
    fly_ash_high = thresholds.get("fly_ash_carbon_high", 5)
    sh_diff = thresholds.get("sh_temp_diff", 15)
    o2_dev_thresh = thresholds.get("o2_deviation", 0.8)

    o2 = data.get("o2") or 0
    co = data.get("co") or 0
    exhaust = data.get("exhaust_temp") or 0
    fly_ash = data.get("fly_ash_carbon") or 0
    coal = data.get("coal_feed") or 0

    if exhaust > exhaust_temp_high and o2 > 5:
        suggestions.append({
            "rule_key": "exhaust_high_o2_high",
            "priority": 50,
            "urgency": "高",
            "diagnosis": f"排烟温度{exhaust:.1f}℃(阈值{exhaust_temp_high}℃)且氧量{o2:.1f}%偏高",
            "action": "减少过剩空气系数，适当降低送风量",
            "expected_effect": "预计排烟热损失降低0.5~1.0个百分点，效率提升约0.3~0.8%",
        })

    if co > co_spike and o2 < 3.5:
        suggestions.append({
            "rule_key": "co_spike_o2_low",
            "priority": 60,
            "urgency": "高",
            "diagnosis": f"CO浓度{co:.0f}ppm(阈值{co_spike}ppm)且氧量{o2:.1f}%偏低",
            "action": "燃烧不完全，建议增加二次风量",
            "expected_effect": "预计化学未完全燃烧损失降低0.3~0.8个百分点，效率提升约0.2~0.5%",
        })

    if fly_ash > fly_ash_high and coal > 100:
        suggestions.append({
            "rule_key": "fly_ash_high_coal_high",
            "priority": 45,
            "urgency": "中",
            "diagnosis": f"飞灰含碳量{fly_ash:.1f}%(阈值{fly_ash_high}%)且给煤量{coal:.1f}t/h偏高",
            "action": "煤粉细度可能不足，建议检查磨煤机出力，调整煤粉细度",
            "expected_effect": "预计机械未完全燃烧损失降低0.4~0.9个百分点，效率提升约0.2~0.6%",
        })

    sh_temps = [data.get("sh1_out_temp"), data.get("sh2_out_temp"),
                data.get("sh3_out_temp"), data.get("sh4_out_temp")]
    sh_temps = [t for t in sh_temps if t is not None]
    if len(sh_temps) >= 2:
        diff = max(sh_temps) - min(sh_temps)
        if diff > sh_diff:
            suggestions.append({
                "rule_key": "sh_temp_diff",
                "priority": 40,
                "urgency": "中",
                "diagnosis": f"过热器最大温差{diff:.1f}℃(阈值{sh_diff}℃)",
                "action": "燃烧偏斜，建议调整燃烧器摆角和配风",
                "expected_effect": "预计过热器温差缩小，减少热偏差降低，安全性提升",
            })

    o2_dev = metrics.get("o2_dev", 0)
    if abs(o2_dev) > o2_dev_thresh:
        direction = "偏高" if o2_dev > 0 else "偏低"
        suggestions.append({
            "rule_key": "o2_deviation",
            "priority": 35,
            "urgency": "低",
            "diagnosis": f"氧量偏差{o2_dev:+.2f}%(阈值±{o2_dev_thresh}%)，氧量{direction}",
            "action": "调整送风量，使氧量接近最佳氧量曲线",
            "expected_effect": "预计优化燃烧配风，综合效率提升约0.1~0.3%",
        })

    main_steam_temp = data.get("main_steam_temp") or 0
    if main_steam_temp < 520:
        suggestions.append({
            "rule_key": "main_steam_temp_low",
            "priority": 30,
            "urgency": "中",
            "diagnosis": f"主蒸汽温度{main_steam_temp:.1f}℃偏低",
            "action": "调整燃烧器摆角和减温水",
            "expected_effect": "提升主蒸汽参数，提高循环效率",
        })

    for s in suggestions:
        s["priority"] += URGENCY_SCORE.get(s["urgency"], 0) * 10
    suggestions.sort(key=lambda x: x["priority"], reverse=True)
    return suggestions[:5]


def persist_suggestions(boiler_id, data, metrics):
    new_sugs = diagnose(data, metrics)
    db.replace_suggestions(boiler_id, new_sugs)
    return db.get_active_suggestions(boiler_id)
