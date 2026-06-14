from collections import deque
from datetime import datetime, timedelta
import statistics
import database as db


class EmissionMonitor:
    def __init__(self, boiler_id="Boiler-1"):
        self.boiler_id = boiler_id
        self.hourly_buffers = {p: deque() for p in ["nox", "so2", "co", "dust"]}
        self.alert_state = {p: {"warning": False, "alarm": False} for p in ["nox", "so2", "co", "dust"]}
        self.active_alert_ids = {}

    def _prune_buffer(self, buf, minutes=60):
        cutoff = datetime.now() - timedelta(minutes=minutes)
        while buf and buf[0][0] < cutoff:
            buf.popleft()

    def process(self, timestamp_str, data):
        ts = datetime.fromisoformat(timestamp_str)
        limits = db.get_emission_limits()
        results = {}
        for pollutant in ["nox", "so2", "co", "dust"]:
            val = data.get(pollutant)
            if val is None:
                continue
            self.hourly_buffers[pollutant].append((ts, val))
            self._prune_buffer(self.hourly_buffers[pollutant])
            buf_vals = [v for _, v in self.hourly_buffers[pollutant]]
            hourly_mean = statistics.mean(buf_vals) if buf_vals else 0
            lim = limits.get(pollutant, {})
            hourly_limit = lim.get("hourly", 100)
            peak_limit = lim.get("peak", 200)
            level = "normal"

            over_peak = val > peak_limit
            over_hourly = hourly_mean > hourly_limit
            near_limit = hourly_mean > hourly_limit * 0.8 or val > peak_limit * 0.8

            if over_peak:
                level = "alarm"
                self._ensure_alert(pollutant, "peak", "alarm", val, peak_limit, hourly_mean)
                self._resolve_alert_if_exists(pollutant, "hourly", "warning")
            elif over_hourly:
                level = "alarm"
                self._ensure_alert(pollutant, "hourly", "alarm", hourly_mean, hourly_limit, val)
                self._resolve_alert_if_exists(pollutant, "hourly", "warning")
            elif near_limit:
                level = "warning"
                self._ensure_alert(pollutant, "hourly", "warning", max(hourly_mean, val), hourly_limit, val)
            else:
                self._resolve_alert_if_exists(pollutant, "peak", "alarm")
                self._resolve_alert_if_exists(pollutant, "hourly", "alarm")
                self._resolve_alert_if_exists(pollutant, "hourly", "warning")

            results[pollutant] = {
                "value": round(val, 2),
                "hourly_mean": round(hourly_mean, 2),
                "level": level,
                "hourly_limit": hourly_limit,
                "peak_limit": peak_limit,
            }
        return results

    def _key(self, pollutant, alert_type, level):
        return f"{pollutant}_{alert_type}_{level}"

    def _ensure_alert(self, pollutant, alert_type, level, value, limit_val, peak_val=None):
        key = self._key(pollutant, alert_type, level)
        if key in self.active_alert_ids:
            alert_id = self.active_alert_ids[key]
            pv = peak_val if peak_val is not None else value
            db.update_alert_peak(alert_id, pv, current_hourly=value)
            return
        existing = db.get_active_alert_by_key(self.boiler_id, pollutant, alert_type, level)
        if existing:
            self.active_alert_ids[key] = existing["id"]
            pv = peak_val if peak_val is not None else value
            db.update_alert_peak(existing["id"], pv, current_hourly=value)
            return
        db.insert_alert(self.boiler_id, pollutant, alert_type, level, value, limit_val)
        new_alert = db.get_active_alert_by_key(self.boiler_id, pollutant, alert_type, level)
        if new_alert:
            self.active_alert_ids[key] = new_alert["id"]

    def _resolve_alert_if_exists(self, pollutant, alert_type, level):
        key = self._key(pollutant, alert_type, level)
        if key in self.active_alert_ids:
            db.resolve_alert(self.active_alert_ids[key])
            del self.active_alert_ids[key]
            return
        existing = db.get_active_alert_by_key(self.boiler_id, pollutant, alert_type, level)
        if existing:
            db.resolve_alert(existing["id"])

    def get_monthly_report(self, boiler_id, year, month):
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)
        data = db.get_hourly_emission_stats(boiler_id, start.isoformat(), end.isoformat())
        if not data:
            return None
        daily = {}
        for row in data:
            ts = datetime.fromisoformat(row["window_start"])
            day_key = ts.date().isoformat()
            if day_key not in daily:
                daily[day_key] = {p: [] for p in ["nox", "so2", "co", "dust"]}
            for p in ["nox", "so2", "co", "dust"]:
                if row.get(p) is not None:
                    daily[day_key][p].append(row[p])
        daily_stats = {}
        for day, vals in daily.items():
            daily_stats[day] = {}
            for p, vs in vals.items():
                daily_stats[day][p] = {
                    "mean": statistics.mean(vs) if vs else 0,
                    "max": max(vs) if vs else 0,
                }
        alerts = db.get_recent_alerts(boiler_id, minutes=60 * 24 * 31)
        total_hours = len(data) * 30 / 3600
        limit = db.get_emission_limits()
        compliant_hours = total_hours
        for a in alerts:
            if a.get("level") == "alarm":
                compliant_hours = max(0, compliant_hours - 0.5)
        compliance_rate = 100.0 * compliant_hours / max(1, total_hours)
        total_emission = {}
        for p in ["nox", "so2", "co", "dust"]:
            vals = [r.get(p, 0) for r in data if r.get(p) is not None]
            if vals:
                total_emission[p] = statistics.mean(vals) * len(data) * 30
            else:
                total_emission[p] = 0
        return {
            "daily_stats": daily_stats,
            "alert_count": len(alerts),
            "compliance_rate": round(compliance_rate, 2),
            "total_emission_kg": total_emission,
            "total_hours": round(total_hours, 1),
        }
