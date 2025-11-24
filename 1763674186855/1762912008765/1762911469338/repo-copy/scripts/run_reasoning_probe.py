import sys, os
sys.path.append(os.getcwd())
from Integration_Layer.integration_registry import registry
import Core_Engines as engines
# bootstrap
engines.bootstrap_register_all_engines(registry, allow_optional=True)
from tests.helpers.engine_ask import ask_engine
prompt = "المشكلة: صمّم نظام ري لحديقة صغيرة (10×20م) بميزانية 1000$، ثم اشرح كيف تطبّق نفس مبادئ التدفق على تنظيم حركة المرور في تقاطع مزدحم. اذكر القيود، المقايضات، وأدوات القياس. اختم بخطوات تنفيذ."
res = ask_engine('Reasoning_Layer', prompt)
import json
print(json.dumps(res, ensure_ascii=False, indent=2))
