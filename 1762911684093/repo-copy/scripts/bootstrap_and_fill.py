"""Bootstrap engines in-process and call a couple of lightweight engines to populate monitoring stats."""
from Integration_Layer.integration_registry import registry
import Core_Engines as engines
import json, traceback

engines.bootstrap_register_all_engines(registry, allow_optional=True)
print('REGISTRY:', sorted(registry.list_names()))

names = ['General_Knowledge', 'NLP_Advanced']
out = {}
for name in names:
    try:
        e = registry.get(name)
    except Exception:
        try:
            e = registry.resolve(name)
        except Exception:
            e = None

    if not e:
        out[name] = 'NOT FOUND'
        continue

    try:
        if hasattr(e, 'process_task'):
            res = e.process_task({'text': 'ما عاصمة فرنسا؟'})
            out[name] = res
        else:
            out[name] = 'NO process_task'
    except Exception:
        out[name] = 'ERR: ' + traceback.format_exc()

print(json.dumps(out, ensure_ascii=False, indent=2))
