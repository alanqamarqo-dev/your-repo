from Integration_Layer.integration_registry import registry
import Core_Engines as CE
CE.bootstrap_register_all_engines(registry, allow_optional=True)
rl = registry.get('Reasoning_Layer')
payload = {'text': "المشكلة: صمّم نظام ري لحديقة صغيرة (10×20م) بميزانية 1000$، ثم اشرح كيف تطبّق نفس مبادئ التدفق على تنظيم حركة المرور في تقاطع مزدحم. اذكر القيود، المقايضات، وادوات القياس. اختم بخطوات تنفيذ."}
res = rl.process_task(payload) # type: ignore
print('OK:', res.get('ok'))
print('\n----- TEXT -----\n')
print(res.get('text'))
