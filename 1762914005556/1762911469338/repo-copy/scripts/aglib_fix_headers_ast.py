import json, pathlib, ast, re, sys
root = pathlib.Path('.').resolve()
report_p = root / 'agl_mass_param_report.json'
if not report_p.exists():
    print('report not found')
    sys.exit(2)
report = json.load(report_p.open('r', encoding='utf-8'))
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
knob_assign_re = re.compile(r"^_AGL_[A-Z0-9_]*\s*=\s*_to_int\('")
changed = [r for r in report if r.get('changed')]
fixed = []
for r in changed:
    p = pathlib.Path(r['file'])
    if not p.exists():
        continue
    src = p.read_text(encoding='utf-8', errors='ignore')
    try:
        mod = ast.parse(src)
    except SyntaxError:
        continue
    lines = src.splitlines()
    # find docstring node (if any)
    doc_node = None
    future_nodes = []
    for node in mod.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            doc_node = node
            continue
        if isinstance(node, ast.ImportFrom) and node.module == '__future__':
            future_nodes.append(node)
    # collect future import lines
    future_lines = []
    future_line_indices = set()
    for fn in future_nodes:
        # lineno is 1-based
        ln = fn.lineno - 1
        future_lines.append(lines[ln])
        future_line_indices.add(ln)
    # remove existing header block and knob lines
    new_src_lines = list(lines)
    # remove header block if present
    header_idx = None
    for i,l in enumerate(new_src_lines[:200]):
        if 'AGL auto-injected knobs (idempotent)' in l:
            header_idx = i
            break
    if header_idx is not None:
        # remove header block through first blank line after header
        j = header_idx+1
        while j < len(new_src_lines) and new_src_lines[j].strip() != '':
            new_src_lines[j] = ''
            j += 1
        new_src_lines[header_idx] = ''
    # remove knob assign lines anywhere
    existing_knobs = []
    for i,l in enumerate(new_src_lines):
        if l and knob_assign_re.match(l.strip()):
            existing_knobs.append(l.strip())
            new_src_lines[i] = ''
    # remove future import original lines (we'll re-insert them after docstring)
    for idx in sorted(future_line_indices):
        new_src_lines[idx] = ''
    # remove original docstring lines (we'll re-insert them)
    doc_lines = []
    if doc_node is not None:
        ds = doc_node
        s_ln = ds.lineno - 1
        e_ln = getattr(ds, 'end_lineno', s_ln)
        doc_lines = lines[s_ln:e_ln+1]
        for k in range(s_ln, e_ln+1):
            new_src_lines[k] = ''
    # collect remaining lines
    remaining = [l for l in new_src_lines if l is not None and l.strip() != '']
    # build new content
    out_lines = []
    if doc_lines:
        out_lines.extend(doc_lines)
    if future_lines:
        # ensure a blank line separation
        if out_lines and out_lines[-1].strip() != '':
            out_lines.append('')
        out_lines.extend(future_lines)
    # header
    out_lines.extend(HEADER_SNIPPET.splitlines())
    # knobs: prefer knobs from report
    knobs = list((r.get('knobs') or {}).items())
    knob_lines = []
    if knobs:
        for name, default in knobs:
            knob_lines.append(f"_{name} = _to_int('{name}', {default})")
    else:
        for ek in existing_knobs:
            knob_lines.append(ek)
    if knob_lines:
        out_lines.extend(knob_lines)
        out_lines.append('')
    # append remaining
    out_lines.extend(remaining)
    new_text = '\n'.join(out_lines) + '\n'
    bak = p.with_suffix(p.suffix + '.bak')
    if not bak.exists():
        p.with_suffix(p.suffix + '.bak').write_text(src, encoding='utf-8')
    p.write_text(new_text, encoding='utf-8')
    fixed.append(str(p))

print('fixed files (ast):', len(fixed))
for f in fixed[:20]:
    print('-', f)
