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
                pollutant TEXT,
                type TEXT,
                level TEXT,
                value REAL,
                limit_val REAL,
                duration REAL DEFAULT 0
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                boiler_id TEXT,
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
        c.execute("""
            CREATE TABLE IF NOT EXISTS config_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_type TEXT,
                old_value TEXT,
                new_value TEXT,
                changed_at TEXT
            )
        """)
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
    with get_db() as conn:
        conn.execute(
            "INSERT INTO alerts (boiler_id, timestamp, pollutant, type, level, value, limit_val) VALUES (?,?,?,?,?,?,?)",
            (boiler_id, datetime.now().isoformat(), pollutant, alert_type, level, value, limit_val),
        )


def get_recent_alerts(boiler_id, minutes=60):
    start = (datetime.now() - timedelta(minutes=minutes)).isoformat()
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM alerts WHERE boiler_id=? AND timestamp>=? ORDER BY timestamp DESC",
            (boiler_id, start),
        ).fetchall()
        return [dict(r) for r in rows]


def add_suggestion(boiler_id, suggestion):
    now = datetime.now()
    expires = now + timedelta(seconds=60)
    with get_db() as conn:
        conn.execute(
            """INSERT INTO suggestions
               (boiler_id, created_at, expires_at, priority, urgency, diagnosis, action, expected_effect, active)
               VALUES (?,?,?,?,?,?,?,?,1)""",
            (
                boiler_id,
                now.isoformat(),
                expires.isoformat(),
                suggestion["priority"],
                suggestion["urgency"],
                suggestion["diagnosis"],
                suggestion["action"],
                suggestion["expected_effect"],
            ),
        )


def get_active_suggestions(boiler_id):
    now = datetime.now().isoformat()
    with get_db() as conn:
        conn.execute("UPDATE suggestions SET active=0 WHERE expires_at<?", (now,))
        rows = conn.execute(
            "SELECT * FROM suggestions WHERE boiler_id=? AND active=1 ORDER BY priority DESC, created_at DESC LIMIT 5",
            (boiler_id,),
        ).fetchall()
        return [dict(r) for r in rows]


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
