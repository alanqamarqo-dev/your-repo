#!/usr/bin/env python3
import sys
from pathlib import Path
p = Path(r"D:\AGL\artifacts\agi_multitest_report.md")
# Ensure stdout is UTF-8
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
print(p.read_text(encoding='utf-8'))
