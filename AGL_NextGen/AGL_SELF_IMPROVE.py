from __future__ import annotations

import os
import sys

# allow running from repo root
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from agl.bench.self_improve import SelfImproveConfig, run_self_improve


def _configure_utf8_console() -> None:
    if os.name != "nt":
        return

    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

    try:
        import ctypes

        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        ctypes.windll.kernel32.SetConsoleCP(65001)
    except Exception:
        pass


def main() -> int:
    _configure_utf8_console()
    suites = (os.getenv("AGL_SELF_IMPROVE_SUITES", "deterministic,causal,planning,planner") or "").strip()
    suite_list = [s.strip() for s in suites.split(",") if s.strip()]

    repeats = int(os.getenv("AGL_BENCH_REPEATS", "3"))
    use_core = os.getenv("AGL_BENCH_USE_CORE", "0") in ("1", "true", "True")

    max_iters = int(os.getenv("AGL_SELF_IMPROVE_ITERS", "1"))
    target_accuracy = float(os.getenv("AGL_SELF_IMPROVE_TARGET", "1.0"))

    config = SelfImproveConfig(
        suites=suite_list,
        repeats=repeats,
        use_core_consciousness=use_core,
        max_iters=max_iters,
        target_accuracy=target_accuracy,
    )

    iters = run_self_improve(config)

    # Print a compact last-pass summary.
    if iters:
        last_iter = iters[-1]
        print({"suite": last_iter.suite, "summary": last_iter.summary, "notes": last_iter.notes})

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
