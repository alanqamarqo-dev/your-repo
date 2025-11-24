"""
Codemod: promote br.query(..., match='and') to helper calls.

This script is conservative and only performs safe rewrites:
- br.query(type=..., trace_id=..., match='and'[, scope=...]) -->
  br.query_by_trace_and_type(trace_id, type, scope=...)
- br.query(..., match='and')[-1] or next(iter(br.query(...))) or max(br.query(...), key=...) -->
  br.latest(trace_id=..., type_=..., scope=...)

Usage:
  python tools/codemods/promote_helpers.py --dry-run
  python tools/codemods/promote_helpers.py --apply
"""

import sys
import argparse
import pathlib
from typing import Optional, List, Tuple, Dict

import libcst as cst
import libcst.matchers as m

ALLOWED_FOR_LATEST = {"type", "trace_id", "match", "scope"}


def _kwdict_from_args(args: List[cst.Arg]) -> Tuple[Dict[str, cst.CSTNode], List[cst.Arg]]:
    kw: Dict[str, cst.CSTNode] = {}
    pos: List[cst.Arg] = []
    for a in args:
        if a.keyword is None:
            pos.append(a)
        else:
            kw[a.keyword.value] = a.value
    return kw, pos


def _is_attr(node: cst.CSTNode, base: str, attr: str) -> bool:
    return m.matches(node, m.Attribute(value=m.Name(base), attr=m.Name(attr)))


def _lit_str(node: cst.CSTNode) -> Optional[str]:
    if m.matches(node, m.SimpleString()):
        s = node.value
        if len(s) >= 2 and s[0] in ("'", '"') and s[-1] == s[0]:
            return s[1:-1]
        return s
    return None


class PromoteHelpersTransformer(cst.CSTTransformer):
    def __init__(self):
        self.modifications: List[str] = []

    def _build_latest_call(self, trace_node: cst.CSTNode, type_node: cst.CSTNode, scope_node: Optional[cst.CSTNode]) -> cst.Call:
        args: List[cst.Arg] = [
            cst.Arg(keyword=cst.Name("trace_id"), value=trace_node),
            cst.Arg(keyword=cst.Name("type_"), value=type_node),
        ]
        if scope_node is not None:
            args.append(cst.Arg(keyword=cst.Name("scope"), value=scope_node))
        return cst.Call(func=cst.Attribute(value=cst.Name("br"), attr=cst.Name("latest")), args=args)

    def leave_Subscript(self, original_node: cst.Subscript, updated_node: cst.Subscript) -> cst.BaseExpression:
        # match a single slice of [-1]
        if not original_node.slice or len(original_node.slice) != 1:
            return updated_node
        slc = original_node.slice[0]
        if not m.matches(slc, m.SubscriptElement(slice=m.Index(value=m.UnaryOperation(operator=m.Minus(), expression=m.Integer(value="1"))))):
            return updated_node

        call = original_node.value
        if not isinstance(call, cst.Call):
            return updated_node
        if not isinstance(call.func, cst.Attribute) or not _is_attr(call.func, "br", "query"):
            return updated_node

        kw, pos = _kwdict_from_args(call.args)
        if pos:
            return updated_node

        t = kw.get("type")
        tr = kw.get("trace_id")
        mt = kw.get("match")
        if t is None or tr is None or mt is None:
            return updated_node
        mt_val = _lit_str(mt)
        if mt_val != "and":
            return updated_node

        if any(k not in ALLOWED_FOR_LATEST for k in kw.keys()):
            return updated_node

        scope = kw.get("scope")
        self.modifications.append(str(original_node))
        return self._build_latest_call(tr, t, scope)

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.BaseExpression:
        # handle wrapper patterns like next(iter(br.query(...))) and max(br.query(...), key=...)
        # next(iter(br.query(...)), default=...)
        if m.matches(updated_node.func, m.Name("next")) and len(updated_node.args) >= 1:
            first = updated_node.args[0].value
            if m.matches(first, m.Call(func=m.Name("iter"))):
                # iter(call) -> check call is br.query
                inner = first
                if isinstance(inner, cst.Call) and isinstance(inner.func, cst.Name):
                    # rare; skip
                    pass
                # more direct: iter(br.query(...)) will have the call as arg
                if isinstance(first, cst.Call) and first.args:
                    arg0 = first.args[0].value
                    if isinstance(arg0, cst.Call) and isinstance(arg0.func, cst.Attribute) and _is_attr(arg0.func, "br", "query"):
                        kw, pos = _kwdict_from_args(arg0.args)
                        if not pos:
                            t = kw.get("type")
                            tr = kw.get("trace_id")
                            mt = kw.get("match")
                            if t and tr and mt and _lit_str(mt) == "and":
                                scope = kw.get("scope")
                                self.modifications.append(str(original_node))
                                return self._build_latest_call(tr, t, scope)

        # max(br.query(...), key=...)
        if m.matches(updated_node.func, m.Name("max")) and len(updated_node.args) >= 1:
            first = updated_node.args[0].value
            if isinstance(first, cst.Call) and isinstance(first.func, cst.Attribute) and _is_attr(first.func, "br", "query"):
                kw, pos = _kwdict_from_args(first.args)
                if not pos:
                    t = kw.get("type")
                    tr = kw.get("trace_id")
                    mt = kw.get("match")
                    if t and tr and mt and _lit_str(mt) == "and":
                        scope = kw.get("scope")
                        self.modifications.append(str(original_node))
                        return self._build_latest_call(tr, t, scope)

        # general br.query(...) -> query_by_trace_and_type(trace_id, type, ...)
        func = original_node.func
        if isinstance(func, cst.Attribute) and _is_attr(func, "br", "query"):
            kw, pos = _kwdict_from_args(original_node.args)
            if pos:
                return updated_node
            t = kw.get("type")
            tr = kw.get("trace_id")
            mt = kw.get("match")
            if t and tr and mt and _lit_str(mt) == "and":
                new_args: List[cst.Arg] = [cst.Arg(value=tr), cst.Arg(value=t)]
                if "scope" in kw:
                    new_args.append(cst.Arg(keyword=cst.Name("scope"), value=kw["scope"]))
                for k, v in kw.items():
                    if k in ("type", "trace_id", "match", "scope"):
                        continue
                    new_args.append(cst.Arg(keyword=cst.Name(k), value=v))
                new_func = cst.Attribute(value=cst.Name("br"), attr=cst.Name("query_by_trace_and_type"))
                self.modifications.append(str(original_node))
                return updated_node.with_changes(func=new_func, args=new_args)

        return updated_node


def process_file(path: pathlib.Path, apply: bool) -> bool:
    try:
        src = path.read_text(encoding="utf-8", errors="strict")
    except Exception:
        return False
    try:
        mod = cst.parse_module(src)
    except Exception:
        return False

    tr = PromoteHelpersTransformer()
    new_mod = mod.visit(tr)

    if not tr.modifications:
        return False

    if apply:
        path.write_text(new_mod.code, encoding="utf-8")
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="apply changes in-place")
    ap.add_argument("--dry-run", action="store_true", help="report only (default)")
    ap.add_argument("--root", default=".", help="root directory to scan")
    args = ap.parse_args()

    apply = bool(args.apply) and not bool(args.dry_run)

    root = pathlib.Path(args.root)
    changed: List[str] = []
    skipped: List[str] = []

    for p in root.rglob("*.py"):
        if any(seg in p.parts for seg in (".venv", "__pycache__", "site-packages", "build", "dist")):
            continue
        if p.as_posix().endswith("promote_helpers.py"):
            continue
        if p.as_posix().endswith("enforce_trace_and_type.py"):
            continue
        try:
            ok = process_file(p, apply=apply)
            if ok:
                changed.append(str(p))
        except Exception:
            skipped.append(str(p))

    if changed:
        print(("Would modify:\n" if not apply else "Modified files:\n") + " - " + "\n - ".join(changed))
    if skipped:
        print("Skipped files (parse/transform issues):")
        for s in skipped:
            print(" -", s)

    sys.exit(0)


if __name__ == "__main__":
    main()
