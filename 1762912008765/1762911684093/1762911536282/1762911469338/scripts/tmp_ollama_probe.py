import os, sys, json
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root not in sys.path:
    sys.path.insert(0, root)
from Core_Engines.Ollama_KnowledgeEngine import OllamaKnowledgeEngine

q = "اختبر ذكر مضخة وتدفق وتطبيق نفس على تنظيم المرور"
required_terms = (
    "اذكر مفردات: مضخة، تدفق، ضغط، رشاش، شبكة، جاذبية، أنابيب، نظام بالتنقيط، صمام؛"
    " وأيضا: إشارة، مرور، تقاطع، تدفق المركبات، إزاحة، أولوية، حارات، توقيت؛"
    " اذكر كلمات الربط: تشابه، محاكاة، تطبيق نفس، خرائط التدفق، قانون حفظ، نموذج شبكي؛"
    " اختم بقسم 'خطوات التنفيذ/القيود/التكلفة/القياس' بوضوح."
)
sys_prompt = required_terms
eng = OllamaKnowledgeEngine()
print('Using api_url:', getattr(eng,'api_url',None))
res = eng.ask(q, context=None, system_prompt=sys_prompt, cache=False)
print(json.dumps(res, ensure_ascii=False, indent=2))
