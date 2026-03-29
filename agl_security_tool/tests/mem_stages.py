"""Memory profiler — measures RAM per pipeline STAGE on real contracts."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import tracemalloc, gc, time
import psutil

tracemalloc.start()
proc = psutil.Process()

def snap(label):
    gc.collect()
    traced = tracemalloc.get_traced_memory()
    rss = proc.memory_info().rss
    print(f"  [{label}] traced={traced[0]/1024**2:.1f}MB (peak={traced[1]/1024**2:.1f}MB), RSS={rss/1024**2:.0f}MB")
    return rss

print("=== AGL Pipeline Stage-by-Stage Memory ===")
print(f"Available RAM: {psutil.virtual_memory().available / 1024**3:.1f} GB")
print()

# Step 1: Load engines
snap("BEFORE load_engines")
from agl_security_tool.audit_pipeline import load_engines, discover_project
from agl_security_tool.audit_pipeline import run_shared_parsing, run_core_deep_scan
from agl_security_tool.audit_pipeline import run_z3_symbolic, run_state_extraction
from agl_security_tool.audit_pipeline import run_detectors, run_exploit_reasoning
from agl_security_tool.audit_pipeline import run_heikal_math, deduplicate_cross_layer

target = os.path.join(os.path.dirname(__file__), "..", "test_contracts")
engines = load_engines(target, core_config={"skip_llm": True, "skip_deep_analyzer": True})
snap("AFTER load_engines")

# Step 2: Discover
project = discover_project(target, config={
    "exclude_tests": True, "exclude_mocks": True, "scan_dependencies": False
})
project["project_path"] = target
n_files = len(project["contracts"])
print(f"\n  Project: {n_files} files")
snap("AFTER discover_project")

# Step 2.5: Shared parsing
print("\n--- Stage 2.5: Shared Parsing ---")
t0 = time.time()
shared = run_shared_parsing(engines, project)
print(f"  Time: {time.time()-t0:.1f}s")
rss1 = snap("AFTER shared_parsing")

# Step 3: Core deep scan
print("\n--- Stage 3: Core Deep Scan ---")
t0 = time.time()
deep = run_core_deep_scan(engines, project, shared_parse=shared)
print(f"  Time: {time.time()-t0:.1f}s")
rss2 = snap("AFTER core_deep_scan")
print(f"  ↑ Delta: +{(rss2-rss1)/1024**2:.0f} MB")

# Step 4: Z3
print("\n--- Stage 4: Z3 Symbolic ---")
t0 = time.time()
z3_res = run_z3_symbolic(engines, project, shared_parse=shared)
print(f"  Time: {time.time()-t0:.1f}s")
rss3 = snap("AFTER z3_symbolic")
print(f"  ↑ Delta: +{(rss3-rss2)/1024**2:.0f} MB")

# Step 5: State extraction
print("\n--- Stage 5: State Extraction ---")
t0 = time.time()
state = run_state_extraction(engines, project, shared_parse=shared)
print(f"  Time: {time.time()-t0:.1f}s")
rss4 = snap("AFTER state_extraction")
print(f"  ↑ Delta: +{(rss4-rss3)/1024**2:.0f} MB")

# Step 6: Detectors
print("\n--- Stage 6: Detectors ---")
t0 = time.time()
det = run_detectors(engines, project, shared_parse=shared)
print(f"  Time: {time.time()-t0:.1f}s")
rss5 = snap("AFTER detectors")
print(f"  ↑ Delta: +{(rss5-rss4)/1024**2:.0f} MB")

# Step 7: Exploit Reasoning
print("\n--- Stage 7: Exploit Reasoning ---")
t0 = time.time()
exploit = run_exploit_reasoning(engines, project, deep_scan_results=deep, shared_parse=shared)
print(f"  Time: {time.time()-t0:.1f}s")
rss6 = snap("AFTER exploit_reasoning")
print(f"  ↑ Delta: +{(rss6-rss5)/1024**2:.0f} MB")

# Step 8: Heikal Math
print("\n--- Stage 8: Heikal Math ---")
t0 = time.time()
heikal = run_heikal_math(engines, project, shared_parse=shared)
print(f"  Time: {time.time()-t0:.1f}s")
rss7 = snap("AFTER heikal_math")
print(f"  ↑ Delta: +{(rss7-rss6)/1024**2:.0f} MB")

# Dedup
print("\n--- Cross-layer Dedup ---")
all_results = {
    "deep_scan": deep, "z3_symbolic": z3_res, "state_extraction": state,
    "detectors": det, "exploit_reasoning": exploit, "heikal_math": heikal,
}
deduped = deduplicate_cross_layer(all_results, shared)
rss8 = snap("AFTER dedup")

print(f"\n{'='*60}")
print(f"  TOTAL PEAK RSS: {proc.memory_info().rss/1024**2:.0f} MB")
print(f"  Traced peak: {tracemalloc.get_traced_memory()[1]/1024**2:.0f} MB")

# Top allocations
print("\n--- Top 15 Memory Allocations ---")
stats = tracemalloc.take_snapshot().statistics('lineno')
for s in stats[:15]:
    print(f"  {s}")
