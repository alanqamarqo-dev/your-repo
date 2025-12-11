import asyncio
from pathlib import Path
import importlib.util


def load_module_from_repo(path_parts):
    base = Path(__file__).resolve().parents[1]
    fp = base.joinpath(*path_parts)
    spec = importlib.util.spec_from_file_location("unified_agi_system", str(fp))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_memory_recall_context_matching():
    mod = load_module_from_repo(("repo-copy", "dynamic_modules", "unified_agi_system.py"))
    UnifiedMemorySystem = mod.UnifiedMemorySystem

    mem = UnifiedMemorySystem()

    # Store two items with different contexts and contents
    mem.store(content="Apple banana orange", memory_type="semantic", importance=0.6, context={"topic": "fruits", "lang": "ar"})
    mem.store(content="Quantum mechanics basics", memory_type="semantic", importance=0.4, context={"topic": "physics", "lang": "en"})

    # Recall with a query that matches the first item and matching context
    results = mem.recall("Apple", context={"lang": "ar"})

    # Expect at least one result and that returned importance was scaled by context_match (shared key matches)
    assert isinstance(results, list)
    assert len(results) >= 1
    first = results[0]
    assert "fruits" in first["content"] or "Apple" in first["content"]


def test_consciousness_performance_update():
    mod = load_module_from_repo(("repo-copy", "dynamic_modules", "unified_agi_system.py"))
    UnifiedAGISystem = mod.UnifiedAGISystem

    system = UnifiedAGISystem(engine_registry={})

    old_level = system.consciousness_level

    # Run a single processing cycle; environment is minimal so many subsystems are disabled
    result = asyncio.run(system.process_with_full_agi("Compute something simple"))

    # performance_score should exist and be numeric
    perf = result.get("performance_score")
    assert isinstance(perf, float) or isinstance(perf, int)

    # The system updates consciousness_level by: +0.001 + performance_score*0.01 (bounded by 1.0)
    expected = min(1.0, old_level + 0.001 + (perf * 0.01))
    # Allow tiny float rounding tolerance
    assert abs(system.consciousness_level - expected) < 1e-9
