# -*- coding: utf-8 -*-
"""
Unified runner for a medical-project query using AGL's `agl_pipeline`.

Saves nothing by default — prints the answer and a provenance summary.

Run (PowerShell):
$env:PYTHONPATH='D:/AGL/repo-copy'; $env:AGL_FAST_MODE='1'; \
& D:/AGL/.venv/Scripts/python.exe tools/run_medical_project_query.py "سؤالك هنا"
"""
import json
import sys
import time
import argparse
import os
from textwrap import dedent
from typing import Any, Dict
from pathlib import Path
import datetime as _dt

# Defer importing the heavy AGL pipeline until needed (avoid expensive startup when
# using the fast single-LLM path). We'll import inside `main()` when required.
agl_pipeline = None
_IMPORT_ERROR = None


PROJECT_CONTEXT = dedent("""
أنت تعمل كـ "نظام AGL" يساعد باحثين في إعداد بحث ميداني بعنوان: «الأدوية المهرّبة بين تحدّيات الرقابة الدوائية والحاجة العلاجية للمرضى» في محافظة مأرب – اليمن.
المطلوب من النظام:
- إعطاء إجابات طبية/دوائية دقيقة قدر الإمكان (مع مراعاة كونه نموذجًا لغويًا).
- ربط الإجابات بسياق تهريب الأدوية: الأسباب، القنوات، الآثار على المرضى، خصوصًا الأمراض المزمنة مثل: ارتفاع ضغط الدم، السكري، الفشل الكلوي.
- الاستفادة من: Strategic Memory, Continual Learning, RAG / rag_index, Executive Agent عند الحاجة.
أجب بالعربية الفصحى الواضحة، مع تنظيم منطقي، ويفضّل أن تُظهر بنية التفكير (خطوات، نقاط) عندما يكون ذلك مفيدًا للباحث.
""")


def build_full_question(user_question: str) -> str:
    user_question = (user_question or "").strip()
    return PROJECT_CONTEXT + "\n\nسؤال الباحث:\n" + user_question


def summarize_provenance(prov: Dict[str, Any]) -> None:
    print("\n=== ملخص الأنظمة الداخلية (provenance summary) ===")
    if not prov:
        print("- لا يوجد حقل provenance في المخرجات (out).")
        return

    # 1) winner
    winner = prov.get("winner") or {}
    if winner:
        engine = winner.get("engine")
        domains = winner.get("domains")
        print(f"- المحرك الفائز: {engine!r} | المجالات: {domains}")
    else:
        print("- لم أجد معلومات واضحة عن المحرك الفائز داخل provenance.winner.")

    # 2) RAG
    rag_info = prov.get("rag") or prov.get("rag_info") or {}
    if rag_info:
        used = rag_info.get("used")
        print(f"- RAG: {'استُخدم ✅' if used else 'موجود لكن قد لا يكون مستخدمًا صراحة'}")
        preview = rag_info.get("ctx_preview") or rag_info.get("summary")
        if preview:
            preview_str = str(preview)
            if len(preview_str) > 200:
                preview_str = preview_str[:200] + "..."
            print(f" * مقتطف سياق RAG: {preview_str}")
    else:
        print("- RAG: لا توجد إشارة صريحة (rag / rag_info) في الـ provenance.")

    # 3) Continual Learning / learned facts
    cl = prov.get("continual_learning") or prov.get("learned_facts") or {}
    if cl:
        print("- Continual Learning / Learned Facts: توجد إشارة داخل provenance.")
        keys = list(cl.keys()) if isinstance(cl, dict) else []
        if keys:
            print(f" * مفاتيح مرتبطة: {keys[:5]}")
    else:
        print("- Continual Learning: لا توجد إشارة واضحة (قد يكون مدمجًا في طبقات أخرى).")

    # 4) Strategic Memory / LTM
    sm = prov.get("strategic_memory") or prov.get("ltm") or {}
    if sm:
        print("- Strategic Memory / LTM: هناك بيانات مرتبطة داخل provenance.")
        keys = list(sm.keys()) if isinstance(sm, dict) else []
        if keys:
            print(f" * مفاتيح مرتبطة: {keys[:5]}")
    else:
        print("- Strategic Memory / LTM: لم أجد حقولًا صريحة، ربما مدمجة في winner أو حلول أخرى.")

    # 5) Executive Agent / Taskmaster
    exec_info = prov.get("executive_agent") or prov.get("taskmaster") or {}
    if exec_info:
        print("- Executive Agent / Taskmaster: مذكور في الـ provenance.")

    print("\n=== JSON كامل للـ provenance (للفحص التفصيلي) ===")
    try:
        print(json.dumps(prov, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"(تعذر طباعة JSON منسّق للـ provenance: {e})")
        print(str(prov))


def main() -> None:
    global agl_pipeline
    # If `agl_pipeline` hasn't been imported yet that's fine; we import lazily below
    # when needed. Do not fail immediately here.
    parser = argparse.ArgumentParser(
        description="Run medical project query through AGL (fast or full pipeline)."
    )
    parser.add_argument(
        "question",
        nargs="?",
        help="السؤال الطبي/البحثي الذي تريد توجيهه للنظام AGL",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="استخدم المحرك السريع medical_qa_fast بدلاً من المسار المتعدد الخطوات.",
    )
    args = parser.parse_args()

    if args.question:
        user_q = args.question
    else:
        print("أدخل سؤالك (يفضّل أن يكون متعلقًا بتهريب الأدوية / السياق الطبي في مأرب):")
        user_q = input("> ").strip()

    if not user_q:
        print("لم يتم إدخال سؤال. إنهاء.")
        return

    full_question = build_full_question(user_q)
    print("\n=== تشغيل AGL عبر agl_pipeline ===")
    print(f"سؤال (مع سياق المشروع):\n{full_question}\n")

    # Allow a fast single-LLM path for medical queries to avoid heavy multi-step
    # processing. Enable via env `AGL_MEDICAL_FAST=1` / `AGL_FAST_MODE=1` or CLI `--fast`.
    env_fast = os.getenv("AGL_MEDICAL_FAST", "0") == "1" or os.getenv("AGL_FAST_MODE", "0") == "1"
    use_fast = args.fast or env_fast

    start_run = time.time()
    if use_fast:
        # Prefer a dedicated medical fast engine if available; fallback to direct HostedLLMAdapter
        try:
            # Prefer a clean fast implementation if present
            try:
                from Self_Improvement.medical_qa_fast_clean import medical_qa_fast as medical_qa_fast_impl
                print("[INFO] Running medical fast path via medical_qa_fast_clean engine")
            except Exception:
                from Self_Improvement.medical_qa_fast import medical_qa_fast as medical_qa_fast_impl
                print("[INFO] Running medical fast path via medical_qa_fast engine")
            out = medical_qa_fast_impl(full_question, timeout_s=float(os.getenv("AGL_MEDICAL_TIMEOUT", "25")))
        except Exception as e:
            print("[WARN] medical_qa_fast import/call failed, falling back to HostedLLMAdapter; error:", e)
            try:
                from Self_Improvement.hosted_llm_adapter import HostedLLMAdapter
                hosted = HostedLLMAdapter()
                task = {"question": full_question, "task_type": "qa_single", "engine_hint": "medical_fast"}
                print("[INFO] Running medical fast path via HostedLLMAdapter (single call)")
                out = hosted.process_task(task, timeout_s=25.0)
            except Exception as e2:
                print("[WARN] fast path failed, falling back to agl_pipeline; error:", e2)
                # Import agl_pipeline lazily for fallback
                try:
                    from Self_Improvement.Knowledge_Graph import agl_pipeline as _agl
                    agl_pipeline = _agl
                except Exception as e3:
                    print("agl_pipeline import failed:", e3)
                    return
                try:
                    out = agl_pipeline(full_question)
                except Exception as e4:
                    print("agl_pipeline raised an exception:", e4)
                    return
    else:
        # Import agl_pipeline lazily to avoid heavy initialization when not needed
        try:
            from Self_Improvement.Knowledge_Graph import agl_pipeline as _agl
            agl_pipeline = _agl
        except Exception as e:
            print("ERROR: could not import agl_pipeline from Self_Improvement.Knowledge_Graph:", e)
            return
        try:
            out = agl_pipeline(full_question)
        except Exception as e:
            print("agl_pipeline raised an exception:", e)
            return

    # record elapsed and persist a minimal run record (works for dict or plain outputs)
    elapsed = time.time() - start_run
    if isinstance(out, dict):
        # support multiple adapter output shapes: direct 'answer' or nested under 'content'
        answer = out.get("answer") or out.get("final_answer") or out.get("result")
        if not answer and isinstance(out.get("content"), dict):
            answer = out.get("content", {}).get("answer") or out.get("content", {}).get("final") or out.get("content", {}).get("response")
        print("\n=== الإجابة النهائية من AGL ===\n")
        print(answer or "(لم أجد حقل 'answer' في المخرجات)")
        prov = out.get("provenance") or {}
        summarize_provenance(prov)
        # Append run log
        try:
            LOG_PATH = Path("artifacts/medical_queries.jsonl")
            LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            # Determine whether RAG was used by checking multiple provenance places.
            rag_used = False
            if isinstance(prov, dict):
                # Preferred explicit flag (pipeline-style)
                try:
                    rag_used = bool((prov.get("rag") or prov.get("rag_info") or {}).get("used"))
                except Exception:
                    rag_used = False
                # If not explicit, inspect raw_provenance/meta for a short-circuit source marker
                if not rag_used:
                    raw = prov.get("raw_provenance") or prov.get("meta") or {}
                    try:
                        source = (raw or {}).get("source")
                        if source in ("rag_shortcircuit", "rag_pipeline", "rag_hybrid", "rag"):
                            rag_used = True
                    except Exception:
                        pass

            record = {
                "ts": _dt.datetime.utcnow().isoformat() + "Z",
                "user_question": user_q,
                "full_question": full_question,
                "answer": answer,
                "winner_engine": (prov.get("winner") or {}).get("engine") if isinstance(prov, dict) else None,
                "rag_used": bool(rag_used),
                "provenance": prov,
                "latency_s": float(elapsed),
                # also expose a simple steps timeline if not provided by provenance
                "steps": prov.get("events") if isinstance(prov, dict) and prov.get("events") else [float(elapsed)],
            }
            with LOG_PATH.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as _e:
            print(f"[WARN] تعذر حفظ لوج التجربة: {_e}")
    else:
        print("\n=== مخرجات AGL (غير قياسية) ===\n")
        print(out)
        # Save a minimal record so we can analyze timings even when out is not a dict
        try:
            LOG_PATH = Path("artifacts/medical_queries.jsonl")
            LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            record = {
                "ts": _dt.datetime.utcnow().isoformat() + "Z",
                "user_question": user_q,
                "full_question": full_question,
                "answer": str(out)[:1000],
                "winner_engine": None,
                "rag_used": False,
                "provenance": {},
                "latency_s": float(elapsed),
                "steps": [float(elapsed)],
            }
            with LOG_PATH.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            pass


if __name__ == "__main__":
    main()
