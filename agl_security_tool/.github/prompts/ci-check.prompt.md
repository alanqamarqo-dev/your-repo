---
description: "Run quick CI health check on WSL - imports, parser, detectors, weights"
tools: [read, search, execute]
argument-hint: "Scope (e.g. full, imports only, detectors only)"
---
Run a quick CI health check via WSL. Execute this script:

```bash
cd <project-root>           # root of agl_security_tool checkout
export PYTHONPATH=$(dirname $PWD)
PYTHON=python               # or .venv/bin/python

# 1. Import check
echo "=== IMPORTS ===" 
$PYTHON -c "from agl_security_tool.core import AGLSecurityAudit; print('core: OK')"
$PYTHON -c "from agl_security_tool.detectors import DetectorRunner; print('detectors: OK')"
$PYTHON -c "from agl_security_tool.audit_pipeline import run_audit; print('pipeline: OK')"

# 2. Parser check
echo "=== PARSER ==="
$PYTHON -c "
from agl_security_tool.detectors.solidity_parser import SoliditySemanticParser
p = SoliditySemanticParser()
c = p.parse(open('test_contracts/vulnerable/reentrancy_vault.sol').read())
print(f'Parsed {len(c)} contracts, {sum(len(x.functions) for x in c)} functions')
"

# 3. Detector check
echo "=== DETECTORS ==="
$PYTHON -c "
from agl_security_tool.detectors import DetectorRunner
r = DetectorRunner()
print(f'{len(r.list_detectors())} detectors registered')
"

# 4. Weights check
echo "=== WEIGHTS ==="
$PYTHON -c "
import json
w = json.load(open('artifacts/risk_weights.json'))['weights']
for k,v in w.items():
    flag = ' !! NEGATIVE' if k=='w_heuristic' and v<0 else ''
    print(f'  {k}: {v:+.4f}{flag}')
"
```
