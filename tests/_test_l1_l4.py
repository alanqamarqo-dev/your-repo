"""Test that all 4 advanced layers now activate during scan."""

import sys, os, time, io

_PROJECT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
os.chdir(_PROJECT_ROOT)
sys.path.insert(0, _PROJECT_ROOT)
sys.stderr = io.StringIO()

from agl_security_tool import AGLSecurityAudit

audit = AGLSecurityAudit()

print("=== Testing scan with L1-L4 integration ===")
t0 = time.time()
r = audit.scan("vulnerable.sol")
elapsed = time.time() - t0

layers = r.get("layers_used", [])
print(f"\nTime: {elapsed:.1f}s")
print(f"Layers active ({len(layers)}):")
for l in layers:
    print(f"  + {l}")

print(f"\n--- Results ---")
print(f"Unified findings: {len(r.get('all_findings_unified', []))}")

# Check Layer 1: State Extraction
se = r.get("state_extraction")
if se:
    print(
        f"\n[L1] State Extraction: {se['entities']} entities, {se['relationships']} rels, {se['fund_flows']} flows"
    )
else:
    print(f"\n[L1] State Extraction: NOT ACTIVATED")

# Check Temporal Analysis
ta = r.get("temporal_analysis")
if ta:
    print(
        f"[L1+] Temporal: CEI={ta.get('cei_violations',0)}, Reentrancy={ta.get('reentrancy_risks',0)}, WriteConf={ta.get('write_conflicts',0)}, Effects={ta.get('effects_count',0)}, Mutations={ta.get('mutations_count',0)}"
    )
else:
    print(f"[L1+] Temporal Analysis: NOT ACTIVATED")

# Check Layer 2: Action Space
as_data = r.get("action_space")
if as_data:
    print(
        f"[L2] Action Space: {as_data['total_actions']} actions, {as_data['attack_sequences']} sequences, {as_data['attack_surfaces']} surfaces, {as_data['high_value_targets']} targets"
    )
else:
    print(f"[L2] Action Space: NOT ACTIVATED")

# Check Layer 3: Attack Simulation
atk = r.get("attack_simulation")
if atk:
    print(
        f"[L3] Attack Sim: {atk['total_sequences_tested']} tested, {atk['profitable_attacks']} profitable, ${atk['total_profit_usd']:.2f} profit"
    )
else:
    print(f"[L3] Attack Simulation: NOT ACTIVATED")

# Check Layer 4: Search Engine
sr = r.get("search_results")
if sr:
    print(
        f"[L4] Search: {sr['profitable_sequences']} profitable sequences, {sr['total_evaluated']} evaluated"
    )
else:
    print(f"[L4] Search Engine: NOT ACTIVATED")

# Show findings from new layers
for label, key in [
    ("temporal_findings", "Temporal"),
    ("action_space_findings", "ActionSpace"),
    ("attack_findings", "Attack"),
    ("search_findings", "Search"),
    ("validation_findings", "Validation"),
]:
    items = r.get(label, [])
    if items:
        print(f"\n  {key} findings ({len(items)}):")
        for f in items[:3]:
            print(f"    [{f.get('severity','?').upper()}] {f.get('title','')[:100]}")

# Warnings
warnings = r.get("warnings", [])
if warnings:
    print(f"\n--- Warnings ({len(warnings)}) ---")
    for w in warnings:
        print(f"  ! {w[:150]}")

print(f"\n=== DONE ===")
