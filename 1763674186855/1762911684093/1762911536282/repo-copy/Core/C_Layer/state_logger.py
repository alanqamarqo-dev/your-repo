# -*- coding: utf-8 -*-
import os
import json
import time
import pathlib
import threading
import queue
import uuid
import subprocess
from collections import deque
from typing import Deque, Dict, Any, Optional
import shutil
import gzip
from datetime import datetime, timedelta


def _get_git_sha_short() -> Optional[str]:
    try:
        p = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True)
        return p.stdout.strip()
    except Exception:
        return None


def _redact(obj: Any, keys_to_redact=None):
    """A conservative recursive redactor to remove probable secrets.

    keys_to_redact: iterable of substrings to match in keys (case-insensitive).
    Returns a copy with redacted values replaced by '<REDACTED>'.
    """
    if keys_to_redact is None:
        keys_to_redact = ("password", "secret", "api_key", "apikey", "token", "ssn", "idnumber")
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            kl = str(k).lower()
            if any(substr in kl for substr in keys_to_redact):
                out[k] = "<REDACTED>"
            else:
                out[k] = _redact(v, keys_to_redact)
        return out
    elif isinstance(obj, list):
        return [_redact(x, keys_to_redact) for x in obj]
    else:
        return obj


class StateLogger:
    """
    يحفظ آخر N لقطات حالة إلى الذاكرة + إلى ملفات JSON متسلسلة زمنيًا.

    Enhancements:
    - schema_version and standard tags
    - optional write-through to Core_Memory bridge (AGL_C_LAYER_BRIDGE_WRITE)
    - optional sanitization/redaction before storing (AGL_SANITIZE_SNAPSHOTS)
    - optional async writer queue (AGL_SNAPSHOT_ASYNC)
    - basic runtime metrics (snapshots_written, bridge_failures, avg_write_ms)
    """

    def __init__(self, maxlen: int = None):
        # feature flags
        self.enabled = os.getenv("AGL_C_LAYER_SNAPSHOTS", "0") == "1"
        self.sanitize = os.getenv("AGL_SANITIZE_SNAPSHOTS", "0") == "1"
        self.bridge_write = os.getenv("AGL_C_LAYER_BRIDGE_WRITE", "0") == "1"
        self.async_write = os.getenv("AGL_SNAPSHOT_ASYNC", "0") == "1"

        # sizes and retention
        self.maxlen = int(os.getenv("AGL_C_LAYER_SNAPSHOTS_N", str(maxlen or 20)))
        self.queue_max = int(os.getenv("AGL_SNAPSHOT_QUEUE_MAX", "1000"))

        # in-memory buffer
        self.buf: Deque[Dict[str, Any]] = deque(maxlen=self.maxlen)

        # paths (respect global artifacts dir if provided)
        artifacts_base = os.getenv("AGL_ARTIFACTS_DIR", "artifacts")
        self.dir = pathlib.Path(artifacts_base) / "state" / "snapshots"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.metrics_path = pathlib.Path(artifacts_base) / "state" / "metrics.jsonl"
        self.metrics_path.parent.mkdir(parents=True, exist_ok=True)

        # metrics
        self.metrics = {
            "snapshots_written": 0,
            "bridge_failures": 0,
            "queue_dropped": 0,
            "avg_write_ms": 0.0,
        }

        # async writer
        self._queue: Optional[queue.Queue] = None
        self._worker: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        if self.async_write:
            self._queue = queue.Queue(maxsize=self.queue_max)
            self._worker = threading.Thread(target=self._writer_loop, daemon=True)
            self._worker.start()

        # rotation counter to avoid running rotation on every write
        self._rotate_counter = 0

        # static tags
        self.run_id = os.getenv("AGL_RUN_ID", str(uuid.uuid4()))
        self.git_sha = os.getenv("AGL_GIT_SHA", _get_git_sha_short())

    def _writer_loop(self):
        while not self._stop_event.is_set():
            try:
                item = self._queue.get(timeout=0.5)
            except Exception:
                continue
            try:
                self._do_write(item)
            except Exception:
                # best-effort: update metrics
                self.metrics["queue_dropped"] += 1
            finally:
                try:
                    self._queue.task_done()
                except Exception:
                    pass

    def stop(self):
        if self._worker:
            self._stop_event.set()
            self._worker.join(timeout=1.0)

    def _serialize_record(self, record: Dict[str, Any]) -> str:
        return json.dumps(record, ensure_ascii=False, indent=2)

    def _do_write(self, record: Dict[str, Any]) -> None:
        """Actual synchronous write to disk and optional bridge."""
        t0 = time.time()
        # Write as JSONL line into a rolling snapshots.jsonl file for better IO
        try:
            line = json.dumps(record, ensure_ascii=False)
            jsonl = self.dir / "snapshots.jsonl"
            # append a single-line JSON entry
            with jsonl.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
            self.metrics["snapshots_written"] += 1
        except Exception:
            # best-effort: ignore disk write failures but continue
            pass

        # optional bridge write
        if self.bridge_write:
            try:
                from Core_Memory.bridge_singleton import get_bridge
                br = get_bridge()
                # store minimal envelope using the bridge API: put(type, payload, to=...)
                try:
                    br.put("c_layer_snapshot", record, to="ltm")
                except Exception:
                    try:
                        br.put("c_layer_snapshot", record, to="stm")
                    except Exception:
                        self.metrics["bridge_failures"] += 1
            except Exception:
                self.metrics["bridge_failures"] += 1

        t1 = time.time()
        wms = (t1 - t0) * 1000.0
        # moving average update (simple)
        prev = self.metrics.get("avg_write_ms", 0.0)
        alpha = 0.2
        self.metrics["avg_write_ms"] = (alpha * wms) + (1 - alpha) * prev

        # append metrics line
        try:
            with self.metrics_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"ts": time.time(), **self.metrics}, ensure_ascii=False) + "\n")
        except Exception:
            pass

        # If snapshot contains milestone-like tags, emit a lightweight biography event
        try:
            tags_obj = record.get("tags") or {}
            if isinstance(tags_obj, dict):
                tags_set = set(tags_obj.keys()) | set([str(v) for v in tags_obj.values() if isinstance(v, str)])
            elif isinstance(tags_obj, list):
                tags_set = set(tags_obj)
            else:
                tags_set = set()

            if tags_set & {"milestone", "success", "failure"}:
                try:
                    # avoid hard dependency on SelfModel instantiation: use identity_singleton if present
                    from Core_Consciousness.Self_Model import SelfModel
                    from Core_Memory.bridge_singleton import get_bridge
                    sm = None
                    try:
                        sm = SelfModel.identity_singleton()
                    except Exception:
                        try:
                            sm = SelfModel()
                        except Exception:
                            sm = None
                    if sm is not None:
                        sm.add_biography_event(kind="snapshot", note=f"state:{record.get('ts')}", source="StateLogger")
                        try:
                            sm.persist_profile(get_bridge())
                        except Exception:
                            pass
                        # optional auto-consolidation: best-effort, enabled via env var
                        try:
                            if os.getenv('AGL_ENABLE_AUTO_CONSOLIDATE', '0') == '1':
                                try:
                                    sm.consolidate_memory(get_bridge())
                                except Exception:
                                    pass
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass

        # optionally apply retention/rotation/compression policy, but only every N writes
        try:
            rotate_every = int(os.getenv("AGL_SNAPSHOT_ROTATE_EVERY", "1") or 1)
            self._rotate_counter = getattr(self, "_rotate_counter", 0) + 1
            if self._rotate_counter % max(rotate_every, 1) == 0:
                if os.getenv("AGL_SNAPSHOT_RETENTION_DAYS") or os.getenv("AGL_SNAPSHOT_MAX_FILES"):
                    try:
                        self._apply_retention_and_rotation()
                    except Exception:
                        pass
        except Exception:
            pass

    def snapshot(self, state: Dict[str, Any], tags: Optional[Dict[str, Any]] = None) -> str:
        """
        Record a snapshot. Returns path string (or empty if disabled).
        """
        if not self.enabled:
            return ""

        ts = time.time()

        # build standard record
        rec = {
            "schema_version": "1.0",
            "ts": ts,
            "state": state,
            "metrics": {},
            "errors": None,
            "tags": {
                "component": "C_Layer",
                "phase": tags.get("phase") if tags else "tick",
                "run_id": self.run_id,
                "git_sha": self.git_sha,
                **(tags or {}),
            },
        }

        # optional sanitization
        if self.sanitize:
            try:
                rec["state"] = _redact(rec["state"]) if rec["state"] is not None else rec["state"]
            except Exception:
                rec["state"] = {}

        # add to in-memory buffer
        try:
            self.buf.append(rec)
        except Exception:
            pass

        # enqueue or write immediately
        if self.async_write and self._queue is not None:
            try:
                self._queue.put_nowait(rec)
                # return a logical placeholder path (not yet flushed)
                return str(self.dir / f"{int(ts*1000)}.json")
            except queue.Full:
                self.metrics["queue_dropped"] += 1
                # fall back to synchronous write
                try:
                    self._do_write(rec)
                except Exception:
                    pass
                return str(self.dir / f"{int(ts*1000)}.json")
        else:
            try:
                self._do_write(rec)
            except Exception:
                pass
            return str(self.dir / f"{int(ts*1000)}.json")

    def latest(self):
        return self.buf[-1] if self.buf else None

    # --- retention / rotation / compression utilities ---
    def _gzip_file(self, path: pathlib.Path) -> None:
        try:
            gz = path.with_suffix(path.suffix + ".gz")
            with path.open("rb") as f_in, gzip.open(gz, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
            try:
                path.unlink()
            except Exception:
                pass
        except Exception:
            pass

    def _apply_retention_and_rotation(self) -> None:
        """Apply retention/rotation/compression according to environment variables.

        Strategies supported: age, count (comma-separated in AGL_SNAPSHOT_ROTATE_STRATEGY)
        """
        try:
            keep_days = int(os.getenv("AGL_SNAPSHOT_RETENTION_DAYS", "0") or 0)
            max_files = int(os.getenv("AGL_SNAPSHOT_MAX_FILES", "0") or 0)
            do_compress = os.getenv("AGL_SNAPSHOT_COMPRESS_OLD", "0") == "1"
            strategy = os.getenv("AGL_SNAPSHOT_ROTATE_STRATEGY", "age").split(",")

            # list files (json and gz)
            json_files = sorted(self.dir.glob("*.json"), key=lambda p: p.stat().st_mtime)
            gz_files = sorted(self.dir.glob("*.json.gz"), key=lambda p: p.stat().st_mtime)

            now = datetime.utcnow()

            # AGE strategy: compress or delete files older than keep_days
            if "age" in strategy and keep_days > 0:
                cutoff = now - timedelta(days=keep_days)
                for p in list(json_files):
                    try:
                        mtime = datetime.utcfromtimestamp(p.stat().st_mtime)
                        if mtime < cutoff:
                            if do_compress:
                                # compress JSON file to .json.gz
                                try:
                                    self._gzip_file(p)
                                except Exception:
                                    try:
                                        p.unlink()
                                    except Exception:
                                        pass
                            else:
                                try:
                                    p.unlink()
                                except Exception:
                                    pass
                    except Exception:
                        pass

            # refresh lists
            json_files = sorted(self.dir.glob("*.json"), key=lambda p: p.stat().st_mtime)
            gz_files = sorted(self.dir.glob("*.json.gz"), key=lambda p: p.stat().st_mtime)
            all_files = json_files + gz_files

            # COUNT strategy: keep newest max_files, drop older
            if "count" in strategy and max_files > 0 and len(all_files) > max_files:
                to_drop = len(all_files) - max_files
                for p in all_files[:to_drop]:
                    try:
                        p.unlink()
                    except Exception:
                        pass

            # update a simple rotation metric
            try:
                prev = self.metrics.get("rotation_runs", 0)
                self.metrics["rotation_runs"] = prev + 1
            except Exception:
                pass
        except Exception:
            # best-effort: don't let rotation break writes
            pass

