import importlib, sys, os
from pprint import pprint

def safe_import(mod):
    try:
        return importlib.import_module(mod), None
    except Exception as e:
        return None, e

checks = {}
# try several candidate module paths (some repos use different package roots)
candidates = [
    'AGL.Infra.engine_monitor','AGL.Infra.health',
    'Infra.engine_monitor','infra.engine_monitor','infra.health',
    'Core_Engines.engine_monitor','AGL.Infra.engine_monitor'
]
for c in candidates:
    mod, err = safe_import(c)
    checks[c] = (mod is not None, str(err) if err else None)
    if mod:
        # list some attrs
        checks[c+'_attrs'] = [a for a in dir(mod) if a.lower().startswith('engine') or 'health' in a.lower() or a in ('ENGINE_STATS','monitor_engine','engines_health_snapshot')][:20]

# search for trace_id text in likely orchestrator files
trace_found = False
orchestrator_paths = [
    os.path.join('Integration_Layer','planner.py'),
    os.path.join('Integration_Layer','Action_Router.py'),
    os.path.join('AGL_UI','main.py'),
    'server.py', 'AGL.py'
]
for p in orchestrator_paths:
    try:
        with open(p,'r',encoding='utf-8',errors='ignore') as f:
            txt = f.read()
            if 'trace_id' in txt:
                checks['trace_in_'+p] = True
                trace_found = True
            else:
                checks['trace_in_'+p] = False
    except Exception as e:
        checks['trace_in_'+p] = str(e)

checks['trace_id_anywhere'] = trace_found
pprint(checks)
