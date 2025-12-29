import io,os
p = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'generated', 'MedicalAssistant_v1', 'child_system.json'))
with open(p, 'r', encoding='utf-8') as f:
    s = f.read()
old = "def route_task(self, task_type, task_data):\n    '''"
new = "def route_task(self, task_type, task_data):\n        '''"
if old in s:
    s = s.replace(old, new)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(s)
    print('patched')
else:
    print('pattern not found')
