"""AGL Science Reasoning Test runner

Creates a small scientific reasoning benchmark (4 items) and runs them
through the project's LLM adapter `Core_Engines.LLM_OpenAI.LLMOpenAIEngine`.

Outputs a JSON report to `artifacts/reports/AGL_SciTest_report.json` with
per-item raw_output, normalized_output, latency_ms, decision, expected and
correct flags, plus an overall score.

Usage:
  .\\.venv\\Scripts\\python.exe scripts/AGL_SciTest_runner.py

Environment:
  - Set AGL_REQUIRE_ENGINES=1 to enforce engine availability.
  - Optionally set --model-only to disallow heuristic fallback.
"""
from __future__ import annotations

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
_AGL_MAX_TOKENS = _to_int('AGL_MAX_TOKENS', 512)

try:
    import os
    def _to_int(name, default):
        try:
            return int(os.environ.get(name, str(default)))
        except Exception:
            return default
except Exception:
    def _to_int(name, default): return default
import time
import json
import os
import math
from pathlib import Path
from typing import Any, Dict, List
REPORT_DIR = Path('artifacts/reports')
REPORT_DIR.mkdir(parents=True, exist_ok=True)
OUT = REPORT_DIR / 'AGL_SciTest_report.json'
def normalize_answer(s: str) -> str:
    if s is None:
        return ''
    return ' '.join(s.strip().split())
def numeric_close(a: float, b: float, rel_tol=0.01, abs_tol=0.001) -> bool:
    return math.isclose(a, b, rel_tol=rel_tol, abs_tol=abs_tol)
def build_items() -> List[Dict[str, Any]]:
    return [{'id': 'physics_freefall_ratio', 'prompt': 'في تجربة فيزيائية في الفراغ، سقط جسمان من ارتفاعين مختلفين. الجسم A سقط من 20 مترًا، والجسم B من 80 مترًا. بفرض تسارع الجاذبية g=9.8 م/ث^2، ما نسبة زمن سقوط B إلى A؟ اكتب رقماً أو وصفًا قصيراً (مثلاً: "2" أو "مرتين").', 'expected': '2', 'type': 'numeric_ratio'}, {'id': 'chemistry_ph', 'prompt': 'محلول يحتوي على تركيز 0.1 مول من HCl في لتر واحد. ما قيمة pH المحلول عند 25°C؟ اكتب رقماً.', 'expected': '1', 'type': 'numeric'}, {'id': 'ohm_law', 'prompt': 'دائرة تحتوي على مقاومة R=10 أوم ومصدر جهد V=20 فولت. ما شدة التيار I (بالأمبير)؟ اكتب رقماً مع وحدة إذا أردت.', 'expected': '2', 'type': 'numeric'}, {'id': 'le_chatelier_exothermic', 'prompt': 'إذا زادت درجة الحرارة في تفاعل طارد للحرارة، فهل يزيد أم يقل معدل التفاعل؟ وهل يتجه التفاعل للأمام أم للخلف؟ أعط إجابة قصيرة وقابلة للتقييم.', 'expected': 'rate_up_but_shift_backward', 'type': 'qualitative'}]
def heuristic_judge(item: Dict[str, Any], out_text: str) -> Dict[str, Any]:
    out = normalize_answer(out_text)
    ok = False
    note = ''
    if item['type'] in ('numeric', 'numeric_ratio'):
        import re
        m = re.search('([-+]?[0-9]*\\.?[0-9]+([eE][-+]?[0-9]+)?)', out)
        if m:
            val = float(m.group(1))
            exp = float(item['expected'])
            if item['type'] == 'numeric_ratio':
                ok = numeric_close(val, exp, rel_tol=0.05)
            else:
                ok = numeric_close(val, exp, rel_tol=0.01)
            note = f'parsed_number={val}'
        else:
            note = 'no_number_parsed'
    else:
        lo = out.lower()
        keywords_forward = ['يزيد', 'يزداد', 'تزداد', 'سرعة']
        keywords_backward = ['الخلف', 'تتجه للخلف', 'تقل', 'تتراجع']
        found_up = any((k in lo for k in keywords_forward))
        found_back = any((k in lo for k in keywords_backward))
        ok = found_up and found_back
        note = f'found_up={found_up},found_back={found_back}'
    return {'normalized': out, 'correct': ok, 'note': note}
def main(model_only: bool=False):
    try:
        from Core_Engines.LLM_OpenAI import LLMOpenAIEngine
    except Exception as e:
        print('Failed to import LLM engine:', e)
        raise
    engine = LLMOpenAIEngine()
    items = build_items()
    results: List[Dict[str, Any]] = []
    for it in items:
        prompt = it['prompt']
        rec: Dict[str, Any] = dict(id=it['id'], prompt=prompt, expected=it['expected'])
        t0 = time.time()
        try:
            raw_text = ''
            if hasattr(engine, 'respond'):
                try:
                    raw = engine.respond(prompt)
                    if isinstance(raw, dict):
                        raw_text = raw.get('text') or raw.get('response') or str(raw)
                    else:
                        raw_text = str(raw)
                except TypeError:
                    try:
                        raw = engine.respond(prompt)
                        raw_text = raw.get('text') if isinstance(raw, dict) else str(raw)
                    except Exception as e:
                        if hasattr(engine, '_call'):
                            try:
                                raw = engine._call(system='You are a helpful assistant.', prompt=prompt, temperature=0.2, max_tokens=_AGL_MAX_TOKENS)
                                raw_text = raw if isinstance(raw, str) else raw.get('text') if isinstance(raw, dict) else str(raw)
                            except Exception as e2:
                                rec['error'] = repr(e2)
                        else:
                            rec['error'] = repr(e)
                except Exception as e:
                    rec['error'] = repr(e)
            else:
                try:
                    raw = engine._call(system='You are a helpful assistant.', prompt=prompt, temperature=0.2, max_tokens=_AGL_MAX_TOKENS)
                    raw_text = raw if isinstance(raw, str) else raw.get('text') if isinstance(raw, dict) else str(raw)
                except Exception as e:
                    rec['error'] = repr(e)
        except Exception as e:
            raw_text = ''
            rec['error'] = repr(e)
        t1 = time.time()
        rec['raw_output'] = raw_text
        rec['latency_ms'] = int((t1 - t0) * 1000)
        judgment = heuristic_judge(it, raw_text)
        rec.update(judgment)
        results.append(rec)
    correct = sum((1 for r in results if r.get('correct')))
    total = len(results)
    report = {'runs': 1, 'score': correct / total, 'correct': correct, 'total': total, 'details': results, 'engine': getattr(engine, 'last_backend_used', getattr(engine, 'local_kind', 'unknown'))}
    with OUT.open('w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print('Wrote report to', OUT)
    print('Score: {}/{} = {:.2f}'.format(correct, total, correct / total))
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--model-only', action='store_true', help='Require model-only (no heuristic fallback) — currently advisory')
    args = p.parse_args()
    main(model_only=args.model_only)
