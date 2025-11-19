import re, sys, pathlib

PATTERN = re.compile(
    r"""br\.query\s*\(
        (?P<args>[^)]*)
    \)""", re.X | re.S
)

def needs_fix(args: str) -> bool:
    has_type     = re.search(r'\btype\s*=', args) is not None
    has_trace_id = re.search(r'\btrace_id\s*=', args) is not None
    has_match    = re.search(r'\bmatch\s*=', args) is not None
    return has_type and has_trace_id and not has_match

def add_match_and(call: str) -> str:
    # يضيف match='and' إن لم يوجد
    m = PATTERN.search(call)
    if not m: return call
    args = m.group('args')
    if not needs_fix(args): return call
    if args.strip().endswith(','):
        new_args = args + " match='and'"
    else:
        new_args = args + ", match='and'"
    return call.replace(args, new_args)

def fix_file(p: pathlib.Path):
    text = p.read_text(encoding='utf-8')
    changed = False
    def repl(m):
        nonlocal changed
        before = m.group(0)
        after  = add_match_and(before)
        if after != before:
            changed = True
        return after
    new_text = PATTERN.sub(repl, text)
    if changed:
        p.write_text(new_text, encoding='utf-8')
        return True
    return False

def main():
    root = pathlib.Path('.')
    exts = {'.py'}
    touched = []
    for f in root.rglob('*.py'):
        if any(seg in f.parts for seg in ('.venv','__pycache__','site-packages','build','dist')):
            continue
        if f.suffix in exts:
            try:
                if fix_file(f):
                    touched.append(str(f))
            except Exception as e:
                print(f"SKIP {f}: {e}")
    print("Modified files:" if touched else "No changes needed.")
    for t in touched:
        print(" -", t)

if __name__ == '__main__':
    main()
