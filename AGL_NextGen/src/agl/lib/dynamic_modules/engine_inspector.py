"""Inspect the Mathematical_Brain module for available entry points."""

import ast
from pathlib import Path


class Inspector(ast.NodeVisitor):
    def visit_FunctionDef(self, node: ast.FunctionDef):
        print(f"Function: {node.name}")

    def visit_ClassDef(self, node: ast.ClassDef):
        print(f"Class: {node.name}")


def inspect_module(module_path: Path) -> None:
    try:
        source = module_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"File not found: {module_path}")
        return

    tree = ast.parse(source, module_path.as_posix())
    inspector = Inspector()
    inspector.visit(tree)


if __name__ == "__main__":
    inspect_module(Path(r"D:\AGL\repo-copy\Core_Engines\Mathematical_Brain.py"))