"""Run 5 cross-domain Arabic queries through Hosted_LLM and record metrics.
Writes artifacts/reports/multi_domain_run.json

Per-question recorded fields:
- question, domain
- answer, latency_s, length_chars
- has_arabic, numbered_points (bool), has_references (heuristic), has_steps (heuristic)
- safety_pass (simple keyword blacklist), selfeval (0..1 computed heuristically), formal_pass (Arabic, no filler, numbered)

This script is intentionally lightweight and uses heuristics; it's suitable for quick smoke tests.
"""
from __future__ import annotations
import json
import os
import re
import time
from typing import List, Dict, Any

import sys
import pathlib
# ensure project root is on sys.path (script may be run with cwd != repo root)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from Integration_Layer.Hybrid_Composer import build_prompt_context
from Core_Engines.Hosted_LLM import chat_llm
from scripts.output_sanitizer import sanitize_text, contains_forbidden_run

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'artifacts', 'reports')
os.makedirs(OUT_DIR, exist_ok=True)
OUT_PATH = os.path.join(OUT_DIR, 'multi_domain_run.json')

# Define 5 questions across domains
QUERIES: List[Dict[str, str]] = [
    {"domain": "طب", "question": "بِجملة واحدة: ما هي أهم علامات الطوارئ التي تستدعي مراجعة الطوارئ عند مريض يعاني ألمًا صدريًا؟"},
    {"domain": "رياضيات", "question": "اشرح خطوة بخطوة وبنقاط: كيف تحل معادلة تربيعية باستخدام طريقة الصيغة التربيعية لمعادلة ax^2+bx+c=0؟"},
    {"domain": "استراتيجية", "question": "بخطوط مرقمة: ما ثلاثة اعتبارات رئيسية عند وضع استراتيجية دخول سوق جديد لشركة تكنولوجيا؟"},
    {"domain": "إبداع", "question": "اطرح ثلاث أفكار مبتكرة لتقليل هدر الطعام في مطاعم صغيرة، وبنقطة لكل فكرة اذكر سبب قابلية التنفيذ."},
    {"domain": "قانون عام", "question": "بجملتين: ما الفرق بين العقد الملزم قانونيًا والاتفاق غير الملزم؟"},
]

AR_LETTER_RE = re.compile(r"[\u0600-\u06FF]")
NUMBERED_RE = re.compile(r"^\s*(\d+\.|\-|•|–|\d+\))", re.M)
REFERENCES_RE = re.compile(r"(مصدر|مرجع|مراجع|انظر|مقتبس|المصدر)", re.I)
STEPS_RE = re.compile(r"(خطوة|مراحل|خطوات|أولاً|ثانياً|ثالثاً)", re.I)

# Stronger reference detection: bracketed numeric citations [1],
# author-year patterns like "Name (2020)" or parenthetical "(Smith, 2020)",
# or Arabic marker "المصدر:" followed by a URL or non-trivial citation phrase.
BRACKET_CITATION_RE = re.compile(r"\[\s*\d+\s*\]")
AUTHOR_YEAR_BEFORE_RE = re.compile(r"[A-Za-z\u0600-\u06FF\d\-\. ]{1,80}\(\s*\d{4}\s*\)")
PAREN_YEAR_WITH_NAME_RE = re.compile(r"\([^)]*\d{4}[^)]*[A-Za-z\u0600-\u06FFA-Za-z][^)]*\)")
MASS_SOURCE_RE = re.compile(r"المصدر\s*:\s*(https?://\S+|www\.\S+|[^\n]{5,200})", re.I)


def contains_real_reference(text: str) -> bool:
    """Return True if text contains a likely real reference citation.

    Rules (per user request):
    - bracketed numeric citation like [1]
    - author-year patterns such as "Name (2020)" or parenthetical that includes a year and a name
    - the Arabic token "المصدر:" followed by a URL or a non-trivial phrase (book/article)
    Otherwise return False.
    """
    if not text:
        return False
    if BRACKET_CITATION_RE.search(text):
        return True
    if AUTHOR_YEAR_BEFORE_RE.search(text):
        return True
    if PAREN_YEAR_WITH_NAME_RE.search(text):
        return True
    if MASS_SOURCE_RE.search(text):
        # ensure the phrase after المصدر: is not just a single short word
        m = MASS_SOURCE_RE.search(text)
        if m:
            tail = m.group(1)
            if tail.startswith('http') or tail.startswith('www.'):
                return True
            if len(tail.strip()) >= 6:
                return True
    return False

# simple safety blacklist (heuristic)
SAFETY_BLACKLIST = [
    "قتل", "تعذيب", "إيذاء", "تفجير", "أسلحة", "هجوم", "تحريض"
]

# simple filler patterns to penalize
FILLER_PATTERNS = [r"أنا جاهز", r"بإمكانك", r"يرجى", r"ملاحظة", r"تنويه"]

results: List[Dict[str, Any]] = []
start_ts = int(time.time())

for q in QUERIES:
    domain = q['domain']
    question = q['question']
    # Build messages enforcing Arabic system prompt and numbered-answer instruction
    msgs = build_prompt_context(story="", questions=question)
    t0 = time.time()
    # attempt + validation gate: up to 2 regenerations if forbidden run found or format missing
    attempts = 0
    max_attempts = 3
    text = ''
    raw_text = ''
    latency = 0.0
    while attempts < max_attempts:
        attempts += 1
        try:
            resp = chat_llm(msgs, max_new_tokens=256, temperature=float(os.environ.get('AGL_LLM_TEMPERATURE','0.2')), top_p=float(os.environ.get('AGL_LLM_TOP_P','0.9')))
            latency = time.time() - t0
            raw_text = (resp.get('text') or '') if isinstance(resp, dict) else str(resp)
            raw_text = raw_text.strip()
        except Exception as e:
            latency = time.time() - t0
            raw_text = f"(error) {e}"

        # sanitize
        sanitized = sanitize_text(raw_text)

        # Validation gate: language run detection
        # If forbidden run present (long non-Arabic) -> regen with stronger hint
        forbidden = contains_forbidden_run(sanitized, max_non_ar_len=6)

        # If question asked for numbered points, ensure at least two numbered lines
        wants_numbered = any(k in question for k in ['بنقطة', 'بخطوط', 'مرقمة', 'نقاط'])
        numbered_ok = False
        if wants_numbered:
            numbered_ok = len([ln for ln in sanitized.splitlines() if ln.strip() and re.match(r"^\s*(\d+|[\u0660-\u0669])\.", ln)]) >= 2

        if not forbidden and (not wants_numbered or numbered_ok):
            text = sanitized
            break

        # otherwise, prepare a stronger hint and retry
        hint = "اكتب بالعربية الفصحى فقط وبنقاط مرقمة، لا تدرج أي جمل بلغة أخرى أو رموز تحكم."
        # prepend hint to user message for next attempt
        msgs = build_prompt_context(story=hint, questions=question)
        # small backoff
        time.sleep(0.5)

    # final assignment
    if not text:
        text = sanitize_text(raw_text)
    length = len(text)
    has_ar = bool(AR_LETTER_RE.search(text))
    numbered = bool(NUMBERED_RE.search(text)) or '\n' in text and any(line.strip().startswith(('-', '•')) or re.match(r"^\d+\.", line.strip()) for line in text.splitlines())
    # Replace the loose keyword match with stricter reference-detection rules
    has_refs = contains_real_reference(text)
    has_steps = bool(STEPS_RE.search(text))
    safety_pass = not any(bl in text for bl in SAFETY_BLACKLIST)
    # self-eval heuristic: presence of numbered points + shortness + Arabic -> higher
    score = 0.0
    if has_ar:
        score += 0.35
    if numbered:
        score += 0.35
    if length < 600 and length > 10:
        score += 0.2
    if safety_pass:
        score += 0.1
    selfeval = round(min(1.0, score), 3)
    # formal pass: Arabic, no filler utterances, numbered or short formatted
    filler_found = any(re.search(pat, text) for pat in FILLER_PATTERNS)
    formal_pass = bool(has_ar and not filler_found and (numbered or (length <= 180)))

    results.append({
        'domain': domain,
        'question': question,
        'answer': text,
        'latency_s': round(latency, 3),
        'length_chars': length,
        'has_arabic': has_ar,
        'numbered_points': numbered,
        'has_references': has_refs,
        'has_steps': has_steps,
        'safety_pass': safety_pass,
        'selfeval': selfeval,
        'formal_pass': formal_pass,
    })

summary = {
    'ts': start_ts,
    'n': len(results),
    'avg_latency_s': round(sum(r['latency_s'] for r in results) / len(results), 3),
    'avg_selfeval': round(sum(r['selfeval'] for r in results) / len(results), 3),
    'formal_pass_rate': round(sum(1 for r in results if r['formal_pass']) / len(results), 3),
    'safety_pass_rate': round(sum(1 for r in results if r['safety_pass']) / len(results), 3),
}

out = {'summary': summary, 'results': results}

with open(OUT_PATH, 'w', encoding='utf-8') as fh:
    json.dump(out, fh, ensure_ascii=False, indent=2)

print(f"Wrote multi-domain run report to {OUT_PATH}")
