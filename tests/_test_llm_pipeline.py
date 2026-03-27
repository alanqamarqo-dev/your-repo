"""Test: Full pipeline including LLM enrichment layer."""
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agl_security_tool"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "AGL_NextGen", "src"))

from agl_security_tool.core import AGLSecurityAudit

print("=" * 70)
print("  AGL FULL PIPELINE TEST — INCLUDING LLM ANALYSIS")
print("=" * 70)

# Initialize
t0 = time.time()
audit = AGLSecurityAudit()
print(f"\n[INIT] {time.time()-t0:.1f}s")

# Check engines
print(f"  Layer 1 (Analyzer):    {'✅' if audit._analyzer else '❌'}")
print(f"  Layer 2 (Orchestrator): {'✅' if audit._orchestrator else '❌'}")
print(f"  Layer 2f (Suite):      {'✅' if audit._suite else '❌'}")
print(f"  Layer 3 (Offensive):   {'✅' if audit._engine else '❌'}")
print(f"  Layer 4 (22 Detectors): {'✅' if audit._detector_runner else '❌'}")

# Check LLM availability
llm_status = "❌ Not available"
if audit._orchestrator and hasattr(audit._orchestrator, 'llm') and audit._orchestrator.llm:
    if audit._orchestrator.llm.available:
        llm_status = "✅ Ollama (orchestrator LLMBackend)"
    else:
        llm_status = "⚠️ Ollama DOWN — will try HoloLLM fallback"
elif audit._engine and hasattr(audit._engine, 'holo_brain') and audit._engine.holo_brain:
    llm_status = "✅ HolographicLLM (offensive engine)"
print(f"  Layer 5 (LLM):         {llm_status}")

# Scan vulnerable.sol
target = os.path.join(os.path.dirname(__file__), "vulnerable.sol")
if not os.path.exists(target):
    print(f"\n❌ File not found: {target}")
    sys.exit(1)

print(f"\n[SCAN] {target}")
t1 = time.time()
result = audit.scan(target)
elapsed = time.time() - t1

print(f"[DONE] {elapsed:.1f}s")
print(f"\n  Layers: {result.get('layers_used', [])}")
print(f"  Total unified: {result.get('total_findings', 0)}")
print(f"  Before dedup:  {result.get('total_before_dedup', 0)}")
print(f"  Duplicates removed: {result.get('duplicates_removed', 0)}")

sev = result.get("severity_summary", {})
print(f"\n  CRITICAL: {sev.get('CRITICAL',0)}  HIGH: {sev.get('HIGH',0)}  MEDIUM: {sev.get('MEDIUM',0)}  LOW: {sev.get('LOW',0)}")

# Show unified findings with LLM enrichment
print("\n" + "=" * 70)
print("  UNIFIED FINDINGS (with LLM enrichment)")
print("=" * 70)
for i, f in enumerate(result.get("all_findings_unified", []), 1):
    sev = f.get("severity", "?").upper()
    title = f.get("title", f.get("text", "Unknown"))
    line = f.get("line", "?")
    conf = f.get("confidence", "?")
    sources = f.get("confirmed_by", [])
    print(f"\n  [{i}] [{sev}] L{line}: {title}")
    print(f"      Confidence: {conf}  Sources: {sources}")
    
    # LLM enrichment fields
    if f.get("llm_explanation"):
        print(f"      🧠 LLM Explanation: {f['llm_explanation'][:200]}")
    if f.get("fix"):
        print(f"      🔧 Fix: {f['fix'][:200]}")
    if f.get("poc"):
        print(f"      💥 PoC: {f['poc'][:200]}")

# Warnings
warnings = result.get("warnings", [])
if warnings:
    print(f"\n⚠️ Warnings ({len(warnings)}):")
    for w in warnings:
        print(f"  - {w}")

print(f"\n{'='*70}")
print(f"  Total time: {time.time()-t0:.1f}s")
print(f"{'='*70}")
