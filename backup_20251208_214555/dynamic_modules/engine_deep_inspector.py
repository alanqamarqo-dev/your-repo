"""List public methods within the Mathematical_Brain classes."""

import ast
from pathlib import Path


class EngineDeepInspector(ast.NodeVisitor):
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        for method in node.body:
            if not isinstance(method, ast.FunctionDef):
                continue
            if method.name.startswith("_"):
                continue
            print(f"{node.name}.{method.name}")


def inspect_module(module_path: Path) -> None:
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source, module_path.as_posix())
    inspector = EngineDeepInspector()
    inspector.visit(tree)


if __name__ == "__main__":
    inspect_module(Path(r"D:\AGL\repo-copy\Core_Engines\Mathematical_Brain.py"))