import json, importlib, sys, pathlib
root = pathlib.Path('.').resolve()
report_path = root / 'agl_mass_param_report.json'
if not report_path.exists():
    print('REPORT_NOT_FOUND')
    sys.exit(2)
report = json.load(report_path.open('r',encoding='utf-8'))
failed=[]
ok=[]

def to_module(p):
    p=pathlib.Path(p).resolve()
    rel = p.relative_to(root)
    mod = '.'.join(rel.with_suffix('').parts)
    return mod

for r in report:
    if not r.get('changed'): continue
    mod = to_module(r['file'])
    try:
        importlib.invalidate_caches()
        importlib.import_module(mod)
        print('IMPORT_OK', mod)
        ok.append(mod)
    except Exception as e:
        print('IMPORT_FAIL', mod, '->', e)
        failed.append((mod, str(e)))

print(f"\nSUMMARY: ok={len(ok)} fail={len(failed)}")
if failed:
    print('\nFirst failures:')
    for m,e in failed[:10]: print('-', m, ':', e)
    sys.exit(1)
