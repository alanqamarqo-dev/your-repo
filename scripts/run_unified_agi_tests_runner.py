import importlib.util
from pathlib import Path
import sys


def load_module(path):
    spec = importlib.util.spec_from_file_location("test_mod", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    base = Path(__file__).resolve().parents[1]
    test_path = base / "tests" / "test_unified_agi_system_math.py"
    if not test_path.exists():
        print("Test file not found:", test_path)
        sys.exit(2)

    mod = load_module(test_path)

    tests = [
        "test_memory_recall_context_matching",
        "test_consciousness_performance_update",
    ]

    for t in tests:
        print(f"Running {t}...", end=" ")
        try:
            getattr(mod, t)()
            print("OK")
        except AssertionError as e:
            print("FAILED: AssertionError", e)
            raise
        except Exception as e:
            print("FAILED: Exception", e)
            raise

    print("All tests finished.")


if __name__ == '__main__':
    main()
