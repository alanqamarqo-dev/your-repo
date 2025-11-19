#!/usr/bin/env python3
"""Simple AGL daemon that runs periodic cycles (reasoning, live training, memory sync).

This is intentionally lightweight and resilient: missing project-specific
callables are handled gracefully so the daemon won't crash on import.
Adjust function imports to match your project's module paths if needed.
"""
from __future__ import annotations

# --- path bootstrap (put at top of scripts/agl_daemon.py) ---
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# ------------------------------------------------------------

import time
import json
import traceback
import os
from datetime import datetime, UTC
from typing import Any

LOG_DIR = os.path.join("artifacts", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Default intervals (seconds)
EVERY_REASONING = 3 * 60 * 60
EVERY_LIVE_TRAIN = 6 * 60 * 60
EVERY_MEMORY_SYNC = 24 * 60 * 60

last_reasoning = 0.0
last_live_train = 0.0
last_memory_sync = 0.0


def log_event(name: str, ok: bool = True, info: Any = None, err: Any = None) -> None:
    rec = {
        "ts": datetime.now(UTC).isoformat(),
        "event": name,
        "ok": ok,
        "info": info or {},
        "err": (str(err) if err else None),
    }
    path = os.path.join(LOG_DIR, "daemon.log")
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass
    print(rec)


def run_reasoning_cycle() -> Any:
    try:
        # prefer a simple project-level stub
        from AGL.reasoning import run_reasoning_cycle as _rr  # type: ignore
        return _rr()
    except Exception as e:
        return {"error": "reasoning_impl_missing", "exc": str(e)}


def run_live_training() -> Any:
    try:
        from scripts.live_training import run_live_training as _lt  # type: ignore
        return _lt()
    except Exception as e:
        return {"error": "live_training_impl_missing", "exc": str(e)}


def run_memory_sync() -> Any:
    try:
        from AGL.memory import run_memory_sync as _ms  # type: ignore
        return _ms()
    except Exception as e:
        return {"error": "memory_sync_impl_missing", "exc": str(e)}


def health_ping() -> None:
    try:
        import urllib.request, json as _json
        with urllib.request.urlopen("http://127.0.0.1:8000/api/system/status", timeout=2) as r:
            body = _json.loads(r.read().decode("utf-8"))
        log_event("health", True, body, None)
    except Exception as e:
        log_event("health", False, None, str(e))


def main() -> None:
    global last_reasoning, last_live_train, last_memory_sync
    log_event("daemon_start", True, {"pid": os.getpid()})

    try:
        while True:
            now = time.time()

            if now - last_reasoning > EVERY_REASONING:
                try:
                    out = run_reasoning_cycle()
                    log_event("reasoning_cycle", True, {"result": out})
                except Exception:
                    log_event("reasoning_cycle", False, None, traceback.format_exc())
                last_reasoning = now

            if now - last_live_train > EVERY_LIVE_TRAIN:
                try:
                    out = run_live_training()
                    log_event("live_training", True, {"result": out})
                except Exception:
                    log_event("live_training", False, None, traceback.format_exc())
                last_live_train = now

            if now - last_memory_sync > EVERY_MEMORY_SYNC:
                try:
                    out = run_memory_sync()
                    log_event("memory_sync", True, {"result": out})
                except Exception:
                    log_event("memory_sync", False, None, traceback.format_exc())
                last_memory_sync = now

            # light health ping every ~10 minutes
            if int(now) % (10 * 60) < 2:
                try:
                    health_ping()
                except Exception:
                    pass

            time.sleep(5)
    except KeyboardInterrupt:
        log_event("daemon_stop", True, {"reason": "keyboard_interrupt"})


if __name__ == "__main__":
    main()
