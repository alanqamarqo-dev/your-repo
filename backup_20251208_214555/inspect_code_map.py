import os
import ast
import json
from pathlib import Path
from typing import Dict, Any

ROOT = Path(__file__).parent
OUT_PATH = ROOT / "artifacts" / "agl_code_map.json"
TARGET_DIRS = [
    "Self_Improvement",
    "Core_Engines",
    "tools",
    "tests",
]


def is_py_file(path: Path) -> bool:
    return path.is_file() and path.suffix == ".py"


def analyze_file(path: Path) -> Dict[str, Any]:
    rel = path.relative_to(ROOT).as_posix()
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    loc = len(lines)
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return {
            "path": rel,
            "loc": loc,
            "functions": [],
            "classes": [],
            "syntax_ok": False,
        }

    funcs = []
    classes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            funcs.append(node.name)
        elif isinstance(node, ast.AsyncFunctionDef):
            funcs.append(node.name + " (async)")
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)

    return {
        "path": rel,
        "loc": loc,
        "functions": sorted(set(funcs)),
        "classes": sorted(set(classes)),
        "syntax_ok": True,
    }


def main():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    results = []
    for tdir in TARGET_DIRS:
        base = ROOT / tdir
        if not base.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            for fname in filenames:
                if fname.endswith(".py"):
                    fpath = Path(dirpath) / fname
                    info = analyze_file(fpath)
                    results.append(info)

    # sort by path
    results.sort(key=lambda x: x["path"])
    summary = {
        "root": str(ROOT),
        "files": results,
        "total_files": len(results),
        "total_loc": sum(f["loc"] for f in results),
    }
    OUT_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[INFO] saved code map to {OUT_PATH}")
    print(f"[INFO] total_files = {summary['total_files']}, total_loc = {summary['total_loc']}")


if __name__ == "__main__":
    main()
