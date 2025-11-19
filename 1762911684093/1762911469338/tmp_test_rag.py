from Integration_Layer import rag_wrapper as rw
import os
os.environ['AGL_OLLAMA_KB_MOCK']='1'
os.environ['AGL_EXTERNAL_INFO_MOCK']='1'
print('AGL_LLM_MODEL=',os.getenv('AGL_LLM_MODEL'))
res = rw.rag_answer('تعلم المفهوم الجديد من الأمثلة:\nأمثلة إيجابية: طيور تطير في سرب؛ سيارات في زحام مروري\nأمثلة سلبية: جنود يسيرون؛ عمال في مصنع\nسَمِّ هذا المفهوم وعلّم قاعدة عامة قابلة للتطبيق على سياقات جديدة.')
print('RES:',res)
print('ANS:',res.get('answer'))
