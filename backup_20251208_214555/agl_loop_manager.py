#!/usr/bin/env python3
"""AGL Loop Manager (nightly-like pipeline).

This entry point keeps the AGI daytime server running separately (start the
`server_fixed.py`/uvicorn process beforehand) and then cycles through:
- knowledge harvesting (workers/knowledge_harvester.py)
- night-cycle analysis (night_cycle.py)
- self-engineering work (scripts/self_engineer_run.py)
- system audit (workers/generate_system_audit.py)

Each iteration produces a fresh `artifacts/system_audit.json`, which the
server now loads at startup as the "short-term conscious memory" for the
next run.
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON = Path(sys.executable)

LOOP_STEPS = [
    (Path("repo-copy") / "workers" / "knowledge_harvester.py", "Harvest knowledge and facts"),
    (Path("night_cycle.py"), "Dream/night-cycle tuning"),
    (Path("repo-copy") / "scripts" / "self_engineer_run.py", "Self-improvement run"),
    (Path("workers") / "generate_system_audit.py", "Generate system audit"),
]
SLEEP_SECONDS = 5


def run_process(script_path: Path, description: str) -> bool:
    if not script_path.exists():
        print(f"⚠️ Chapter missing: {script_path} ({description})")
        return False

    cmd = [str(PYTHON), str(script_path)]
    print(f"→ {description}: {cmd}")

    try:
        subprocess.run(cmd, cwd=ROOT, check=True)
        return True
    except subprocess.CalledProcessError as exc:
        print(f"⚠️ {description} failed (exit {exc.returncode})")
    except Exception as exc:
        print(f"⚠️ {description} unexpected error: {exc}")
    return False


def main() -> None:
    print("🚀 Starting AGL Loop Manager. Ensure server_fixed.py (or uvicorn server) is already running.")

    while True:
        for script, description in LOOP_STEPS:
            # fix script path relative to repo root
            absolute_path = (ROOT / script).resolve()
            run_process(absolute_path, description)

        print(f"💤 Loop complete. Sleeping for {SLEEP_SECONDS} seconds before next day...")
        time.sleep(SLEEP_SECONDS)


if __name__ == "__main__":
    main()
