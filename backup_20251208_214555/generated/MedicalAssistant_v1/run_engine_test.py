import json, os
p = os.path.join(os.path.dirname(__file__), 'child_system.json')
with open(p, 'r', encoding='utf-8') as f:
    child = json.load(f)

code = child['components']['engine_management']
# execute engine management code in a sandboxed dict
ns = {}
exec(code, ns)
# EngineManager should now be in ns
EM = ns.get('EngineManager')
if EM is None:
    print('EngineManager not defined')
else:
    em = EM()
    res = em.process_with_engine('MathematicalBrain', {'symptoms': 'cough'})
    print('Engine response:', res)

# Also try route_task with a known task_type mapping
try:
    rt = em.route_task('رياضيات', {'x': 1})
    print('Route task result:', rt)
except Exception as e:
    print('route_task error:', e)
