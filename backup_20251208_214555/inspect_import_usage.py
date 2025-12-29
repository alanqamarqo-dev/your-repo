# inspect_import_usage.py
import os
import ast
from pathlib import Path
from collections import defaultdict
import json

ROOT = Path(__file__).parent
OUT_PATH = ROOT / "artifacts" / "agl_import_usage.json"
TARGET_DIRS = [
    "Self_Improvement",
    "Core_Engines",
    "tools",
]


def iter_py_files():
    for tdir in TARGET_DIRS:
        base = ROOT / tdir
        if not base.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            for fname in filenames:
                if fname.endswith(".py"):
                    yield Path(dirpath) / fname


def analyze_imports(path: Path, module_usage, file_imports):
    rel = path.relative_to(ROOT).as_posix()
    text = path.read_text(encoding="utf-8", errors="ignore")
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.add(node.module.split(".")[0])
    file_imports[rel] = sorted(imported_modules)
    for m in imported_modules:
        module_usage[m] += 1


def main():
    module_usage = defaultdict(int)
    file_imports = {}
    for f in iter_py_files():
        analyze_imports(f, module_usage, file_imports)
    # sort usage descending
    usage_sorted = sorted(module_usage.items(), key=lambda x: x[1], reverse=True)
    data = {
        "module_usage": usage_sorted,
        "file_imports": file_imports,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[INFO] saved import usage to {OUT_PATH}")
    print("[TOP 20 MODULE NAMES BY IMPORT COUNT]")
    for name, cnt in usage_sorted[:20]:
        print(f"- {name}: {cnt}")


if __name__ == "__main__":
    main()
