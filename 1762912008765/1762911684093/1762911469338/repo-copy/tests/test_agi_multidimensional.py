import time
import json
import os
from typing import Dict, Any

import pytest

from Core_Engines.Hosted_LLM import chat_llm


def now_ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())


def record_interaction(log: Dict[str, Any], name: str, prompt: str, resp: Dict[str, Any]):
    entry = {
        "name": name,
        "timestamp": now_ts(),
        "prompt": prompt,
        "response": resp,
    }
    log.setdefault("interactions", []).append(entry)


def simple_keyword_score(text: str, keywords) -> float:
    t = (text or "").lower()
    hits = 0
    for k in keywords:
        if k.lower() in t:
            hits += 1
    # scale to 0..10
    if not keywords:
        return 0.0
    return min(10.0, (hits / len(keywords)) * 10.0)


def length_score(text: str, ideal_chars: int = 800) -> float:
    l = len(text or "")
    return min(10.0, (l / ideal_chars) * 10.0)


def run_task(name: str, prompt: str, keywords=None, ideal_chars=800) -> Dict[str, Any]:
    messages = [
        {"role": "system", "content": "You are an expert assistant. Answer concisely and rigorously."},
        {"role": "user", "content": prompt},
    ]
    start = time.time()
    resp = chat_llm(messages, max_new_tokens=1024)
    duration = time.time() - start
    text = ""
    if isinstance(resp, dict):
        # prefer top-level text, then answer.text; otherwise stringify safely
        t = resp.get("text")
        if isinstance(t, str) and t:
            text = t
        else:
            ans = resp.get("answer")
            if isinstance(ans, dict) and isinstance(ans.get("text"), str):
                text = ans.get("text")
            else:
                try:
                    text = json.dumps(resp, ensure_ascii=False)
                except Exception:
                    text = str(resp)
    else:
        text = str(resp)

    # ensure text is a plain string for scorers
    if not isinstance(text, str):
        text = str(text or "")

    # scoring heuristics
    kw_score = simple_keyword_score(text, keywords or [])
    len_score = length_score(text, ideal_chars=ideal_chars)
    # simple average of metrics
    score = round((kw_score * 0.6 + len_score * 0.4), 2)

    return {
        "ok": True,
        "duration": duration,
        "text": text,
        "score": score,
        "kw_score": kw_score,
        "len_score": len_score,
        "raw_resp": resp,
    }


def aggregate_scores(scores: Dict[str, Dict[str, Any]]) -> float:
    # weights from user prompt
    weights = {
        "multidisciplinary": 0.20,
        "fast_learning": 0.25,
        "creativity": 0.15,
        "contextual": 0.20,
        "ambiguity": 0.20,
    }
    total = 0.0
    for k, w in weights.items():
        s = scores.get(k, {}).get("score", 0.0)
        # s is 0..10 -> convert to 0..100
        total += (s * 10.0) * w
    return round(total, 2)


def write_artifact(out: Dict[str, Any], path: str = "artifacts/agi_multitest_result.json"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)


def test_agi_multidimensional_run():
    """Run a multi-dimensional AGI test and write results to artifacts.

    This test is intentionally permissive: it does not assert a pass/fail by default.
    Set environment variable AGI_STRICT=1 to make the test assert the 85% threshold.
    """
    log: Dict[str, Any] = {"run_ts": now_ts(), "interactions": []}

    scores = {}

    # 1) Multidisciplinary reasoning
    prompt1 = (
        "تحليل مترابط: توقع تأثير ارتفاع أسعار النفط على الاقتصاد الكلي، "
        "الاستقرار الجيوسياسي، الانتقال للطاقة المتجددة، والسلوك الاستهلاكي. قدم سببية واضحة." 
    )
    r1 = run_task("multidisciplinary", prompt1, keywords=["econom", "geo", "renew", "consume", "inflation", "energy", "geopolit"], ideal_chars=600)
    record_interaction(log, "multidisciplinary", prompt1, r1["raw_resp"]) 
    scores["multidisciplinary"] = r1

    # 2) Fast learning (game strategy)
    prompt2 = (
        "تعلم واستخرج استراتيجية فائزة للعبة: لاعبان يختاران أرقام 1-9 بدون تكرار؛"
        "من يجمع 3 أرقام مجموعها 15 يفوز. اشرح الاستراتيجية باختصار ودليل رياضي."
    )
    r2 = run_task("fast_learning", prompt2, keywords=["15", "strategy", "win", "magic"], ideal_chars=400)
    record_interaction(log, "fast_learning", prompt2, r2["raw_resp"]) 
    scores["fast_learning"] = r2

    # 3) Creativity
    prompt3 = (
        "اكتب قصة خيال علمي تجمع بين فيزياء الكم، الأساطير الإسكندنافية، والاقتصاد السلوكي. "
        "تأكد من تماسك الرموز والطبقات.")
    r3 = run_task("creativity", prompt3, keywords=["quantum", "odin", "behavioral", "norse", "econom"], ideal_chars=1200)
    record_interaction(log, "creativity", prompt3, r3["raw_resp"]) 
    scores["creativity"] = r3

    # 4) Contextual understanding (Arabic short text)
    prompt4 = (
        "النص: 'كان الصمت أكثر إيلامًا من الصراخ. النظرات التي تبادلوها قالت أكثر مما تستطيع الكلمات حمله."
        " في تلك اللحظة، فهم أن بعض الجروح لا تندمل.'\n\n" 
        "المطلوب: 1) تحليل المشاعر والدوافع غير المعلنة 2) استنتاج العلاقة بين الشخصيات 3) التنبؤ بما سيحدث لاحقًا مع التبرير"
    )
    r4 = run_task("contextual", prompt4, keywords=["صمت", "جروح", "نظرات", "مشاعر", "علاقة"], ideal_chars=400)
    record_interaction(log, "contextual", prompt4, r4["raw_resp"]) 
    scores["contextual"] = r4

    # 5) Ambiguity adaptation
    prompt5 = (
        "شركة تواجه انخفاضًا في المبيعات رغم جودة المنتج. دون طرح أسئلة إضافية، حلل الأسباب المحتملة "
        "واقترح حلولاً عملية مع قيود المعلومات المحدودة."
    )
    r5 = run_task("ambiguity", prompt5, keywords=["marketing", "pricing", "distribution", "perception", "quality"], ideal_chars=600)
    record_interaction(log, "ambiguity", prompt5, r5["raw_resp"]) 
    scores["ambiguity"] = r5

    overall = aggregate_scores(scores)

    result = {
        "run_ts": log["run_ts"],
        "overall_score_percent": overall,
        "weights": {"multidisciplinary": 20, "fast_learning": 25, "creativity": 15, "contextual": 20, "ambiguity": 20},
        "scores": scores,
        "interactions": log["interactions"],
    }

    write_artifact(result)

    # Output summary for human inspection
    print("AGI multidimensional test finished. Overall:", overall)
    print("Artifact:", os.path.abspath("artifacts/agi_multitest_result.json"))

    strict = os.getenv("AGI_STRICT", "0") in ("1", "true", "True")
    if strict:
        assert overall >= 85.0, f"AGI overall score below threshold: {overall}%"
