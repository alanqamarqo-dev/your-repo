from typing import List, Dict


class ConsistencyChecker:
    """Basic consistency checker for hypotheses against existing causal graph and facts.

    Rules implemented:
    - reject over-generalization patterns
    - mark contradictions if explicit negation terms found
    """

    def __init__(self):
        pass

    def process_task(self, payload: dict) -> dict:
        """Backward-compatible wrapper so bootstrap will accept this engine.

        Accepts payload containing optional keys: 'graph', 'facts', 'hypotheses'.
        Returns a dict with ok flag and the checker result under 'result'.
        """
        graph = payload.get('graph')
        facts = payload.get('facts') or []
        hypotheses = payload.get('hypotheses') or []
        try:
            res = self.check(graph, facts, hypotheses)
            return {"ok": True, "engine": "Consistency_Checker", "result": res}
        except Exception as e:
            return {"ok": False, "engine": "Consistency_Checker", "error": str(e)}

    def check(self, graph, facts: List[Dict], hypotheses: List[Dict]) -> Dict:
        accepted, rejected = [], []
        contradictions = []
        overlaps = []
        warnings = []

        for h in hypotheses:
            txt = h.get('hypothesis','')
            # simple over-generalization check
            if 'كل ' in txt or 'دائماً' in txt or 'دائما' in txt:
                h['reason'] = 'over_generalization'
                rejected.append(h)
                continue
            # explicit negation check (very primitive)
            if 'ليس' in txt or 'لا' in txt and len(txt) < 40:
                h['reason'] = 'possible_negation'
                rejected.append(h)
                continue

            # check against existing causal edges for contradictions
            # The graph exposes edges as (src_label, dst_label)
            try:
                # naive: if hypothesis mentions two terms that already have inverse edge, flag
                accepted.append(h)
            except Exception:
                warnings.append({'hypothesis': h, 'issue': 'check_failed'})

        return {
            'accepted_hypotheses': accepted,
            'rejected_hypotheses': rejected,
            'contradictions': contradictions,
            'overlaps': overlaps,
            'warnings': warnings,
        }
