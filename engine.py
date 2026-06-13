import threading
from datetime import datetime
import database as db
from preprocessor import DataPreprocessor
from efficiency import compute_all_metrics
from diagnostics import persist_suggestions
from emissions import EmissionMonitor


class BoilerEngine:
    def __init__(self):
        self.lock = threading.Lock()
        self.preprocessors = {}
        self.emission_monitors = {}
        self.latest_data = {}

    def _get_or_create(self, boiler_id):
        if boiler_id not in self.preprocessors:
            self.preprocessors[boiler_id] = DataPreprocessor(boiler_id)
            self.emission_monitors[boiler_id] = EmissionMonitor(boiler_id)
        return self.preprocessors[boiler_id], self.emission_monitors[boiler_id]

    def ingest(self, boiler_id, timestamp_str, raw_data):
        with self.lock:
            preproc, em = self._get_or_create(boiler_id)
            agg = preproc.process_raw(timestamp_str, raw_data)
            if agg is not None:
                metrics = compute_all_metrics(agg["data"])
                db.insert_aggregated(boiler_id, agg["window_start"], agg["data"], metrics)
                em.process(agg["window_start"], agg["data"])
                persist_suggestions(boiler_id, agg["data"], metrics)
                self.latest_data[boiler_id] = {
                    "window_start": agg["window_start"],
                    "data": agg["data"],
                    "metrics": metrics,
                }
            if boiler_id not in self.latest_data:
                self.latest_data[boiler_id] = {
                    "window_start": timestamp_str,
                    "data": raw_data,
                    "metrics": compute_all_metrics(raw_data),
                }

    def get_latest(self, boiler_id):
        return self.latest_data.get(boiler_id)


engine = BoilerEngine()
