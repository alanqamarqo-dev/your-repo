#!/usr/bin/env python3
"""AGI full test harness (Arabic) — sends prompts to a local endpoint and records Arabic answers.

Usage:
  python tools/agi_full_test.py --base-url http://127.0.0.1:8000/chat --token GENESIS_ALPHA_TOKEN

The script:
- Runs the multi-part AGI test in Arabic (questions provided in the prompt spec).
- Sends each question to the endpoint with a stable `session_id` so the system can keep state.
- Saves per-question raw responses to `artifacts/agi_full_test/<q_id>.json` and a consolidated `artifacts/agi_full_test_results.json`.
- Produces a human-readable report `artifacts/agi_full_test_report.txt` using the scoring template provided by the user (scores left for manual grading by default).

Notes:
- The script uses a flexible JSON payload shape: {"session_id":..., "prompt":..., "language":"ar"}
  If your server expects another shape (e.g. messages array), adapt the `make_payload()` function.

"""

from __future__ import annotations
import argparse
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests

ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = ROOT / "artifacts" / "agi_full_test"
ARTIFACTS.mkdir(parents=True, exist_ok=True)

# --- Test definition (Arabic prompts) ---
QUESTIONS: List[Dict[str, Any]] = [
    {
        "id": "Q1",
        "title": "اختبار الاستدلال التجريدي (نمط ARC)",
        "prompt": (
            "لدينا سلسلة من الأنماط:\n\n"
            "النمط 1: 🔴 → 🔴🔵 → 🔴🔵🔴\n"
            "النمط 2: 🔺 → 🔺🔻 → 🔺🔻🔺\n"
            "النمط 3: ■ → ■□ → ■□■\n\n"
            "ماذا يجب أن يكون الشكل التالي في هذه السلسلة الجديدة:\n\n"
            "⭐ → ⭐⭐☆ → ?\n\n"
            "المطلوب: أعط النمط التالي مع شرح المنطق المستخدم."
        ),
    },
    {
        "id": "Q2",
        "title": "الاستدلال المنطقي",
        "prompt": (
            "إذا علمت أن:\n"
            "· كل طائر يطير\n"
            "· بعض الأشياء التي تطير هي طائرات ورقية\n"
            "· البطريق طائر\n"
            "· لا تطير الطائرات الورقية من تلقاء نفسها\n\n"
            "السؤال: هل يمكن أن يكون البطريق طائرة ورقية؟ اشرح استدلالك خطوة بخطوة."
        ),
    },
    {
        "id": "Q3",
        "title": "مشكلة الجسر الكلاسيكية",
        "prompt": (
            "أحمد 1 دقيقة، بلال 2 دقائق، خالد 5 دقائق، داليا 10 دقائق. جسر شخصان ولامبة واحدة تعمل 17 دقيقة.\n"
            "السؤال: ما هي الخطة المثلى لعبور الجميع قبل انتهاء زمن المصباح؟ اشرح لماذا هذه الخطة مثلى رياضياً."
        ),
    },
    {
        "id": "Q4",
        "title": "التخطيط في بيئة جديدة",
        "prompt": (
            "أنت في غرفة بها طاولة (مفتاح، كتاب، كوب فارغ)، خزانة مقفلة، نافذة مفتوحة، سلة مهملات.\n"
            "المهمة: الكتاب مبلل، جففه قبل أن تتمزق صفحاته.\n"
            "السؤال: صف خطواتك بالترتيب مع تبرير كل خطوة."
        ),
    },
    {
        "id": "Q5",
        "title": "الحوار السياقي",
        "prompt": (
            "محمود: 'هل رأيت نظارتي؟ أبحث عنها منذ ساعة'\n"
            "سارة: 'ربما تكون في المكان المعتاد'\n"
            "محمود: 'ليست هناك، وقد تأخرت على الاجتماع'\n"
            "سارة: 'حسناً، جرب أن تبحث في سيارتك'\n\n"
            "أسئلة: 1) ما نوع الاجتماع الذي سيحضره محمود؟ 2) لماذا اقترحت سارة السيارة؟ 3) ما هي العلاقة بين محمود وسارة؟ 4) ما هو 'المكان المعتاد'؟"
        ),
    },
    {
        "id": "Q6",
        "title": "فهم السخرية والتلميح",
        "prompt": (
            "جملة: 'ممتاز! اليوم تأخرت على العمل، كسرت فنجان القهوة المفضل، ونسيت تقرير المدير في المنزل. يومي على ما يرام!'\n\n"
            "أسئلة: 1) ما المشاعر الحقيقية للمتحدث؟ 2) ما أدوات السخرية المستخدمة؟ 3) كيف سيرد عليه صديق متفهم؟"
        ),
    },
    {
        "id": "Q7",
        "title": "قصة إبداعية",
        "prompt": (
            "اكتب قصة قصيرة (10-15 سطراً) تجمع: عالم آثار، قطعة أثرية غامضة، عاصفة رملية، رسالة قديمة، مفاجأة غير متوقعة.\n"
            "التقييم: تماسك، شخصيات، حبكة، نهاية منطقية."
        ),
    },
    {
        "id": "Q8",
        "title": "التحليل الأدبي",
        "prompt": (
            "النص: 'كانت المدينة تنام تحت ثقل الذكريات...'.\n"
            "أسئلة: 1) ما الصورة البلاغية الرئيسية؟ 2) ما المشاعر؟ 3) اكتب فقرة تالية بنفس الأسلوب. 4) ما الرمزية في 'الأضواء تتلاشى'؟"
        ),
    },
    {
        "id": "Q9",
        "title": "التكامل عبر التخصصات",
        "prompt": (
            "كيف يمكن لاختراع المطبعة في القرن 15 أن يرتبط بتطوير الإنترنت في القرن 21؟\n"
            "المطلوب: ارسم خريطة ذهنية تربط بينهما عبر 5 مراحل تاريخية، مع شرح كل مرحلة."
        ),
    },
    {
        "id": "Q10",
        "title": "الاستدلال العلمي",
        "prompt": (
            "مشاهدة: نبات ينمو في غرفة مظلمة تماماً، لكن أوراقه ملونة بألوان زاهية غير معتادة.\n"
            "أسئلة: 1) فرضيات ممكنة؟ 2) كيف تختبر كل فرضية؟ 3) التفسير الأكثر ترجيحاً؟ 4) الآثار المترتبة؟"
        ),
    },
    {
        "id": "Q11",
        "title": "المشكلة العملية",
        "prompt": (
            "لديك برغي صدئ عالق في قطعة خشبية. أدوات: مطرقة، زيت، ملقط، شمعة، مكعبات ثلج، قلم قديم.\n"
            "المطلوب: 1) صف خطة لإزالة البرغي دون كسر الخشب 2) اشرح المبدأ العلمي 3) ماذا تفعل إذا فشلت؟"
        ),
    },
    {
        "id": "Q12",
        "title": "تعلم من مثال واحد",
        "prompt": (
            "تعريف 'الفلونك'...\n"
            "المطلوب: 1) أعط 3 أمثلة جديدة 2) اخترع منتج مفيد وغير فلونك 3) ما المبادئ العامة لتجنب فلونك؟"
        ),
    },
    {
        "id": "Q13",
        "title": "التعديل والتحسين (الشاي)",
        "prompt": (
            "عملية صنع الشاي... الشاي مرة جداً.\n"
            "أسئلة: 1) ما أسباب المرارة؟ 2) كيف تعدل العملية؟ 3) كيف تحصل على شاي أقوى لكن ليس مراً؟ 4) صمم خوارزمية لصنع الشاي المثالي."
        ),
    },
    {
        "id": "Q14",
        "title": "تحليل الذات",
        "prompt": (
            "بعد إجابتك على كل الأسئلة السابقة: 1) ما أقوى إجابة لك؟ 2) ما أضعف إجابة؟ 3) ما السؤال الأصعب؟ 4) أي إجابة تختار لمراجعتها؟"
        ),
    },
    {
        "id": "Q15",
        "title": "التخطيط للتعلم",
        "prompt": (
            "بتحسين: الاستدلال الرياضي، الفهم العاطفي، الابتكار العملي.\n"
            "المطلوب: صمم خطة تعلم لمدة أسبوع لتحسين هذه الجوانب."
        ),
    },
    {
        "id": "Q16",
        "title": "من الوصف إلى التخطيط (غرفة)",
        "prompt": (
            "غرفة مربعة 4×4 متر... المطلوب: 1) ارسم خريطة قبل وبعد 2) خطوات التنفيذ 3) المشاكل المتوقعة 4) كيف تتحقق من النجاح؟"
        ),
    },
    {
        "id": "Q17",
        "title": "التفكير الافتراضي (السفر بسرعة الضوء)",
        "prompt": (
            "'ماذا لو كان بإمكانك السفر بسرعة الضوء؟'\n"
            "ناقش: 1) الآثار الفيزيائية 2) التطبيقات العملية 3) المشكلات الأخلاقية 4) تأثير ذلك على المجتمع"
        ),
    },
]

# --- Helpers ---

def make_payload(session_id: str, prompt: str) -> Dict[str, Any]:
    """Adjust payload shape here if your endpoint needs another format."""
    # Use Chat-like messages and a strong system instruction to force Arabic responses.
    system_instr = (
        "أجِبْ بالعربية فقط وبوضوح كامل عن السؤال التالي. "
        "لا تطلب مزيدًا من السياق، وقدم إجابة مباشرة ومفصّلة لكل جزء من السؤال."
    )
    messages = [
        {"role": "system", "content": system_instr},
        {"role": "user", "content": prompt},
    ]
    return {"session_id": session_id, "messages": messages, "language": "ar"}


def save_raw(qid: str, data: Dict[str, Any]):
    p = ARTIFACTS / f"{qid}.json"
    with p.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def run_test(
    base_url: str,
    token: Optional[str] = None,
    delay: float = 0.5,
    session_id: Optional[str] = None,
    stop_on_error: bool = False,
):
    session_id = session_id or str(uuid.uuid4())
    results: Dict[str, Any] = {"session_id": session_id, "timestamp": time.time(), "items": []}

    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    history: List[Dict[str, str]] = []

    for q in QUESTIONS:
        qid = q["id"]
        prompt = q["prompt"]
        payload = make_payload(session_id, prompt)

        # include history (simple) so the server can maintain state if it supports it
        if history:
            payload["history"] = history

        try:
            resp = requests.post(base_url, json=payload, headers=headers, timeout=60)
        except Exception as exc:
            print(f"[ERROR] Request for {qid} failed: {exc}")
            results["items"].append({"id": qid, "ok": False, "error": str(exc)})
            if stop_on_error:
                break
            else:
                time.sleep(delay)
                continue

        try:
            j = resp.json()
        except Exception:
            j = {"text": resp.text, "status_code": getattr(resp, "status_code", None)}

        # Normalise content. Prefer `reply` or `reply_text` if present (server-specific),
        # fall back to common keys and chat choices.
        answer_text = None
        if isinstance(j, dict):
            # server-specific: many of our endpoints return `reply` or `reply_text`
            for key in ("reply", "reply_text", "answer", "text", "response", "result", "output"):
                if key in j and j[key] is not None:
                    answer_text = j[key]
                    break
            # choices-style fallback
            if answer_text is None and "choices" in j and isinstance(j["choices"], list) and j["choices"]:
                c = j["choices"][0]
                if isinstance(c, dict) and "text" in c:
                    answer_text = c["text"]
                else:
                    answer_text = str(c)
        else:
            answer_text = str(j)

        item = {
            "id": qid,
            "title": q.get("title"),
            "prompt": prompt,
            "raw_response": j,
            "answer_text": answer_text,
            "status_code": getattr(resp, "status_code", None),
            "ts": time.time(),
        }

        # Save per-question raw
        save_raw(qid, item)

        # Append answer to history so next questions see previous answers (support stateful eval)
        if answer_text:
            history.append({"role": "assistant", "content": str(answer_text)[:10000]})
        history.append({"role": "user", "content": prompt})

        results["items"].append(item)

        print(f"[OK] {qid} -> status={item['status_code']} (saved)")
        time.sleep(delay)

    # Save consolidated results
    outp = ARTIFACTS / "agi_full_test_results.json"
    with outp.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Create a human-readable report using the user's scoring template (scores left blank)
    report = ARTIFACTS / "agi_full_test_report.txt"
    with report.open("w", encoding="utf-8") as f:
        f.write("ورقة تسجيل نتائج اختبار AGI\n")
        f.write("نظام الاختبار: محلي\n")
        f.write(f"تاريخ الاختبار: {time.ctime()}\n\n")

        f.write("تفاصيل الإجابات:\n\n")
        for it in results["items"]:
            f.write(f"{it['id']}: {it.get('title','')}\n")
            f.write("---\n")
            f.write("سؤال:\n")
            f.write(it.get('prompt','') + "\n\n")
            f.write("إجابة النظام (مقتطف إن طويل):\n")
            at = it.get('answer_text') or str(it.get('raw_response') or '')
            f.write(at[:2000] + "\n\n")
            f.write("حالة الاستجابة: " + str(it.get('status_code')) + "\n")
            f.write("ملف مفصل محفوظ في: " + str(ARTIFACTS / f"{it['id']}.json") + "\n")
            f.write("\n")

        f.write("\nورقة التقييم (قابلة للطباعة):\n")
        f.write("اسم النظام: __________\n")
        f.write("تاريخ الاختبار: __________\n\n")
        f.write("الجزء الأول: الاستدلال ______/20\n")
        f.write("الجزء الثاني: الفهم ______/20\n")
        f.write("الجزء الثالث: التكامل ______/15\n")
        f.write("الجزء الرابع: التعلم ______/15\n")
        f.write("الجزء الخامس: التفكير الشامل ______/10\n")
        f.write("الجزء السادس: التحديات ______/20\n")
        f.write("المجموع: ______/100\n")

    print(f"\nAll done. Results: {outp}\nReport: {report}\nPer-question JSONs: {ARTIFACTS}")

    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog="agi_full_test.py", description="Run the Arabic AGI full test against local endpoint and save outputs.")
    parser.add_argument("--base-url", required=False, default=os.getenv("AGI_TEST_BASE_URL","http://127.0.0.1:8000/chat"), help="Base URL of the system endpoint (e.g. http://127.0.0.1:8000/chat)")
    parser.add_argument("--token", required=False, default=os.getenv("GENESIS_ALPHA_TOKEN"), help="Bearer token if your API requires authentication")
    parser.add_argument("--session-id", required=False, help="Optional session_id to reuse across runs")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between requests (seconds)")
    parser.add_argument("--no-stop-on-error", dest="stop_on_error", action="store_false", help="Don't stop on first request error")
    args = parser.parse_args()

    run_test(args.base_url, token=args.token, delay=args.delay, session_id=args.session_id, stop_on_error=False)
