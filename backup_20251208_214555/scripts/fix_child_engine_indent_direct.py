import os
p = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'generated', 'MedicalAssistant_v1', 'child_system.json'))
with open(p, 'r', encoding='utf-8') as f:
    s = f.read()
pos = s.find('def route_task')
if pos == -1:
    print('def not found')
else:
    qpos = s.find("'''", pos)
    if qpos == -1:
        print("triple quote not found")
    else:
        # find start of the line containing the triple quote
        line_start = s.rfind('\n', 0, qpos) + 1
        ws = s[line_start:qpos]
        print('ws repr:', repr(ws))
        if ws.startswith('    '):
            # insert 4 more spaces
            new_ws = '        ' + ws.lstrip(' ')
            new_s = s[:line_start] + new_ws + s[qpos:]
            with open(p, 'w', encoding='utf-8') as f:
                f.write(new_s)
            print('patched insert spaces')
        else:
            print('unexpected ws, not patched')
