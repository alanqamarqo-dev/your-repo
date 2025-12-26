from Integration_Layer import rag_wrapper as rw
from tests.test_agi_academic_challenge import _normalize_ar, SYNONYMS, _semantic_hit
import os
os.environ['AGL_OLLAMA_KB_MOCK']='0'
os.environ['AGL_EXTERNAL_INFO_MOCK']='0'
os.environ['AGL_FEATURE_ENABLE_RAG']='1'
os.environ['AGL_LLM_MODEL']='qwen2.5:7b-instruct'
os.environ['AGL_LLM_BASEURL']='http://127.0.0.1:11434'

prompt = (
    "تعلم المفهوم الجديد من الأمثلة:\n"
    "أمثلة إيجابية: طيور تطير في سرب؛ سيارات في زحام مروري\n"
    "أمثلة سلبية: جنود يسيرون؛ عمال في مصنع\n"
    "سَمِّ هذا المفهوم وعلّم قاعدة عامة قابلة للتطبيق على سياقات جديدة."
)
res = rw.rag_answer(prompt)
ans = res.get('answer')
print('ANSWER:\n', ans)
print('\nNORMALIZED ANSWER:\n', _normalize_ar(ans))
for key, group in SYNONYMS.items():
    print('\nGroup:', key)
    for kw in group:
        print('  kw:', kw, '-> norm:', _normalize_ar(kw), 'in ans?', _normalize_ar(kw) in _normalize_ar(ans))
print('\n_semantic_hit:', _semantic_hit(ans))
