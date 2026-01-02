"""
Turn contract helpers for knowledge engines.

This module provides small utilities to create and normalize a unified
"turn" JSON contract so different engines return the same shape.

Contract example:
{
  "turn_id": "uuid",
  "user": {"id":"u1","lang":"ar","role":"default"},
  "query": {"text":"…", "mods":{}, "context_ids":[]},
  "routing": {"intent": null, "tools": [], "needs_external": false},
  "working": {"scratch":[], "calls":[]},
  "answer": {"text": null, "citations": [], "confidence": null},
  "safety": {"flags": [], "passed": null},
  "metrics": {"latency_ms":0, "tokens_in":0, "tokens_out":0}
}

Only a small, robust normalization is provided here — engines can call
`make_turn(...)` to build an initial turn and `normalize_engine_response`
to convert engine-specific results into the canonical form.
"""
from __future__ import annotations

import time
import uuid
from typing import Any, Dict, Iterable, List, Optional


def _now_ms() -> int:
    return int(time.time() * 1000)


def make_turn(
    text: str,
    user_id: str = "u1",
    lang: str = "ar",
    role: str = "default",
    mods: Optional[Dict[str, bool]] = None,
    context_ids: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    """Create a new turn contract filled with the provided query text.

    The function returns a dict following the agreed contract. Engines
    should treat this as input and return the same top-level shape.
    """
    if mods is None:
        mods = {}
    if context_ids is None:
        context_ids = []

    return {
        "turn_id": str(uuid.uuid4()),
        "user": {"id": user_id, "lang": lang, "role": role},
        "query": {"text": text, "mods": mods, "context_ids": list(context_ids)},
        "routing": {"intent": None, "tools": [], "needs_external": False},
        "working": {"scratch": [], "calls": []},
        "answer": {"text": None, "citations": [], "confidence": None},
        "safety": {"flags": [], "passed": None},
        "metrics": {"latency_ms": 0, "tokens_in": 0, "tokens_out": 0},
    }


def normalize_engine_response(
    turn: Dict[str, Any],
    engine_result: Dict[str, Any],
    latency_ms: Optional[int] = None,
    tokens_in: int = 0,
    tokens_out: int = 0,
) -> Dict[str, Any]:
    """Normalize an engine-specific response into the turn contract.

    engine_result is expected to be a dict (best-effort). Common keys used
    by engines: 'ok', 'text', 'sources', 'confidence', 'error'. This helper
    fills answer, safety and metrics based on those values and preserves the
    original engine_result under working.calls for diagnostics.
    """
    now = _now_ms()
    if latency_ms is None and "_start_ms" in turn.get("working", {}):
        latency_ms = max(0, now - int(turn["working"].get("_start_ms", now)))
    latency_ms = int(latency_ms) if latency_ms is not None else 0

    # Ensure basic structure exists
    out = dict(turn)
    out.setdefault("working", {}).setdefault("calls", [])

    # capture the raw engine result for debugging
    out["working"]["calls"].append({"engine_result": engine_result})

    ok = bool(engine_result.get("ok", True)) if isinstance(engine_result, dict) else False
    text = None
    citations: List[str] = []
    confidence = None

    if isinstance(engine_result, dict):
        # text may be under several fields
        text = engine_result.get("text") or engine_result.get("answer") or engine_result.get("output")
        # sources can be list or single string
        src = engine_result.get("sources") or engine_result.get("citations")
        if isinstance(src, str):
            citations = [src]
        elif isinstance(src, list):
            citations = [str(s) for s in src]
        # confidence heuristics
        confidence = engine_result.get("confidence") or engine_result.get("score")
        # errors
        if not ok and not text:
            # embed error text if present
            if engine_result.get("error"):
                text = f"(error) {engine_result.get('error')}"

    if text is None:
        text = ""

    # If text is a dict (nested answer structure), try to unwrap to a plain string.
    if isinstance(text, dict):
        # prefer nested 'text' field if present
        if isinstance(text.get('text'), str):
            text = text.get('text')
        else:
            # pick the first string value found in the dict (shallow)
            first_val = None
            for v in text.values():
                if isinstance(v, str) and v.strip():
                    first_val = v.strip()
                    break
            if first_val is not None:
                text = first_val
            else:
                # fallback to string representation
                try:
                    text = str(text)
                except Exception:
                    text = ''

    # If text is a string that looks like a repr of a dict (eg: "{'.': '...'}"),
    # attempt to parse/unpack it to the inner string.
    if isinstance(text, str):
        ts = text.strip()
        if ts.startswith('{') and ("'" in ts or '"' in ts) and ':' in ts:
            try:
                import ast

                inner = ast.literal_eval(ts)
                if isinstance(inner, dict):
                    for v in inner.values():
                        if isinstance(v, str) and v.strip():
                            text = v.strip()
                            break
            except Exception:
                # ignore parse errors and keep original text
                pass

    # fill answer
    out["answer"] = {"text": text, "citations": citations, "confidence": confidence}

    # safety: naive default (engines may set flags)
    out["safety"] = out.get("safety", {"flags": [], "passed": None})

    # metrics
    out["metrics"] = {
        "latency_ms": int(latency_ms),
        "tokens_in": int(tokens_in or 0),
        "tokens_out": int(tokens_out or 0),
    }

    return out
