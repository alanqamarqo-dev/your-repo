"""Lightweight resource guard used to monitor CPU / memory and trigger emergency action.

This module tries to use psutil when available; otherwise it falls back to
best-effort measurements (may be limited on Windows without psutil).

Usage example:
    from tools.resource_guard import ResourceGuard
    with ResourceGuard():
        run_long_task()

Environment variables supported:
 - AGL_GUARD_ENABLED (1 to enable; default 1 when used)
 - AGL_GUARD_MAX_CPU_PCT (int, default 95)
 - AGL_GUARD_MAX_RSS_MB (int, default 8192)
 - AGL_GUARD_CHECK_INTERVAL (float seconds, default 1.0)

When thresholds are exceeded the guard will write an emergency report to
`artifacts/emergency_guard.json` and then terminate the process using os._exit(3).
"""

from __future__ import annotations
import os
import time
import threading
import json
import datetime
from typing import Optional, Callable

try:
    import psutil
except Exception:
    psutil = None


def _default_emergency_action(reason: str, snapshot: dict):
    os.makedirs('artifacts', exist_ok=True)
    path = os.path.join('artifacts', f'emergency_guard_{int(time.time())}.json')
    data = {
        'reason': reason,
        'snapshot': snapshot,
        'time': datetime.datetime.utcnow().isoformat() + 'Z'
    }
    try:
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
    except Exception:
        pass
    # Forcefully terminate to avoid further damage
    os._exit(3)


class ResourceGuard:
    def __init__(self,
                 max_cpu_pct: Optional[float]=None,
                 max_rss_mb: Optional[float]=None,
                 check_interval: float=1.0,
                 emergency_callback: Optional[Callable[[str, dict], None]] = None):
        self.enabled = os.getenv('AGL_GUARD_ENABLED', '1') == '1'
        self.max_cpu_pct = float(max_cpu_pct if max_cpu_pct is not None else os.getenv('AGL_GUARD_MAX_CPU_PCT', '95'))
        self.max_rss_mb = float(max_rss_mb if max_rss_mb is not None else os.getenv('AGL_GUARD_MAX_RSS_MB', '8192'))
        self.check_interval = float(os.getenv('AGL_GUARD_CHECK_INTERVAL', str(check_interval)))
        self.emergency_callback = emergency_callback or _default_emergency_action
        self._stop = threading.Event()
        self._thread = None

    def _snapshot(self):
        snap = {'pid': os.getpid()}
        try:
            if psutil:
                p = psutil.Process()
                with p.oneshot():
                    snap['cpu_percent_process'] = p.cpu_percent(interval=None)
                    snap['rss_mb'] = p.memory_info().rss / (1024*1024)
                    snap['system_cpu_percent'] = psutil.cpu_percent(interval=None)
                    snap['virtual_mem_mb'] = psutil.virtual_memory().used / (1024*1024)
            else:
                # best effort fallback
                snap['cpu_percent_process'] = None
                snap['rss_mb'] = None
                snap['system_cpu_percent'] = None
                snap['virtual_mem_mb'] = None
        except Exception as e:
            snap['error'] = str(e)
        return snap

    def _monitor_loop(self):
        # If psutil is available, initialize cpu_percent sampling
        if psutil:
            try:
                psutil.cpu_percent(interval=None)
                psutil.Process().cpu_percent(interval=None)
            except Exception:
                pass

        while not self._stop.wait(self.check_interval):
            snap = self._snapshot()
            try:
                cpu = snap.get('cpu_percent_process')
                rss = snap.get('rss_mb')
                if cpu is not None and cpu > self.max_cpu_pct:
                    self.emergency_callback(f'cpu_exceeded_{cpu}', snap)
                    return
                if rss is not None and rss > self.max_rss_mb:
                    self.emergency_callback(f'rss_exceeded_{rss}', snap)
                    return
            except Exception:
                try:
                    self.emergency_callback('monitor_exception', {'snapshot': snap})
                finally:
                    return

    def start(self):
        if not self.enabled:
            return
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.stop()
        return False
