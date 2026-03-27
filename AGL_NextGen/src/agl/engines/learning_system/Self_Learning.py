"""Self-learning orchestrator: generate candidates from base laws, evaluate on data,
and persist results to ImprovementHistory and ExperienceMemory.
"""
from typing import List, Dict, Optional
import time
from .ExperienceMemory import append_experience, read_experiences
from agl.lib.knowledge_base.Improvement_History import ImprovementHistory
from agl.engines.learning_system.Law_Learner import fit_model_auto
import os


class SelfLearning:
    def __init__(self, experience_path: Optional[str] = None, history_path: Optional[str] = None):
        self.experience_path = experience_path or os.path.join(os.getcwd(), 'data', 'experience_memory.jsonl')
        self.history = ImprovementHistory(storage_path=history_path)

    def generate_candidates(self, base_formula: str, max_candidates: int = 4) -> List[str]:
        # simple template-based candidate generator (safe fallback)
        base = str(base_formula)
        cands = []
        if base != 'x':
            cands.append(base)
        # if formula mentions x, add common functional forms
        if 'x' in base or base == 'x':
            # We prefer generic forms that LawLearner can fit
            cands.extend(['k*x', 'k*x + b', 'a*x**n'])
        # deduplicate and limit
        out = []
        for c in cands:
            if c not in out:
                out.append(c)
            if len(out) >= max_candidates:
                break
        return out

    def evaluate(self, candidate: str, samples: List[Dict]) -> Dict:
        # infer x,y names if possible
        xname = None
        yname = None
        if samples and isinstance(samples, list) and isinstance(samples[0], dict):
            keys = list(samples[0].keys())
            if len(keys) >= 2:
                xname, yname = keys[0], keys[1]

        if not xname or not yname:
            fit = {'error': 'no_x_y_names_in_samples'}
        else:
            try:
                data = {xname: [s.get(xname) for s in samples], yname: [s.get(yname) for s in samples]}
                fit = fit_model_auto(candidate, yname, xname, data)
                fit['x_var'] = xname
                fit['y_var'] = yname
            except Exception as e:
                fit = {'error': str(e)}

        rec = {'candidate': candidate, 'fit': fit, 'n_samples': len(samples) if samples else 0, 'ts': int(time.time())}
        # persist to history
        try:
            self.history.record(rec)
        except Exception:
            pass
        # persist to experience memory (append JSONL)
        try:
            append_experience(self.experience_path, rec)
        except Exception:
            pass
        return rec

    def run(self, base_formula: str, samples: List[Dict], max_candidates: int = 4) -> List[Dict]:
        results = []
        cands = self.generate_candidates(base_formula, max_candidates=max_candidates)
        for c in cands[:max_candidates]:
            r = self.evaluate(c, samples)
            results.append(r)
        return results

