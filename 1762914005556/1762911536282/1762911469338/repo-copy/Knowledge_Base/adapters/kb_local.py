import json
from typing import List, Dict, Any


class LocalKBAdapter:
    def __init__(self, path: str):
        self.path = path
        self.rows: List[Dict[str, Any]] = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        self.rows.append(json.loads(line))
                    except Exception:
                        continue
        except FileNotFoundError:
            self.rows = []

    def search_text(self, query: str, top_k: int = 8):
        scored = []
        q_words = set(query.split())
        for r in self.rows:
            t = r.get("text", "")
            s = 0.0
            if query in t:
                s += 1.0
            s += len(q_words & set(t.split())) * 0.1
            if s > 0:
                scored.append((s, r))
        scored.sort(key=lambda x: -x[0])
        from Core_Engines.GK_types import GKEvidence, GKSource
        out = []
        for s, r in scored[:top_k]:
            out.append(GKEvidence(text=r.get("text", ""), source=GKSource(uri=r.get("uri", "seed://"), title=r.get("title", "seed"), provider=r.get("provider", "local")), score=float(s)))
        return out
