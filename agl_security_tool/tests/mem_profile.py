"""Memory profiler — measures RAM per engine."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import tracemalloc, gc
import psutil

tracemalloc.start()

def mb(bytes_val):
    return f"{bytes_val / 1024**2:.1f} MB"

print("=== AGL Pipeline Memory Profile ===")
print(f"System RAM: {psutil.virtual_memory().total / 1024**3:.1f} GB")
print(f"Available: {psutil.virtual_memory().available / 1024**3:.1f} GB")
print()

proc = psutil.Process()
engines = {}

def measure(label, fn):
    gc.collect()
    before = tracemalloc.get_traced_memory()[0]
    rss_before = proc.memory_info().rss
    try:
        result = fn()
        gc.collect()
        after = tracemalloc.get_traced_memory()[0]
        rss_after = proc.memory_info().rss
        traced_delta = after - before
        rss_delta = rss_after - rss_before
        print(f"  {label}: traced={mb(traced_delta)}, RSS delta={mb(rss_delta)}, total RSS={mb(rss_after)}")
        return result
    except Exception as e:
        print(f"  {label}: FAILED - {str(e)[:100]}")
        return None

# === Imports ===
print("\n--- Engine Imports ---")

measure("1. SecurityScanner (core)", 
    lambda: __import__("agl_security_tool.core", fromlist=["SecurityScanner"]))

measure("2. Z3 Symbolic Engine",
    lambda: __import__("agl_security_tool.z3_symbolic_engine", fromlist=["Z3SymbolicEngine"]))

measure("3. Detectors + AST Parser",
    lambda: __import__("agl_security_tool.detectors.solidity_ast_parser", fromlist=["SolidityASTParserFull"]))

measure("4. Heikal Math",
    lambda: __import__("agl_security_tool.heikal_math", fromlist=["HeikalTunnelingScorer"]))

measure("5. Attack Engine",
    lambda: __import__("agl_security_tool.attack_engine", fromlist=["AttackEngine"]))

measure("6. Search Engine",
    lambda: __import__("agl_security_tool.search_engine", fromlist=["SearchEngine"]))

measure("7. Contract Intelligence",
    lambda: __import__("agl_security_tool.contract_intelligence", fromlist=["ContractIntelligence"]))

measure("8. Deep Analyzer",
    lambda: __import__("agl_security_tool.deep_analyzer", fromlist=["DeepAnalyzer"]))

measure("9. Action Space",
    lambda: __import__("agl_security_tool.action_space", fromlist=["ActionSpaceBuilder"]))

measure("10. State Extraction",
    lambda: __import__("agl_security_tool.state_extraction", fromlist=["StateExtractionEngine"]))

measure("11. Exploit Reasoning",
    lambda: __import__("agl_security_tool.exploit_reasoning", fromlist=["ExploitReasoning"]))

measure("12. Risk Core",
    lambda: __import__("agl_security_tool.risk_core", fromlist=["RiskCore"]))

# === Now test actual init ===
print("\n--- Engine Initialization ---")

from agl_security_tool.audit_pipeline import init_engines
engines_result = measure("init_engines()", lambda: init_engines())

print(f"\n--- Final ---")
final = tracemalloc.get_traced_memory()
print(f"Traced: current={mb(final[0])}, peak={mb(final[1])}")
print(f"Process RSS: {mb(proc.memory_info().rss)}")

# Top 10 memory consumers
print("\n--- Top 10 Memory Allocations ---")
snapshot = tracemalloc.take_snapshot()
stats = snapshot.statistics('lineno')
for s in stats[:10]:
    print(f"  {s}")
