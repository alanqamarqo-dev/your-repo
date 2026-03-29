---
description: "Fix WSL environment issues: missing packages, broken distributions, venv problems"
tools: [read, edit, search, execute]
argument-hint: "Issue to fix (e.g. missing pytest, invalid pydantic, all issues)"
---
Fix the WSL development environment for AGL Security Tool.

Known issues to check and fix:
1. Invalid `~ydantic` distribution in `.venv_linux/lib/python3.12/site-packages/`
2. Missing packages: `pytest-timeout`, `semgrep`
3. Verify all core imports work after fixes

Commands to run via WSL:
```bash
cd /mnt/d/AGL/agl_security_tool
export PYTHONPATH=/mnt/d/AGL

# Fix invalid distribution
find .venv_linux -name '~*' -type d -exec rm -rf {} + 2>/dev/null

# Install missing packages
.venv_linux/bin/python -m pip install pytest-timeout

# Verify
.venv_linux/bin/python -m pip check 2>&1 | head -20
.venv_linux/bin/python -c "from agl_security_tool.detectors import DetectorRunner; print('OK')"
```
