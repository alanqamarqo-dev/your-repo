"""Orchestrator for the self-improvement loop (diagnose -> propose -> fit -> validate -> select -> integrate).

This is a high-level skeleton that wires the stubs added elsewhere. It is
intended for incremental development and smoke testing.
"""
from typing import Dict, Any, List
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
import io
import os
import shutil
from datetime import datetime
from Core_Engines.Model_Structure_Searcher import propose_structures, StructureCandidate, describe_candidate
from Learning_System.Fitness_Criteria import score_result
from Learning_System.Uncertainty_Propagation import pred_confidence_intervals
from typing import Any, Dict, List, Optional
def _safe_import(module_name: str, attr: Optional[str]=None):
    try:
        mod = __import__(module_name, fromlist=[attr] if attr else [])
        return getattr(mod, attr) if attr else mod
    except Exception:
        return None
try:
    _AGL_SELF_PROPOSE_BUDGET = int(os.environ.get('AGL_SELF_PROPOSE_BUDGET', '5'))
except Exception:
    _AGL_SELF_PROPOSE_BUDGET = 5
try:
    _AGL_SELF_MAX_ITERS = int(os.environ.get('AGL_SELF_MAX_ITERS', '3'))
except Exception:
    _AGL_SELF_MAX_ITERS = 3
try:
    _AGL_META_MAX_CANDIDATES = int(os.environ.get('AGL_META_MAX_CANDIDATES', '3'))
except Exception:
    _AGL_META_MAX_CANDIDATES = 3
class SelfEngineer:
    def __init__(self, cfg: Dict[str, Any]=None):
        self.cfg = cfg or {}
        promo = self.cfg.get('promotion') if isinstance(self.cfg, dict) else None
        self.promotion_rules = promo or {'min_rmse_improvement_pct': 0.15, 'max_ece': 0.08, 'min_bic_gain': 10, 'require_units_ok': True, 'require_safety_ok': True}
        try:
            from infra.monitoring.trace import emit as _emit
            self._emit = _emit
        except Exception:
            self._emit = lambda *a, **k: None
    def diagnose(self, models_report: Dict[str, Any], data_profile: Dict[str, Any]) -> Dict[str, Any]:
        kb_path = os.path.join('Knowledge_Base', 'Learned_Patterns.json')
        gaps = []
        try:
            with io.open(kb_path, 'r', encoding='utf-8-sig') as f:
                kb = json.load(f)
            pats = kb.get('patterns', []) if isinstance(kb, dict) else []
        except Exception:
            pats = []
        if len(pats) < 4:
            gaps.append('insufficient_patterns')
        if not models_report:
            suggested_task = 'predict_y'
        else:
            suggested_task = models_report.get('task', 'predict_y')
        try:
            self._emit('self_engineer.diagnose', {'gaps': gaps, 'suggested_task': suggested_task, 'rationale': 'diagnosis_summary', 'confidence': None})
        except Exception:
            pass
        return {'gaps': gaps, 'constraints': {}, 'suggested_task': suggested_task}
    def propose(self, task: str, data_profile: Dict[str, Any], constraints: Dict[str, Any], budget: int=None, decision_id: Optional[str]=None) -> List[StructureCandidate]:
        if budget is None:
            budget = _AGL_SELF_PROPOSE_BUDGET
        cands = propose_structures(task, data_profile, constraints, budget=budget)
        try:
            self._emit('self_engineer.propose', {'task': task, 'n_cands': len(cands), 'decision_id': decision_id, 'rationale': f'propose_{task}', 'confidence': None})
        except Exception:
            pass
        return cands
    def fit_and_score(self, candidate: StructureCandidate, train, val, decision_id: Optional[str]=None) -> Dict[str, Any]:
        desc = describe_candidate(candidate)
        complexity = len(str(desc.get('expr', ''))) if isinstance(desc, dict) else 1
        rmse = max(0.01, 1.0 / (1.0 + complexity))
        bic = 50.0 + complexity * 2.0
        ece = 0.05 * (1.0 if complexity < 5 else 1.5)
        stability = 0.8 if complexity < 8 else 0.5
        metrics = {'rmse': rmse, 'bic': bic, 'ece': ece, 'stability': stability}
        params = {'a': 1.0 / (1.0 + complexity), 'b': 0.0}
        ci = pred_confidence_intervals(None, None)
        score = score_result(metrics)
        conf = None
        try:
            ece_val = metrics.get('ece')
            rmse_val = metrics.get('rmse')
            if isinstance(ece_val, (int, float)):
                conf = max(0.0, min(1.0, 1.0 - float(ece_val)))
            elif isinstance(rmse_val, (int, float)):
                conf = max(0.0, min(1.0, 1.0 / (1.0 + float(rmse_val))))
        except Exception:
            conf = None
        out = {'candidate': desc, 'metrics': metrics, 'params': params, 'ci': ci, 'score': score}
        try:
            self._emit('self_engineer.fit_and_score', {'candidate': desc.get('id') or desc.get('expr'), 'metrics': metrics, 'decision_id': decision_id or (desc.get('id') or desc.get('expr')), 'rationale': 'fit_and_score_based_on_complexity', 'confidence': conf})
        except Exception:
            pass
        return out
    def _validate_candidate(self, winner: Dict[str, Any]) -> Dict[str, Any]:
        """Run unit/safety validators. Returns dict {units_ok: bool, safety_ok: bool, issues: []}.
        For now this is a lightweight stub: checks presence of 'units' in candidate and simple physics checks.
        """
        issues = []
        cand = winner.get('candidate', {})
        units_ok = True
        safety_ok = True
        expr = cand.get('expr', '') if isinstance(cand, dict) else ''
        if not expr:
            issues.append('empty_expr')
            units_ok = False
            safety_ok = False
        if '/0' in str(expr):
            issues.append('divide_by_zero_pattern')
            safety_ok = False
        return {'units_ok': units_ok, 'safety_ok': safety_ok, 'issues': issues}
    def select(self, scored: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not scored:
            return {}
        winner = max(scored, key=lambda x: x.get('score', -1000000000.0))
        try:
            self._emit('self_engineer.select', {'winner': winner.get('candidate', {}).get('id'), 'decision_id': winner.get('candidate', {}).get('id'), 'rationale': 'highest_score', 'confidence': winner.get('score')})
        except Exception:
            pass
        return winner
    def integrate(self, winner: Dict[str, Any]) -> Dict[str, Any]:
        kb_lock = os.path.join('Knowledge_Base', 'Learned_Patterns.lock.json')
        kb_main = os.path.join('Knowledge_Base', 'Learned_Patterns.json')
        try:
            if os.path.exists(kb_main):
                with io.open(kb_main, 'r', encoding='utf-8-sig') as f:
                    kb = json.load(f)
            elif os.path.exists(kb_lock):
                with io.open(kb_lock, 'r', encoding='utf-8-sig') as f:
                    kb = json.load(f)
            else:
                kb = {'version': 'G.min', 'updated_at': 'auto', 'patterns': []}
            if not isinstance(kb, dict):
                kb = {'version': 'G.min', 'updated_at': 'auto', 'patterns': []}
            pats = kb.get('patterns') if isinstance(kb, dict) else []
            if not isinstance(pats, list):
                pats = []
            candidate = winner.get('candidate') or {}
            entry = {'base': candidate.get('base', candidate.get('id', 'candidate')), 'winner': candidate.get('id', candidate.get('base', 'candidate')), 'fit': winner.get('params', {}), 'score': winner.get('score', 0.0)}
            pats.append(entry)
            kb['patterns'] = pats
            kb['updated_at'] = datetime.utcnow().isoformat() + 'Z'
            tmp = kb_main + '.tmp'
            with io.open(tmp, 'w', encoding='utf-8') as f:
                json.dump(kb, f, indent=2, ensure_ascii=False)
            shutil.move(tmp, kb_main)
            try:
                self._emit('self_engineer.integrate', {'entry': entry, 'promoted': True, 'decision_id': entry.get('winner'), 'rationale': 'auto_integrate', 'confidence': entry.get('score')})
            except Exception:
                pass
            return {'promoted': True, 'entry': entry}
        except Exception as e:
            return {'promoted': False, 'error': str(e)}
    def run_loop(self, task: str, models_report: Dict[str, Any], data_profile: Dict[str, Any], max_iters: int=None, auto_promote: bool=False, out_dir: str='reports/self_engineer') -> Dict[str, Any]:
        if max_iters is None:
            max_iters = _AGL_SELF_MAX_ITERS
        os.makedirs(out_dir, exist_ok=True)
        runs = []
        kb_lock = os.path.join('Knowledge_Base', 'Learned_Patterns.lock.json')
        kb_main = os.path.join('Knowledge_Base', 'Learned_Patterns.json')
        try:
            if os.path.exists(kb_lock):
                shutil.copyfile(kb_lock, kb_main)
        except Exception:
            pass
        prev_bic = None
        for it in range(max_iters):
            cycle = self.run_cycle(task, models_report, data_profile, budget=_AGL_SELF_PROPOSE_BUDGET, dry_run=True)
            winner = cycle.get('winner') or {}
            scored_metrics = winner.get('metrics', {})
            promotion = {'promote': False, 'reason': None}
            valid = self._validate_candidate(winner)
            if prev_bic is None:
                prev_bic = scored_metrics.get('bic')
            bic_gain = 0.0
            if prev_bic is not None and scored_metrics.get('bic') is not None:
                bic_gain = prev_bic - scored_metrics.get('bic')
            rmse_improve_pct = 0.0
            baseline_rmse = 1.0
            if scored_metrics.get('rmse') is not None:
                rmse_improve_pct = (baseline_rmse - scored_metrics.get('rmse')) / baseline_rmse
            rules = self.promotion_rules
            cond_bic = bic_gain >= rules.get('min_bic_gain', 10)
            cond_rmse = rmse_improve_pct >= rules.get('min_rmse_improvement_pct', 0.15)
            cond_ece = scored_metrics.get('ece', 1.0) <= rules.get('max_ece', 0.08)
            cond_units = not rules.get('require_units_ok', True) or valid.get('units_ok', False)
            cond_safety = not rules.get('require_safety_ok', True) or valid.get('safety_ok', False)
            promote_decision = (cond_bic or (cond_rmse and cond_ece)) and cond_units and cond_safety
            if auto_promote and promote_decision:
                promoted = self.integrate(winner)
                promotion = {'promote': bool(promoted.get('promoted')), 'reason': 'auto_promote', 'result': promoted}
            else:
                promotion = {'promote': False, 'reason': 'conditions_not_met_or_auto_disabled', 'detail': {'bic_gain': bic_gain, 'rmse_improve_pct': rmse_improve_pct, 'ece': scored_metrics.get('ece'), 'units_ok': valid.get('units_ok'), 'safety_ok': valid.get('safety_ok')}}
            prev_bic = scored_metrics.get('bic') or prev_bic
            run_record = {'iter': it + 1, 'cycle': cycle, 'validate': valid, 'promotion': promotion}
            runs.append(run_record)
            ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            out_file = os.path.join(out_dir, f'run_iter_{it + 1}_{ts}.json')
            try:
                with io.open(out_file, 'w', encoding='utf-8') as f:
                    json.dump(run_record, f, indent=2, ensure_ascii=False)
            except Exception:
                pass
        summary = {'task': task, 'iterations': len(runs), 'runs': runs}
        summary_file = os.path.join(out_dir, f"run_summary_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json")
        try:
            with io.open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
        return summary
    def run_cycle(self, task: str, models_report: Dict[str, Any], data_profile: Dict[str, Any], budget: int=None, dry_run: bool=True):
        if budget is None:
            budget = _AGL_SELF_PROPOSE_BUDGET
        diag = self.diagnose(models_report, data_profile)
        constraints = diag.get('constraints', {})
        candidates = self.propose(task, data_profile, constraints, budget=budget)
        scored = []
        for c in candidates:
            r = self.fit_and_score(c, None, None)
            scored.append(r)
        winner = self.select(scored)
        if not dry_run:
            promoted = self.integrate(winner)
        else:
            promoted = {'promoted': False}
        return {'diagnosis': diag, 'candidates': [s['candidate'] for s in scored], 'winner': winner, 'promoted': promoted}
    def meta_improvement_cycle(self, test_reports: Optional[List[Dict[str, Any]]]=None, max_candidates: int=None, min_impact_score: float=0.15) -> List[Dict[str, Any]]:
        """
        يقود دورة تحسين ميتا تعتمد على نتائج الاختبارات والتغطية وسجل التحسينات.
        """
        Improvement_History = _safe_import('Knowledge_Base.Improvement_History', 'ImprovementHistory')
        Feedback_Analyzer = _safe_import('Learning_System.Feedback_Analyzer', 'FeedbackAnalyzer')
        history_entries: List[Dict[str, Any]] = []
        if Improvement_History:
            try:
                ih = Improvement_History()
                if hasattr(ih, 'get_recent'):
                    history_entries = ih.get_recent(n=50) or []
                elif hasattr(ih, 'list'):
                    history_entries = ih.list(limit=_AGL_LIMIT) or []
            except Exception:
                history_entries = []
        structured_signals = self._aggregate_signals(history_entries, test_reports or [])
        analyzed: Dict[str, Any] = {}
        if Feedback_Analyzer:
            try:
                fa = Feedback_Analyzer()
                if hasattr(fa, 'analyze'):
                    analyzed = fa.analyze(structured_signals) or {}
                elif hasattr(fa, 'analyze_feedback'):
                    analyzed = fa.analyze_feedback(structured_signals) or {}
            except Exception:
                analyzed = {}
        else:
            analyzed = self._fallback_analysis(structured_signals)
        if max_candidates is None:
            max_candidates = _AGL_META_MAX_CANDIDATES
        candidates = self._generate_improvement_candidates(analyzed)
        candidates.sort(key=lambda c: c.get('impact_score', 0.0), reverse=True)
        accepted = [c for c in candidates if c.get('impact_score', 0.0) >= min_impact_score][:max_candidates]
        if Improvement_History:
            try:
                ih = Improvement_History()
                for c in accepted:
                    if hasattr(ih, 'add_proposal'):
                        ih.add_proposal(c)
                    elif hasattr(ih, 'append'):
                        try:
                            ih.append('proposal', c)
                        except Exception:
                            pass
                    elif hasattr(ih, 'save'):
                        try:
                            ih.save({'type': 'proposal', 'data': c})
                        except Exception:
                            pass
            except Exception:
                pass
        return accepted
    def _aggregate_signals(self, history_entries: List[Dict[str, Any]], test_reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        signals: Dict[str, Any] = {'failures': [], 'coverage_gaps': [], 'flaky_tests': [], 'recent_fixes': []}
        for e in history_entries:
            try:
                et = (e.get('type') or '').lower()
            except Exception:
                et = ''
            if et in ('fix', 'patch', 'proposal'):
                signals['recent_fixes'].append({'component': e.get('component') or e.get('target') or 'unknown', 'note': e.get('note') or e.get('summary') or ''})
        for rep in test_reports:
            try:
                rtype = (rep.get('type') or '').lower()
                payload = rep.get('payload') or {}
            except Exception:
                continue
            if rtype == 'pytest':
                for f in payload.get('failures', []):
                    signals['failures'].append({'test': f.get('nodeid') or f.get('name') or 'unknown', 'error': f.get('message') or '', 'trace': f.get('trace') or ''})
                for flaky in payload.get('flaky', []):
                    signals['flaky_tests'].append(flaky)
            elif rtype == 'coverage':
                for f in payload.get('files', []):
                    missing = f.get('missing') or []
                    if missing:
                        signals['coverage_gaps'].append({'file': f.get('path'), 'lines': missing})
        return signals
    def _fallback_analysis(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        weights: Dict[str, float] = {}
        for f in signals.get('failures', []):
            comp = f.get('test', '')
            if '::' in comp:
                mod = comp.split('::', 1)[0]
            else:
                mod = comp
            weights[mod] = weights.get(mod, 0.0) + 0.25
        for gap in signals.get('coverage_gaps', []):
            path = (gap.get('file') or '').replace('\\', '/')
            base = path.split('/', 1)[0] if '/' in path else path
            bump = 0.25 if base.startswith('Core_Engines') else 0.15
            weights[path] = weights.get(path, 0.0) + bump
        return {'priority_weights': weights, 'signals': signals}
    def _generate_improvement_candidates(self, analyzed: Dict[str, Any]) -> List[Dict[str, Any]]:
        weights: Dict[str, float] = analyzed.get('priority_weights', {})
        signals = analyzed.get('signals', {})
        ranked = sorted(weights.items(), key=lambda kv: kv[1], reverse=True)
        try:
            se_top = int(os.getenv('AGL_ROUTER_RESULT_LIMIT', '15'))
        except Exception:
            se_top = 15
        top_targets = [r[0] for r in ranked[:se_top]]
        candidates: List[Dict[str, Any]] = []
        for tgt in top_targets:
            if 'Advanced_Exponential_Algebra.py' in tgt or 'tensor_utils.py' in tgt or 'Core_Engines' in tgt:
                patch = '\n# مثال رقعة تحسين سلامة العمليات المصفوفية\nfrom Core_Engines.tensor_utils import safe_matmul, safe_zeros_like\n\ndef lie_bracket(self, A, B):\n    """قوس لي: [A, B] = AB - BA (نسخة آمنة backend-agnostic)"""\n    AB = safe_matmul(torch, A, B)\n    BA = safe_matmul(torch, B, A)\n    return AB - BA\n\ndef structure_constants(self, basis_elements):\n    """ثوابت البنية باستخدام safe_zeros_like عند غياب dtype"""\n    import torch as _torch\n    n = len(basis_elements)\n    proto = basis_elements[0]\n    try:\n        dt = getattr(proto, "dtype", None) or (_torch.float32 if hasattr(_torch, "float32") else None)\n        sc = _torch.zeros((n, n, n), dtype=dt) if dt is not None else _torch.zeros((n, n, n))\n    except Exception:\n        sc = _torch.zeros((n, n, n))\n    return sc\n'.strip()
                candidates.append({'title': 'تعزيز سلامة عمليات المصفوفات', 'component': 'Core_Engines/Advanced_Exponential_Algebra.py:lie_bracket,structure_constants', 'rationale': 'تقليل أخطاء backend (TensorLike/dtype) عبر طبقة أمان موحّدة.', 'change_type': 'safety', 'suggested_patch': patch, 'impact_score': min(1.0, 0.4 + weights.get(tgt, 0) / 1.5), 'metadata': {'target': tgt}})
                break
        low_cov_files = [g.get('file') for g in signals.get('coverage_gaps', []) if g.get('file') and ('Core_Engines' in g.get('file') or 'Learning_System' in g.get('file'))][:2]
        if low_cov_files:
            test_patch = f"""\n# إضافة اختبارات استقرائية لرفع التغطية\n# مثال: tests/test_meta_improvement_cycle_extra.py\nimport pytest\n\ndef test_meta_cycle_smoke():\n    from Learning_System.Self_Engineer import SelfEngineer\n    se = SelfEngineer()\n    out = se.meta_improvement_cycle(test_reports=[{{"type":"pytest","payload":{{"failures":[]}}}}], max_candidates=1)\n    assert isinstance(out, list) and len(out) >= 0\n\n# يُفضّل إضافة حالات تغطي مسارات الحافة للملفات:\n# {', '.join(low_cov_files)}\n""".strip()
            candidates.append({'title': 'اختبارات تغطية إضافية للملفات منخفضة التغطية', 'component': ', '.join(low_cov_files), 'rationale': 'رفع التغطية وتقليل الديون التقنية حول وحدات حرجة.', 'change_type': 'tests', 'suggested_patch': test_patch, 'impact_score': 0.3 + min(0.3, 0.05 * len(low_cov_files)), 'metadata': {'files': low_cov_files}})
        if signals.get('failures'):
            first_fail = signals['failures'][0]
            doc_patch = f'\n"""توضيح حالات الحافة:\n"""\n'.strip()
            candidates.append({'title': 'توثيق حالات الحافة بناءً على إخفاقات سابقة', 'component': first_fail.get('test', 'unknown'), 'rationale': 'تحسين قابلية الصيانة ووضوح سبب القرارات التقنية.', 'change_type': 'docs', 'suggested_patch': doc_patch, 'impact_score': 0.2, 'metadata': {'source': 'pytest_failures'}})
        return candidates
def quick_smoke():
    se = SelfEngineer()
    out = se.run_cycle(task='predict_y', models_report={}, data_profile={}, budget=_AGL_SELF_PROPOSE_BUDGET, dry_run=True)
    print('Smoke output:', out)
    return out
if __name__ == '__main__':
    quick_smoke()
