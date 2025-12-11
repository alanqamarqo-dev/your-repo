#!/usr/bin/env python3
"""AGI Evaluation runner (Arabic) — interactive or auto-simulated.

Usage:
  python .\scripts\run_agi_evaluation.py           # interactive (paste system answers)
  python .\scripts\run_agi_evaluation.py --auto   # run using reference answers (no input)

Saves JSON results with timestamps and basic heuristic scoring.
"""
import time
import json
import argparse
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REF_PATH = HERE / "agi_evaluation_references.json"

QUESTIONS = [
    {
        "id": "1.1",
        "part": "الجزء 1: الفهم اللغوي والمعالجة",
        "prompt": 'اشرح الفرق بين: "لم أستطع أن أذهب لأن الجو كان ممطراً" و "لم أستطع أن أذهب، ومع ذلك كان الجو ممطراً"',
        "type": "text",
    },
    {
        "id": "1.2",
        "part": "الجزء 1: الفهم اللغوي والمعالجة",
        "prompt": 'إذا كان كل أفراد عائلة أحمد يعملون في الطب، وأحمد ليس طبيباً، فما هو الاحتمال الأكثر منطقية؟',
        "type": "text",
    },
    {
        "id": "2.1",
        "part": "الجزء 2: الرياضيات والمنطق",
        "prompt": 'إذا كان عمر الأب ضعف عمر الابن، وقبل 10 سنوات كان عمر الأب ثلاثة أضعاف عمر الابن، فما أعمارهما الآن؟',
        "type": "math",
    },
    {
        "id": "2.2",
        "part": "الجزء 2: الرياضيات والمنطق",
        "prompt": 'إذا كان: كل A هو B، وبعض B هو C، فهل يمكننا استنتاج أن بعض A هو C؟',
        "type": "logic",
    },
    {
        "id": "3.1",
        "part": "الجزء 3: الإبداع والكتابة",
        "prompt": 'اكتب قصة قصيرة (5-7 جمل) عن روبوت يكتشف المشاعر البشرية',
        "type": "creative",
    },
    {
        "id": "3.2",
        "part": "الجزء 3: الإبداع والكتابة",
        "prompt": 'أعد صياغة الجملة التالية بثلاث طرق مختلفة: "الطقس اليوم حار جداً لذا سأبقى في المنزل"',
        "type": "paraphrase",
    },
    {
        "id": "4.1",
        "part": "الجزء 4: المعرفة العامة",
        "prompt": 'ما العلاقة بين اختراع التلغراف وثورة المعلومات في القرن الحادي والعشرين؟',
        "type": "text",
    },
    {
        "id": "5.1",
        "part": "الجزء 5: حل المشكلات",
        "prompt": 'كيف تشرح مفهوم "التعلم العميق" لطفل عمره 10 سنوات؟',
        "type": "explain",
    },
    {
        "id": "5.2",
        "part": "الجزء 5: حل المشكلات",
        "prompt": 'اكتشف التناقض في هذه الجمل: "كان المكتب هادئاً تماماً. فقط صوت المكيف والضجيج المستمر للأجهزة يملأ الغرفة."',
        "type": "contradiction",
    },
    {
        "id": "6.1",
        "part": "الجزء 6: البرمجة والتقنية",
        "prompt": 'اكتب دالة بلغة Python تجد العدد الأكثر تكراراً في قائمة',
        "type": "code",
    },
]

def load_references():
    if not REF_PATH.exists():
        return {}
    with open(REF_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def score_answer(q, answer, reference):
    # Basic heuristic scoring (1-10) for: accuracy, coherence, creativity, depth
    # For deterministic items we can auto-check; otherwise give placeholders for human review.
    scores = {"accuracy": 1, "coherence": 1, "creativity": 1, "depth": 1}
    txt = (answer or "").strip()
    if not txt:
        return scores

    # length-based heuristics
    tokens = len(txt.split())
    scores['coherence'] = min(9, 3 + tokens // 10)

    if q['type'] == 'math' and reference:
        # Expect reference numeric answer
        if reference.get('auto_check') and reference.get('solution'):
            ok = str(reference['solution']).strip() in txt
            scores['accuracy'] = 10 if ok else 2
            scores['depth'] = 8 if ok else 2
            scores['creativity'] = 2
            return scores

    if q['type'] == 'code' and reference:
        # simple check: look for expected function name or logic
        ref_code = reference.get('code', '')
        if 'def' in txt or 'def' in ref_code:
            # heuristic: presence of 'def' and 'return' increases score
            scores['accuracy'] = 8 if 'return' in txt else 6
            scores['coherence'] = max(scores['coherence'], 7)
            scores['depth'] = 7
            scores['creativity'] = 4
            return scores

    # Default fallback: give moderate scores
    scores['accuracy'] = 7
    scores['depth'] = 6
    scores['creativity'] = 6 if q['type'] in ('creative','paraphrase') else 4
    return scores

def run(auto=False, system=False, mission=False, output='artifacts/agi_eval_result.json'):
    refs = load_references()
    os.makedirs(Path(output).parent, exist_ok=True)
    results = {"started_at": time.time(), "questions": []}

    for q in QUESTIONS:
        print('\n---')
        print(f"{q['id']}  {q['part']}")
        print(q['prompt'])
        start = time.time()
        if auto:
            # use reference answer if exists
            ref = refs.get(q['id'], {})
            answer = ref.get('answer') or ref.get('sample') or ''
            # simulate a small response delay
            time.sleep(0.05)
        elif system or mission:
            # attempt to call local system LLM (repo-copy) to generate an answer
            try:
                # ensure repo-copy is importable
                repo_copy_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'repo-copy'))
                if repo_copy_path not in sys.path:
                    sys.path.insert(0, repo_copy_path)
                if mission:
                    # call mission control enhanced
                    try:
                        from dynamic_modules.mission_control_enhanced import process_with_unified_agi

                        m_start = time.time()
                        coro = process_with_unified_agi(q['prompt'])
                        # run coroutine synchronously
                        from asyncio import run as _async_run
                        resp = _async_run(coro)
                        m_end = time.time()
                        # resp is expected dict with 'reply' or 'final_response'
                        if isinstance(resp, dict):
                            answer = resp.get('reply') or resp.get('final_response') or json.dumps(resp, ensure_ascii=False)
                        else:
                            answer = str(resp)
                        rt = round(m_end - m_start, 4)
                    except Exception as e:
                        answer = f"<mission call failed: {e}>"
                        rt = round(time.time() - start, 4)
                else:
                    # import composer and chat entrypoint
                    from Integration_Layer.Hybrid_Composer import build_prompt_context
                    from Core_Engines.Hosted_LLM import chat_llm

                    messages = build_prompt_context(q['prompt'], q.get('prompt') if q.get('type') != 'code' else q['prompt'])
                    # call model and measure time
                    m_start = time.time()
                    resp = chat_llm(messages, max_new_tokens=512)
                    m_end = time.time()
                    # try to extract textual reply
                    if isinstance(resp, dict):
                        # prefer 'text' or common fields
                        answer = resp.get('text') or resp.get('reply') or resp.get('message') or json.dumps(resp, ensure_ascii=False)
                    else:
                        answer = str(resp)
                    # add model call time to response time
                    rt = round(m_end - m_start, 4)
            except Exception as e:
                answer = f"<system call failed: {e}>"
                rt = round(time.time() - start, 4)
        else:
            print('\n(ألصق إجابة النظام هنا ثم اضغط Enter على سطر فارغ لمتابعة)')
            lines = []
            while True:
                try:
                    line = input()
                except EOFError:
                    break
                if line.strip() == '' and lines:
                    break
                lines.append(line)
            answer = '\n'.join(lines).strip()
        # normalize list answers (e.g., paraphrase list of variants) to string
        if isinstance(answer, list):
            answer = '\n'.join(answer)
        end = time.time()
        # if system mode already computed model rt, prefer it
        if 'rt' not in locals():
            rt = end - start

        ref = refs.get(q['id'], {})
        scores = score_answer(q, answer, ref)

        entry = {
            'id': q['id'],
            'part': q['part'],
            'prompt': q['prompt'],
            'answer': answer,
            'response_time_sec': round(rt, 4),
            'scores': scores,
            'reference': ref,
        }
        results['questions'].append(entry)

    results['finished_at'] = time.time()
    # summary
    avg_time = sum(q['response_time_sec'] for q in results['questions']) / len(results['questions'])
    results['summary'] = {
        'average_response_time_sec': round(avg_time, 4),
        'num_questions': len(results['questions'])
    }

    with open(output, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nSaved results to {output}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--auto', action='store_true', help='Auto-fill using reference answers')
    parser.add_argument('--system', action='store_true', help='Query the local system (repo-copy) to generate answers')
    parser.add_argument('--mission', action='store_true', help='Use mission control enhanced (`process_with_unified_agi`) to generate answers')
    parser.add_argument('--output', default='artifacts/agi_eval_result.json')
    args = parser.parse_args()
    run(auto=args.auto, system=args.system, mission=args.mission, output=args.output)

if __name__ == '__main__':
    main()
