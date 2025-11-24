#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CI helper: generate a timestamped visual report under reports/ with the current UTC timestamp.
Intended to be called by CI after training completes.
"""
from __future__ import annotations
import os, datetime, subprocess, sys
from datetime import timezone

out_dir = os.path.join('reports', 'auto_visual')
os.makedirs(out_dir, exist_ok=True)
now = datetime.datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
out_path = os.path.join(out_dir, f'models_visual_{now}.html')
figdir = os.path.join(out_dir, 'figs')

cmd = [sys.executable, '-m', 'scripts.make_visual_report', '--glob-dir', 'artifacts/models', '--out', out_path, '--figdir', figdir]
print('Running:', ' '.join(cmd))
res = subprocess.run(cmd)
if res.returncode == 0:
    print('wrote', out_path)
    sys.exit(0)
else:
    print('report generation failed', res.returncode)
    sys.exit(res.returncode)
