"""Test: solc health check + Slither/Mythril fast-skip + Semgrep still works."""
import sys, time, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tool_backends import ToolBackendRunner

runner = ToolBackendRunner()
print(f"Status: {runner.status()}")

test_file = os.path.join(os.path.dirname(__file__), "..", "test_contracts", "negative_evidence_test.sol")
test_file = os.path.abspath(test_file)

if not os.path.exists(test_file):
    print(f"SKIP: test file not found: {test_file}")
    sys.exit(0)

t0 = time.monotonic()
result = runner.analyze(test_file)
elapsed = time.monotonic() - t0
print(f"Analyze took: {elapsed:.2f}s")
print(f"Total findings: {result['total_findings']}")

for tool, status in result["tool_status"].items():
    err = status.get("error", "")
    print(f"  {tool}: success={status['success']}, findings={status['findings_count']}, "
          f"error={err[:80] + '...' if len(err) > 80 else err}")

# Verify Semgrep still works
sem = result["tool_status"].get("semgrep", {})
if sem.get("success"):
    print(f"\n✅ Semgrep works: {sem['findings_count']} findings")
else:
    print(f"\n⚠️ Semgrep issue: {sem.get('error', 'unknown')}")

# Verify Slither/Mythril report clear errors
for tool in ("slither", "mythril"):
    ts = result["tool_status"].get(tool, {})
    if not ts.get("available", True) and "solc" in ts.get("error", ""):
        print(f"✅ {tool}: correctly reports solc error (no wasted timeout)")
    elif ts.get("success"):
        print(f"✅ {tool}: working! {ts['findings_count']} findings")
    else:
        print(f"⚠️ {tool}: status unclear: {ts}")
