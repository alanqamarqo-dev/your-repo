"""Quick test: verify pipeline runs with skip_llm=True without loading LLM models."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import psutil, time

proc = psutil.Process()
print(f"Available RAM: {psutil.virtual_memory().available / 1024**3:.1f} GB")

rss0 = proc.memory_info().rss
print(f"RSS before: {rss0/1024**2:.0f} MB")

# Step 1: Create core with skip_llm
from agl_security_tool.core import AGLSecurityAudit
core = AGLSecurityAudit(config={"skip_llm": True, "skip_deep_analyzer": True})
rss1 = proc.memory_info().rss
print(f"RSS after init: {rss1/1024**2:.0f} MB (+{(rss1-rss0)/1024**2:.0f})")

# Verify deep_analyzer was NOT loaded
assert core._deep_analyzer is None, "deep_analyzer should be None when skip_deep_analyzer=True"
print("[PASS] deep_analyzer is None")

# Step 2: Scan a small test contract
test_file = os.path.join(os.path.dirname(__file__), "..", "test_contracts", "vulnerable", "unchecked_call.sol")
if not os.path.exists(test_file):
    # fallback to any .sol
    for root, dirs, files in os.walk(os.path.join(os.path.dirname(__file__), "..", "test_contracts")):
        for f in files:
            if f.endswith(".sol"):
                test_file = os.path.join(root, f)
                break
        if os.path.exists(test_file):
            break

print(f"\nScanning: {os.path.basename(test_file)}")
t0 = time.time()
result = core.deep_scan(test_file)
elapsed = time.time() - t0
rss2 = proc.memory_info().rss
print(f"RSS after scan: {rss2/1024**2:.0f} MB (+{(rss2-rss1)/1024**2:.0f})")
print(f"Scan time: {elapsed:.1f}s")

findings = result.get("all_findings_unified", result.get("findings", []))
print(f"Findings: {len(findings)}")
layers = result.get("layers_used", [])
print(f"Layers: {layers}")

# Verify NO LLM layers
assert "llm_analysis" not in layers, "llm_analysis should not appear when skip_llm=True"
assert "deep_protocol_analysis" not in layers, "deep_protocol_analysis should not appear"
print("[PASS] No LLM layers used")
print(f"\n=== SUCCESS: Pipeline works without LLM, peak RSS={rss2/1024**2:.0f} MB ===")
