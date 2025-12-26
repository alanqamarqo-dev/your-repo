from pathlib import Path
p=Path(r'D:/AGL/repo-copy/Core_Memory/Conscious_Bridge.py')
s=p.read_text()
for i,line in enumerate(s.splitlines(), start=1):
    if 'try:' in line:
        print('TRY', i, line)
    if 'except' in line:
        print('EXC', i, line)
