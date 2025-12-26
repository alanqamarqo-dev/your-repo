from pathlib import Path
p=Path(r'D:/AGL/repo-copy/Core_Memory/Conscious_Bridge.py')
s=p.read_text()
for i in range(495, 510):
    line = s.splitlines()[i]
    print(f"{i+1:4}: {repr(line)}")
