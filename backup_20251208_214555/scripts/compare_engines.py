import sys, os, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Integration_Layer import Domain_Router

try:
    from Core_Engines.OpenAI_KnowledgeEngine import OpenAIKnowledgeEngine
except Exception:
    OpenAIKnowledgeEngine = None

GK = None
try:
    GK = Domain_Router.get_engine('knowledge')
except Exception:
    GK = None

prompts = [
    'ما هي سرعة الضوء؟',
    'ما هو قانون نيوتن الثاني؟',
    'ما الفرق بين الطاقة والقدرة؟',
    'كيف أثبت Python على Windows؟',
    'كيف أصنع نسخة احتياطية لقاعدة بيانات؟',
    'أعطني 3 أفكار لتطبيق تعليمي',
    'أخبرني بنكتة قصيرة',
    'ما هي أكبر قارة؟',
    'ما سبب تغير الفصول؟',
    'احسب 12 * 34',
]

results = []
for p in prompts:
    entry = {'prompt': p}
    # GK direct
    try:
        if GK is not None:
            gk_raw = GK.ask(p, context=[])
            entry['gk_raw'] = gk_raw
            try:
                entry['gk_text'] = Domain_Router._safe_text(gk_raw)
            except Exception:
                entry['gk_text'] = str(gk_raw)
        else:
            entry['gk_raw'] = None # type: ignore
            entry['gk_text'] = None # type: ignore
    except Exception as e:
        entry['gk_raw'] = None # type: ignore
        entry['gk_text'] = f'ERROR: {e}'

    # OpenAI direct
    try:
        if OpenAIKnowledgeEngine is not None:
            oa = OpenAIKnowledgeEngine()
            oa_raw = oa.ask(p, context=[])
            entry['openai_raw'] = oa_raw # type: ignore
            if isinstance(oa_raw, dict):
                entry['openai_text'] = oa_raw.get('text') or oa_raw.get('answer') or None # type: ignore
            else:
                entry['openai_text'] = str(oa_raw)
        else:
            entry['openai_raw'] = None # type: ignore
            entry['openai_text'] = None # type: ignore
    except Exception as e:
        entry['openai_raw'] = None # type: ignore
        entry['openai_text'] = f'ERROR: {e}'

    # Full route
    try:
        routed = Domain_Router.route(p, context=[])
        entry['route'] = routed # type: ignore
        entry['route_text'] = routed.get('reply_text') or routed.get('text') or None # type: ignore
    except Exception as e:
        entry['route'] = None # type: ignore
        entry['route_text'] = f'ERROR: {e}'

    results.append(entry)

outp = os.path.join('artifacts', 'engine_comparison.json')
os.makedirs(os.path.dirname(outp), exist_ok=True)
with open(outp, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print('Saved', outp)
