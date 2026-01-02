"""Discover dormant Python modules that aren't imported into server_fixed."""

import ast
import os
from pathlib import Path
from typing import Iterable, Set, Tuple


TARGET_SUBDIRS = ("Core_Engines", "Solvers", "Scientific_Systems")


def scan_python_files(base_dir: Path) -> list[Path]:
    """Return all .py files under the configured subdirectories."""

    py_files = []
    for subdir in TARGET_SUBDIRS:
        folder = base_dir / subdir
        if not folder.is_dir():
            continue
        for root, _, files in os.walk(folder):
            for file in files:
                if file.endswith(".py"):
                    py_files.append(Path(root) / file)
    return py_files


def parse_imports(source: str) -> Set[str]:
    """Extract module names imported in the given source text."""

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    imports: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
                imports.add(node.module.split(".")[0])
            for alias in node.names:
                imports.add(alias.name)
                imports.add(alias.name.split(".")[0])
    return imports


def unused_modules(py_files: Iterable[Path], server_fixed_path: Path, repo_root: Path) -> list[Tuple[str, Path]]:
    """Return modules that exist in TARGET_SUBDIRS but are not imported in server_fixed.py."""

    if not server_fixed_path.is_file():
        return []
    with server_fixed_path.open("r", encoding="utf-8") as sf:
        imported = parse_imports(sf.read())

    dormant: list[Tuple[str, Path]] = []
    for path in py_files:
        if path.samefile(server_fixed_path):
            continue
        module_name = path.stem
        relative = path.relative_to(repo_root)
        module_path = str(relative.with_suffix("")).replace(os.sep, ".")
        if (module_name in imported) or (module_path in imported):
            continue
        dormant.append((module_name, path))
    return dormant


def describe_functionality(module_name: str) -> str:
    """Turn a module name into a short intent description."""

    if not module_name:
        return "undetermined capability"
    return module_name.replace("_", " ").title()


def write_report(report_path: Path, unused: Iterable[Tuple[str, Path]]) -> None:
    """Save the dormant modules summary to the requested report path."""

    with report_path.open("w", encoding="utf-8") as report_file:
        unused_list = list(unused)
        report_file.write(f"Found {len(unused_list)} Dormant Modules:\n")
        for module_name, module_path in unused_list:
            functionality = describe_functionality(module_name)
            line = (
                f"{module_name} - Not imported. -> Recommendation: Import {module_name} to enable {functionality}."
            )
            report_file.write(line + "\n")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    repo_copy = repo_root / "repo-copy"
    server_fixed_path = repo_copy / "server_fixed.py"
    report_path = repo_root / "dormant_power.txt"

    py_files = scan_python_files(repo_copy)
    unused = unused_modules(py_files, server_fixed_path, repo_copy)
    write_report(report_path, unused)
    print(f"Report saved to {report_path} ({len(unused)} dormant modules).")


if __name__ == "__main__":
    main()