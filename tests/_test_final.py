"""Final test: Full pipeline with LLM enrichment → JSON output."""

import sys, os, json, time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import logging

logging.disable(logging.CRITICAL)

print("[1] Loading engines...", flush=True)
t0 = time.time()
from agl_security_tool.core import AGLSecurityAudit

audit = AGLSecurityAudit()
print(f"    Loaded in {time.time()-t0:.1f}s", flush=True)

# Show engine status
engines = {
    "Layer1_Analyzer": bool(audit._analyzer),
    "Layer2_Orchestrator": bool(audit._orchestrator),
    "Layer2f_Suite": bool(audit._suite),
    "Layer3_Offensive": bool(audit._engine),
    "Layer4_Detectors": bool(audit._detector_runner),
    "LLM_Ollama": bool(
        audit._orchestrator
        and hasattr(audit._orchestrator, "llm")
        and audit._orchestrator.llm
        and audit._orchestrator.llm.available
    ),
    "LLM_HoloLLM": bool(
        audit._engine
        and hasattr(audit._engine, "holo_brain")
        and audit._engine.holo_brain
    ),
}
for k, v in engines.items():
    print(f"    {k}: {'YES' if v else 'NO'}", flush=True)

# Scan
target = os.path.join(os.path.dirname(__file__), "vulnerable.sol")
print(f"\n[2] Scanning {os.path.basename(target)}...", flush=True)
t1 = time.time()
result = audit.scan(target)
elapsed = time.time() - t1
print(f"    Done in {elapsed:.1f}s", flush=True)
print(f"    Layers: {result.get('layers_used', [])}", flush=True)

# Save full result to JSON
with open("_llm_full_result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
print(f"    Full result saved to _llm_full_result.json", flush=True)

# Show unified findings with LLM enrichment
unified = result.get("all_findings_unified", [])
print(f"\n[3] UNIFIED FINDINGS ({len(unified)}):", flush=True)
llm_enriched_count = 0
for i, f in enumerate(unified, 1):
    sev = f.get("severity", "?").upper()
    title = f.get("title", f.get("text", "Unknown"))
    line = f.get("line", "?")
    conf = f.get("confidence", "?")
    sources = f.get("confirmed_by", [])
    has_llm = "llm_explanation" in f
    has_fix = "fix" in f
    has_poc = "poc" in f

    if has_llm or has_fix or has_poc:
        llm_enriched_count += 1

    print(f"\n  [{i}] [{sev}] L{line}: {title}", flush=True)
    print(f"      Conf: {conf}  Sources: {sources}", flush=True)

    if has_llm:
        print(f"      LLM: {f['llm_explanation'][:200]}", flush=True)
    if has_fix:
        print(f"      FIX: {f['fix'][:200]}", flush=True)
    if has_poc:
        print(f"      POC: {f['poc'][:200]}", flush=True)

# Check for raw LLM response in result
if result.get("llm_raw_response"):
    print(f"\n  [RAW LLM] ({len(result['llm_raw_response'])} chars):", flush=True)
    print(f"  {result['llm_raw_response'][:300]}...", flush=True)

# Summary
sev = result.get("severity_summary", {})
print(f"\n[4] SUMMARY:", flush=True)
print(
    f"    CRITICAL={sev.get('CRITICAL',0)} HIGH={sev.get('HIGH',0)} MEDIUM={sev.get('MEDIUM',0)} LOW={sev.get('LOW',0)}",
    flush=True,
)
print(
    f"    Total: {result.get('total_findings',0)} (before dedup: {result.get('total_before_dedup',0)})",
    flush=True,
)
print(f"    LLM-enriched findings: {llm_enriched_count}", flush=True)
print(f"    Time: {result.get('time_seconds','?')}s", flush=True)
if result.get("warnings"):
    print(f"    Warnings: {result['warnings']}", flush=True)

print(f"\n    TOTAL test time: {time.time()-t0:.1f}s", flush=True)
