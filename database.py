import sqlite3
import threading
from datetime import datetime, timedelta
from contextlib import contextmanager
import json
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "boiler_monitor.db")

_local = threading.local()


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


DEFAULT_POINT_LIMITS = {
    "main_steam_temp": {"name": "主蒸汽温度", "unit": "℃", "min": 450, "max": 580},
    "main_steam_press": {"name": "主蒸汽压力", "unit": "MPa", "min": 10, "max": 20},
    "main_steam_flow": {"name": "主蒸汽流量", "unit": "t/h", "min": 0, "max": 1200},
    "feedwater_temp": {"name": "给水温度", "unit": "℃", "min": 150, "max": 300},
    "feedwater_flow": {"name": "给水流量", "unit": "t/h", "min": 0, "max": 1300},
    "exhaust_temp": {"name": "排烟温度", "unit": "℃", "min": 80, "max": 200},
    "furnace_press": {"name": "炉膛负压", "unit": "Pa", "min": -300, "max": 100},
    "o2": {"name": "氧量", "unit": "%", "min": 0, "max": 15},
    "co": {"name": "一氧化碳", "unit": "ppm", "min": 0, "max": 5000},
    "nox": {"name": "氮氧化物", "unit": "mg/m³", "min": 0, "max": 1000},
    "so2": {"name": "二氧化硫", "unit": "mg/m³", "min": 0, "max": 1000},
    "dust": {"name": "粉尘", "unit": "mg/m³", "min": 0, "max": 200},
    "coal_feed": {"name": "给煤量", "unit": "t/h", "min": 0, "max": 200},
    "primary_air": {"name": "送风量", "unit": "t/h", "min": 0, "max": 800},
    "induced_air": {"name": "引风量", "unit": "t/h", "min": 0, "max": 1000},
    "sh1_out_temp": {"name": "过热器1出口温度", "unit": "℃", "min": 300, "max": 500},
    "sh2_out_temp": {"name": "过热器2出口温度", "unit": "℃", "min": 350, "max": 520},
    "sh3_out_temp": {"name": "过热器3出口温度", "unit": "℃", "min": 400, "max": 560},
    "sh4_out_temp": {"name": "过热器4出口温度", "unit": "℃", "min": 400, "max": 560},
    "rh1_out_temp": {"name": "再热器1出口温度", "unit": "℃", "min": 300, "max": 500},
    "rh2_out_temp": {"name": "再热器2出口温度", "unit": "℃", "min": 350, "max": 520},
    "rh3_out_temp": {"name": "再热器3出口温度", "unit": "℃", "min": 400, "max": 540},
    "rh4_out_temp": {"name": "再热器4出口温度", "unit": "℃", "min": 400, "max": 540},
    "drum_level": {"name": "汽包水位", "unit": "mm", "min": -300, "max": 300},
    "fly_ash_carbon": {"name": "飞灰含碳量", "unit": "%", "min": 0, "max": 20},
}

DEFAULT_EMISSION_LIMITS = {
    "nox": {"hourly": 100, "peak": 200, "name": "氮氧化物", "unit": "mg/m³"},
    "so2": {"hourly": 50, "peak": 100, "name": "二氧化硫", "unit": "mg/m³"},
    "co": {"hourly": 100, "peak": 500, "name": "一氧化碳", "unit": "ppm"},
    "dust": {"hourly": 10, "peak": 30, "name": "粉尘", "unit": "mg/m³"},
}

DEFAULT_O2_CURVE = {
    "0.2": 7.0,
    "0.3": 6.5,
    "0.4": 6.0,
    "0.5": 5.0,
    "0.6": 4.5,
    "0.7": 4.0,
    "0.8": 3.8,
    "0.9": 3.6,
    "1.0": 3.5,
}

DEFAULT_DIAG_THRESHOLDS = {
    "exhaust_temp_high": 145,
    "co_spike": 200,
    "fly_ash_carbon_high": 5,
    "sh_temp_diff": 15,
    "o2_deviation": 0.8,
}

DEFAULT_Q5_TABLE = {
    "0.2": 2.8,
    "0.3": 2.3,
    "0.4": 2.0,
    "0.5": 1.8,
    "0.6": 1.6,
    "0.7": 1.5,
    "0.8": 1.4,
    "0.9": 1.3,
    "1.0": 1.2,
}


def init_db():
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS raw_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                boiler_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                data_json TEXT NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS aggregated_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                boiler_id TEXT NOT NULL,
                window_start TEXT NOT NULL,
                data_json TEXT NOT NULL,
                efficiency REAL,
                q2 REAL,
                q3 REAL,
                q4 REAL,
                q5 REAL,
                o2_dev REAL,
                nox_intensity REAL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS point_limits (
                point_key TEXT PRIMARY KEY,
                point_name TEXT,
                unit TEXT,
                min_val REAL,
                max_val REAL,
                updated_at TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS emission_limits (
                pollutant TEXT PRIMARY KEY,
                name TEXT,
                unit TEXT,
                hourly REAL,
                peak REAL,
                updated_at TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS o2_curve (
                load_ratio TEXT PRIMARY KEY,
                o2_value REAL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS diag_thresholds (
                rule_key TEXT PRIMARY KEY,
                value REAL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS q5_table (
                load_ratio TEXT PRIMARY KEY,
                q5_value REAL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                boiler_id TEXT,
                timestamp TEXT,
                start_time TEXT,
                resolved_time TEXT,
                pollutant TEXT,
                type TEXT,
                level TEXT,
                value REAL,
                peak_value REAL DEFAULT 0,
                limit_val REAL,
                duration REAL DEFAULT 0,
                status TEXT DEFAULT 'active',
                notified INTEGER DEFAULT 0
            )
        """)
        try:
            c.execute("ALTER TABLE alerts ADD COLUMN start_time TEXT")
        except Exception:
            pass
        try:
            c.execute("ALTER TABLE alerts ADD COLUMN resolved_time TEXT")
        except Exception:
            pass
        try:
            c.execute("ALTER TABLE alerts ADD COLUMN peak_value REAL DEFAULT 0")
        except Exception:
            pass
        try:
            c.execute("ALTER TABLE alerts ADD COLUMN status TEXT DEFAULT 'active'")
        except Exception:
            pass
        try:
            c.execute("ALTER TABLE alerts ADD COLUMN notified INTEGER DEFAULT 0")
        except Exception:
            pass
        c.execute("""
            CREATE TABLE IF NOT EXISTS suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                boiler_id TEXT,
                rule_key TEXT,
                created_at TEXT,
                expires_at TEXT,
                priority INTEGER,
                urgency TEXT,
                diagnosis TEXT,
                action TEXT,
                expected_effect TEXT,
                active INTEGER DEFAULT 1
            )
        """)
        try:
            c.execute("ALTER TABLE suggestions ADD COLUMN rule_key TEXT")
        except Exception:
            pass
        c.execute("""
            CREATE TABLE IF NOT EXISTS config_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_type TEXT,
                old_value TEXT,
                new_value TEXT,
                changed_at TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS health_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                boiler_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                combustion_score REAL,
                steam_water_score REAL,
                emission_score REAL,
                efficiency_score REAL,
                overall_score REAL,
                combustion_details TEXT,
                steam_water_details TEXT,
                emission_details TEXT,
                efficiency_details TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS predictive_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                boiler_id TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                param_key TEXT NOT NULL,
                param_name TEXT,
                predicted_exceed_time TEXT,
                current_value REAL,
                predicted_peak REAL,
                threshold_value REAL,
                minutes_to_exceed REAL,
                status TEXT DEFAULT 'active'
            )
        """)
        try:
            c.execute("ALTER TABLE predictive_alerts ADD COLUMN resolved_at TEXT")
        except Exception:
            pass
        try:
            c.execute("ALTER TABLE predictive_alerts ADD COLUMN confirmed_at TEXT")
        except Exception:
            pass
        try:
            c.execute("ALTER TABLE predictive_alerts ADD COLUMN muted_until TEXT")
        except Exception:
            pass
        c.execute("CREATE INDEX IF NOT EXISTS idx_health_boiler_ts ON health_scores(boiler_id, timestamp)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_pred_alert_boiler ON predictive_alerts(boiler_id, status)")
        conn.commit()
        _seed_defaults(conn)


def _seed_defaults(conn):
    c = conn.cursor()
    for k, v in DEFAULT_POINT_LIMITS.items():
        c.execute("SELECT count(*) FROM point_limits WHERE point_key=?", (k,))
        if c.fetchone()[0] == 0:
            c.execute(
                "INSERT INTO point_limits VALUES (?,?,?,?,?,?)",
                (k, v["name"], v["unit"], v["min"], v["max"], datetime.now().isoformat()),
            )
    for k, v in DEFAULT_EMISSION_LIMITS.items():
        c.execute("SELECT count(*) FROM emission_limits WHERE pollutant=?", (k,))
        if c.fetchone()[0] == 0:
            c.execute(
                "INSERT INTO emission_limits VALUES (?,?,?,?,?,?)",
                (k, v["name"], v["unit"], v["hourly"], v["peak"], datetime.now().isoformat()),
            )
    for k, v in DEFAULT_O2_CURVE.items():
        c.execute("SELECT count(*) FROM o2_curve WHERE load_ratio=?", (k,))
        if c.fetchone()[0] == 0:
            c.execute("INSERT INTO o2_curve VALUES (?,?)", (k, v))
    for k, v in DEFAULT_DIAG_THRESHOLDS.items():
        c.execute("SELECT count(*) FROM diag_thresholds WHERE rule_key=?", (k,))
        if c.fetchone()[0] == 0:
            c.execute("INSERT INTO diag_thresholds VALUES (?,?)", (k, v))
    for k, v in DEFAULT_Q5_TABLE.items():
        c.execute("SELECT count(*) FROM q5_table WHERE load_ratio=?", (k,))
        if c.fetchone()[0] == 0:
            c.execute("INSERT INTO q5_table VALUES (?,?)", (k, v))
    conn.commit()


def insert_raw(boiler_id, timestamp, data_dict):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO raw_data (boiler_id, timestamp, data_json) VALUES (?,?,?)",
            (boiler_id, timestamp, json.dumps(data_dict, ensure_ascii=False)),
        )


def insert_aggregated(boiler_id, window_start, data_dict, metrics):
    with get_db() as conn:
        conn.execute(
            """INSERT INTO aggregated_data
               (boiler_id, window_start, data_json, efficiency, q2, q3, q4, q5, o2_dev, nox_intensity)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                boiler_id,
                window_start,
                json.dumps(data_dict, ensure_ascii=False),
                metrics.get("efficiency"),
                metrics.get("q2"),
                metrics.get("q3"),
                metrics.get("q4"),
                metrics.get("q5"),
                metrics.get("o2_dev"),
                metrics.get("nox_intensity"),
            ),
        )


def get_point_limits():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM point_limits").fetchall()
        return {
            r["point_key"]: {
                "name": r["point_name"],
                "unit": r["unit"],
                "min": r["min_val"],
                "max": r["max_val"],
            }
            for r in rows
        }


def get_emission_limits():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM emission_limits").fetchall()
        return {
            r["pollutant"]: {
                "name": r["name"],
                "unit": r["unit"],
                "hourly": r["hourly"],
                "peak": r["peak"],
            }
            for r in rows
        }


def get_o2_curve():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM o2_curve ORDER BY load_ratio").fetchall()
        return [(float(r["load_ratio"]), r["o2_value"]) for r in rows]


def get_diag_thresholds():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM diag_thresholds").fetchall()
        return {r["rule_key"]: r["value"] for r in rows}


def get_q5_table():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM q5_table ORDER BY load_ratio").fetchall()
        return [(float(r["load_ratio"]), r["q5_value"]) for r in rows]


def update_point_limits(limits_dict):
    with get_db() as conn:
        old = get_point_limits()
        for k, v in limits_dict.items():
            conn.execute(
                """UPDATE point_limits SET point_name=?, unit=?, min_val=?, max_val=?, updated_at=?
                   WHERE point_key=?""",
                (v["name"], v["unit"], v["min"], v["max"], datetime.now().isoformat(), k),
            )
            conn.execute(
                "INSERT INTO config_history VALUES (?,?,?,?,?)",
                (
                    "point_limits:" + k,
                    json.dumps(old.get(k), ensure_ascii=False),
                    json.dumps(v, ensure_ascii=False),
                    datetime.now().isoformat(),
                ),
            )


def update_emission_limits(limits_dict):
    with get_db() as conn:
        old = get_emission_limits()
        for k, v in limits_dict.items():
            conn.execute(
                """UPDATE emission_limits SET name=?, unit=?, hourly=?, peak=?, updated_at=?
                   WHERE pollutant=?""",
                (v["name"], v["unit"], v["hourly"], v["peak"], datetime.now().isoformat(), k),
            )
            conn.execute(
                "INSERT INTO config_history VALUES (?,?,?,?,?)",
                (
                    "emission_limits:" + k,
                    json.dumps(old.get(k), ensure_ascii=False),
                    json.dumps(v, ensure_ascii=False),
                    datetime.now().isoformat(),
                ),
            )


def get_recent_aggregated(boiler_id, minutes=30):
    start = (datetime.now() - timedelta(minutes=minutes)).isoformat()
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM aggregated_data WHERE boiler_id=? AND window_start>=? ORDER BY window_start",
            (boiler_id, start),
        ).fetchall()
        result = []
        for r in rows:
            d = json.loads(r["data_json"])
            d["window_start"] = r["window_start"]
            d["efficiency"] = r["efficiency"]
            d["q2"] = r["q2"]
            d["q3"] = r["q3"]
            d["q4"] = r["q4"]
            d["q5"] = r["q5"]
            d["o2_dev"] = r["o2_dev"]
            d["nox_intensity"] = r["nox_intensity"]
            result.append(d)
        return result


def get_aggregated_range(boiler_id, start_time, end_time):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM aggregated_data WHERE boiler_id=? AND window_start>=? AND window_start<=? ORDER BY window_start",
            (boiler_id, start_time, end_time),
        ).fetchall()
        result = []
        for r in rows:
            d = json.loads(r["data_json"])
            d["window_start"] = r["window_start"]
            d["efficiency"] = r["efficiency"]
            d["q2"] = r["q2"]
            d["q3"] = r["q3"]
            d["q4"] = r["q4"]
            d["q5"] = r["q5"]
            d["o2_dev"] = r["o2_dev"]
            d["nox_intensity"] = r["nox_intensity"]
            result.append(d)
        return result


def insert_alert(boiler_id, pollutant, alert_type, level, value, limit_val):
    now = datetime.now().isoformat()
    with get_db() as conn:
        conn.execute(
            """INSERT INTO alerts
               (boiler_id, timestamp, start_time, pollutant, type, level, value, peak_value, limit_val, duration, status, notified)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (boiler_id, now, now, pollutant, alert_type, level, value, value, limit_val, 0, 'active', 0),
        )


def get_recent_alerts(boiler_id, minutes=60):
    start = (datetime.now() - timedelta(minutes=minutes)).isoformat()
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM alerts WHERE boiler_id=? AND timestamp>=? ORDER BY timestamp DESC",
            (boiler_id, start),
        ).fetchall()
        return [dict(r) for r in rows]


def get_active_alerts(boiler_id):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM alerts WHERE boiler_id=? AND status='active' ORDER BY start_time ASC",
            (boiler_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_active_alert_by_key(boiler_id, pollutant, alert_type, level):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM alerts WHERE boiler_id=? AND pollutant=? AND type=? AND level=? AND status='active' ORDER BY start_time DESC LIMIT 1",
            (boiler_id, pollutant, alert_type, level),
        ).fetchone()
        return dict(row) if row else None


def update_alert_peak(alert_id, value, current_hourly=None):
    with get_db() as conn:
        now = datetime.now()
        row = conn.execute("SELECT * FROM alerts WHERE id=?", (alert_id,)).fetchone()
        if row:
            start_ts = datetime.fromisoformat(row["start_time"])
            duration = (now - start_ts).total_seconds()
            new_peak = max(row["peak_value"] or 0, value or 0)
            update_fields = ["peak_value=?", "duration=?"]
            update_values = [new_peak, duration]
            if current_hourly is not None:
                update_fields.append("value=?")
                update_values.append(current_hourly)
            update_values.append(alert_id)
            conn.execute(
                f"UPDATE alerts SET {', '.join(update_fields)} WHERE id=?",
                tuple(update_values),
            )


def resolve_alert(alert_id):
    with get_db() as conn:
        now = datetime.now().isoformat()
        row = conn.execute("SELECT * FROM alerts WHERE id=?", (alert_id,)).fetchone()
        if row:
            start_ts = datetime.fromisoformat(row["start_time"])
            duration = (datetime.fromisoformat(now) - start_ts).total_seconds()
            conn.execute(
                "UPDATE alerts SET status='resolved', resolved_time=?, duration=? WHERE id=?",
                (now, duration, alert_id),
            )


def resolve_all_active_for_pollutant(boiler_id, pollutant):
    with get_db() as conn:
        now = datetime.now().isoformat()
        rows = conn.execute(
            "SELECT * FROM alerts WHERE boiler_id=? AND pollutant=? AND status='active'",
            (boiler_id, pollutant),
        ).fetchall()
        for row in rows:
            start_ts = datetime.fromisoformat(row["start_time"])
            duration = (datetime.fromisoformat(now) - start_ts).total_seconds()
            conn.execute(
                "UPDATE alerts SET status='resolved', resolved_time=?, duration=? WHERE id=?",
                (now, duration, row["id"]),
            )


def get_unnotified_alerts(boiler_id):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM alerts WHERE boiler_id=? AND notified=0 ORDER BY timestamp ASC",
            (boiler_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def mark_alerts_notified(alert_ids):
    if not alert_ids:
        return
    with get_db() as conn:
        for aid in alert_ids:
            conn.execute("UPDATE alerts SET notified=1 WHERE id=?", (aid,))


def get_alert_history(boiler_id, limit=50):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM alerts WHERE boiler_id=? ORDER BY timestamp DESC LIMIT ?",
            (boiler_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def get_alert_count(boiler_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM alerts WHERE boiler_id=?",
            (boiler_id,),
        ).fetchone()
        return row["cnt"] if row else 0


def add_suggestion(boiler_id, suggestion):
    now = datetime.now()
    expires = now + timedelta(seconds=60)
    rule_key = suggestion.get("rule_key")
    with get_db() as conn:
        conn.execute("UPDATE suggestions SET active=0 WHERE expires_at<?", (now.isoformat(),))
        if rule_key:
            conn.execute(
                "UPDATE suggestions SET active=0 WHERE boiler_id=? AND rule_key=? AND active=1",
                (boiler_id, rule_key),
            )
        conn.execute(
            """INSERT INTO suggestions
               (boiler_id, rule_key, created_at, expires_at, priority, urgency, diagnosis, action, expected_effect, active)
               VALUES (?,?,?,?,?,?,?,?,?,1)""",
            (
                boiler_id,
                rule_key,
                now.isoformat(),
                expires.isoformat(),
                suggestion["priority"],
                suggestion["urgency"],
                suggestion["diagnosis"],
                suggestion["action"],
                suggestion["expected_effect"],
            ),
        )


def replace_suggestions(boiler_id, new_suggestions):
    now = datetime.now()
    with get_db() as conn:
        conn.execute("UPDATE suggestions SET active=0 WHERE boiler_id=?", (boiler_id,))
        for s in new_suggestions:
            expires = now + timedelta(seconds=60)
            conn.execute(
                """INSERT INTO suggestions
                   (boiler_id, rule_key, created_at, expires_at, priority, urgency, diagnosis, action, expected_effect, active)
                   VALUES (?,?,?,?,?,?,?,?,?,1)""",
                (
                    boiler_id,
                    s.get("rule_key"),
                    now.isoformat(),
                    expires.isoformat(),
                    s["priority"],
                    s["urgency"],
                    s["diagnosis"],
                    s["action"],
                    s["expected_effect"],
                ),
            )


def get_active_suggestions(boiler_id):
    now = datetime.now().isoformat()
    with get_db() as conn:
        conn.execute("UPDATE suggestions SET active=0 WHERE expires_at<?", (now,))
        rows = conn.execute(
            "SELECT * FROM suggestions WHERE boiler_id=? AND active=1 ORDER BY priority DESC, created_at DESC",
            (boiler_id,),
        ).fetchall()
        seen_keys = set()
        deduped = []
        duplicate_ids = []
        for r in rows:
            rk = r["rule_key"] if "rule_key" in r.keys() else None
            if not rk:
                diag = r["diagnosis"] or ""
                if "排烟温度" in diag and "氧量" in diag:
                    rk = "exhaust_high_o2_high"
                elif "CO浓度" in diag and "氧量" in diag:
                    rk = "co_spike_o2_low"
                elif "飞灰含碳量" in diag and "给煤量" in diag:
                    rk = "fly_ash_high_coal_high"
                elif "过热器" in diag and "温差" in diag:
                    rk = "sh_temp_diff"
                elif "氧量偏差" in diag:
                    rk = "o2_deviation"
                elif "主蒸汽温度" in diag and "偏低" in diag:
                    rk = "main_steam_temp_low"
                else:
                    rk = f"gen_{diag[:15]}"
            if rk in seen_keys:
                duplicate_ids.append(r["id"])
                continue
            seen_keys.add(rk)
            item = dict(r)
            if "rule_key" not in item:
                item["rule_key"] = rk
            deduped.append(item)
        for did in duplicate_ids:
            conn.execute("UPDATE suggestions SET active=0 WHERE id=?", (did,))
        return deduped[:5]

def clear_all_suggestions(boiler_id=None):
    with get_db() as conn:
        if boiler_id:
            conn.execute("UPDATE suggestions SET active=0 WHERE boiler_id=?", (boiler_id,))
        else:
            conn.execute("UPDATE suggestions SET active=0")


def get_config_history(limit=50):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM config_history ORDER BY changed_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_hourly_emission_stats(boiler_id, start_time, end_time):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM aggregated_data WHERE boiler_id=? AND window_start>=? AND window_start<=? ORDER BY window_start",
            (boiler_id, start_time, end_time),
        ).fetchall()
        result = []
        for r in rows:
            d = json.loads(r["data_json"])
            d["window_start"] = r["window_start"]
            result.append(d)
        return result


def insert_health_score(boiler_id, scores, details):
    now = datetime.now().isoformat()
    with get_db() as conn:
        conn.execute(
            """INSERT INTO health_scores
               (boiler_id, timestamp, combustion_score, steam_water_score, emission_score,
                efficiency_score, overall_score, combustion_details, steam_water_details,
                emission_details, efficiency_details)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                boiler_id,
                now,
                scores.get("combustion"),
                scores.get("steam_water"),
                scores.get("emission"),
                scores.get("efficiency"),
                scores.get("overall"),
                json.dumps(details.get("combustion"), ensure_ascii=False),
                json.dumps(details.get("steam_water"), ensure_ascii=False),
                json.dumps(details.get("emission"), ensure_ascii=False),
                json.dumps(details.get("efficiency"), ensure_ascii=False),
            ),
        )


def get_latest_health_score(boiler_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM health_scores WHERE boiler_id=? ORDER BY timestamp DESC LIMIT 1",
            (boiler_id,),
        ).fetchone()
        if not row:
            return None
        result = dict(row)
        for key in ["combustion_details", "steam_water_details", "emission_details", "efficiency_details"]:
            if result.get(key):
                try:
                    result[key] = json.loads(result[key])
                except Exception:
                    pass
        return result


def get_health_score_history(boiler_id, minutes=120):
    start = (datetime.now() - timedelta(minutes=minutes)).isoformat()
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM health_scores WHERE boiler_id=? AND timestamp>=? ORDER BY timestamp",
            (boiler_id, start),
        ).fetchall()
        return [dict(r) for r in rows]


def insert_predictive_alert(boiler_id, param_key, param_name, predicted_exceed_time,
                            current_value, predicted_peak, threshold_value, minutes_to_exceed):
    now = datetime.now().isoformat()
    with get_db() as conn:
        conn.execute(
            """INSERT INTO predictive_alerts
               (boiler_id, generated_at, param_key, param_name, predicted_exceed_time,
                current_value, predicted_peak, threshold_value, minutes_to_exceed, status)
               VALUES (?,?,?,?,?,?,?,?,?, 'active')""",
            (
                boiler_id,
                now,
                param_key,
                param_name,
                predicted_exceed_time,
                current_value,
                predicted_peak,
                threshold_value,
                minutes_to_exceed,
            ),
        )


def expire_old_predictive_alerts(boiler_id):
    now = datetime.now().isoformat()
    with get_db() as conn:
        conn.execute(
            "UPDATE predictive_alerts SET status='expired' WHERE boiler_id=? AND predicted_exceed_time<? AND status='active'",
            (boiler_id, now),
        )


def get_active_predictive_alerts(boiler_id):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM predictive_alerts WHERE boiler_id=? AND status='active' ORDER BY minutes_to_exceed ASC",
            (boiler_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def resolve_predictive_alert(alert_id):
    with get_db() as conn:
        now = datetime.now().isoformat()
        conn.execute(
            "UPDATE predictive_alerts SET status='resolved', resolved_at=? WHERE id=?",
            (now, alert_id),
        )


def update_predictive_alert(alert_id, predicted_exceed_time, current_value, predicted_peak, minutes_to_exceed):
    with get_db() as conn:
        conn.execute(
            """UPDATE predictive_alerts
               SET predicted_exceed_time=?, current_value=?, predicted_peak=?, minutes_to_exceed=?
               WHERE id=?""",
            (predicted_exceed_time, current_value, predicted_peak, minutes_to_exceed, alert_id),
        )


def get_health_scores_by_time_range(boiler_id, start_time, end_time):
    with get_db() as conn:
        rows = conn.execute(
            """SELECT combustion_score, steam_water_score, emission_score, efficiency_score 
               FROM health_scores 
               WHERE boiler_id=? AND timestamp>=? AND timestamp<=? 
               ORDER BY timestamp""",
            (boiler_id, start_time, end_time),
        ).fetchall()
        return [dict(r) for r in rows]


def confirm_predictive_alert(alert_id):
    with get_db() as conn:
        now = datetime.now().isoformat()
        conn.execute(
            "UPDATE predictive_alerts SET confirmed_at=?, status='confirmed' WHERE id=?",
            (now, alert_id),
        )


def mute_predictive_alert(alert_id, minutes=30):
    with get_db() as conn:
        muted_until = (datetime.now() + timedelta(minutes=minutes)).isoformat()
        conn.execute(
            "UPDATE predictive_alerts SET muted_until=?, status='muted' WHERE id=?",
            (muted_until, alert_id),
        )


def get_non_muted_predictive_alerts(boiler_id, only_unconfirmed=False):
    now = datetime.now().isoformat()
    with get_db() as conn:
        query = """SELECT * FROM predictive_alerts 
                   WHERE boiler_id=? AND status IN ('active', 'confirmed') 
                   AND (muted_until IS NULL OR muted_until < ?)"""
        params = [boiler_id, now]
        if only_unconfirmed:
            query += " AND confirmed_at IS NULL"
        query += " ORDER BY CASE WHEN confirmed_at IS NULL THEN 0 ELSE 1 END, minutes_to_exceed ASC"
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
