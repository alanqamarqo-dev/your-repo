import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from Integration_Layer.call_engine import call_engine_and_parse

p = "المشكلة: صمّم نظام ري لحديقة صغيرة (10×20م) بميزانية 1000$، ثم اشرح كيف تطبّق نفس مبادئ التدفق على تنظيم حركة المرور في تقاطع مزدحم. اذكر القيود، المقايضات، وأدوات القياس. اختم بخطوات تنفيذ."
parsed, raw_text, attempts, meta = call_engine_and_parse(None, p, force_json=True)
print('parsed:', parsed)
print('attempts:', attempts)
print('meta type:', type(meta))
if isinstance(meta, dict):
    print('meta keys:', list(meta.keys()))
print('raw_text:\n', raw_text)
