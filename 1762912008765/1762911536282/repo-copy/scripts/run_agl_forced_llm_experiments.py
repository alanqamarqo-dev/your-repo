"""Run repeated experiments forcing KnowledgeOrchestrator -> external LLM with a strong Arabic SYSTEM_PROMPT.

For each test the script:
 - runs an initial orchestrator call
 - runs N improvement iterations where the previous answer is passed back with an instruction to improve
 - saves all intermediate outputs and timings to reports/aglh_forced_llm_experiments.json

This helps measure incremental learning-like improvements at the prompt level.
"""
from __future__ import annotations

from __future__ import annotations
# === AGL auto-injected knobs (idempotent) ===
try:
    import os
    def _to_int(name, default):
        try:
            return int(os.environ.get(name, str(default)))
        except Exception:
            return default
except Exception:
    def _to_int(name, default): return default
_AGL_PREVIEW_1000 = _to_int('AGL_PREVIEW_1000', 1000)

try:
    import os
    def _to_int(name, default):
        try:
            return int(os.environ.get(name, str(default)))
        except Exception:
            return default
except Exception:
    def _to_int(name, default): return default
import os
import time
import json
from pathlib import Path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Core_Engines.KnowledgeOrchestrator import KnowledgeOrchestrator
REPORTS_DIR = Path('reports')
REPORTS_DIR.mkdir(exist_ok=True)
OUT_PATH = REPORTS_DIR / 'aglh_forced_llm_experiments.json'
SYSTEM_PROMPT = 'أنت منظومة AGL المتكاملة. أجب بالعربية فقط وبنبرة رسمية ومفصّلة. لكل مهمة قدم: ملخّصًا سريعًا، ثم خطة خطوة-بخطوة قابلة للتنفيذ، ثم مؤشرات قياس أداء رقمية حيث ينطبق، ثم تقييمًا ذاتيًا للنتيجة بنقاط (0-100) عبر المعايير: الفهم، الاستدلال، الإبداع، التكامل، الفهم العاطفي. لا تستخدم أي مسترجع محلي أو قاعدة بيانات داخلية — أجب استنادًا إلى قدرات النموذج التوليدي فقط. لا تضف مراجع مصدرية مزيفة. إذا لم تكن متأكدًا من معلومة، اعترف بذلك وقدم خطوات لجمع الدليل.'
def build_tests():
    tests = []
    tests.append({'id': 1, 'name': 'الفهم والسياق', 'prompt': 'قصة:\n' + 'كان أحمد يلعب في الحديقة. رأى قطة جميلة تلاحق فراشة.\n' + 'ثم سمع صوت بكاء طفل صغير. ترك القطة وركض لمساعدة الطفل.\n\n' + 'الأسئلة:\n1. لماذا ترك أحمد القطة؟\n2. ما هي المشاعر المحتملة لأحمد في كل موقف؟\n3. كيف كان يمكن أن يتصرف بشكل مختلف؟'})
    tests.append({'id': 2, 'name': 'حل المشكلات المعقدة', 'prompt': 'المهمة: تصميم نظام ري ذكي لحديقة\nالمتطلبات:\n- توفير 30% من المياه\n- مراعاة أنواع النباتات المختلفة\n- التكيف مع أحوال الطقس\n- التكلفة لا تتجاوز 200 دولار\n\nالمطلوب: خطة تنفيذ مفصلة مع مبررات لكل اختيار'})
    tests.append({'id': 3, 'name': 'التعلم والتبادل بين المجالات', 'prompt': 'تعلم وتطبيق:\nالمفهوم الجديد = "مبدأ حفظ الطاقة: الطاقة لا تفنى ولا تستحدث ولكن تتحول من شكل لآخر"\n\nالمطلوب:\n1. شرح المبدأ بكلماتك الخاصة\n2. تطبيق المبدأ في مجال الاقتصاد أو العلاقات الاجتماعية\n3. استنتاج قاعدة جديدة بناءً على هذا المبدأ'})
    tests.append({'id': 4, 'name': 'الإبداع والابتكار', 'prompt': 'الإبداع والابتكار:\nالمشكلة = "كيف نساعد كبار السن على تذكر تناول الأدوية في أوقاتها؟"\n\nالمطلوب:\n1. 3 أفكار إبداعية لحل المشكلة\n2. اختيار أفضل فكرة وتطويرها\n3. تحديد التحديات وكيفية التغلب عليها'})
    tests.append({'id': 5, 'name': 'التفكير الاستراتيجي', 'prompt': 'التفكير الاستراتيجي:\nالهدف = "زيادة الوعي البيئي في الحي خلال 6 أشهر"\nالميزانية = "500 دولار"\nالمشاركون = "متطوعون من الشباب"\n\nالمطلوب: خطة استراتيجية شاملة تشمل: مراحل التنفيذ، مؤشرات النجاح، إدارة المخاطر، الاستدامة'})
    return tests
def extract_text(resp: dict) -> str:
    if not isinstance(resp, dict):
        return str(resp)
    for k in ('text', 'reply_text', 'reply', 'message', 'description'):
        v = resp.get(k)
        if v:
            return v
    data = resp.get('data') if isinstance(resp.get('data'), dict) else None
    if data and isinstance(data.get('text'), str):
        return data.get('text')
    return json.dumps(resp, ensure_ascii=False)[:_AGL_PREVIEW_1000]
def run_experiments(iterations=None):
    if iterations is None:
        iterations = int(os.environ.get('AGL_EXPERIMENT_ROUNDS', '3'))
    os.environ['AGL_EXTERNAL_INFO_IMPL'] = 'ollama_adapter'
    os.environ['AGL_OLLAMA_KB_MODEL'] = os.environ.get('AGL_OLLAMA_KB_MODEL', 'qwen2.5:7b-instruct')
    os.environ['AGL_OLLAMA_KB_CACHE_ENABLE'] = '0'
    os.environ['AGL_EXTERNAL_SYSTEM_PROMPT'] = SYSTEM_PROMPT
    os.environ['AGL_FORCE_EXTERNAL'] = '1'
    ko = KnowledgeOrchestrator()
    try:
        ko.retriever = None
    except Exception:
        pass
    tests = build_tests()
    suite = {'mode': 'forced_llm_iterative', 'system_prompt': SYSTEM_PROMPT, 'timestamp': time.time(), 'tests': []}
    for t in tests:
        print(f"Running test {t['id']} '{t['name']}' (initial + {iterations - 1} improvements)")
        record = {'id': t['id'], 'name': t['name'], 'rounds': []}
        prompt = t['prompt']
        start = time.time()
        resp = ko.orchestrate(prompt)
        dur = time.time() - start
        text = extract_text(resp)
        record['rounds'].append({'round': 0, 'prompt': prompt, 'response': resp, 'text': text, 'duration': dur})
        prev_text = text
        for i in range(1, iterations):
            improve_prompt = f'راجع الإجابة السابقة وحسّنها: قدم نسخة محسنة بالعربية كمخطط واضح خطوة‑بخطوة.\nالمعايير: الفهم، الاستدلال، الإبداع، التكامل، الفهم العاطفي.\nالإجابة السابقة:\n{prev_text}\n\nالمهمة الأصلية:\n{prompt}'
            start = time.time()
            resp2 = ko.orchestrate(improve_prompt)
            dur2 = time.time() - start
            text2 = extract_text(resp2)
            record['rounds'].append({'round': i, 'prompt': improve_prompt, 'response': resp2, 'text': text2, 'duration': dur2})
            prev_text = text2
        suite['tests'].append(record)
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(suite, f, ensure_ascii=False, indent=2)
    print(f'Experiments complete. Results saved to: {OUT_PATH}')
if __name__ == '__main__':
    run_experiments()
