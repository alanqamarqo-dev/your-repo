import os
import json
import time
import pathlib

from Integration_Layer.integration_registry import registry
from Core_Engines import bootstrap_register_all_engines
from tests.helpers.engine_ask import ask_engine

# إعدادات افتراضية للثبات
os.environ.setdefault("AGL_TEST_SCAFFOLD_FORCE", "1")
os.environ.setdefault("AGL_LLM_PROVIDER", "offline")
TIMEOUT_S = float(os.environ.get("AGENT_PER_ENGINE_TIMEOUT_S", "12"))
PASS_RATE_MIN = float(os.environ.get("AGL_STABILITY_PASS_RATE_MIN", "0.80"))

PROBE = "اختبار ثبات قصير: أعطني سطرًا واحدًا يثبت أن المحرك متصل ويستقبل المهمة."
ART_DIR = pathlib.Path("artifacts")
ART_DIR.mkdir(exist_ok=True, parents=True)
OUT = ART_DIR / "stability_matrix.json"


def _is_callable_engine(obj):
    return hasattr(obj, "process_task") or hasattr(obj, "ask")


def test_stability_matrix_collect():
    # 1) ملء الريجستري (idempotent)
    try:
        bootstrap_register_all_engines(registry)
    except Exception:
        pass

    names = sorted(registry.list_names())
    results = []
    for name in names:
        eng = registry.get(name)
        if not eng or not _is_callable_engine(eng):
            continue
import os
import time
import json
import pathlib
import concurrent.futures as cf
from tests.helpers.engine_ask import ask_engine
from Integration_Layer.integration_registry import registry
from Core_Engines import bootstrap_register_all_engines

OUT = pathlib.Path("artifacts")
OUT.mkdir(parents=True, exist_ok=True)
REPORT_P = OUT / "stability_matrix.json"

PROBE = "سؤال قصير: قارن بين سقاية الري والتعليم في سطرين."
TIMEOUT_S = float(os.environ.get("AGENT_PER_ENGINE_TIMEOUT_S", "12"))
PASS_RATE_MIN = float(os.environ.get("AGL_STABILITY_PASS_RATE_MIN", "0.80"))
PROVIDERS = os.environ.get("AGL_PROVIDERS_MATRIX", "offline").split(",")


def _ensure_envs(provider: str):
    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONPATH", "repo-copy")
    os.environ.setdefault("AGL_TEST_SCAFFOLD_FORCE", "1")
    os.environ["AGL_LLM_PROVIDER"] = provider.strip()


def _probe_engine(name: str):
    start = time.time()
    try:
        res = ask_engine(name, PROBE)
        ok = bool(res.get("ok", False))
        text_ok = bool(str(res.get("text", "")).strip())
        engine = res.get("engine", name)
        elapsed = time.time() - start
        return {
            "engine": engine,
            "name": name,
            "ok": ok and text_ok,
            "elapsed_s": elapsed,
            "error": None if (ok and text_ok) else "empty_or_not_ok",
        }
    except Exception as e:
        elapsed = time.time() - start
        return {"engine": name, "name": name, "ok": False, "elapsed_s": elapsed, "error": str(e)}


def _run_matrix_for_provider(provider: str):
    _ensure_envs(provider)
    try:
        bootstrap_register_all_engines(registry)
    except Exception:
        pass
    names = sorted(registry.list_names())
    tasks = []
    with cf.ThreadPoolExecutor(max_workers=min(16, max(4, len(names)))) as ex:
        for n in names:
            eng = registry.get(n)
            if not eng:
                continue
            if not (hasattr(eng, "process_task") or hasattr(eng, "ask")):
                continue
            tasks.append(ex.submit(_probe_engine, n))
        results = [t.result(timeout=TIMEOUT_S + 2) for t in tasks]

    passed = [r for r in results if r["ok"] and r["elapsed_s"] <= TIMEOUT_S]
    pass_rate = len(passed) / max(1, len(results))
    return {"provider": provider, "pass_rate": pass_rate, "timeout_s": TIMEOUT_S, "results": results}


def test_stability_matrix():
    matrix = []
    for provider in PROVIDERS:
        matrix.append(_run_matrix_for_provider(provider))

    # احفظ التقرير
    REPORT_P.write_text(json.dumps({"matrix": matrix}, ensure_ascii=False, indent=2), encoding="utf-8")

    # طبّق العتبة على أوّل مزوّد (الأساسي) على الأقل
    baseline = matrix[0]
    assert baseline["pass_rate"] >= PASS_RATE_MIN, f"Pass rate too low: {baseline['pass_rate']:.2%} — see {REPORT_P}"
    # اطبع أبطأ 5 (معلومات)
    slow = sorted(baseline["results"], key=lambda r: r["elapsed_s"], reverse=True)[:5]
    print("Top-5 slow engines:", [(r["engine"], round(r["elapsed_s"], 3)) for r in slow])
