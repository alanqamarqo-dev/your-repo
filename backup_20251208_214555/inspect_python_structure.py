import os
import json
import ast
from pathlib import Path

# Root and artifacts
ROOT = Path(__file__).resolve().parent
ARTIFACTS_DIR = ROOT / "artifacts"
ARTIFACTS_DIR.mkdir(exist_ok=True)

STRUCT_PATH = ARTIFACTS_DIR / "python_code_structure.json"
IMPORT_GRAPH_PATH = ARTIFACTS_DIR / "python_import_graph.json"


def iter_python_files(root: Path):
    """
    Walk all .py files under root, skipping common virtual/dev folders.
    Yields (full_path, rel_path)
    """
    for dirpath, dirnames, filenames in os.walk(root):
        dirpath = Path(dirpath)
        try:
            rel_dir = dirpath.relative_to(root)
        except Exception:
            rel_dir = Path(".")

        # skip common folders
        if any(part in {".git", ".venv", "venv", "__pycache__", ".idea", ".vscode"} for part in rel_dir.parts):
            continue

        for name in filenames:
            if not name.endswith(".py"):
                continue
            full = dirpath / name
            rel = full.relative_to(root)
            yield full, rel


def build_module_index(root: Path):
    """
    Build simple module index: path -> module name (dot-separated).
    E.g. Self_Improvement/Knowledge_Graph.py -> Self_Improvement.Knowledge_Graph
    """
    index = {}
    for full, rel in iter_python_files(root):
        parts = list(rel.parts)
        # handle __init__.py as package
        if parts[-1] == "__init__.py":
            mod_name = ".".join(parts[:-1])
        else:
            mod_name = ".".join(parts).replace(".py", "")
        index[mod_name] = str(rel).replace("\\", "/")
    return index


def resolve_import_to_file(module_name: str, module_index: dict):
    """
    Try to resolve an import/module name to a file path in module_index.
    Returns path string or None.
    """
    if not module_name:
        return None

    if module_name in module_index:
        return module_index[module_name]

    parts = module_name.split(".")
    while parts:
        candidate = ".".join(parts)
        if candidate in module_index:
            return module_index[candidate]
        parts.pop()
    return None


def analyze_python_file(full_path: Path, rel_path: Path, module_index: dict):
    """
    Analyze one .py file and collect:
      - classes (name, lineno, methods)
      - functions (name, lineno)
      - loops (for/while) with lineno
      - imports (type, module, name, lineno)
      - internal_deps (resolved files) and external_deps
    """
    info = {
        "path": str(rel_path).replace("\\", "/"),
        "module": None,
        "classes": [],
        "functions": [],
        "loops": [],
        "imports": [],
        "internal_deps": [],
        "external_deps": [],
        "parse_error": None,
    }

    parts = list(rel_path.parts)
    if parts[-1] == "__init__.py":
        info["module"] = ".".join(parts[:-1])
    else:
        info["module"] = ".".join(parts).replace(".py", "")

    try:
        src = full_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        info["parse_error"] = f"read_error: {e}"
        return info

    try:
        tree = ast.parse(src, filename=str(rel_path))
    except Exception as e:
        info["parse_error"] = f"syntax_error: {e}"
        return info

    # 1) classes and functions at module level
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            methods = [
                m.name for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            info["classes"].append({
                "name": node.name,
                "lineno": node.lineno,
                "methods": methods,
            })
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            info["functions"].append({
                "name": node.name,
                "lineno": node.lineno,
            })

    # 2) loops anywhere
    for node in ast.walk(tree):
        if isinstance(node, (ast.For, ast.AsyncFor)):
            loop_type = "for"
        elif isinstance(node, ast.While):
            loop_type = "while"
        else:
            continue

        info["loops"].append({
            "type": loop_type,
            "lineno": getattr(node, "lineno", None),
        })

    # 3) imports
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name
                imported_modules.add(mod)
                info["imports"].append({
                    "type": "import",
                    "module": mod,
                    "name": None,
                    "lineno": node.lineno,
                })
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            for alias in node.names:
                name = alias.name
                if base:
                    mod = f"{base}.{name}"
                else:
                    mod = name
                imported_modules.add(mod)
                info["imports"].append({
                    "type": "from",
                    "module": base,
                    "name": name,
                    "lineno": node.lineno,
                })

    # 4) classify internal vs external
    internal = set()
    external = set()
    for mod in imported_modules:
        resolved = resolve_import_to_file(mod, module_index)
        if resolved:
            internal.add(resolved)
        else:
            external.add(mod)

    info["internal_deps"] = sorted(internal)
    info["external_deps"] = sorted(external)

    return info


def main():
    module_index = build_module_index(ROOT)

    all_infos = []
    for full, rel in iter_python_files(ROOT):
        fi = analyze_python_file(full, rel, module_index)
        all_infos.append(fi)

    # build import graph edges
    edges = []
    for fi in all_infos:
        src_path = fi["path"]
        for target in fi.get("internal_deps", []):
            edges.append({"from": src_path, "to": target})

    # write outputs
    try:
        STRUCT_PATH.write_text(
            json.dumps({"root": str(ROOT), "total_files": len(all_infos), "files": all_infos}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as e:
        print("Failed to write structure:", e)

    try:
        IMPORT_GRAPH_PATH.write_text(json.dumps({"root": str(ROOT), "edges": edges}, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print("Failed to write import graph:", e)

    # quick summary
    print("=== Python structure scan complete ===")
    print(f"Root: {ROOT}")
    print(f"Total .py files: {len(all_infos)}")

    ranked = [
        (fi["path"], len(fi.get("classes", [])) + len(fi.get("functions", [])))
        for fi in all_infos
    ]
    ranked.sort(key=lambda x: x[1], reverse=True)
    print("\n== Top 10 files by (classes+functions) ==")
    for path, count in ranked[:10]:
        print(f"- {path:60s}  defs={count}")


if __name__ == "__main__":
    main()
