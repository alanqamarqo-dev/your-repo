# === AGL auto-injected knobs (idempotent) ===
try:
    import os
    def _to_int(name, default):
        try:
            return int(os.environ.get(name, str(default)))
        except Exception:
            return default
except Exception:
    def _to_int(name, default): return default
_AGL_LIMIT = _to_int('AGL_LIMIT', 20)

try:
    import os
    def _to_int(name, default):
        try:
            return int(os.environ.get(name, str(default)))
        except Exception:
            return default
except Exception:
    def _to_int(name, default): return default
import json
from pathlib import Path
from typing import List, Dict, Any
class MetaReasoner:
    def __init__(self, memory_path: str='artifacts/memory/long_term.jsonl'):
        self.memory_path = Path(memory_path)
    def _read_memory(self, limit: int=500) -> List[Dict[str, Any]]:
        if not self.memory_path.exists():
            return []
        out = []
        try:
            with self.memory_path.open('r', encoding='utf-8') as f:
                for ln in f:
                    ln = ln.strip()
                    if not ln:
                        continue
                    try:
                        out.append(json.loads(ln))
                    except Exception:
                        continue
        except Exception:
            return []
        return out[-limit:]
    def analyze_reasoning_patterns(self) -> Dict[str, Any]:
        """Run a lightweight analysis over long-term memory to extract patterns and statistics."""
        rows = self._read_memory(limit=_AGL_LIMIT)
        stats = {'n_entries': len(rows), 'domains': {}, 'keywords': {}}
        for r in rows:
            dom = r.get('domain') or r.get('candidate', {}).get('base') or 'unknown'
            stats['domains'][dom] = stats['domains'].get(dom, 0) + 1
            txt = str(r.get('text', ''))
            for word in txt.split():
                w = word.strip('.,:;"\'\'()[]{}').lower()
                if 4 <= len(w) <= 30:
                    stats['keywords'][w] = stats['keywords'].get(w, 0) + 1
        stats['top_domains'] = sorted(stats['domains'].items(), key=lambda kv: kv[1], reverse=True)[:10]
        stats['top_keywords'] = sorted(stats['keywords'].items(), key=lambda kv: kv[1], reverse=True)[:30]
        return stats
    def generate_self_improvement_plan(self, max_candidates: int=3) -> List[Dict[str, Any]]:
        """Generate a self-improvement plan by delegating to SelfEngineer.meta_improvement_cycle when available.
		Falls back to simple heuristics if SelfEngineer is not importable.
		"""
        try:
            from Learning_System.Self_Engineer import SelfEngineer
            se = SelfEngineer()
            candidates = se.meta_improvement_cycle(test_reports=[], max_candidates=max_candidates)
            return candidates
        except Exception:
            mem = self._read_memory(limit=_AGL_LIMIT)
            weights = {}
            for r in mem:
                comp = r.get('domain') or 'unknown'
                weights[comp] = weights.get(comp, 0) + 1
            ranked = sorted(weights.items(), key=lambda kv: kv[1], reverse=True)[:max_candidates]
            out = []
            for dom, cnt in ranked:
                out.append({'title': f'Gather more coverage for {dom}', 'impact_score': float(cnt) / max(1, len(mem)), 'component': dom})
            return out
if __name__ == '__main__':
    mr = MetaReasoner()
    print('Memory entries:', mr.analyze_reasoning_patterns().get('n_entries'))
