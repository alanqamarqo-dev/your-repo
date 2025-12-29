p = r'd:\\AGL\\repo-copy\\generated\\MedicalAssistant_v1\\child_system.json'
with open(p, 'r', encoding='utf-8') as f:
    s = f.read()
idx = s.find('def route_task')
print('idx', idx)
print(s[idx:idx+120])
print(repr(s[idx:idx+120]))
