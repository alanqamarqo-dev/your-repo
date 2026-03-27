from __future__ import annotations
import json
import time
from typing import Any, Dict

from agl.lib.core_memory.bridge_singleton import get_bridge


class StateLogger:
    """Assembles a conscious state snapshot and stores it via the bridge.

    The StateLogger writes a line to artifacts/conscious_state_log.jsonl and
    attempts to persist an aggregated snapshot to LTM.
    """

    def __init__(self):
        self.br = get_bridge()

    def log(self, snapshot: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
        record = {
            'ts': time.time(),
            'snapshot': snapshot,
            'intent': intent,
        }

        # append to jsonl
        try:
            with open('artifacts/conscious_state_log.jsonl', 'a', encoding='utf-8') as fh:
                fh.write(json.dumps(record) + '\n')
        except Exception:
            pass

        # persist to LTM
        try:
            self.br.put({'type': 'state_log', 'payload': record, 'ts': time.time()}, scope='ltm')
        except Exception:
            try:
                self.br.put({'type': 'state_log', 'payload': record, 'ts': time.time()}, scope='stm')
            except Exception:
                pass

        return record

