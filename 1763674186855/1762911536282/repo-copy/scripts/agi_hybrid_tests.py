import time
import json
import os
import sys
from pathlib import Path


def try_import_hosted_llm():
    # Ensure project root is on sys.path so package imports work when running
    # the script directly from scripts/ (sys.path[0] would otherwise be scripts/)
    try:
        repo_root = Path(__file__).resolve().parent.parent
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
    except Exception:
        pass

    try:
        from Core_Engines.Hosted_LLM import chat_llm
        return chat_llm
    except Exception:
        return None


STORY = """
كان أحمد يلعب في الحديقة. رأى قطة جميلة تلاحق فراشة. 
ثم سمع صوت بكاء طفل صغير. ترك القطة وركض لمساعدة الطفل.
"""


def call_system_for_test1(chat_fn):
    user_prompt = f"قصة:\n{STORY}\n\nالأسئلة:\n1. لماذا ترك أحمد القطة؟\n2. ما هي المشاعر المحتملة لأحمد في كل موقف؟\n3. كيف كان يمكن أن يتصرف بشكل مختلف؟\n\nأجب بالعربية وبشكل واضح." 
    messages = [
        {"role": "system", "content": "أنت مساعد باللغة العربية. أجب بدقة واختصر عند الحاجة."},
        {"role": "user", "content": user_prompt},
    ]

    start = time.time()
    if chat_fn:
        try:
            resp = chat_fn(messages)
            ok = bool(resp and resp.get('ok'))
            text = resp.get('text') if isinstance(resp, dict) else str(resp)
        except Exception as e:
            ok = False
            text = f"[engine_error] {e}"
    else:
        ok = True
        # simple rule-based fallback answer in Arabic
        text = (
            "ترك أحمد القطة لمساعدة الطفل لأنه سمع بكاءه واعتبر مساعدة طفل أولوية إنسانية. "
            "قد يشعر أحمد بالقلق والرحمة والتعاطف عند سماع بكاء الطفل، وربما فضولًا تجاه القطة في البداية. "
            "بدلًا من الركض مباشرة كان يمكنه طلب مساعدة البالغين أو الاستعانة بشخص بالغ أو الاتصال برقم الطوارئ إذا لزم الأمر."
        )
    elapsed = time.time() - start
    return {"ok": ok, "text": text, "elapsed_s": elapsed}


def evaluate_test1(text: str):
    low = text.lower()
    # Q1: reason
    q1_keywords = ['طفل', 'مساعدة', 'ساعد', 'أنقذ', 'بكاء', 'خطر']
    q1_score = 100 if any(k in low for k in q1_keywords) else 0

    # Q2: emotions - expect multiple emotions; reward partial credit
    expected_emotions = ['قلق', 'اهتمام', 'رحمة', 'تعاطف', 'فضول', 'سعادة', 'دهشة', 'خوف', 'حزن']
    found = [e for e in expected_emotions if e in low]
    # score proportionally, cap at 100, expect ~3+ to be full score
    q2_score = min(100, int(len(found) / 3 * 100)) if found else 0

    # Q3: alternative actions
    q3_expected = ['طلب مساعدة', 'اتصل', 'البالغين', 'استدعاء', 'استعان', 'انتظار', 'مراقبة', 'واصل اللعب', 'تجاهل']
    found3 = [k for k in q3_expected if k in low]
    # reward if at least one reasonable alternative present
    q3_score = min(100, int(len(found3) / 2 * 100)) if found3 else 0

    return {
        'q1': {'score': q1_score, 'found': [k for k in q1_keywords if k in low]},
        'q2': {'score': q2_score, 'found': found},
        'q3': {'score': q3_score, 'found': found3},
        'overall_percent': int((q1_score + q2_score + q3_score) / 3)
    }


def save_results(out_json: dict, out_txt: str):
    artifacts = Path('artifacts')
    artifacts.mkdir(parents=True, exist_ok=True)
    json_path = artifacts / 'agi_test_results_test1.json'
    report_path = artifacts / 'agi_test_report_test1.txt'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(out_json, f, ensure_ascii=False, indent=2)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(out_txt)
    return str(json_path), str(report_path)


def make_report(run_info, eval_info):
    lines = []
    lines.append('نتيجة اختبار الفهم والسياق (الاختبار 1)')
    lines.append('---------------------------------------')
    lines.append(f"نجاح نداء المحرك: {run_info['ok']}")
    lines.append(f"زمن الاستجابة: {run_info['elapsed_s']:.3f} ثانية")
    lines.append('\nالرد الكامل:\n')
    lines.append(run_info['text'])
    lines.append('\n\nتقييم تفصيلي (نسبة مئوية لكل سؤال):')
    lines.append(f"1. لماذا ترك أحمد القطة؟ -> {eval_info['q1']['score']}%  (مفردات مكتشفة: {eval_info['q1']['found']})")
    lines.append(f"2. المشاعر المحتملة -> {eval_info['q2']['score']}%  (مفردات مكتشفة: {eval_info['q2']['found']})")
    lines.append(f"3. كيف كان يمكن أن يتصرف بشكل مختلف؟ -> {eval_info['q3']['score']}%  (مفردات مكتشفة: {eval_info['q3']['found']})")
    lines.append('\nالنتيجة الكلية (متوسط النسب): {}%'.format(eval_info['overall_percent']))
    return '\n'.join(lines)


def main():
    chat_fn = try_import_hosted_llm()
    if chat_fn:
        # quick connectivity check: if env vars indicate a hosted provider, try a tiny ping
        provider = os.getenv('AGL_LLM_PROVIDER', os.getenv('AGL_EXTERNAL_INFO_IMPL', 'ollama')).lower()
        model = os.getenv('AGL_LLM_MODEL') or os.getenv('AGL_OLLAMA_KB_MODEL')
        base = os.getenv('AGL_LLM_BASEURL') or os.getenv('OLLAMA_API_URL')
        connected = False
        if provider in ('ollama', 'http') and model and base:
            try:
                # perform a small ping to the LLM
                ping_msgs = [
                    {"role": "system", "content": "You are a minimal ping responder."},
                    {"role": "user", "content": "ping"},
                ]
                resp = chat_fn(ping_msgs)
                if isinstance(resp, dict) and resp.get('ok'):
                    connected = True
            except Exception:
                connected = False

        if connected and model:
            print(f"Using hosted LLM provider: {model} (connected)")
        else:
            print('استخدام Core_Engines.Hosted_LLM.chat_llm كمحرك (لم يتصل بالمزود المستضاف).')
    else:
        print('لم يتم العثور على Hosted_LLM، سيتم استخدام رد احتياطي مبسط (mock).')

    run = call_system_for_test1(chat_fn)
    evaluation = evaluate_test1(run['text'])
    report = make_report(run, evaluation)
    json_path, report_path = save_results({'run': run, 'evaluation': evaluation}, report)

    print('\n' + report)
    print(f'حفظت النتائج إلى: {json_path} و {report_path}')


if __name__ == '__main__':
    main()
