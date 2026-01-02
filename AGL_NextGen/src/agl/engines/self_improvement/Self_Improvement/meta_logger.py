# -*- coding: utf-8 -*-
import json
import os
import time
import uuid

OUT_DIR = os.path.join(os.getcwd(), 'artifacts', 'run_logs')
os.makedirs(OUT_DIR, exist_ok=True)


class MetaLogger:
    @staticmethod
    def start_session(state):
        session_id = str(uuid.uuid4())
        meta = {"session_id": session_id, "start": time.time(), "question": getattr(state, 'question', '')}
        return meta

    @staticmethod
    def finish_session(meta, state):
        try:
            meta.update({
                "end": time.time(),
                "elapsed_s": time.time() - meta.get("start", time.time()),
                "engines_used": [c.get("engine") for c in getattr(state, "engine_calls", [])],
                "rag_used": getattr(state, "rag_used", False),
                "metrics": getattr(state, "metrics", {}),
                "session_id": meta.get("session_id"),
            })
            fn = os.path.join(OUT_DIR, f"session_{meta['session_id']}.jsonl")
            with open(fn, 'a', encoding='utf-8') as fh:
                fh.write(json.dumps(meta, ensure_ascii=False) + "\n")
        except Exception:
            pass

    @staticmethod
    def log_event(session_id: str, event_type: str, payload: dict):
        """Append a structured event to run_logs for the given session id."""
        try:
            evt = {"session_id": session_id, "ts": time.time(), "event": event_type, "payload": payload}
            fn = os.path.join(OUT_DIR, f"events_{session_id}.jsonl")
            with open(fn, 'a', encoding='utf-8') as fh:
                fh.write(json.dumps(evt, ensure_ascii=False) + "\n")
        except Exception:
            pass

    @staticmethod
    def log_snapshot(session_id: str, snapshot: dict):
        """Write a snapshot entry for the given session id."""
        try:
            snap = {"session_id": session_id, "ts": time.time(), "snapshot": snapshot}
            fn = os.path.join(OUT_DIR, f"snapshots_{session_id}.jsonl")
            with open(fn, 'a', encoding='utf-8') as fh:
                fh.write(json.dumps(snap, ensure_ascii=False) + "\n")
        except Exception:
            pass
