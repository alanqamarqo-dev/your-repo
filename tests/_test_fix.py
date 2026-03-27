"""Test Z3 fix - quick scan on Aave V3 Pool.sol"""

import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from agl_security_tool.core import AGLSecurityAudit

print("=" * 60)
print("Testing on Aave V3 Pool.sol (after fixes)")
print("=" * 60)

a = AGLSecurityAudit()
_PROJECT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
_POOL_SOL = os.path.join(_PROJECT_ROOT, "aave-v3-core", "contracts", "protocol", "pool", "Pool.sol")
r = a.scan(_POOL_SOL)

unified = r.get("all_findings_unified", [])
print(f"\nTotal unified: {len(unified)}")

by_sev = {}
for f in unified:
    s = f.get("severity", "?").upper()
    by_sev[s] = by_sev.get(s, 0) + 1
for s in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
    print(f"  {s}: {by_sev.get(s, 0)}")

# Z3 findings
z3c = sum(
    1
    for f in unified
    if "z3" in str(f.get("source", "")).lower()
    or "z3" in str(f.get("detector_id", "")).lower()
)
print(f"\nZ3 findings: {z3c}")

# Layers
print(f"Layers: {r.get('layers_used', [])}")

# Show CRITICAL/HIGH
print("\nCRITICAL/HIGH findings:")
for f in unified:
    if f.get("severity", "").upper() in ("CRITICAL", "HIGH"):
        print(f"  [{f['severity'].upper():>8}] {f.get('title', '?')[:80]}")

# Raw counts
print(f"\nRaw counts:")
print(f"  Pattern: {len(r.get('findings', []))}")
print(f"  Suite: {len(r.get('suite_findings', []))}")
print(f"  Detectors: {len(r.get('detector_findings', []))}")
print(f"  Z3 symbolic: {len(r.get('z3_findings', []))}")
