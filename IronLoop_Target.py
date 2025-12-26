import time
import datetime
import random
import json
import uuid

class LogEntry:
    def __init__(self, timestamp, level, source, message, request_id):
        self.timestamp = timestamp
        self.level = level
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
        # Simulating parsing overhead
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
        chain = []
        # PERFORMANCE FLAW: O(N) scan for every request. 
        # If called M times, complexity is O(M*N).
        # Should use a hash map (dictionary) for O(1) lookup.
        for entry in self.log_history:
            if entry.request_id == target_request_id:
                chain.append(entry)
        return chain

    def detect_critical_failures(self):
        """
        Scans logs for critical errors that need immediate alerting.
        """
        critical_events = []
        for entry in self.log_history:
            # LOGIC FLAW: Case sensitivity.
            # Input data uses "Critical", "Error", "Warning".
            # This check misses "Critical" because it expects uppercase "CRITICAL".
            if entry.level == "CRITICAL": 
                critical_events.append(entry)
                self.alerts.append(f"ALERT: {entry.message}")
        return critical_events

    def correlate_all_requests(self):
        """
        Groups all logs by request ID for batch processing.
        """
        # PERFORMANCE FLAW: Nested loops O(N^2).
        # Extremely slow on large datasets.
        correlated = {}
        unique_ids = []
        
        # Get unique IDs first (inefficiently)
        for entry in self.log_history:
            if entry.request_id not in unique_ids:
                unique_ids.append(entry.request_id)
        
        # Nested scan
        for rid in unique_ids:
            group = []
            for entry in self.log_history:
                if entry.request_id == rid:
                    group.append(entry)
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
