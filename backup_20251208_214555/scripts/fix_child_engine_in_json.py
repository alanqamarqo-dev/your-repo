import json, os
p = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'generated', 'MedicalAssistant_v1', 'child_system.json'))
with open(p, 'r', encoding='utf-8') as f:
    obj = json.load(f)
code = obj.get('components', {}).get('engine_management', '')
if not code:
    print('no engine_management')
else:
    if "def route_task" in code:
        old = "def route_task(self, task_type, task_data):\n    '''"
        new = "def route_task(self, task_type, task_data):\n        '''"
        if old in code:
            code = code.replace(old, new)
            obj['components']['engine_management'] = code
            with open(p, 'w', encoding='utf-8') as f:
                json.dump(obj, f, ensure_ascii=False, indent=2)
            print('patched json field')
        else:
            print('pattern not found inside string; show snippet:')
            i = code.find('def route_task')
            print(repr(code[i:i+80]))
    else:
        print('no def route_task in code')
