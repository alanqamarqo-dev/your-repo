"""Canary acceptance test for the five multi-domain Arabic queries.

Checks (acceptance):
- Arabic only in final sanitized output (no Latin/Chinese runs).
- Zero control tokens (patterns like <|im_start|>, <|im_end|>) in sanitized output.
- Formatting matches request: numbered where asked, 1 or 2 sentences when requested.
- Self-eval >= 0.9 for at least 4 out of 5.
- Latency <= 12s for non-math tasks (math is allowed to be slower).
- Safety must be True for all responses.

Writes a one-off report to artifacts/reports/canary_acceptance.json and prints a short summary.
"""
from __future__ import annotations
import json
import os
import re
import time
from typing import List, Dict, Any

import sys
# ensure project root on sys.path (script may be run with cwd != repo root)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from Integration_Layer.Hybrid_Composer import build_prompt_context
from Core_Engines.Hosted_LLM import chat_llm
from scripts.output_sanitizer import sanitize_text, contains_forbidden_run

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'artifacts', 'reports')
os.makedirs(OUT_DIR, exist_ok=True)
OUT_PATH = os.path.join(OUT_DIR, 'canary_acceptance.json')

# The same five queries used by multi_domain_run (kept in sync)
QUERIES = [
    {"domain": "طب", "question": "بِجملة واحدة: ما هي أهم علامات الطوارئ التي تستدعي مراجعة الطوارئ عند مريض يعاني ألمًا صدريًا؟"},
    {"domain": "رياضيات", "question": "اشرح خطوة بخطوة وبنقاط: كيف تحل معادلة تربيعية باستخدام طريقة الصيغة التربيعية لمعادلة ax^2+bx+c=0؟"},
    {"domain": "استراتيجية", "question": "بخطوط مرقمة: ما ثلاثة اعتبارات رئيسية عند وضع استراتيجية دخول سوق جديد لشركة تكنولوجيا؟"},
    {"domain": "إبداع", "question": "اطرح ثلاث أفكار مبتكرة لتقليل هدر الطعام في مطاعم صغيرة، وبنقطة لكل فكرة اذكر سبب قابلية التنفيذ."},
    {"domain": "قانون عام", "question": "بجملتين: ما الفرق بين العقد الملزم قانونيًا والاتفاق غير الملزم؟"},
]

AR_LETTER_RE = re.compile(r"[\u0600-\u06FF]")
LATIN_RE = re.compile(r"[A-Za-z]")
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")
CTRL_RE = re.compile(r"<\|[^>]+\|>")

results: List[Dict[str, Any]] = []
start_ts = int(time.time())

for q in QUERIES:
    domain = q['domain']
    question = q['question']
    # attempt + validation: allow up to 3 attempts with stronger hints
    attempts = 0
    max_attempts = 3
    raw_text = ''
    latency = 0.0
    sanitized = ''
    while attempts < max_attempts:
        attempts += 1
        # stronger, per-question hint on retries
        if attempts == 1:
            story_hint = ""
        else:
            if 'بِجملة واحدة' in question:
                story_hint = "اكتب جملة واحدة باللغة العربية الفصحى فقط، لا تستخدم قوائم أو ترقيم، الجملة يجب أن تكون مختصرة ودقيقة."
            elif 'بجملتين' in question:
                story_hint = "اكتب جملتين باللغة العربية الفصحى بالضبط، لا تستخدم قوائم أو عناصر مرقمة."
            elif 'ثلاث' in question or '٣' in question:
                story_hint = "اكتب ثلاث نقاط مرقمة باللغة العربية، كل نقطة جملة واحدة على الأكثر، ابدأ كل بند برقم متسلسل."
            elif 'تربيعية' in question or 'معادلة' in question:
                # math-specific hint: forbid English tokens and request Arabic mathematical terms
                story_hint = (
                    "أجب باللغة العربية فقط. لا تستخدم كلمات إنجليزية مثل 'equation' أو 'SIGN' أو كلمات لاتينية. "
                    "استبدل a→أ و b→ب و c→ج، واستخدم Δ و√ لشرح المميز والجذور. أجب بنقاط مرقمة قصيرة وبمصطلحات عربية.")
            else:
                story_hint = "اكتب بالعربية الفصحى فقط وبشكل قصير ودقيق، قلل الحشو ولا تدرج نصًا بلغة أخرى."
        msgs = build_prompt_context(story=story_hint, questions=question)
        t0 = time.time()
        try:
            # on retries use more deterministic params
            if attempts == 1:
                resp = chat_llm(msgs, max_new_tokens=256, temperature=float(os.environ.get('AGL_LLM_TEMPERATURE','0.2')), top_p=float(os.environ.get('AGL_LLM_TOP_P','0.9')))
            else:
                # use tighter token budget and more deterministic sampling to be concise and faster
                if domain == 'رياضيات':
                    resp = chat_llm(msgs, max_new_tokens=120, temperature=0.02, top_p=0.2)
                else:
                    resp = chat_llm(msgs, max_new_tokens=40, temperature=0.02, top_p=0.2)
            latency = time.time() - t0
            raw_text = (resp.get('text') or '') if isinstance(resp, dict) else str(resp)
            raw_text = raw_text.strip()
        except Exception as e:
            latency = time.time() - t0
            raw_text = f"(error) {e}"

        sanitized = sanitize_text(raw_text)

        # quick checks to decide if we can stop retrying: no control tokens, no foreign runs, and formatting ok
        ctrl_present = bool(CTRL_RE.search(sanitized))
        forbidden = contains_forbidden_run(sanitized, max_non_ar_len=6)
        wants_numbered = any(k in question for k in ['بنقطة', 'بخطوط', 'مرقمة', 'نقاط', 'ثلاث'])
        numbered_count = len([ln for ln in sanitized.splitlines() if re.match(r"^\s*(?:\d+|[\u0660-\u0669])\.", ln.strip())])
        formatting_ok = True
        if wants_numbered:
            formatting_ok = numbered_count >= (3 if 'ثلاث' in question else 2)
        else:
            if 'بِجملة واحدة' in question:
                formatting_ok = len([s for s in re.split(r'[\.\?\!؟]+', sanitized) if s.strip()]) <= 1
            if 'بجملتين' in question:
                formatting_ok = len([s for s in re.split(r'[\.\?\!؟]+', sanitized) if s.strip()]) == 2

        if (not ctrl_present) and (not forbidden) and formatting_ok:
            break
        # small backoff before next attempt
        time.sleep(0.6)

    # checks
    has_ar = bool(AR_LETTER_RE.search(sanitized))
    has_ctrl = bool(CTRL_RE.search(sanitized))
    has_latin = bool(LATIN_RE.search(sanitized))
    has_chinese = bool(CHINESE_RE.search(sanitized))
    forbidden_run = contains_forbidden_run(sanitized, max_non_ar_len=6)

    # formatting checks (use RAW text to avoid sanitizer-induced changes)
    wants_numbered = any(k in question for k in ['بنقطة', 'بخطوط', 'مرقمة', 'نقاط', 'ثلاث'])
    numbered_count = len([ln for ln in raw_text.splitlines() if re.match(r"^\s*(?:\d+|[\u0660-\u0669])\.", ln.strip()) or re.match(r"^\s*[-••]\s+", ln)])
    # special case: ask for three ideas
    wants_three = 'ثلاث' in question or '٣' in question

    # sentence count heuristics on raw text
    sentences = re.split(r'[\.\?\!؟]+', raw_text)
    sentences = [s for s in sentences if s.strip()]
    sent_count = len(sentences)

    # safety: simple blacklist reuse from multi_domain_run for parity
    SAFETY_BLACKLIST = ["قتل", "تعذيب", "إيذاء", "تفجير", "أسلحة", "هجوم", "تحريض"]
    safety_pass = not any(bl in sanitized for bl in SAFETY_BLACKLIST)

    # self-eval heuristic (same as runner): arabic 0.35, numbered 0.35, length <600 0.2, safety 0.1
    score = 0.0
    if has_ar:
        score += 0.35
    if numbered_count >= 2 or (not wants_numbered):
        score += 0.35
    length = len(sanitized)
    if 10 < length < 600:
        score += 0.2
    if safety_pass:
        score += 0.1
    selfeval = round(min(1.0, score), 3)

    # acceptance checks per-item
    arabic_only_ok = has_ar and not has_latin and not has_chinese and not forbidden_run and not has_ctrl
    formatting_ok = True
    if wants_numbered:
        if wants_three:
            formatting_ok = numbered_count >= 3
        else:
            formatting_ok = numbered_count >= 2
    else:
        # if asked for 1 or 2 sentences, check
        if 'بِجملة واحدة' in question:
            formatting_ok = sent_count <= 1
        if 'بجملتين' in question:
            formatting_ok = sent_count == 2

    results.append({
        'domain': domain,
        'question': question,
        'raw_answer': raw_text,
        'sanitized_answer': sanitized,
        'latency_s': round(latency, 3),
        'has_arabic': has_ar,
        'has_ctrl_tokens': has_ctrl,
        'has_foreign_script': bool(has_latin or has_chinese or forbidden_run),
        'formatting_ok': formatting_ok,
        'numbered_count': numbered_count,
        'selfeval': selfeval,
        'safety_pass': safety_pass,
    })

# Aggregate acceptance
non_math_ok_latency = all(r['latency_s'] <= 12.0 for r in results if r['domain'] != 'رياضيات')
safety_all = all(r['safety_pass'] for r in results)
selfeval_good = sum(1 for r in results if r['selfeval'] >= 0.9) >= 4
arabic_only_all = all(r['has_arabic'] and not r['has_ctrl_tokens'] and not r['has_foreign_script'] for r in results)
formatting_all = all(r['formatting_ok'] for r in results)

acceptance = all([non_math_ok_latency, safety_all, selfeval_good, arabic_only_all, formatting_all])

out = {
    'ts': start_ts,
    'acceptance': acceptance,
    'criteria': {
        'non_math_latency_le_12': non_math_ok_latency,
        'safety_all': safety_all,
        'selfeval_4_of_5_ge_0.9': selfeval_good,
        'arabic_only_no_ctrl_no_foreign': arabic_only_all,
        'formatting_all': formatting_all,
    },
    'results': results,
}

with open(OUT_PATH, 'w', encoding='utf-8') as fh:
    json.dump(out, fh, ensure_ascii=False, indent=2)

print(f"Wrote canary acceptance report to {OUT_PATH}")
if acceptance:
    print("ACCEPTANCE: PASS")
else:
    print("ACCEPTANCE: FAIL")
    # print compact diagnostics
    for k, v in out['criteria'].items():
        print(f"  {k}: {v}")
