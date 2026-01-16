from __future__ import annotations
import os
import time
from typing import Any, Dict, Optional

def _to_int(name, default):
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default

_AGL_INTENT_TOP_N = _to_int("AGL_INTENT_TOP_N", 3)


from agl.lib.core_memory.bridge_singleton import get_bridge


class IntentGenerator:
    """Intent generator with EMA-driven rules and hysteresis to reduce flapping.

    Keeps last_intent state to implement entry/exit thresholds.
    """

    def __init__(self):
        self.br = get_bridge()
        self.last_intent: Optional[str] = None

        # thresholds/config (can be overridden with env vars later)
        self.L_HI_ENTER = float(os.getenv('AGL_INTENT_LAT_HI_ENTER', '220'))
        self.L_HI_EXIT = float(os.getenv('AGL_INTENT_LAT_HI_EXIT', '180'))
        self.S_LO_ENTER = float(os.getenv('AGL_INTENT_S_LO_ENTER', '0.90'))
        self.S_LO_EXIT = float(os.getenv('AGL_INTENT_S_LO_EXIT', '0.95'))
        self.Z_ANOMALY = float(os.getenv('AGL_INTENT_Z_ANOMALY', '3.0'))

    def decide(self, snapshot: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Decide on an intent given a snapshot (as returned by PerceptionLoop.run_once).

        Uses EMA fields from SelfModel.snapshot when available and applies hysteresis.
        """
        if snapshot is None:
            # try to read latest perception
            try:
                recent = self.br.query(type='perception', scope='stm')
                snapshot = recent[-1].get('payload') if recent else {}
            except Exception:
                snapshot = {}

        # PerceptionLoop returns a dict with keys: metrics and snapshot (selfmodel)
        metrics = snapshot.get('metrics', {}) if isinstance(snapshot, dict) else {}
        sm_snapshot = snapshot.get('snapshot') if isinstance(snapshot, dict) else snapshot

        ema_lat = None
        ema_suc = None
        z = 0.0
        if isinstance(sm_snapshot, dict):
            ema_lat = sm_snapshot.get('ema_latency_ms')
            ema_suc = sm_snapshot.get('ema_success_rate')
            z = sm_snapshot.get('latency_z', 0.0) or 0.0

        # fallback to immediate metrics if ema missing
        if ema_lat is None:
            ema_lat = metrics.get('latency_ms', 100.0)
        if ema_suc is None:
            ema_suc = metrics.get('success_rate', 1.0)

        # Hysteresis logic
        chosen: str
        # anomaly has highest priority
        if z >= self.Z_ANOMALY or (ema_suc is not None and ema_suc <= self.S_LO_ENTER):
            chosen = 'investigate_anomaly'
        elif ema_lat >= self.L_HI_ENTER:
            # check if already in optimize_latency; if so allow looser exit
            if self.last_intent == 'optimize_latency':
                # remain until we cross the exit threshold
                if ema_lat >= self.L_HI_EXIT:
                    chosen = 'optimize_latency'
                else:
                    chosen = 'maintain_stability'
            else:
                chosen = 'optimize_latency'
        else:
            # if we were previously in investigate and success recovered, respect exit
            if self.last_intent == 'investigate_anomaly' and ema_suc is not None and ema_suc < self.S_LO_EXIT:
                chosen = 'investigate_anomaly'
            else:
                chosen = 'maintain_stability'

        # store for next decision
        self.last_intent = chosen

        reason = f"ema_lat={ema_lat:.1f}, ema_suc={ema_suc:.3f}, z={z:.2f}"

        intent = {
            'type': 'intent',
            'intent_type': chosen,
            'reason': reason,
            'ts': time.time(),
            'payload': snapshot,
        }

        # persist into LTM so it's durable
        try:
            self.br.put(intent, scope='ltm')
        except Exception:
            try:
                self.br.put(intent, scope='stm')
            except Exception:
                pass

        return intent

