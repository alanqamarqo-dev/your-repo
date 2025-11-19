import json
import os, sys
# Ensure repository root is on PYTHONPATH
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root not in sys.path:
    sys.path.insert(0, root)
from Core_Engines.Reasoning_Layer import ReasoningLayer

p = (
    "المشكلة: صمّم نظام ري لحديقة صغيرة (10×20م) بميزانية 1000$، ثم اشرح كيف تطبّق نفس مبادئ التدفق "
    "على تنظيم حركة المرور في تقاطع مزدحم. اذكر القيود، المقايضات، وأدوات القياس. اختم بخطوات تنفيذ."
)
rl = ReasoningLayer()
res = rl.process_task({'query': p})
print(json.dumps(res, ensure_ascii=False, indent=2))
