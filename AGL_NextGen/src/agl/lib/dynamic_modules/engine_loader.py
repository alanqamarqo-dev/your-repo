"""Dynamic loader that wraps deep engine modules for on-demand invocation."""

import importlib
import sys
from pathlib import Path
from typing import Any


def load_and_run(module_name: str, function_name: str, *args: Any, **kwargs: Any) -> Any:
    """Import `module_name` from the repo and execute `function_name` with the supplied args."""

    repo_root = Path(__file__).resolve().parents[1]
    repo_str = str(repo_root)
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)

    # Ensure the Core_Engines directory is available for deep modules
    core_path = repo_root / "Core_Engines"
    core_str = str(core_path)
    if core_str not in sys.path:
        sys.path.append(core_str)

    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(f"Could not import {module_name}: {exc}") from exc

    func = getattr(module, function_name, None)
    if not callable(func):
        raise AttributeError(f"{module_name}.{function_name} is not callable or missing")

    try:
        return func(*args, **kwargs)
    except Exception as exc:
        raise RuntimeError(f"Error while running {module_name}.{function_name}: {exc}") from exc


def _test_loader() -> None:
    """Simple test that demonstrates invoking Mathematical_Brain if available."""

    candidate_module = "Mathematical_Brain"
    candidate_function = "dummy_function"

    try:
        result = load_and_run(candidate_module, candidate_function)
        print(f"{candidate_module}.{candidate_function} -> {result}")
    except Exception as exc:
        print(f"Test load failed: {exc}")


if __name__ == "__main__":
    _test_loader()