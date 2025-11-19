from __future__ import annotations
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
_AGL_PREVIEW_1000 = _to_int('AGL_PREVIEW_1000', 1000)

try:
    import os
    def _to_int(name, default):
        try:
            return int(os.environ.get(name, str(default)))
        except Exception:
            return default
except Exception:
    def _to_int(name, default): return default
import re, json, math
from typing import Dict, Any, Tuple, List
AR_SPACES = re.compile('[ \\t]+')
def ar_norm(s: str) -> str:
    if not isinstance(s, str):
        return ''
    s = s.strip()
    s = s.replace('ة', 'ه').replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    s = s.replace('ى', 'ي').replace('ؤ', 'و').replace('ئ', 'ي')
    lines = s.splitlines()
    norm_lines = [AR_SPACES.sub(' ', line).strip() for line in lines]
    return '\n'.join(norm_lines)
def has_any(s: str, tokens: List[str]) -> bool:
    s = ar_norm(s)
    try:
        norm_toks = [ar_norm(t) for t in tokens]
    except Exception:
        norm_toks = tokens
    return any((t in s for t in norm_toks))
def score_rubric(parts: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
    try:
        from agi_eval import WEIGHTS as AGI_WEIGHTS
    except Exception:
        AGI_WEIGHTS = {'flex': 0.4, 'philo': 0.2, 'fewshot': 0.0, 'creative': 0.2, 'self': 0.1, 'transfer': 0.1}
    weights = AGI_WEIGHTS
    total = sum((max(0.0, min(100.0, parts[k])) * w for k, w in weights.items()))
    return (total, {k: round(max(0.0, min(100.0, parts[k])), 2) for k in parts})
def mk_report(case: str, raw: Dict[str, Any], parts: Dict[str, float]) -> Dict[str, Any]:
    total, each = score_rubric(parts)
    return {'case': case, 'ok': total >= 85.0, 'score_total': round(total, 2), 'axes': each, 'raw_excerpt': (raw.get('text') or raw.get('reply_text') or '')[:_AGL_PREVIEW_1000]}
