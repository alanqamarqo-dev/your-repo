# -*- coding: utf-8 -*-
"""
Winograd Schema evaluation harness (Arabic examples).

Usage:
  # run live (will attempt to import Core_Engines.External_InfoProvider)
  $env:PYTHONPATH='D:\\AGL'; .venv\\Scripts\\python.exe scripts\\winograd_test.py --live

Notes:
 - If --live is provided or AGL_EXTERNAL_INFO_ENABLED=1, the script will try to call
   ExternalInfoProvider.fetch_facts(question, hints=[...]) and use the provider's
   "answer" field as the system answer.
 - If the provider call fails, the script falls back to a small lexical heuristic
   (this is only to allow the test to complete; the live run is the authoritative mode).

The comparison is loose: normalized, case-insensitive substring/equals match with the
expected target. Results are written to stdout and a JSON summary file under
artifacts/reports/winograd_results.json
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Examples (10 diverse Winograd-style pairs in Arabic)
winograd_examples = [
    {"الجملة": "التمساح أكل الطفل لأنه كان جائعاً", "السؤال": "من كان جائعاً؟", "الإجابة_الصحيحة": "التمساح"},
    {"الجملة": "التمساح أكل الطفل لأنه كان صغيراً", "السؤال": "من كان صغيراً؟", "الإجابة_الصحيحة": "الطفل"},
    {"الجملة": "وضعت التفاحة في الوعاء لأنه كان كبيراً", "السؤال": "ما كان كبيراً؟", "الإجابة_الصحيحة": "الوعاء"},
    {"الجملة": "وضعت التفاحة في الوعاء لأنه كان ناضجاً", "السؤال": "ما كان ناضجاً؟", "الإجابة_الصحيحة": "التفاحة"},
    # Additional Winograd-like Arabic examples (simple variants)
    {"الجملة": "أخذت المعلمة القلم من الطالب لأنها كانت مشغولة", "السؤال": "من كانت مشغولة؟", "الإجابة_الصحيحة": "المعلمة"},
    {"الجملة": "أخذت المعلمة القلم من الطالب لأنه كان سيئاً", "السؤال": "من كان سيئاً؟", "الإجابة_الصحيحة": "القلم"},
    {"الجملة": "أعطت الأم الكتاب للطفل لأنه كان مهتماً", "السؤال": "من كان مهتماً؟", "الإجابة_الصحيحة": "الطفل"},
    {"الجملة": "أعطت الأم الكتاب للطفل لأنه كان قديمًا", "السؤال": "ما كان قديمًا؟", "الإجابة_الصحيحة": "الالكتاب"},
    {"الجملة": "أغلق المهندس الباب لأنه كان صاخباً", "السؤال": "ما كان صاخباً؟", "الإجابة_الصحيحة": "الباب"},
    {"الجملة": "أغلق المهندس الباب لأنه كان معطلاً", "السؤال": "ما كان معطلاً؟", "الإجابة_الصحيحة": "الباب"}
]

# small normalizer

def normalize(s: str) -> str:
    if s is None:
        return ""
    return " ".join(s.strip().lower().split())


# tiny fallback heuristic: pronoun/keyword proximity
def heuristic_answer(sentence: str, question: str) -> str:
    # very simple approach: look for candidate nouns in the sentence (split tokens)
    toks = [t.strip('.,؟!؛"\'') for t in sentence.split()]
    # prefer explicit nouns from the sentence that match question tokens
    qwords = question.replace('؟', '').split()
    # choose last noun-like token before comma/that contains likely adjectives
    # fallback: return first token (very weak)
    if len(toks) >= 2:
        return toks[0]
    return sentence


# use provider when live

def ask_provider(sentence: str, question: str, model: str | None = None) -> Dict[str, Any]:
    try:
        from Core_Engines.External_InfoProvider import ExternalInfoProvider
    except Exception as e:
        return {"ok": False, "error": f"import_failed: {e}"}

    try:
        prov = ExternalInfoProvider(model=model)
    except Exception as e:
        return {"ok": False, "error": f"init_failed: {e}"}

    q = f"Sentence: {sentence}\nQuestion: {question}\nAnswer briefly (single token or short phrase)."
    try:
        res = prov.fetch_facts(q, hints=["winograd", "coreference"])
    except Exception as e:
        return {"ok": False, "error": f"fetch_failed: {e}"}

    if not res.get("ok"):
        return {"ok": False, "error": res.get("error")}

    return {"ok": True, "answer": res.get("answer"), "facts": res.get("facts", [])}


def evaluate(use_live: bool, model: str | None = None) -> Dict[str, Any]:
    results: List[Dict[str, Any]] = []
    correct = 0
    for ex in winograd_examples:
        sent = ex["الجملة"]
        q = ex["السؤال"]
        gold = ex["الإجابة_الصحيحة"]
        system_answer = None
        provider_info = None
        if use_live:
            prov = ask_provider(sent, q, model=model)
            provider_info = prov
            if prov.get("ok"):
                system_answer = prov.get("answer")
        if system_answer is None:
            # fallback: very small lexical heuristic
            system_answer = heuristic_answer(sent, q)
        norm_sys = normalize(system_answer)
        norm_gold = normalize(gold)
        # accept if gold substring appears in system answer or equality
        correct_flag = (norm_gold in norm_sys) or (norm_sys in norm_gold)
        if correct_flag:
            correct += 1
        results.append({
            "الجملة": sent,
            "السؤال": q,
            "الإجابة_النظام": system_answer,
            "الإجابة_الصحيحة": gold,
            "صحيح": bool(correct_flag),
            "provider_info": provider_info,
        })
    accuracy = 100.0 * correct / len(winograd_examples)
    return {"results": results, "accuracy": accuracy, "count": len(winograd_examples)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--live', action='store_true', help='Use live ExternalInfoProvider')
    parser.add_argument('--model', type=str, default=None, help='Optional model name override')
    args = parser.parse_args()

    Path('artifacts/reports').mkdir(parents=True, exist_ok=True)
    use_live = args.live or os.getenv('AGL_EXTERNAL_INFO_ENABLED', '0') == '1'

    print('Running Winograd Schema test (count =', len(winograd_examples), ')')
    if use_live:
        print('[info] Running in live mode (will call ExternalInfoProvider)')
    else:
        print('[info] Running in heuristic (offline) mode')

    summary = evaluate(use_live=use_live, model=args.model)

    # write JSON report
    outp = Path('artifacts/reports/winograd_results.json')
    with outp.open('w', encoding='utf-8') as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)

    print('\nPer-example results:')
    for r in summary['results']:
        print('-' * 60)
        print('الجملة:', r['الجملة'])
        print('السؤال:', r['السؤال'])
        print('إجابة النظام:', r['الإجابة_النظام'])
        print('الإجابة الصحيحة:', r['الإجابة_الصحيحة'])
        print('صحيح؟', r['صحيح'])
        if r['provider_info']:
            print('مزود: ', r['provider_info'].get('answer'), r['provider_info'].get('error'))

    print('\nالملخص:')
    print(' - عدد الأمثلة:', summary['count'])
    print(f" - الدقّة: {summary['accuracy']:.1f}%")
    print('\nتفصيل محفوظ في:', str(outp))
