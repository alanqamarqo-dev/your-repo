import re, os
p = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'generated', 'MedicalAssistant_v1', 'child_system.json'))
s = open(p, 'r', encoding='utf-8').read()
new, n = re.subn(r"(def route_task\([^\)]*\):\n) {4}'''", r"\1        '''", s)
if n:
    open(p, 'w', encoding='utf-8').write(new)
    print('patched', n)
else:
    print('no-match')
