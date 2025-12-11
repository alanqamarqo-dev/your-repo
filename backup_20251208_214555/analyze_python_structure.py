import json
from pathlib import Path

STRUCT_PATH = Path("artifacts/python_code_structure.json")

PROJECT_ROOT_PREFIXES = (
    "Self_Improvement/",
    "Core_",
    "Integration_Layer/",
    "Core_Memory/",
    "tools/",
    "scripts/",
    "tests/",
    "Knowledge_Graph.py",
)


def is_project_file(path: str) -> bool:
    # normalize
    p = path.replace('\\', '/')
    # exclude venv/embedded snapshots
    if p.startswith('.venv') or '.venv_embed' in p:
        return False
    if p.startswith('1762') or '/1762' in p:
        return False
    if p.startswith('.tmp_') or p.startswith('.temp_'):
        return False
    # keep if starts with any project prefix or exact match
    for prefix in PROJECT_ROOT_PREFIXES:
        if p.startswith(prefix) or p == prefix:
            return True
    return False


def load_structure():
    data = json.loads(STRUCT_PATH.read_text(encoding="utf-8"))
    return data


def summarize_top_project_files(files, top_n=30):
    project_files = [f for f in files if is_project_file(f["path"]) ]
    scored = []
    for f in project_files:
        defs_count = len(f.get("classes", [])) + len(f.get("functions", []))
        scored.append((defs_count, f["path"]))
    scored.sort(reverse=True)
    print(f"Total project .py files (filtered): {len(project_files)}")
    print(f"Top {top_n} files by (classes+functions):")
    for defs_count, path in scored[:top_n]:
        print(f"- {path:60} defs={defs_count}")
    return project_files


def show_deps(files, target_path: str):
    """Print dependencies for a target file: what it imports and who imports it."""
    print("\n=== Dependency summary for:", target_path, "===\n")
    target = None
    for f in files:
        if f["path"] == target_path:
            target = f
            break
    if not target:
        print("File not found in filtered project files.")
        return

    print("Internal deps (this file imports):")
    for dep in target.get("internal_deps", []):
        print(" ->", dep)

    print("\nExternal deps (external modules):")
    for dep in target.get("external_deps", []):
        print(" ->", dep)

    print("\nFiles that depend ON this file (import it):")
    for f in files:
        if target_path in f.get("internal_deps", []):
            print(" <-", f["path"])


def main():
    if not STRUCT_PATH.exists():
        print("Missing artifacts/python_code_structure.json — run inspect_python_structure.py first.")
        return
    data = load_structure()
    files = data.get("files", [])
    print("Root:", data.get("root"))
    print("Total .py (ALL, including venv):", data.get("total_files"))

    project_files = summarize_top_project_files(files, top_n=30)

    targets = [
        "Self_Improvement/Knowledge_Graph.py",
        "Self_Improvement/hosted_llm_adapter.py",
        "Integration_Layer/Conversation_Manager.py",
    ]
    for target in targets:
        show_deps(project_files, target)


if __name__ == "__main__":
    main()
