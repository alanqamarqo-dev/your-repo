import json, os
p = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'generated', 'MedicalAssistant_v1', 'child_system.json'))
with open(p, 'r', encoding='utf-8') as f:
    child = json.load(f)
code = child.get('components', {}).get('engine_management', '')
if "def route_task(self, task_type, task_data):\n    '''" in code:
    code = code.replace("def route_task(self, task_type, task_data):\n    '''", "def route_task(self, task_type, task_data):\n        '''")
    child['components']['engine_management'] = code
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(child, f, ensure_ascii=False, indent=2)
    print('Patched engine_management indentation')
else:
    print('No pattern found; no change')
