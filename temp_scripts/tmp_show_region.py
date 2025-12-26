from pathlib import Path
p=Path(r'D:/AGL/repo-copy/Core_Memory/Conscious_Bridge.py')
s=p.read_text().splitlines()
for i in range(480, 540):
    print(f"{i+1:4}: {s[i]}")
