import argparse, ast, os, sys, json, pathlib, re
from typing import Dict, List, Tuple

EXCLUDE_DIRS = {
    ".venv", "venv", "__pycache__", ".git", "stubs", "site-packages",
    "tests/lint", "AGL/rag"  # عدّل بما يناسبك
}

# حدود/أسماء شائعة سنحوّلها تلقائياً عند رصدها:
KW_MAP = {
    "k": ("AGL_K_DEFAULT", 3),
    "top_k": ("AGL_TOP_K", 5),
    "limit": ("AGL_LIMIT", 20),
    "max_steps": ("AGL_MAX_STEPS", 8),
    "max_tokens": ("AGL_MAX_TOKENS", 512),
}

# سلايس عرض شائعة -> أسماء مناسبة:
SLICE_CANDIDATES = {
    20: ("AGL_PREVIEW_20", 20),
    120: ("AGL_PREVIEW_120", 120),
    500: ("AGL_PREVIEW_500", 500),
    1000: ("AGL_PREVIEW_1000", 1000),
    1200: ("AGL_PREVIEW_1200", 1200),
}

HEADER_SNIPPET = """# === AGL auto-injected knobs (idempotent) ===
try:
    import os
    def _to_int(name, default):
        try:
            return int(os.environ.get(name, str(default)))
        except Exception:
            return default
except Exception:
    def _to_int(name, default): return default
"""

def should_skip(path: pathlib.Path) -> bool:
    parts = set(path.parts)
    return any(d in parts for d in EXCLUDE_DIRS)

class Rewriter(ast.NodeTransformer):
    def __init__(self):
        super().__init__()
        self.knobs: Dict[str, int] = {}   # name -> default
        self.changed = False

    # 1) keyword args like top_k=5
    def visit_keyword(self, node: ast.keyword):
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, int):
            if node.arg in KW_MAP:
                name, default = KW_MAP[node.arg]
                self._ensure_knob(name, default)
                self.changed = True
                return ast.keyword(arg=node.arg, value=ast.Name(id=f"_{name}", ctx=ast.Load()))
        return self.generic_visit(node)

    # 2) slices like x[:120]
    def visit_Subscript(self, node: ast.Subscript):
        self.generic_visit(node)
        # Only handle slices like [:N]
        if isinstance(node.slice, ast.Slice):
            up = node.slice.upper
            if isinstance(up, ast.Constant) and isinstance(up.value, int) and up.value in SLICE_CANDIDATES:
                name, default = SLICE_CANDIDATES[up.value]
                self._ensure_knob(name, default)
                self.changed = True
                node.slice.upper = ast.Name(id=f"_{name}", ctx=ast.Load())
        return node

    def _ensure_knob(self, name, default):
        self.knobs[name] = self.knobs.get(name, default)

def inject_header_and_knobs(src_code: str, knobs: Dict[str, int]) -> str:
    # إذا كان الـ HEADER موجود مسبقاً لا نعيد إدخاله
    header_present = "AGL auto-injected knobs (idempotent)" in src_code
    if not header_present:
        src_code = HEADER_SNIPPET + "\n" + src_code

    # تأكد أن _to_int معرّف قبل الاستخدام (الـ HEADER يقوم بذلك)
    # أدرج تعريفات _AGL_* (idempotent):
    lines = src_code.splitlines()
    insert_at = 0
    # بعد نهاية الـ HEADER كاملة (إذا وُجد)
    for i, line in enumerate(lines[:200]):
        if "AGL auto-injected knobs (idempotent)" in line:
            # compute insert point as after the full header snippet
            header_lines = HEADER_SNIPPET.splitlines()
            insert_at = i + len(header_lines)
            break

    def knob_line(name, default):
        return f"_{name} = _to_int('{name}', {default})"

    new_knobs_block = []
    for name, default in knobs.items():
        pat = re.compile(rf"_{re.escape(name)}\s*=\s*_to_int\(")
        if not any(pat.search(l) for l in lines[:200]):  # لا تكرّر
            new_knobs_block.append(knob_line(name, default))

    if new_knobs_block:
        lines[insert_at:insert_at] = new_knobs_block + [""]

    return "\n".join(lines) + ("\n" if not src_code.endswith("\n") else "")

def process_file(path: pathlib.Path, apply: bool, backup: bool) -> Tuple[bool, Dict]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False, {"file": str(path), "error": "SyntaxError"}

    rw = Rewriter()
    new_tree = rw.visit(tree)
    ast.fix_missing_locations(new_tree)

    if not rw.changed:
        return False, {"file": str(path), "changed": False}

    new_code = ast.unparse(new_tree)
    new_code = inject_header_and_knobs(new_code, rw.knobs)

    if apply:
        if backup:
            bak = path.with_suffix(path.suffix + ".bak")
            if not bak.exists():
                bak.write_text(text, encoding="utf-8")
        path.write_text(new_code, encoding="utf-8")

    return True, {"file": str(path), "changed": True, "knobs": rw.knobs}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="repo root")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--backup", action="store_true")
    ap.add_argument("--report", default="agl_mass_param_report.json")
    args = ap.parse_args()

    root = pathlib.Path(args.root).resolve()
    results: List[Dict] = []
    for p in root.rglob("*.py"):
        if should_skip(p): continue
        ok, info = process_file(p, apply=args.apply, backup=args.backup)
        results.append(info)

    changed = [r for r in results if r.get("changed")]
    print(f"[DONE] scanned={len(results)} changed={len(changed)}")
    with open(args.report, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    sys.exit(main())
