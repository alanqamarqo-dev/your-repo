"""Pytest configuration — exclude standalone scripts that call sys.exit at module level."""
import pathlib

_here = pathlib.Path(__file__).parent

# Standalone scripts (not pytest tests) — they call sys.exit() at module level
collect_ignore = [
    str(_here / "_test_attack_engine.py"),
    str(_here / "_test_llm_minimal.py"),
    str(_here / "_test_llm_pipeline.py"),
    str(_here / "_test_temporal_model.py"),
    str(_here / "_test_tool_usability.py"),
    str(_here / "ci_run_all.py"),
    str(_here / "diagnose_layers.py"),
    str(_here / "test_solc_check.py"),
    str(_here / "test_ast_vs_regex.py"),
    str(_here / "test_fix.py"),
    str(_here / "check_func_match.py"),
    str(_here / "diagnose_layers_v2.py"),
    str(_here / "test_no_llm.py"),
    str(_here / "test_layer_breakdown.py"),
    str(_here / "test_layers_1_to_4.py"),
]

# Also ignore all _test_* and _*.py standalone scripts via glob
collect_ignore_glob = [
    str(_here / "_*.py"),
    str(_here / "*.txt"),
]
