"""Pytest configuration — exclude standalone scripts and enforce timeouts."""
import pathlib
import threading

import pytest

_here = pathlib.Path(__file__).parent

# Standalone scripts (not pytest tests) — they have def main() instead of test functions
collect_ignore = [
    str(_here / "test_solc_check.py"),
    str(_here / "test_ast_vs_regex.py"),
    str(_here / "test_fix.py"),
    str(_here / "test_no_llm.py"),
    str(_here / "test_layer_breakdown.py"),
    str(_here / "test_tools_standalone.py"),
    str(_here / "test_slither_mythril.py"),
]

# Also ignore all _*.py standalone scripts and helper files
collect_ignore_glob = [
    str(_here / "_*.py"),
    str(_here / "*.txt"),
]


# ── Built-in timeout safety net (no pytest-timeout needed) ──────────
_DEFAULT_TIMEOUT = 120  # seconds per non-slow test


@pytest.hookimpl(trylast=True)
def pytest_runtest_call(item):
    """Kill tests that exceed timeout — prevents infinite hangs."""
    timeout = _DEFAULT_TIMEOUT
    marker = item.get_closest_marker("timeout")
    if marker and marker.args:
        timeout = int(marker.args[0])

    failed = [False]

    def _watchdog():
        failed[0] = True
        import _thread
        _thread.interrupt_main()

    timer = threading.Timer(timeout, _watchdog)
    timer.daemon = True
    timer.start()
    try:
        item.runtest()
    except KeyboardInterrupt:
        if failed[0]:
            raise TimeoutError(
                f"Test '{item.nodeid}' exceeded {timeout}s timeout"
            ) from None
        raise
    finally:
        timer.cancel()

    return True
