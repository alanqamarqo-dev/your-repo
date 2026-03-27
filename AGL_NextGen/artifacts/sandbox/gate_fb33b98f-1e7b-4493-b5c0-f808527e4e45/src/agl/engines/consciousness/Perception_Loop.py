from __future__ import annotations
import json
import threading
import time
from typing import Any, Dict, List, Optional

from agl.lib.core_memory.bridge_singleton import get_bridge
from .Self_Model import SelfModel
import os
from typing import Any, Dict

# configurable small window to iterate recent events without heavy loops
try:
    _AGL_PERCEPTION_EVENTS_LIMIT = int(os.environ.get('AGL_PERCEPTION_EVENTS_LIMIT', '20'))
except Exception:
    _AGL_PERCEPTION_EVENTS_LIMIT = 20
# controlled by AGL_PERCEPTION_EVENTS_LIMIT (default 20)


# heuristics for significant events
SIGNIFICANT_FEEDBACK_KEYS = {"user_feedback", "evaluation", "reward", "grade"}
FAILURE_KEYS = {"error", "exception", "failure", "crash"}
ACHIEVEMENT_TAGS = {"milestone", "achievement", "success"}


def _is_significant_event(evt: Dict[str, Any]) -> bool:
    pld = evt.get("payload") or {}
    tags = set((evt.get("tags") or [])) | set((pld.get("tags") or []))
    if SIGNIFICANT_FEEDBACK_KEYS & set(pld.keys()):
        return True
    if FAILURE_KEYS & set(pld.keys()):
        return True
    if tags & ACHIEVEMENT_TAGS:
        return True
    return False


def _emit_bio_from_event(self_model: SelfModel, evt: Dict[str, Any]) -> None:
    """Creates a short biography entry + optional profile persist. Safe/guarded."""
    try:
        pld = evt.get("payload") or {}
        # classify brief
        if any(k in pld for k in FAILURE_KEYS):
            kind = "failure"
            note = pld.get("error") or pld.get("failure") or "task failure"
        elif any(k in pld for k in SIGNIFICANT_FEEDBACK_KEYS):
            kind = "feedback"
            note = str(pld.get("user_feedback") or pld.get("evaluation") or pld.get("reward") or pld.get("grade"))
        else:
            kind = "achievement"
            note = "milestone reached"

        # use new API form if available
        try:
            self_model.add_biography_event(kind=kind, note=note, source="PerceptionLoop")
        except TypeError:
            # fallback to legacy
            try:
                self_model.add_biography_event(note, None, {'source': 'PerceptionLoop'})
            except Exception:
                pass

        # light adjustments to core values
        try:
            if kind == "failure":
                self_model.set_core_value("humility", +0.05, mode="delta")
                self_model.set_core_value("perseverance", +0.05, mode="delta")
            elif kind in ("feedback", "achievement"):
                self_model.set_core_value("discipline", +0.03, mode="delta")
                self_model.set_core_value("optimism", +0.03, mode="delta")
        except Exception:
            pass

        # persist profile (best-effort)
        try:
            from agl.lib.core_memory.bridge_singleton import get_bridge
            br = get_bridge()
            self_model.persist_profile(br)
        except Exception:
            pass
    except Exception:
        # never break perception loop
        pass


class PerceptionLoop(threading.Thread):
    """Perception loop that samples the ConsciousBridge and updates SelfModel.

    For testing we expose run_once() which performs a single sampling/analysis.
    """

    def __init__(self, self_model: SelfModel, interval: float = 2.0, sample_scope: str = 'stm'):
        super().__init__(daemon=True)
        self.self_model = self_model
        self.interval = interval
        self._stop_event = threading.Event()
        self.br = get_bridge()
        # timestamp for last generated intrinsic goal (seconds)
        self._last_goal_ts = 0.0
        # interval between intrinsic goal generations (seconds)
        try:
            self._goal_interval = float(os.getenv('AGL_INTRINSIC_GOAL_INTERVAL', '300') or '300')
        except Exception:
            self._goal_interval = 300.0
        # sample_scope: 'stm' (default), 'ltm' or 'all' (both)
        self.sample_scope = sample_scope

    def stop(self):
        self._stop_event.set()

    def run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.run_once()
            except Exception:
                pass
            time.sleep(self.interval)

    def run_once(self, trace_id: Optional[str] = None, trace_debug: bool = False) -> Dict[str, Any]:
        """Perform one perception sampling cycle.

        Returns a dict that is also saved to artifacts/perception_log.json.
        """
        # gather simple metrics from bridge
        br = self.br
        # determine scope to sample
        scope = None if self.sample_scope == 'all' else self.sample_scope

        # count events in selected scope (or for a trace if provided)
        try:
            if trace_id:
                # strict intersection for trace-specific sampling
                if scope is None:
                    evs = br.query(trace_id=trace_id, match='and')
                else:
                    evs = br.query(trace_id=trace_id, scope=scope, match='and')
            else:
                if scope is None:
                    evs = br.query()
                else:
                    evs = br.query(scope=scope)
        except Exception:
            evs = []

        types = [e.get('type') for e in evs]
        total = len(types)
        # simplistic success determination: presence of 'rationale' or 'analogy_map'
        successes = sum(1 for t in types if t in ('rationale', 'analogy_map', 'plan', 'prompt_plan'))
        errors = sum(1 for t in types if t in ('error', 'failure'))

        # compute metrics
        success_rate = (successes / total) if total else 1.0
        latency_ms = 100.0
        # try to read average latency from bridge metrics if present
        try:
            if scope is None:
                metrics = br.query(type='metric')
            else:
                metrics = br.query(type='metric', scope=scope)
            if metrics:
                # assume payload contains latency_ms
                vals = [m.get('payload', {}).get('latency_ms', 100.0) for m in metrics]
                latency_ms = sum(vals) / len(vals)
        except Exception:
            pass

        load = getattr(br, 'stm', None)
        bridge_load = len(load._od) if getattr(load, '_od', None) is not None else 0

        metrics = {
            'latency_ms': latency_ms,
            'success_rate': success_rate,
            'error_count': errors,
            'bridge_load': bridge_load,
            'total_events': total,
        }

        # update self model
        self.self_model.update_from_metrics(metrics)

        # emit biography events for significant recent events (best-effort, non-blocking)
        try:
            # iterate a small window to avoid heavy loops
            for evt in (evs or [])[:_AGL_PERCEPTION_EVENTS_LIMIT]:
                try:
                    if _is_significant_event(evt):
                        _emit_bio_from_event(self.self_model, evt)
                except Exception:
                    pass
        except Exception:
            pass

        # Intrinsic hooks: emotion updates and intrinsic reward-based goal triggering
        try:
            if os.getenv('AGL_ENABLE_INTRINSIC_GOAL', '0') == '1':
                now = time.time()
                for evt in (evs or [])[:_AGL_PERCEPTION_EVENTS_LIMIT]:
                    try:
                        pld = evt.get('payload') or {}
                        # update emotion model if present
                        try:
                            em = getattr(self.self_model, 'emotion_model', None)
                            if em is not None and isinstance(pld, dict):
                                em.update_from_event(pld)
                        except Exception:
                            pass

                        # compute intrinsic reward from the event
                        try:
                            reward = 0.0
                            if hasattr(self.self_model, 'intrinsic_reward'):
                                reward = float(self.self_model.intrinsic_reward({'context': pld, 'note': pld.get('note')}))
                            # if reward is high and enough time passed, generate a personal goal
                            if reward >= 0.6 and (now - getattr(self, '_last_goal_ts', 0.0)) > getattr(self, '_goal_interval', 300.0):
                                try:
                                    g = self.self_model.generate_personal_goal()
                                    self._last_goal_ts = now
                                    # persist profile after goal generation
                                    try:
                                        from agl.lib.core_memory.bridge_singleton import get_bridge
                                        br = get_bridge()
                                        self.self_model.persist_profile(br)
                                    except Exception:
                                        pass
                                except Exception:
                                    pass
                        except Exception:
                            pass
                    except Exception:
                        pass
        except Exception:
            pass

        snapshot = self.self_model.snapshot()

        # optional debug sampling of recent events for diagnostics
        recent_events_sample = []
        if trace_debug:
            try:
                # sample up to first/last 5 events for quick inspection
                if evs:
                    n = 5
                    recent_events_sample = evs[:n] + evs[-n:]
            except Exception:
                recent_events_sample = []

        out = {
            'timestamp': time.time(),
            'trace_id': trace_id,
            'metrics': metrics,
            'snapshot': snapshot,
            'recent_event_types': types,
        }

        if trace_debug:
            out['recent_events_sample'] = recent_events_sample

        # append to artifacts/perception_log.json (overwrite latest)
        try:
            with open('artifacts/perception_log.json', 'w', encoding='utf-8') as fh:
                json.dump(out, fh, ensure_ascii=False, indent=2)
        except Exception:
            pass

        # Optional: Curiosity detection hook (best-effort, guarded)
        try:
            if os.getenv('AGL_ENABLE_CURIOSITY', '0') == '1':
                try:
                    # lazy import to avoid boot-time coupling
                    from agl.engines.Self_Reflective import create_curiosity_engine
                    engine = create_curiosity_engine()
                    triggers = engine.detect_curiosity_triggers(evs)
                    # register detected triggers (engine will best-effort write via StateLogger or artifacts)
                    for t in triggers:
                        try:
                            engine.register_question(t)
                        except Exception:
                            pass
                except Exception:
                    # do not let curiosity hook break perception
                    pass
        except Exception:
            pass

        return out

