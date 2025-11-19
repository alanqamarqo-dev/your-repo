import os
import sys
import json

# ensure project root is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Core_Engines.KnowledgeOrchestrator import KnowledgeOrchestrator

# Paths
INPUT_PATH = os.path.join('reports', 'agl_test_input.txt')
OUTPUT_PATH = os.path.join('reports', 'agl_orchestrated_response.json')

# Integrated-system instruction for external provider (Arabic-only, act as integrated AGL)
SYSTEM_PROMPT = (
    "أنت منظومة AGL المتكاملة — تصرف كوحدة واحدة تتألف من مكونات: التخطيط، التنفيذ، التعلم، التحقق، والتقييم. "
    "أجب بالعربية فقط. لكل جزء قدم ملخصًا واضحًا وخطوات عملية قابلة للتنفيذ وأمثلة رقمية حيث ينطبق. "
    "عند الإجابة قدم تقييمًا مباشرًا إذا طُلِب. انتهِ بجواب موجز وخطوات تالية قابلة للتنفيذ."
)


def split_into_parts(text: str):
    # Split on the marker 'الجزء ' but keep the first chunk (title) if present
    chunks = text.split('\n\nالجزء ')
    if len(chunks) == 1:
        return [text]
    parts = []
    # first chunk may include header
    header = chunks[0].strip()
    for c in chunks[1:]:
        parts.append('الجزء ' + c.strip())
    return parts


def main():
    if not os.path.exists(INPUT_PATH):
        print('Input test file not found:', INPUT_PATH)
        raise SystemExit(1)

    with open(INPUT_PATH, 'r', encoding='utf-8') as fh:
        test_text = fh.read()

    parts = split_into_parts(test_text)

    # Set env so that KnowledgeOrchestrator's OllamaAdapter uses the system prompt
    os.environ['AGL_EXTERNAL_INFO_IMPL'] = 'ollama_adapter'
    os.environ['AGL_EXTERNAL_INFO_MODEL'] = os.environ.get('AGL_OLLAMA_KB_MODEL', 'qwen2.5:7b-instruct')
    os.environ['AGL_EXTERNAL_SYSTEM_PROMPT'] = SYSTEM_PROMPT
    os.environ['AGL_OLLAMA_KB_CACHE_ENABLE'] = '0'

    ko = KnowledgeOrchestrator()
    # Force orchestrator to bypass any local retriever and call the external provider (LLM)
    ko.retriever = None

    results = {'parts': [], 'engine_trace': []}

    for i, part in enumerate(parts, start=1):
        print(f'Running orchestrator on part {i} (len={len(part)})')
        res = ko.orchestrate(part)
        results['parts'].append({'part': i, 'prompt': part, 'result': res})
        # collect trace
        if res.get('engine_trace'):
            results['engine_trace'].append({'part': i, 'trace': res.get('engine_trace')})

    # Optionally, ask orchestrator to evaluate the combined answers (simple prompt)
    combined_answers = '\n\n'.join([p['result'].get('text','') for p in results['parts']])
    eval_prompt = (
        'قيم الإجابات أعلاه رقمياً بالنسبة للمعايير: الفهم المتكامل (25%), العمق والتفاصيل (25%), '
        'الإبداع والمرونة (20%), التخطيط المنطقي (20%), الفهم العاطفي والاجتماعي (10%). أعطِ لكل معيار درجة 0-100 واحسب النتيجة النهائية.'
    )
    eval_input = combined_answers + '\n\n' + eval_prompt
    print('Running orchestrator for final evaluation...')
    eval_res = ko.orchestrate(eval_input)
    # keep evaluation in a list to match existing results shape and avoid static-typing mismatches
    results['evaluation'] = [eval_res]

    # write to a forced-LLM output file to preserve previous runs
    forced_output = os.path.join('reports', 'agl_orchestrated_response_forced_llm.json')
    os.makedirs(os.path.dirname(forced_output), exist_ok=True)
    with open(forced_output, 'w', encoding='utf-8') as fh:
        json.dump(results, fh, ensure_ascii=False, indent=2)

    print('Wrote orchestrated response to', forced_output)


if __name__ == '__main__':
    main()
