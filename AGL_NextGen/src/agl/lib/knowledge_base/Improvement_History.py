import os
import json
import time
from typing import Optional


class ImprovementHistory:
    """Persistent improvement history stored as JSONL.

    Each record is a dict; .record(...) appends record and writes a JSON line.
    """
    def __init__(self, storage_path: Optional[str] = None):
        self.history = []
        self.storage_path = storage_path or os.path.join(os.getcwd(), 'data', 'improvement_history.jsonl')
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        # load existing
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            self.history.append(json.loads(line))
                        except Exception:
                            continue
            except Exception:
                # ignore load errors
                pass

    def record(self, item: dict):
        rec = dict(item)
        rec.setdefault('ts', int(time.time()))
        self.history.append(rec)
        try:
            with open(self.storage_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(rec, ensure_ascii=False) + '\n')
        except Exception:
            # ignore write errors to keep system robust
            pass

    def all(self):
        return list(self.history)

