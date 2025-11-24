from pathlib import Path
p=Path(r'D:/AGL/repo-copy/Core_Memory/Conscious_Bridge.py')
s=p.read_text()
needle = "getattr(self, '_use_embeddings'"
pos = s.find(needle)
print('pos', pos)
print(repr(s[pos-40:pos+140]))
