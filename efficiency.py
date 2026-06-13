import database as db


def _interpolate(table, x):
    xs = [p[0] for p in table]
    ys = [p[1] for p in table]
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    for i in range(len(xs) - 1):
        if xs[i] <= x <= xs[i + 1]:
            ratio = (x - xs[i]) / (xs[i + 1] - xs[i])
            return ys[i] + ratio * (ys[i + 1] - ys[i])
    return ys[-1]


def calc_load_ratio(data, rated_flow=1000.0):
    flow = data.get("main_steam_flow") or 0
    return max(0.1, min(1.0, flow / rated_flow))


def calc_q2(data, ambient_temp=25.0):
    exhaust_temp = data.get("exhaust_temp") or 130
    o2 = data.get("o2") or 4.0
    delta_t = exhaust_temp - ambient_temp
    cp_flue_gas = 1.38
    excess_air = 21.0 / max(0.1, (21.0 - o2))
    q2 = 0.35 * delta_t * cp_flue_gas * excess_air / 100.0
    return max(3.0, min(12.0, q2))


def calc_q3(data):
    co = data.get("co") or 50.0
    co_pct = co / 10000.0
    q3 = 235.0 * co_pct * 10.0
    return max(0.05, min(2.0, q3))


def calc_q4(data):
    fly_ash_carbon = data.get("fly_ash_carbon") or 2.0
    ash_ratio = 0.3
    q4 = fly_ash_carbon * ash_ratio * 3.2
    return max(0.5, min(8.0, q4))


def calc_q5(data, rated_flow=1000.0):
    load = calc_load_ratio(data, rated_flow)
    q5_table = db.get_q5_table()
    return _interpolate(q5_table, load)


def calc_efficiency(data, rated_flow=1000.0):
    q2 = calc_q2(data)
    q3 = calc_q3(data)
    q4 = calc_q4(data)
    q5 = calc_q5(data, rated_flow)
    efficiency = 100.0 - q2 - q3 - q4 - q5
    return {
        "efficiency": max(80.0, min(97.0, efficiency)),
        "q2": q2,
        "q3": q3,
        "q4": q4,
        "q5": q5,
    }


def calc_o2_deviation(data, rated_flow=1000.0):
    load = calc_load_ratio(data, rated_flow)
    o2_curve = db.get_o2_curve()
    optimal_o2 = _interpolate(o2_curve, load)
    actual_o2 = data.get("o2") or 0.0
    return actual_o2 - optimal_o2


def calc_nox_intensity(data, rated_flow=1000.0, steam_enthalpy=3.0):
    nox = data.get("nox") or 50.0
    flow = data.get("main_steam_flow") or rated_flow * 0.7
    flue_gas_flow = flow * 1.3
    if flow <= 0:
        return 0.0
    power_mw = flow * steam_enthalpy / 3.6
    emission_g_per_h = nox * flue_gas_flow * 1000.0 / 1000000.0
    return emission_g_per_h * 1000.0 / max(0.1, power_mw)


def compute_all_metrics(data, rated_flow=1000.0):
    eff = calc_efficiency(data, rated_flow)
    o2_dev = calc_o2_deviation(data, rated_flow)
    nox_int = calc_nox_intensity(data, rated_flow)
    result = dict(eff)
    result["o2_dev"] = round(o2_dev, 3)
    result["nox_intensity"] = round(nox_int, 3)
    result["load_ratio"] = round(calc_load_ratio(data, rated_flow), 3)
    return result
