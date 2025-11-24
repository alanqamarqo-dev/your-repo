# -*- coding: utf-8 -*-
"""
مساعد تشغيل اختبار AGI الشامل
"""

import subprocess
import sys
import os
import json
import time

def run_agi_comprehensive_test():
    """تشغيل اختبار AGI الشامل مع إعدادات مخصصة"""

    # إعداد متغيرات البيئة
    env_vars = {
        "AGL_EMBEDDINGS_ENABLE": "1",
        "AGL_RETRIEVER_BLEND_ALPHA": "0.65",
        "AGL_SELF_LEARNING_ENABLE": "1",
        "AGL_DELIBERATION_ENABLE": "1",
        "AGL_EMOTION_CONTEXT_ENABLE": "1",
        "AGL_PLANNER_ENABLE": "1",
        "AGL_ASSOC_GRAPH_ENABLE": "1",
        "PYTHONPATH": os.getcwd()
    }

    # تحديث environment
    for key, value in env_vars.items():
        os.environ[key] = value

    # Print override notice early if AGL_ENGINE_IMPLS provided
    try:
        def _print_override_notice():
            spec = os.getenv("AGL_ENGINE_IMPLS", "").strip()
            if not spec:
                return
            print("\n[override] AGL_ENGINE_IMPLS detected — attempting dynamic engine overrides.", flush=True)
            mapping = {}
            try:
                if spec.startswith("{"):
                    mapping = json.loads(spec)
                else:
                    for kv in spec.split(","):
                        if "=" in kv:
                            k, v = kv.split("=", 1)
                            mapping[k.strip()] = v.strip()
            except Exception:
                mapping = {"__raw__": spec}
            print(f"[override] requested engines: {', '.join(sorted(mapping.keys())) or '(parsed failed)'}", flush=True)
            for k, v in mapping.items():
                print(f"[override]  - {k} => {v}", flush=True)

        _print_override_notice()
    except Exception:
        pass

    try:
        # تشغيل الاختبار كمسكريبت مستقل
        result = subprocess.run(
            [sys.executable, os.path.join("tests", "test_agi_comprehensive.py")],
            capture_output=True,
            text=True,
            encoding="utf-8"
        )

        print("نتائج الاختبار:")
        print(result.stdout)

        if result.stderr:
            print("الأخطاء:")
            print(result.stderr)

        # --- self-learning autorun: run a training epoch after the test finishes ---
        try:
            if os.getenv("AGL_SELF_LEARNING_ENABLE", "0") == "1":
                from Self_Improvement import Self_Improvement_Engine as SIE
                mgr = SIE.SelfLearningManager()
                res = mgr.run_training_epoch()
                print("Self-learning autorun:", res)
        except Exception as e:
            # don't fail the runner if autorun errors
            print("Self-learning autorun skipped:", e)

        # === CognitiveIntegrationEngine demo autorun (guarded by env var) ===
        try:
            if os.getenv("AGL_COGNITIVE_INTEGRATION", "0") == "1":
                from Self_Improvement import Knowledge_Graph as KG
                cie = KG.CognitiveIntegrationEngine()
                cie.connect_engines()
                demo_problem = {
                    "title": "Demo: early outbreak detection in hot climate coastal city",
                    "signals": ["social_graph", "satellite_climate", "epidemic_models", "privacy"]
                }
                result = cie.collaborative_solve(
                    problem=demo_problem,
                    domains_needed=["semantic_search", "planning", "reasoning"]
                )
                # robust handling: `solutions` may be a list or an int (count)
                sols_obj = result.get("solutions", []) if isinstance(result, dict) else []
                if isinstance(sols_obj, int):
                    sols_n = sols_obj
                else:
                    try:
                        sols_n = len(sols_obj)
                    except Exception:
                        sols_n = 1 if sols_obj else 0

                print("CognitiveIntegration result:",
                      {"integration_id": result.get("integration_id"),
                       "solutions": sols_n})
            else:
                print("CognitiveIntegration skipped: AGL_COGNITIVE_INTEGRATION!=1")
        except Exception as e:
            print("CognitiveIntegration skipped:", e)

        # === [BEGIN :: Phase-3 autorun in agi_test_runner.py] ===
        try:
            if os.getenv("AGL_COLLECTIVE_INTELLIGENCE","0") == "1":
                print("CollectiveIntelligence autorun:")
                from Self_Improvement import Knowledge_Graph as KG
                cie = KG.CognitiveIntegrationEngine()
                cie.connect_engines()
                demo_problem = {
                    "title": "City mobility decarbonization under heatwaves",
                    "constraints": ["cost<=X", "equity>=Y", "peak-heat mitigation"],
                }
                domains = ["planning","deliberation","retriever","emotion","associative"]
                res = cie.collaborative_solve(demo_problem, domains_needed=domains)
                collective_result = res
                print("CollectiveIntelligence result:", collective_result)
                print("Note: In CI, keep AGL_COLLECTIVE_INTELLIGENCE=0 to avoid nondeterministic fan-out.", flush=True)

                # === [BEGIN :: enrich agi_comprehensive_report.json] ===
                try:
                    report_path = os.path.join("artifacts","agi_comprehensive","agi_comprehensive_report.json")
                    if os.path.exists(report_path):
                        import json, io
                        with io.open(report_path, "r", encoding="utf-8") as f:
                            rep = json.load(f)
                        # نبني ملخصًا صغيرًا من آخر نتيجة مطبوعة
                        def _local_safe_float(x, default=0.0):
                            try:
                                return float(x)
                            except Exception:
                                return default

                        collective_summary = {
                            "integration_id": (collective_result or {}).get("integration_id"),
                            "solutions_n": (collective_result or {}).get("solutions"),
                            "winner_engine": ((collective_result or {}).get("winner") or {}).get("engine"),
                            "top3": [
                                {"engine": (t or {}).get("engine"), "score": _local_safe_float((t or {}).get("score"), 0.0)}
                                for t in ((collective_result or {}).get("top") or [])[:3]
                            ]
                        }
                        rep["collective_summary"] = collective_summary
                        with io.open(report_path, "w", encoding="utf-8") as f:
                            json.dump(rep, f, ensure_ascii=False, indent=2)
                except Exception as _e:
                    print("Note: unable to enrich report with collective_summary:", _e)
                # === [END] ===
            else:
                print("CollectiveIntelligence skipped (AGL_COLLECTIVE_INTELLIGENCE!=1).")
        except Exception as e:
            print("CollectiveIntelligence autorun skipped:", e)
        # === [END :: Phase-3 autorun] ===

        # === [BEGIN :: Generative Creativity autorun] ===
        try:
            def _run_generative_creativity_autorun():
                if os.getenv("AGL_GENERATIVE_CREATIVITY","0") != "1":
                    print("GenerativeCreativity skipped (AGL_GENERATIVE_CREATIVITY != 1)", flush=True)
                    return
                try:
                    from Self_Improvement.Knowledge_Graph import CognitiveIntegrationEngine
                    cie = CognitiveIntegrationEngine()
                    cie.connect_engines()
                    problem = {"title": "Phase-4 ideation demo", "signals": ["cross-domain","future-scenarios","novelty"]}
                    res = cie.collaborative_solve(problem, ())
                    ideas = []
                    for p in (res.get("top") or []):
                        if (p or {}).get("engine") == "gen_creativity":
                            ideas.extend((p or {}).get("content", {}).get("ideas", []))
                    if not ideas:
                        ideas = [{"idea":"(no gen_creativity ideas surfaced in top set)","novelty":0.0}]
                    os.makedirs("artifacts", exist_ok=True)
                    with open("artifacts/generative_ideas.jsonl","a",encoding="utf-8") as f:
                        f.write(json.dumps({"ts": time.time(), "integration_id": res.get("integration_id"),
                                            "ideas": ideas}, ensure_ascii=False)+"\n")
                    print(f"GenerativeCreativity result: {{'integration_id': '{res.get('integration_id')}', 'ideas': {len(ideas)}}}", flush=True)
                except Exception as e:
                    print(f"GenerativeCreativity skipped: {e}", flush=True)

            _run_generative_creativity_autorun()
        except Exception:
            pass
        # === [END :: Generative Creativity autorun] ===

        # Handle cases where `result` may have been reassigned (e.g. to a dict
        # returned by CognitiveIntegration). Accept either a subprocess-like
        # object with `returncode==0` or a dict with status=='success'.
        if (isinstance(result, dict) and result.get("status") == "success") or \
           (hasattr(result, "returncode") and result.returncode == 0):
            return True
        return False

    except Exception as e:
        print(f"خطأ في تشغيل الاختبار: {e}")
        return False

if __name__ == "__main__":
    success = run_agi_comprehensive_test()
    sys.exit(0 if success else 1)
