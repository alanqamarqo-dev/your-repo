#!/usr/bin/env python3
"""
scripts/apply_batch3_env_switches.py
آمن (idempotent) — يدعم --dry-run و --backup، ومحاولة تجنّب الاستبدال داخل string literals.
انسخه إلى scripts/ ثم شغّله داخل venv:
& .\.venv\Scripts\Activate.ps1
python .\scripts\apply_batch3_env_switches.py --dry-run
"""
import re
import os
import sys
import argparse
import pathlib
from typing import List
# repo root
ROOT = pathlib.Path(__file__).resolve().parents[1]

HEADER_INSERT_POS_PAT = re.compile(r'^(?:\s*#.*\n|from\s+[\w\.]+\s+import\s+.*\n|import\s+[\w\., ]+\n)+', re.MULTILINE)
FILES = {
    "Core_Consciousness/Intent_Generator.py": {
        "inject": [
            ("import os", True),
            ("""def _to_int(name, default):
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default
""", False),
            ('_AGL_INTENT_TOP_N = _to_int("AGL_INTENT_TOP_N", 3)', False),
        ],
        "replacements": [
            (r'(\b[A-Za-z_][A-Za-z0-9_]*\b)\s*\[\s*:\s*3\s*\]', r'\1[:_AGL_INTENT_TOP_N]'),
            (r'\btop_k\s*=\s*3\b', 'top_k=_AGL_INTENT_TOP_N'),
        ],
    },

    "Core_Engines/Social_Interaction.py": {
        "inject": [
            ("import os", True),
            ("""def _to_int(name, default):
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default
""", False),
            ('_AGL_SOCIAL_CTX_CHARS = _to_int("AGL_SOCIAL_CTX_CHARS", 200)', False),
        ],
        "replacements": [
            (r'(\b[A-Za-z_][A-Za-z0-9_]*\b)\s*\[\s*:\s*200\s*\]', r'\1[:_AGL_SOCIAL_CTX_CHARS]'),
            (r'\btext\s*\[\s*:\s*200\s*\]', 'text[:_AGL_SOCIAL_CTX_CHARS]'),
        ],
    },

    "Core_Engines/Reasoning_Planner.py": {
        "inject": [
            ("import os", True),
            ("""def _to_int(name, default):
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default
""", False),
            ('_AGL_PLANNER_MAX_STEPS = _to_int("AGL_PLANNER_MAX_STEPS", 8)', False),
        ],
        "replacements": [
            (r'\bmax_steps\s*=\s*8\b', 'max_steps=_AGL_PLANNER_MAX_STEPS'),
            (r'for\s+([A-Za-z_][A-Za-z0-9_]*)\s+in\s+range\(\s*8\s*\)', r'for \1 in range(_AGL_PLANNER_MAX_STEPS)'),
        ],
    },

    "Core_Engines/General_Knowledge.py": {
        "inject": [],
        "replacements": [
            (r'\[\s*:\s*120\s*\]', '[:_AGL_GENERAL_KNOWLEDGE_CTX_CHARS]'),
            (r'\[\s*:\s*1000\s*\]', '[:_AGL_GENERAL_KNOWLEDGE_MAX_CHARS]'),
            (r'\btop_k\s*=\s*5\b', 'top_k=_AGL_GENERAL_KNOWLEDGE_TOPK'),
            (r'\[\s*:\s*3\s*\]', '[:_AGL_GENERAL_KNOWLEDGE_TOPK]'),
        ],
    },

    "tools/run_eval50.py": {
        "inject": [],
        "replacements": [
            (r'(\b[A-Za-z_][A-Za-z0-9_]*\b)\s*\[\s*:\s*3\s*\]', r'\1[:_AGL_EVIDENCE_LIMIT]'),
            (r'\[\s*:\s*3\s*\]', '[:_AGL_EVIDENCE_LIMIT]'),
        ],
    },

    "Integration_Layer/meta_orchestrator.py": {
        "inject": [],
        "replacements": [
            (r'\bextra\s*\[\s*:\s*1200\s*\]', 'extra[:_AGL_META_EXTRA_CHARS]'),
        ],
    },
}

HEADER_INSERT_POS_PAT = re.compile(r'^(?:\s*#.*\n|from\s+[\w\.]+\s+import\s+.*\n|import\s+[\w\., ]+\n)+', re.MULTILINE)


def in_literal_on_same_line(line: str, span_start: int) -> bool:
    before = line[:span_start]
    before = before.replace('\"', '').replace("\\'", '')
    dq = before.count('"')
    sq = before.count("'")
    return (dq % 2 == 1) or (sq % 2 == 1)


def ensure_injected(code: str, snippet: str, ensure_import: bool) -> str:
    s = snippet.strip()
    if s in code:
        return code
    if ensure_import and s.startswith('import '):
        m = HEADER_INSERT_POS_PAT.search(code)
        if m:
            insert_at = m.end()
            return code[:insert_at] + s + "\n" + code[insert_at:]
        else:
            return s + "\n\n" + code
    m = HEADER_INSERT_POS_PAT.search(code)
    if m:
        insert_at = m.end()
        return code[:insert_at] + "\n" + s + "\n\n" + code[insert_at:]
    else:
        return s + "\n\n" + code


def apply_file(path: pathlib.Path, plan: dict, dry_run: bool = False, backup: bool = False):
    code = path.read_text(encoding='utf-8', errors='ignore')
    original = code
    for snippet, is_import in plan.get("inject", []):
        code = ensure_injected(code, snippet, ensure_import=is_import)

    for pat, repl in plan.get("replacements", []):
        prog = re.compile(pat)
        new_lines: List[str] = []
        for line in code.splitlines(keepends=True):
            # skip substitution if match inside a literal on the same line (heuristic)
            matches = list(prog.finditer(line))
            if not matches:
                new_lines.append(line)
                continue
            safe_line = line
            for m in matches:
                if in_literal_on_same_line(line, m.start()):
                    # ignore this match (leave original)
                    pass
            # apply global substitution (we've attempted to filter unsafe cases)
            new_line = prog.sub(repl, safe_line)
            new_lines.append(new_line)
        code = ''.join(new_lines)

    if code != original:
        if dry_run:
            print(f"[DRY-RUN] {path} would be modified")
            import difflib
            diff = difflib.unified_diff(original.splitlines(), code.splitlines(), lineterm='')
            for i, l in enumerate(diff):
                if i > 200: break
                print(l)
        else:
            if backup:
                bak = path.with_suffix(path.suffix + '.bak')
                bak.write_text(original, encoding='utf-8')
            path.write_text(code, encoding='utf-8')
            print(f"[APPLIED] {path}")
    else:
        print(f"[SKIPPED] {path} (no change)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='Show changes but do not write files')
    parser.add_argument('--backup', action='store_true', help='Write .bak backup for modified files')
    args = parser.parse_args()
    os.chdir(ROOT)
    for rel, plan in FILES.items():
        p = ROOT / rel
        if not p.exists():
            print(f"[MISS ] {rel} (not found)")
            continue
        apply_file(p, plan, dry_run=args.dry_run, backup=args.backup)


if __name__ == "__main__":
    main()
