import json, pathlib, sys
p=pathlib.Path('agl_mass_param_report.json')
if not p.exists():
    print('REPORT_NOT_FOUND')
    sys.exit(2)
data=json.load(p.open('r',encoding='utf-8'))
changed=[x for x in data if x.get('changed')]
print('changed files count:', len(changed))
for it in changed[:20]:
    print('-', it['file'], 'knobs=', list((it.get('knobs') or {}).keys()))
