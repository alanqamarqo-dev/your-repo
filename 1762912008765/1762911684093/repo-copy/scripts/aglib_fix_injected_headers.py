import json, pathlib, re, sys
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
    txt = p.read_text(encoding='utf-8', errors='ignore')
    lines = txt.splitlines()
    # collect future_imports at top (allow initial shebang or encoding comment)
    future_lines = []
    idx = 0
    # skip possible shebang or encoding comment
    while idx < len(lines) and (lines[idx].strip().startswith('#!') or lines[idx].strip().startswith('# -*-')):
        idx += 1
    # collect consecutive future imports
    while idx < len(lines) and lines[idx].strip().startswith('from __future__ import'):
        future_lines.append(lines[idx])
        lines[idx] = ''
        idx += 1
    # remove existing header block if present
    header_idx = None
    for i,l in enumerate(lines[:200]):
        if 'AGL auto-injected knobs (idempotent)' in l:
            header_idx = i
            break
    if header_idx is not None:
        # find next blank line after header start
        j = header_idx+1
        while j < len(lines) and lines[j].strip() != '':
            j += 1
        # remove header block lines header_idx..j
        for k in range(header_idx, j+1):
            if k < len(lines):
                lines[k] = ''
    # collect existing knob lines (anywhere)
    existing_knobs = []
    remaining = []
    for l in lines:
        if l is None:
            continue
        if knob_assign_re.match(l.strip()):
            existing_knobs.append(l.strip())
        else:
            remaining.append(l)
    # build new file: shebang if present, future_lines, header, knob defs from report
    new_lines = []
    # preserve initial shebang/encoding comments
    i = 0
    while i < len(lines) and (lines[i].strip().startswith('#!') or lines[i].strip().startswith('# -*-')):
        new_lines.append(lines[i])
        i += 1
    if future_lines:
        new_lines.extend(future_lines)
    # header
    new_lines.extend(HEADER_SNIPPET.splitlines())
    # knobs: prefer knobs from report if present
    knobs = list((r.get('knobs') or {}).items())
    knob_lines = []
    if knobs:
        for name, default in knobs:
            knob_lines.append(f"_{name} = _to_int('{name}', {default})")
    else:
        # fallback to existing knob lines we discovered
        for ek in existing_knobs:
            knob_lines.append(ek)
    if knob_lines:
        new_lines.extend(knob_lines)
        new_lines.append('')
    # append rest of original file excluding removed/blanked lines
    for l in remaining:
        new_lines.append(l)
    new_text = '\n'.join(new_lines) + ('\n' if not new_lines or not new_lines[-1].endswith('\n') else '')
    # write backup if not exists
    bak = p.with_suffix(p.suffix + '.bak')
    if not bak.exists():
        p.with_suffix(p.suffix + '.bak').write_text(txt, encoding='utf-8')
    p.write_text(new_text, encoding='utf-8')
    fixed.append(str(p))

print('fixed files count:', len(fixed))
for f in fixed[:20]:
    print('-', f)
