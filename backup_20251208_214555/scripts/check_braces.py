#!/usr/bin/env python3
from pathlib import Path
p = Path(__file__).resolve().parents[1] / 'run_all.ps1'
s = p.read_text(encoding='utf-8')
open_count = s.count('{')
close_count = s.count('}')
print(f"open={open_count} close={close_count}")
# Find first mismatch by scanning
stack = []
for i,ch in enumerate(s):
    if ch=='{':
        stack.append(i)
    elif ch=='}':
        if stack:
            stack.pop()
        else:
            print(f"Unmatched closing brace at index {i}")
            break
else:
    if stack:
        print(f"Unmatched opening brace at index {stack[-1]}")
    else:
        print('Braces balanced')
