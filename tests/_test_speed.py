"""Speed test — before vs after fix"""

import sys, os, time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from agl_security_tool.core import AGLSecurityAudit

audit = AGLSecurityAudit({"skip_llm": True})

# Test 1: vulnerable.sol
t0 = time.time()
r1 = audit.scan("vulnerable.sol")
t1 = time.time() - t0
print(f"vulnerable.sol:  {t1:.1f}s  layers={r1.get('layers_used')}")

# Test 2: Aave Pool.sol
t0 = time.time()
r2 = audit.scan("aave-v3-core/contracts/protocol/pool/Pool.sol")
t2 = time.time() - t0
print(f"Pool.sol:        {t2:.1f}s  layers={r2.get('layers_used')}")

# Test 3: Aave BorrowLogic.sol
t0 = time.time()
r3 = audit.scan("aave-v3-core/contracts/protocol/libraries/logic/BorrowLogic.sol")
t3 = time.time() - t0
print(f"BorrowLogic.sol: {t3:.1f}s  layers={r3.get('layers_used')}")

print(f"\nTotal: {t1+t2+t3:.1f}s for 3 files")
print(f"Average: {(t1+t2+t3)/3:.1f}s per file")
