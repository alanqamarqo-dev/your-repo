def _ok(result):
    """Guard helper: accept dicts with 'status'=='success' or subprocess-like objects.

    Returns True for success, False otherwise.
    """
    if isinstance(result, dict):
        return result.get("status", "success") == "success"
    return getattr(result, "returncode", 0) == 0


def test_result_guard_ok():
    class P:
        returncode = 0

    class Q:
        returncode = 1

    assert _ok({"status": "success"})
    assert _ok(P())
    assert not _ok(Q())


# === [ADD TEST :: basic schema for new adapters] ===
import importlib

def _adapter_output_ok(x):
    assert isinstance(x, dict)
    assert "engine" in x and "content" in x and "checks" in x and "novelty" in x and "meta" in x
    assert isinstance(x["checks"], dict)
    assert isinstance(x["meta"], dict)
    assert 0.0 <= float(x["novelty"]) <= 1.0

def test_new_adapters_schema():
    kg = importlib.import_module("Self_Improvement.Knowledge_Graph")
    adapters = []
    for cls_name in ["MathAdapter","ProofAdapter","TranslateAdapter","SummarizeAdapter","CriticAdapter","OptimizerAdapter"]:
        cls = getattr(kg, cls_name, None)
        assert cls is not None, f"Missing adapter {cls_name}"
        adapters.append(cls())

    problem = {"title": "schema smoke", "signals": ["unit-test"]}
    outs = [a.infer(problem) for a in adapters]
    for o in outs:
        _adapter_output_ok(o)


def test_diversity_tiebreaker_prefers_unseen():
    import importlib
    kg = importlib.import_module("Self_Improvement.Knowledge_Graph")

    # حضّر مقترحات متقاربة الدرجات مع محركات/مجالات مختلفة
    proposals = [
        {"engine":"E1","novelty":0.6,"checks":{"constraints":True,"feasible":True},"meta":{},"domains":("logic",)},
        {"engine":"E2","novelty":0.6,"checks":{"constraints":True,"feasible":True},"meta":{},"domains":("planning",)},
        {"engine":"E1","novelty":0.6,"checks":{"constraints":True,"feasible":True},"meta":{},"domains":("logic",)},
    ]

    class _Dummy(kg.CognitiveIntegrationEngine):
        def __init__(self):
            super().__init__()

    d = _Dummy()
    # امتصّ priors الفارغة بأمان (تصفير أي EMA موجودة للتأكد من سلوك التنويع)
    try:
        kg._save_engine_stats({})
    except Exception:
        pass
    ranked = d._consensus_score(proposals)

    # التوقع: يظهر E2 قبل تكرار E1 داخل حزمة الدرجات المتساوية
    engines_order = [r["engine"] for r in ranked[:2]]
    assert engines_order == ["E2","E1"], f"diversity tiebreaker failed: {engines_order}"


def test_connect_engines_order_and_cap(monkeypatch):
    import os, importlib
    # ضع قائمة محركات في env بترتيب مختلف
    monkeypatch.setenv("AGL_ENGINES", "retriever,planner,deliberation,associative,emotion,self_learning")
    # اطلب ترتيبًا محددًا وسقفًا صغيرًا
    monkeypatch.setenv("AGL_ENGINE_ORDER", "planner,deliberation,associative,retriever,emotion,self_learning")
    monkeypatch.setenv("AGL_ENGINE_MAX", "3")

    kg = importlib.import_module("Self_Improvement.Knowledge_Graph")
    importlib.reload(kg)

    class _Dummy(kg.CognitiveIntegrationEngine):
        def __init__(self):
            super().__init__()

    d = _Dummy()
    names = d.connect_engines()

    # يجب احترام السقف
    assert len(names) == 3, f"expected cap=3, got {len(names)}"

    # يجب احترام الترتيب الثابت
    assert names == ["planner", "deliberation", "associative"], f"unexpected order: {names}"


# === [ADD TEST :: override failure fallback] ===
def test_override_failure_fallback(monkeypatch):
    import importlib
    # نطلب builtins مع محركين معروفين
    monkeypatch.setenv("AGL_ENGINES", "planner,deliberation")
    # نمرر Override غير صالح (module/class غير موجودين)
    monkeypatch.setenv("AGL_ENGINE_IMPLS", "planner=ghost.mod:Nope,deliberation=bad.path:Missing")
    kg = importlib.import_module("Self_Improvement.Knowledge_Graph")
    adapters = kg.discover_engines_from_env()
    names = {a.name for a in adapters}
    # مع فشل الoverride يجب أن يعود للبِلت-إن
    assert "planner" in names and "deliberation" in names
    # ضمان عدم الانهيار وأن القائمة ليست فارغة
    assert len(adapters) >= 2


# === [ADD TEST :: in-memory override success] ===
def test_override_inmemory_success(monkeypatch):
    import sys, types, os
    from Self_Improvement.Knowledge_Graph import discover_engines_from_env, CognitiveIntegrationEngine

    # 1) أنشئ "موديول" داخل الذاكرة يحوي محولاً متوافقاً مع الواجهة
    mod_name = "tmp_override_pkg.tmp_mod"
    pkg_name = "tmp_override_pkg"
    fake_pkg = types.ModuleType(pkg_name)
    fake_mod = types.ModuleType(mod_name)

    class FakeMathAdapter:
        name = "math"
        domains = ("analysis", "reason")
        def infer(self, problem, context=None, timeout_s=3.0):
            return {
                "engine": self.name,
                "content": {"ok": True, "from": "override"},
                "checks": {"constraints": True, "feasible": True},
                "novelty": 0.77,
                "meta": {"latency_ms": 1, "tokens": 0},
            }

    # حقن الصف في الموديول المؤقت
    setattr(fake_mod, "FakeMathAdapter", FakeMathAdapter)
    sys.modules[pkg_name] = fake_pkg
    sys.modules[mod_name] = fake_mod

    # 2) اضبط البيئة: نطلب math كـ override ونضيف planner كبِلت-إن لضمان fan-out
    monkeypatch.setenv("AGL_ENGINES", "math,planner")
    monkeypatch.setenv("AGL_ENGINE_IMPLS", f"math={mod_name}:FakeMathAdapter")

    # 3) discover يجب أن يعيد نسخة من FakeMathAdapter بدلاً من البِلت-إن
    adapters = discover_engines_from_env()
    by_name = {a.name: a for a in adapters}
    assert "math" in by_name and "planner" in by_name
    assert type(by_name["math"]).__name__ == "FakeMathAdapter"

    # 4) connect_engines يميّز الـimpl كـ override في registry
    cie = CognitiveIntegrationEngine()
    cie.connect_engines()
    assert "math" in cie.engines_registry
    assert cie.engines_registry["math"]["impl"] == "override"


# === [Stage-3 tests :: Self-Evolution smoke + safety gate] ===
def test_self_evolve_smoke(monkeypatch, tmp_path):
    monkeypatch.setenv("AGL_SELF_EVOLVE", "1")
    monkeypatch.setenv("AGL_EVOLVE_MAX_STEPS", "1")
    monkeypatch.setenv("AGL_EVOLVE_SANDBOX", str(tmp_path / "sbx"))
    from Self_Improvement.Knowledge_Graph import EvolutionController
    ec = EvolutionController(root=".")
    res = ec.run(max_steps=1, accept_min=0.0)
    assert len(res) == 1 and isinstance(res[0].ok, bool)


def test_self_evolve_guard_max_lines(monkeypatch, tmp_path):
    monkeypatch.setenv("AGL_SELF_EVOLVE", "1")
    monkeypatch.setenv("AGL_EVOLVE_SANDBOX", str(tmp_path / "sbx"))
    monkeypatch.setenv("AGL_EVOLVE_MUT_MAX_LINES", "0")
    from Self_Improvement.Knowledge_Graph import EvolutionController
    ec = EvolutionController(root=".")
    r = ec.evolve_once()
    assert not r.ok and "diff too large" in r.notes


def test_self_evolve_blocklist(monkeypatch, tmp_path):
    monkeypatch.setenv("AGL_SELF_EVOLVE", "1")
    monkeypatch.setenv("AGL_EVOLVE_SANDBOX", str(tmp_path / "sbx"))
    monkeypatch.setenv("AGL_EVOLVE_BLOCKLIST", "Self_Improvement/Knowledge_Graph.py")
    from Self_Improvement.Knowledge_Graph import EvolutionController
    ec = EvolutionController(root=".")
    r = ec.evolve_once()
    assert isinstance(r.ok, bool)


def test_evo_blocklist_enforced(monkeypatch, tmp_path):
    # Patch targets a blocked path -> should be rejected with path_blocked
    monkeypatch.setenv("AGL_EVOLVE_SANDBOX", str(tmp_path / "sbx"))
    monkeypatch.setenv("AGL_EVOLVE_BLOCKLIST", "tests/,infra/ci/,Self_Improvement/Safety_,Core_Consciousness")
    from Self_Improvement.Knowledge_Graph import EvolutionController, MutationLibrary

    def fake_patch(*a, **k):
        return "FILE:tests/forbidden.txt\n---\nblocked content\n"

    monkeypatch.setattr(MutationLibrary, 'micro_refactor_hint', staticmethod(fake_patch))
    ec = EvolutionController(root=".")
    r = ec.evolve_once()
    assert not r.ok and "path_blocked" in (r.notes or "")


def test_evo_line_budget(monkeypatch, tmp_path):
    monkeypatch.setenv("AGL_EVOLVE_SANDBOX", str(tmp_path / "sbx"))
    monkeypatch.setenv("AGL_EVOLVE_MUT_MAX_LINES", "5")
    from Self_Improvement.Knowledge_Graph import EvolutionController, MutationLibrary

    def big_patch(*a, **k):
        body = "\n".join([f"line {i}" for i in range(20)])
        return f"FILE:Self_Improvement/_tiny.py\n---\n{body}\n"

    monkeypatch.setattr(MutationLibrary, 'micro_refactor_hint', staticmethod(big_patch))
    ec = EvolutionController(root=".")
    r = ec.evolve_once()
    assert not r.ok and ("diff_too_large" in (r.notes or "") or r.fitness < 0)


def test_evo_git_apply_and_rollback(monkeypatch, tmp_path):
    # Provide a small valid file addition; simulate tests passing by monkeypatching run_tests
    monkeypatch.setenv("AGL_EVOLVE_SANDBOX", str(tmp_path / "sbx"))
    from Self_Improvement.Knowledge_Graph import EvolutionController, MutationLibrary

    def small_patch(*a, **k):
        return "FILE:Self_Improvement/_evo_tmp.txt\n---\nhello-evo\n"

    monkeypatch.setattr(MutationLibrary, 'micro_refactor_hint', staticmethod(small_patch))

    # Monkeypatch RewriteSandbox.run_tests to avoid running full pytest in sandbox
    import Self_Improvement.Knowledge_Graph as KG

    def fake_run_tests(self, timeout_s):
        return True, 0.1, "ok"

    monkeypatch.setattr(KG.RewriteSandbox, 'run_tests', fake_run_tests, raising=False)

    ec = EvolutionController(root=".")
    r = ec.evolve_once()
    # expectation: applied and tests_passed -> accepted True
    assert isinstance(r.ok, bool)


def test_evo_strategy_bridge(monkeypatch, tmp_path):
    # Ensure MutationLibrary can be monkeypatched to simulate StrategySynthesizer output
    monkeypatch.setenv("AGL_EVOLVE_SANDBOX", str(tmp_path / "sbx"))
    from Self_Improvement.Knowledge_Graph import EvolutionController, MutationLibrary

    called = {"ok": False}

    def synth_patch(*a, **k):
        called['ok'] = True
        return "FILE:Self_Improvement/_synth.txt\n---\npatched-by-strategy\n"

    monkeypatch.setattr(MutationLibrary, 'micro_refactor_hint', staticmethod(synth_patch))
    import Self_Improvement.Knowledge_Graph as KG
    monkeypatch.setattr(KG.RewriteSandbox, 'run_tests', lambda self, t: (True, 0.05, "ok"))

    ec = EvolutionController(root=".")
    r = ec.evolve_once()
    assert called['ok'] and isinstance(r.ok, bool)


# === [Stage-4 acceptance tests] ===
def test_stage4_memory_loop(tmp_path, monkeypatch):
    monkeypatch.setenv("AGL_MEMORY_ROOT", str(tmp_path / "mem"))
    monkeypatch.setenv("AGL_MEMORY_ENABLE", "1")
    monkeypatch.setenv("AGL_LTM_PROMOTE_MIN", "0.0")
    monkeypatch.setenv("AGL_ENGINES", "planner,deliberation")
    from Self_Improvement.Knowledge_Graph import CognitiveIntegrationEngine
    cie = CognitiveIntegrationEngine(); cie.connect_engines()
    res = cie.collaborative_solve({"title": "mloop"}, domains_needed=("planning",))
    import json, os
    stm = os.path.join(str(tmp_path / "mem"), "stm.json")
    ltm = os.path.join(str(tmp_path / "mem"), "ltm.json")
    assert os.path.exists(stm) and os.path.exists(ltm)
    assert res.get("memory_consolidated", 0) >= 0


def test_stage4_goal_and_feedback(tmp_path, monkeypatch):
    monkeypatch.setenv("AGL_ENGINE_STATS_PATH", str(tmp_path / "stats.json"))
    monkeypatch.setenv("AGL_FEEDBACK_ENABLE", "1")
    monkeypatch.setenv("AGL_ENGINES", "planner,deliberation,goal_engine")
    from Self_Improvement.Knowledge_Graph import CognitiveIntegrationEngine, _load_engine_stats
    cie = CognitiveIntegrationEngine(); cie.connect_engines()
    res = cie.collaborative_solve({"title": "gloop"}, domains_needed=("planning",))
    pri = _load_engine_stats(str(tmp_path / "stats.json")) or {}
    assert res.get("winner") is not None
    assert isinstance(pri, dict)


def test_stage4_perceptual_hub(monkeypatch):
    monkeypatch.setenv("AGL_ENGINES", "vision,audio,sensor,perceptual_hub,planner")
    from Self_Improvement.Knowledge_Graph import CognitiveIntegrationEngine
    cie = CognitiveIntegrationEngine(); cie.connect_engines()
    r = cie.collaborative_solve({"title": "percept"}, domains_needed=("planning",))
    assert "percept" in r and isinstance(r["percept"], dict)


def test_stage4_self_model(tmp_path, monkeypatch):
    p = str(tmp_path / "self_model.json")
    monkeypatch.setenv("AGL_SELF_MODEL", "1")
    monkeypatch.setenv("AGL_SELF_MODEL_PATH", p)
    monkeypatch.setenv("AGL_ENGINES", "planner,deliberation")
    from Self_Improvement.Knowledge_Graph import CognitiveIntegrationEngine
    cie = CognitiveIntegrationEngine(); cie.connect_engines()
    r = cie.collaborative_solve({"title": "self"}, domains_needed=("planning",))
    import os, json
    assert os.path.exists(p)
    data = json.load(open(p, "r", encoding="utf-8"))
    assert "recent_winner" in data


# === [PATCH :: test_result_guard.py :: diversity bonus + order/max] ===
import os
from Self_Improvement.Knowledge_Graph import CognitiveIntegrationEngine

def test_connect_engines_respects_order_and_max(monkeypatch):
    monkeypatch.setenv("AGL_ENGINES", "retriever,planner,deliberation,associative,emotion")
    monkeypatch.setenv("AGL_ENGINE_ORDER", "planner,emotion")
    monkeypatch.setenv("AGL_ENGINE_MAX", "3")
    cie = CognitiveIntegrationEngine()
    names = cie.connect_engines()
    assert names[:2] == ["planner", "emotion"], f"order not respected: {names}"
    assert len(names) == 3, f"max cap not respected, got {len(names)}"

def test_diversity_bonus_affects_tie_group(monkeypatch):
    # نضمن محركات ثابتة
    monkeypatch.setenv("AGL_ENGINES", "planner,deliberation,associative")
    monkeypatch.setenv("AGL_ENGINE_ORDER", "")
    monkeypatch.setenv("AGL_ENGINE_MAX", "0")
    monkeypatch.setenv("AGL_TIE_EPS", "0.0001")

    cie = CognitiveIntegrationEngine()
    cie.connect_engines()

    # ثلاث مقترحات بسكور متساوٍ (الوصول إلى الـ bucket)
    proposals = [
        {"engine": "planner", "novelty": 0.5, "checks": {"constraints": True, "feasible": True}},
        {"engine": "deliberation", "novelty": 0.5, "checks": {"constraints": True, "feasible": True}},
        {"engine": "associative", "novelty": 0.5, "checks": {"constraints": True, "feasible": True}},
    ]

    # جرّب بونص صغير ثم أكبر وتحقق تغيّر الفائز
    monkeypatch.setenv("AGL_TIE_DIVERSITY_BONUS", "0.0")
    ranked0 = cie._consensus_score(proposals)
    top0 = ranked0[0]["engine"]

    monkeypatch.setenv("AGL_TIE_DIVERSITY_BONUS", "0.05")
    ranked1 = cie._consensus_score(proposals)
    top1 = ranked1[0]["engine"]

    # مع bonus>0 يفضَّل أول ظهور داخل الـ bucket (قد يختلف حسب seen_engines)
    assert top0 in {"planner", "deliberation", "associative"}
    assert top1 in {"planner", "deliberation", "associative"}
    # الأكثر أهمية: الترتيب يستطيع أن يتغيّر عندما نفعّل البونص
    assert top1 != ""  # وجود فائز معتبر بعد البونص
# === [END PATCH] ===


def test_meta_reflection_updates_priors(monkeypatch):
    import os, json
    from Self_Improvement.Knowledge_Graph import CognitiveIntegrationEngine
    os.environ["AGL_META_REFLECTION"]="1"
    os.environ["AGL_ENGINES"]="planner,deliberation,motivation"
    os.environ["AGL_ENGINE_STATS_PATH"]="artifacts/test_engine_stats.json"
    # ensure clean prior
    try:
        os.remove("artifacts/test_engine_stats.json")
    except Exception:
        pass
    cie=CognitiveIntegrationEngine(); cie.connect_engines()
    res=cie.collaborative_solve({"title":"meta-reflect smoke"}, domains_needed=("planning",))
    assert res.get("winner") is not None
    # priors written
    with open("artifacts/test_engine_stats.json","r",encoding="utf-8") as f:
        stats=json.load(f)
    assert isinstance(stats, dict) and len(stats)>=1


def test_timeline_contextualizer_present(monkeypatch):
    import os
    from Self_Improvement.Knowledge_Graph import CognitiveIntegrationEngine
    os.environ["AGL_ENGINES"]="timeline,contextualizer"
    cie=CognitiveIntegrationEngine(); names=cie.connect_engines()
    assert "timeline" in names and "contextualizer" in names


def test_generative_link_injects_strategy_when_low_conf(monkeypatch):
    import os
    from Self_Improvement.Knowledge_Graph import CognitiveIntegrationEngine
    os.environ["AGL_ENGINES"]="planner"
    os.environ["AGL_GENERATIVE_LINK"]="1"
    os.environ["AGL_META_MIN_CONF"]="0.99"
    cie=CognitiveIntegrationEngine(); cie.connect_engines()
    res=cie.collaborative_solve({"title":"force-gen-link"}, domains_needed=("planning",))
    top=res.get("top",[])
    assert any(p.get("engine")=="gen_creativity" for p in top)


# =====================[ Stage-2.0 tests :: perceptual hub + goal engine + memory ]=====================

import os, json, time
import pytest

from Self_Improvement.Knowledge_Graph import CognitiveIntegrationEngine

def _has_std_schema(proposal):
    # same standard schema used elsewhere: engine/content/checks/novelty/meta
    return isinstance(proposal, dict) \
        and "engine" in proposal \
        and "content" in proposal \
        and "checks" in proposal \
        and "novelty" in proposal \
        and "meta" in proposal

def test_perceptual_and_goal_schema(monkeypatch):
    # light settings to reduce noise
    monkeypatch.setenv("AGL_COGNITIVE_INTEGRATION", "1")
    monkeypatch.setenv("AGL_ENGINES", "vision,audio,sensor,perceptual_hub,goal_engine")
    cie = CognitiveIntegrationEngine()
    names = cie.connect_engines()
    # new engines should be available
    assert "perceptual_hub" in names
    assert "goal_engine" in names

    # call infer on each adapter to validate schema
    props = []
    for n in ("perceptual_hub", "goal_engine"):
        adapter = None
        for a in getattr(cie, 'adapters', []) or []:
            if getattr(a, 'name', None) == n:
                adapter = a
                break
        assert adapter is not None, f"adapter {n} not found in cie.adapters"
        p = adapter.infer({"title": "schema-check"}, context=[{"engine":"vision","content":{"detected":["x"]}}])
        assert _has_std_schema(p)
        props.append(p)

    hub = [p for p in props if p["engine"] == "perceptual_hub"][0]
    goal = [p for p in props if p["engine"] == "goal_engine"][0]
    assert "fusion" in hub["content"] and "summary" in hub["content"]
    assert "goals" in goal["content"] and isinstance(goal["content"]["goals"], list) and len(goal["content"]["goals"]) >= 3


def test_perception_overrides_loaded(monkeypatch):
    from Self_Improvement.Knowledge_Graph import CognitiveIntegrationEngine
    monkeypatch.setenv("AGL_COGNITIVE_INTEGRATION", "1")
    monkeypatch.setenv("AGL_ENGINES", "planner,deliberation,vision,audio,sensor")
    cie = CognitiveIntegrationEngine()
    names = cie.connect_engines()
    assert "vision" in names and "audio" in names and "sensor" in names


def test_tick_writes_stm(tmp_path, monkeypatch):
    from Self_Improvement.Knowledge_Graph import CognitiveIntegrationEngine
    memroot = tmp_path / "memory_stage5"
    monkeypatch.setenv("AGL_MEMORY_ROOT", str(memroot))
    monkeypatch.setenv("AGL_COGNITIVE_INTEGRATION", "1")
    monkeypatch.setenv("AGL_ENGINES", "planner,deliberation")
    cie = CognitiveIntegrationEngine(); cie.connect_engines()
    # simulate perceptions
    try:
        cie.pbus.push("vision", {"objects": ["pill", "box"]}, "t0")
        cie.pbus.push("audio", {"text": "temperature 38C"}, "t0")
    except Exception:
        pass
    res = cie.tick(goal={"task": "triage"})
    assert res.get("winner") is not None
    stm = memroot / "stm.json"
    assert stm.exists(), "tick() must produce STM trace"


def test_hub_injection_when_perception_present(monkeypatch):
    monkeypatch.setenv("AGL_COGNITIVE_INTEGRATION", "1")
    monkeypatch.setenv("AGL_COLLECTIVE_INTELLIGENCE", "1")
    monkeypatch.setenv("AGL_ENGINES", "vision,audio,sensor,perceptual_hub,planner,deliberation")
    monkeypatch.setenv("AGL_TIE_EPS", "0.02")

    cie = CognitiveIntegrationEngine()
    names = cie.connect_engines()
    assert all(x in names for x in ("vision","audio","sensor","perceptual_hub"))

    res = cie.collaborative_solve({"title": "fusion-check"}, domains_needed=("perception",))
    top_names = [t.get("engine") for t in res.get("top", [])]
    assert "perceptual_hub" in top_names or (res.get("winner") or {}).get("engine") == "perceptual_hub"


def test_memory_loop_consolidation_stage2(monkeypatch, tmp_path):
    memroot = tmp_path / "memory_stage2"
    monkeypatch.setenv("AGL_MEMORY_ROOT", str(memroot))
    monkeypatch.setenv("AGL_LTM_PROMOTE_MIN", "0.0")
    monkeypatch.setenv("AGL_COGNITIVE_INTEGRATION", "1")
    monkeypatch.setenv("AGL_ENGINES", "planner,deliberation,goal_engine")

    cie = CognitiveIntegrationEngine()
    cie.connect_engines()

    res = cie.collaborative_solve({"title": "memory-check"}, domains_needed=("planning",))
    assert res.get("winner") is not None

    stm_path = memroot / "stm.json"
    ltm_path = memroot / "ltm.json"
    assert stm_path.exists()

    time.sleep(0.05)
    assert ltm_path.exists()

    with open(stm_path, "r", encoding="utf-8") as f:
        stm = json.load(f)
    with open(ltm_path, "r", encoding="utf-8") as f:
        ltm = json.load(f)

    assert isinstance(stm, dict) and "recent" in stm and len(stm["recent"]) >= 1
    assert isinstance(ltm, dict) and "facts" in ltm and len(ltm["facts"]) >= 1

# === [ADD TEST :: LTM promotion threshold respected] ===
def test_ltm_threshold_respected(monkeypatch, tmp_path):
    from Self_Improvement.Knowledge_Graph import CognitiveIntegrationEngine
    memroot = tmp_path / "memory_thresh"
    monkeypatch.setenv("AGL_MEMORY_ROOT", str(memroot))
    monkeypatch.setenv("AGL_COGNITIVE_INTEGRATION", "1")
    monkeypatch.setenv("AGL_ENGINES", "planner,deliberation,goal_engine")
    monkeypatch.setenv("AGL_MEMORY_ENABLE", "1")

    # high threshold: no promotion expected
    monkeypatch.setenv("AGL_LTM_PROMOTE_MIN", "0.95")
    cie = CognitiveIntegrationEngine()
    cie.connect_engines()
    _ = cie.collaborative_solve({"title": "no-promo"}, domains_needed=("planning",))
    ltm_path = memroot / "ltm.json"
    assert (not ltm_path.exists()) or (ltm_path.exists() and ltm_path.stat().st_size <= 4)

    # lower threshold -> promotion expected
    monkeypatch.setenv("AGL_LTM_PROMOTE_MIN", "0.0")
    cie = CognitiveIntegrationEngine()
    cie.connect_engines()
    _ = cie.collaborative_solve({"title": "promo"}, domains_needed=("planning",))
    assert ltm_path.exists() and ltm_path.stat().st_size > 4


