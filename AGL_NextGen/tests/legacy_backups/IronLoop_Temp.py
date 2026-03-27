import time
import datetime
import random
import json
import uuid

class LogEntry:
    def __init__(self, timestamp, level, source, message, request_id):
        self.timestamp = timestamp
        self.level = level.upper()  # Fix for case sensitivity
        self.source = source
        self.message = message
        self.request_id = request_id

    def to_dict(self):
        return {
            'ts': self.timestamp,
            'lvl': self.level,
            'src': self.source,
            'msg': self.message,
            'rid': self.request_id
        }

class EnterpriseLogAnalyzer:
    """
    Enterprise-grade log analysis system for high-frequency server logs.
    Designed to correlate requests, detect anomalies, and generate alerts.
    """
    def __init__(self):
        # DESIGN FLAW: In-memory storage without rotation or limit.
        # Will cause MemoryError on long runs.
        self.log_history = [] 
        self.alerts = []
        self.active_sessions = {}

    def ingest_log(self, log_data):
        """Parses and stores a raw log line."""
        entry = LogEntry(
            log_data['timestamp'],
            log_data['level'],
            log_data['source'],
            log_data['message'],
            log_data.get('request_id', str(uuid.uuid4()))
        )
        self.log_history.append(entry)
        self._update_metrics(entry)

    def _update_metrics(self, entry):
        if entry.source not in self.active_sessions:
            self.active_sessions[entry.source] = 0
        self.active_sessions[entry.source] += 1

    def analyze_request_chain(self, target_request_id):
        """
        Finds all logs associated with a specific request ID to trace the transaction.
        """
        chain = [entry for entry in self.log_history if entry.request_id == target_request_id]
        return chain

    def detect_critical_failures(self):
        """
        Scans logs for critical errors that need immediate alerting.
        """
        critical_events = []
        for entry in self.log_history:
            if entry.level == "CRITICAL":  # Fix for case sensitivity
                critical_events.append(entry)
                self.alerts.append(f"ALERT: {entry.message}")
        return critical_events

    def correlate_all_requests(self):
        """
        Groups all logs by request ID for batch processing.
        """
        correlated = {}
        unique_ids = set(entry.request_id for entry in self.log_history)

        for rid in unique_ids:
            group = [entry for entry in self.log_history if entry.request_id == rid]
            correlated[rid] = group
            
        return correlated

    def generate_report(self):
        return {
            'total_logs': len(self.log_history),
            'alerts': len(self.alerts),
            'sessions': len(self.active_sessions)
        }

# Simulation of usage (for testing)
if __name__ == "__main__":
    analyzer = EnterpriseLogAnalyzer()
    print("System initialized.")