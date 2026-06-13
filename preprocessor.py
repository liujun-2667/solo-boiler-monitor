from collections import deque
from datetime import datetime, timedelta
import database as db


class DataPreprocessor:
    def __init__(self, boiler_id="Boiler-1"):
        self.boiler_id = boiler_id
        self.last_values = {}
        self.window_buffer = deque()
        self.smoothing_buffer = {}
        self.current_window_start = None

    def process_raw(self, timestamp_str, raw_data):
        db.insert_raw(self.boiler_id, timestamp_str, raw_data)
        limits = db.get_point_limits()
        filtered = {}
        for key, val in raw_data.items():
            if key not in limits:
                filtered[key] = val
                continue
            lm = limits[key]
            if val is None or (isinstance(val, (int, float)) and (val < lm["min"] or val > lm["max"])):
                filtered[key] = self.last_values.get(key)
            else:
                filtered[key] = val
                self.last_values[key] = val
        for key in limits:
            if key not in filtered or filtered[key] is None:
                filtered[key] = self.last_values.get(key)
        for key, val in filtered.items():
            if key not in self.smoothing_buffer:
                self.smoothing_buffer[key] = deque(maxlen=5)
            if val is not None:
                self.smoothing_buffer[key].append(val)
            buf = self.smoothing_buffer[key]
            if len(buf) >= 3:
                filtered[key] = sum(buf) / len(buf)
            elif len(buf) > 0:
                filtered[key] = buf[-1]
        ts = datetime.fromisoformat(timestamp_str)
        window_ts = ts.replace(second=(ts.second // 30) * 30, microsecond=0)
        if self.current_window_start is None:
            self.current_window_start = window_ts
        self.window_buffer.append({"timestamp": ts, "data": filtered})
        if window_ts != self.current_window_start and len(self.window_buffer) > 0:
            agg = self._aggregate_window(self.current_window_start)
            if agg:
                return agg
            self.current_window_start = window_ts
        return None

    def _aggregate_window(self, window_start):
        if len(self.window_buffer) == 0:
            return None
        keys = set()
        for item in self.window_buffer:
            keys.update(item["data"].keys())
        aggregated = {}
        for key in keys:
            vals = [item["data"][key] for item in self.window_buffer if item["data"].get(key) is not None]
            if vals:
                aggregated[key] = sum(vals) / len(vals)
            else:
                aggregated[key] = self.last_values.get(key)
        self.window_buffer.clear()
        return {"window_start": window_start.isoformat(), "data": aggregated}
