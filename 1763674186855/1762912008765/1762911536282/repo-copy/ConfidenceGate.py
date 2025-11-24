import json, hashlib, time, os
BASELINE = 'reports/baselines/last_success.json'

# Prefer TaskOrchestrator.normalize_text and similar when available
try:
    from Integration_Layer.Task_Orchestrator import normalize_text, similar
except Exception:
    def normalize_text(s: str) -> str:
        return ' '.join(str(s or '').strip().split())

    def similar(a: str, b: str) -> float:
        # fallback simple ratio via SequenceMatcher-like heuristic
        try:
            from difflib import SequenceMatcher
            return SequenceMatcher(None, normalize_text(a), normalize_text(b)).ratio()
        except Exception:
            return 0.0


def compute_inputs_hash(task: str, seed: int, extra=None) -> str:
    # If TaskOrchestrator.stable_inputs_hash exists in the project, prefer it
    try:
        from Integration_Layer.Task_Orchestrator import TaskOrchestrator
        to = TaskOrchestrator()
        # ignore 'extra' in this stable hash to keep it deterministic as designed
        return to.stable_inputs_hash(task, seed)
    except Exception:
        m = hashlib.sha256()
        m.update(normalize_text(task).encode('utf-8'))
        m.update(str(seed).encode('utf-8'))
        if extra is not None:
            m.update(json.dumps(extra, sort_keys=True, ensure_ascii=False).encode('utf-8'))
        return m.hexdigest()


def gate(prev_task: str, curr_task: str, min_similarity: float = 0.90):
    a = normalize_text(prev_task or "")
    b = normalize_text(curr_task or "")
    sim = similar(a, b)
    passed = sim >= float(min_similarity)
    return {"passed": passed, "reason": None if passed else "different_input", "similarity": sim}


def check_gate(current_report: dict) -> dict:
    # legacy behavior: check baseline equality + confidence thresholds
    cur = current_report
    passed = False
    reason = "no_baseline"
    if os.path.exists(BASELINE):
        try:
            with open(BASELINE, 'r', encoding='utf-8-sig') as f:
                base = json.load(f)
        except Exception:
            base = {}
        same_input = (base.get('inputs_hash') == cur.get('inputs_hash'))
        enough_conf = cur.get('confidence_score', 0.0) >= 0.60 and \
                      base.get('confidence_score', 0.0) >= 0.60
        passed = same_input and enough_conf
        reason = "ok" if passed else ("different_input" if not same_input else "low_confidence")
    # اكتب النتيجة في التقرير
    cur['confidence_gate'] = {"passed": passed, "reason": reason}
    return cur


def maybe_update_baseline(current_report: dict):
    if current_report.get('confidence_score', 0.0) >= 0.60:
        os.makedirs(os.path.dirname(BASELINE), exist_ok=True)
        with open(BASELINE, 'w', encoding='utf-8-sig') as f:
            json.dump(current_report, f, ensure_ascii=False, indent=2)


def law_confidence_gate(law_report: dict, rmse_threshold: float = 0.5, min_confidence: float = 0.6) -> dict:
    """Assess a law development report: check RMSE and confidence.

    Returns dict with passed(bool) and details.
    """
    res = law_report.get('result') or law_report.get('fit') or {}
    rmse = res.get('rmse') or res.get('rmse', 1e9)
    conf = res.get('confidence') or law_report.get('confidence_score') or 0.0
    passed = False
    reason = None
    if rmse is None:
        reason = 'no_rmse'
    elif conf is None:
        reason = 'no_confidence'
    else:
        passed = (float(rmse) <= float(rmse_threshold)) and (float(conf) >= float(min_confidence))
        reason = 'ok' if passed else 'low_score_or_high_rmse'
    return {'passed': passed, 'rmse': rmse, 'confidence': conf, 'reason': reason}
