"""Detailed per-layer finding breakdown for a test contract."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from agl_security_tool.core import AGLSecurityAudit

core = AGLSecurityAudit(config={"skip_llm": True, "skip_deep_analyzer": True})
r = core.deep_scan(r"d:\AGL\agl_security_tool\test_contracts\vulnerable\unchecked_call.sol")

print("=== LAYERS USED ===")
for l in r.get("layers_used", []):
    print(f"  {l}")

print("\n=== FINDING COUNTS ===")
print(f"  all_findings_unified: {len(r.get('all_findings_unified', []))}")
print(f"  findings (pattern):   {len(r.get('findings', []))}")
print(f"  suite_findings:       {len(r.get('suite_findings', []))}")
print(f"  detector_findings:    {len(r.get('detector_findings', []))}")
print(f"  symbolic_findings:    {len(r.get('symbolic_findings', []))}")

print("\n=== SEVERITY SUMMARY ===")
for k, v in r.get("severity_summary", {}).items():
    print(f"  {k}: {v}")

print("\n=== ORCHESTRATOR DETAILS ===")
orch = r.get("orchestrator_results", {})
if orch:
    for tool, data in orch.items():
        if isinstance(data, list):
            print(f"  {tool}: {len(data)} findings")
        elif isinstance(data, dict):
            cnt = len(data.get("findings", data.get("issues", []))) if isinstance(data, dict) else 0
            print(f"  {tool}: {cnt} findings")
        else:
            print(f"  {tool}: {type(data).__name__}")

print("\n=== RISK SCORING ===")
for f in r.get("all_findings_unified", [])[:5]:
    sev = f.get("severity", "?")
    orig_sev = f.get("original_severity", "?")
    title = f.get("title", "?")[:60]
    conf = f.get("confidence", 0)
    risk = f.get("risk_breakdown", {})
    prob = risk.get("probability", "?") if isinstance(risk, dict) else "?"
    print(f"  [{sev}] (orig={orig_sev}, conf={conf:.2f}, prob={prob}) {title}")

print("\n=== WARNINGS ===")
for w in r.get("warnings", []):
    print(f"  ⚠ {w}")

print("\n=== TOOL BACKEND NOTES ===")
for k in ("tool_results", "backend_notes", "slither_result", "mythril_result"):
    if k in r:
        print(f"  {k}: {str(r[k])[:200]}")
