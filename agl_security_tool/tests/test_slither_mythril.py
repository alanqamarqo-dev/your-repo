"""Quick test: Slither + Mythril on a real contract."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Force fresh solc check
import tool_backends
tool_backends._solc_check_done = False

from tool_backends import SlitherRunner, MythrilRunner, SemgrepRunner

test_file = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "test_contracts", "vulnerable", "unchecked_call.sol"
))
if not os.path.exists(test_file):
    # fallback
    test_file = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "test_contracts", "negative_evidence_test.sol"
    ))

print(f"Test file: {test_file}")
print(f"File exists: {os.path.exists(test_file)}")
print()

# Slither
print("=" * 50)
print("SLITHER")
print("=" * 50)
sr = SlitherRunner(timeout=120)
print(f"  Available: {sr.available}")
t0 = time.monotonic()
r = sr.analyze(test_file)
elapsed = time.monotonic() - t0
print(f"  Duration: {elapsed:.1f}s")
print(f"  Success: {r.success}")
print(f"  Findings: {len(r.findings)}")
print(f"  Error: {r.error[:200] if r.error else 'none'}")
print(f"  Stderr: {r.stderr[:200] if r.stderr else 'none'}")
for f in r.findings[:10]:
    print(f"    [{f.severity}] {f.detector_name}: {f.title[:80]}")

# Mythril
print()
print("=" * 50)
print("MYTHRIL")
print("=" * 50)
mr = MythrilRunner(timeout=120, max_depth=12)
print(f"  Available: {mr.available}")
t0 = time.monotonic()
r = mr.analyze(test_file)
elapsed = time.monotonic() - t0
print(f"  Duration: {elapsed:.1f}s")
print(f"  Success: {r.success}")
print(f"  Findings: {len(r.findings)}")
print(f"  Error: {r.error[:200] if r.error else 'none'}")
print(f"  Stderr: {r.stderr[:200] if r.stderr else 'none'}")
for f in r.findings[:10]:
    print(f"    [{f.severity}] {f.detector_name}: {f.title[:80]}")

# Semgrep (should still work)
print()
print("=" * 50)
print("SEMGREP")
print("=" * 50)
sg = SemgrepRunner(timeout=60)
print(f"  Available: {sg.available}")
t0 = time.monotonic()
r = sg.analyze(test_file)
elapsed = time.monotonic() - t0
print(f"  Duration: {elapsed:.1f}s")
print(f"  Success: {r.success}")
print(f"  Findings: {len(r.findings)}")
for f in r.findings[:10]:
    print(f"    [{f.severity}] {f.detector_name}: {f.title[:80]}")
