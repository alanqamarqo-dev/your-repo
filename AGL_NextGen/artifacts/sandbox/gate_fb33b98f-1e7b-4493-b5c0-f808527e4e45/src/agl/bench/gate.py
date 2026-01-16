from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class GateConfig:
    suite: str
    regression_suites: List[str]
    repeats: int = 3
    use_core_consciousness: bool = False
    no_system: bool = True
    artifacts_path: Optional[str] = None


def _project_root_from_here() -> str:
    here = os.path.abspath(__file__)  # .../src/agl/bench/gate.py
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(here))))


def _artifacts_dir() -> str:
    p = os.path.join(_project_root_from_here(), "artifacts")
    os.makedirs(p, exist_ok=True)
    return p


def _default_gate_log() -> str:
    return os.path.join(_artifacts_dir(), "self_improve_gate.jsonl")


def _jsonl_append(path: str, obj: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _python_exe() -> str:
    return os.environ.get("PYTHON", "") or "python"


def _extract_last_json(stdout: str) -> Dict[str, Any]:
    # There is a lot of boot logging; grab the last JSON object printed.
    txt = stdout.strip()
    if not txt:
        raise ValueError("empty output")

    # Try: last occurrence of a JSON object.
    last = txt.rfind("{")
    if last < 0:
        raise ValueError("no json object found")
    cand = txt[last:]
    # Best-effort trim to matching end.
    # If the output ends with a JSON dict, json.loads will succeed.
    try:
        return json.loads(cand)
    except Exception:
        pass

    # Fallback: find last balanced {...} with a simple stack scan.
    start_positions = [m.start() for m in re.finditer(r"\{", txt)]
    for start in reversed(start_positions):
        chunk = txt[start:]
        depth = 0
        end = None
        for i, ch in enumerate(chunk):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if end is None:
            continue
        obj_txt = chunk[:end]
        try:
            return json.loads(obj_txt)
        except Exception:
            continue

    raise ValueError("failed to parse json from output")


def _run_bench_summary(project_root: str, suite: str, repeats: int, use_core: bool) -> Dict[str, Any]:
    env = dict(os.environ)
    env["AGL_BENCH_SUITE"] = str(suite)
    env["AGL_BENCH_REPEATS"] = str(int(repeats))
    env["AGL_BENCH_USE_CORE"] = "1" if use_core else "0"
    if os.getenv("AGL_SELF_IMPROVE_GATE_NO_SYSTEM"):
        env["AGL_BENCH_NO_SYSTEM"] = os.getenv("AGL_SELF_IMPROVE_GATE_NO_SYSTEM", "1")

    cmd = [_python_exe(), "-c", "".join([
        "import os, sys, json; ",
        "sys.path.insert(0, os.path.join(r'", project_root.replace("'", "\\'"), "', 'src')); ",
        "from agl.bench.runner import BenchRunner; ",
        "from agl.bench.self_improve import _tasks_for_suite; ",
        "suite=os.environ.get('AGL_BENCH_SUITE','deterministic'); ",
        "rep=BenchRunner(repeats=int(os.environ.get('AGL_BENCH_REPEATS','3')), use_core_consciousness=(os.environ.get('AGL_BENCH_USE_CORE','0')=='1')).run(tasks=_tasks_for_suite(suite)); ",
        "print(json.dumps(rep['summary'], ensure_ascii=False));",
    ])]

    proc = subprocess.run(cmd, cwd=project_root, env=env, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"bench failed rc={proc.returncode} stderr={proc.stderr[-4000:]}")
    return _extract_last_json(proc.stdout)


def _copy_for_sandbox(src_root: str, dst_root: str) -> None:
    os.makedirs(dst_root, exist_ok=True)
    # Minimal copy: src tree + pyproject (optional) is enough for bench.
    shutil.copytree(os.path.join(src_root, "src"), os.path.join(dst_root, "src"), dirs_exist_ok=True)


def _mod_plan_micro_planner_keyword_steps() -> Dict[str, Any]:
    """A safe, deterministic improvement: include salient task tokens in step texts."""

    content = """\
+\"\"\"Micro Planner (improved deterministic)
+Generates a deterministic micro-plan from a prompt and writes it to the ConsciousBridge.
+
+Improvement: surface salient task tokens inside the *step texts* so plans are grounded.
+\"\"\"
+from __future__ import annotations
+
+import re
+from typing import Dict, Any, List
+
+try:
+    from agl.lib.core_memory.bridge_singleton import get_bridge
+except ImportError:
+    def get_bridge():
+        return None
+
+
+_STOP = {
+    # Arabic
+    "اكتب", "خطة", "من", "خطوات", "ل", "لعمل", "عمل", "على", "في", "مع", "ملف", "ملفات", "مشروع",
+    "الى", "إلى", "عن", "ثم",
+    # English
+    "write", "plan", "steps", "for", "with", "and", "the", "a", "an",
+}
+
+
+def _salient_tokens(task: str, *, max_tokens: int = 3) -> List[str]:
+    t = (task or "").strip()
+    if not t:
+        return []
+    # keep Arabic/latin/numbers
+    words = re.findall(r"[A-Za-z0-9_]+|[\u0600-\u06FF]+", t)
+    out: List[str] = []
+    for w in words:
+        w0 = w.strip().lower()
+        if not w0 or w0 in _STOP:
+            continue
+        if len(w0) < 3:
+            continue
+        if w0 not in out:
+            out.append(w0)
+        if len(out) >= max_tokens:
+            break
+    return out
+
+
+class MicroPlanner:
+    name = "Plan_and_Execute_MicroPlanner"
+
+    def process_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
+        task = payload.get('task') or payload.get('prompt') or payload.get('query') or payload.get('text') or ''
+        toks = _salient_tokens(str(task), max_tokens=3)
+        anchor = " ".join(toks) if toks else "المهمة"
+
+        steps = [
+            f"1) تحديد الهدف وجمع المتطلبات (مرتكزات: {anchor})",
+            f"2) اختيار طريقة التنفيذ والأداة المناسبة ({anchor})",
+            f"3) تنفيذ النسخة الأولية ثم التحقق والتوثيق ({anchor})",
+            "4) اختبار تجريبي لمجموعة صغيرة",
+            "5) قياس النتائج وضبط المعلمات",
+            "6) نشر تدريجي ومراقبة",
+        ]
+        plan = {'title': f'خطة تنفيذ قصيرة لـ: {str(task)[:60]}', 'steps': steps}
+        out = {"ok": True, "engine": self.name, "plan": plan, 'text': '؛ '.join(steps)}
+
+        try:
+            br = get_bridge()
+            if br is not None:
+                trace = payload.get('trace_id') if isinstance(payload, dict) else None
+                pid = br.put('plan', {'plan': plan, 'text': out.get('text')}, trace_id=trace)
+                if trace:
+                    try:
+                        pps = br.query_by_trace_and_type(trace, 'prompt_plan', scope='stm')
+                        if pps:
+                            br.link(pps[-1]['id'], pid, 'expanded_into_plan')
+                    except Exception:
+                        pps = [e for e in br.query(trace_id=trace, scope='stm') if e.get('type') == 'prompt_plan']
+                        if pps:
+                            br.link(pps[-1]['id'], pid, 'expanded_into_plan')
+        except Exception:
+            pass
+
+        return out
+
+
+def factory():
+    return MicroPlanner()
+"""

    # The leading '+' are just to prevent accidental patch-like parsing when viewed.
    content = "\n".join([ln[1:] if ln.startswith("+") else ln for ln in content.splitlines()]) + "\n"

    return {
        "id": "micro_planner.keyword_steps.v1",
        "steps": [
            {
                "op": "write_file",
                "path": "src/agl/engines/micro_planner.py",
                "content": content,
            }
        ],
    }


def run_gate_once(config: GateConfig) -> Dict[str, Any]:
    run_id = str(uuid.uuid4())
    ts = time.time()

    base_root = _project_root_from_here()
    log_path = config.artifacts_path or _default_gate_log()

    # Prefer fast, component-level evaluation by default.
    os.environ.setdefault("AGL_SELF_IMPROVE_GATE_NO_SYSTEM", "1" if config.no_system else "0")

    baseline = {
        "suite": config.suite,
        "summary": _run_bench_summary(base_root, config.suite, config.repeats, config.use_core_consciousness),
        "regressions": {},
    }
    for s in config.regression_suites:
        baseline["regressions"][s] = _run_bench_summary(base_root, s, config.repeats, config.use_core_consciousness)

    sandbox_root = os.path.join(_artifacts_dir(), "sandbox", f"gate_{run_id}")
    _copy_for_sandbox(base_root, sandbox_root)

    # Apply one safe modification plan into the sandbox.
    from agl.engines.self_improvement.Self_Improvement.safe_self_mod import SafeSelfModificationSystem

    mod_plan = _mod_plan_micro_planner_keyword_steps()
    sms = SafeSelfModificationSystem(sandbox_dir=sandbox_root, allow_live_apply=True)
    mod_res = sms.safe_self_modify(mod_plan)

    after = {
        "suite": config.suite,
        "summary": _run_bench_summary(sandbox_root, config.suite, config.repeats, config.use_core_consciousness),
        "regressions": {},
    }
    for s in config.regression_suites:
        after["regressions"][s] = _run_bench_summary(sandbox_root, s, config.repeats, config.use_core_consciousness)

    base_acc = float(baseline["summary"].get("accuracy") or 0.0)
    after_acc = float(after["summary"].get("accuracy") or 0.0)

    regress_ok = True
    regress_details: Dict[str, Any] = {}
    for s in config.regression_suites:
        b = float(baseline["regressions"][s].get("accuracy") or 0.0)
        a = float(after["regressions"][s].get("accuracy") or 0.0)
        ok = a >= b
        regress_details[s] = {"baseline": b, "after": a, "ok": ok}
        if not ok:
            regress_ok = False

    accepted = (after_acc > base_acc) and regress_ok

    rec = {
        "run_id": run_id,
        "timestamp": ts,
        "suite": config.suite,
        "repeats": config.repeats,
        "use_core": bool(config.use_core_consciousness),
        "baseline": baseline,
        "after": after,
        "regression_check": regress_details,
        "modification_plan": mod_plan,
        "modification_result": mod_res,
        "sandbox_root": sandbox_root,
        "accepted": accepted,
        "reason": "improved_holdout_and_no_regressions" if accepted else "no_improvement_or_regression",
    }

    _jsonl_append(log_path, rec)
    return rec
