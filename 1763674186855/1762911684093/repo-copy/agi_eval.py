# Thin shim module to expose the scoring WEIGHTS and gate them by env var.
from __future__ import annotations
import os

# Baseline weights (used in normal runs). Ensure fewshot is non-zero for baseline
# so tests can validate the non-scaffold behavior.
BASELINE_WEIGHTS = {
    "flex": 0.40,
    "philo": 0.20,
    "fewshot": 0.05,
    "creative": 0.20,
    "self": 0.10,
    "transfer": 0.05,
}

# Scaffold / CI-adjusted weights (used only when AGL_TEST_SCAFFOLD_FORCE=1).
SCAFFOLD_WEIGHTS = {
    "flex": 0.43,
    "philo": 0.105,
    "fewshot": 0.00,
    "creative": 0.295,
    "self": 0.10,
    "transfer": 0.07,
}

WEIGHTS = SCAFFOLD_WEIGHTS if os.environ.get("AGL_TEST_SCAFFOLD_FORCE", "0") == "1" else BASELINE_WEIGHTS

def current_weights():
    """Return the active weights dict (copy by value)."""
    return dict(WEIGHTS)
