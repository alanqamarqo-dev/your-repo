from typing import Dict, Any


class CurriculumScheduler:
    def __init__(self):
        pass

    def pick_next_domain(self, metrics: Dict[str, Any]) -> str:
        """Simple heuristic: pick domain with highest contradictions per node or lowest causal coverage."""
        # metrics expected: {'contradictions': {domain: n}, 'causal_coverage': {domain: pct}}
        contr = metrics.get('contradictions', {})
        cov = metrics.get('causal_coverage', {})
        # choose domain with max contradictions and lowest coverage
        best = None
        score = None
        for d in set(list(contr.keys()) + list(cov.keys())):
            c = contr.get(d, 0)
            p = cov.get(d, 0.0)
            s = (c + 1) / max(0.01, p)
            if score is None or s > score:
                score = s; best = d
        return best or 'general'
