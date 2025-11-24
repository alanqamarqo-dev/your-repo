import os, json, sys
from pathlib import Path
# ensure repo root on sys.path (same technique as integration_cohesion_check.py)
sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ['AGL_REASONER_MODE'] = 'dkn'
from Integration_Layer.integration_registry import registry
import Core_Engines as CE
CE.bootstrap_register_all_engines(registry, allow_optional=True)
import importlib.util
agl_path = Path(__file__).parent.parent / 'AGL.py'
agl = None
if agl_path.exists():
    spec = importlib.util.spec_from_file_location('agl_module', str(agl_path))
    agl_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(agl_module)  # type: ignore
    try:
        agl = getattr(agl_module, 'create_agl_instance')()
    except Exception:
        try:
            agl = getattr(agl_module, 'AGL')()
        except Exception:
            agl = None
print('AGL created:', bool(agl))
print('registry keys count:', len(list(registry.keys())))
print(json.dumps(sorted(list(registry.keys())), ensure_ascii=False, indent=2))
keys = ['hybrid_composer','task_orchestrator','communication_bus','rag','meta_orchestrator','dkn_bus','knowledge_graph']
for k in keys:
    try:
        v = registry.get(k)
        print(k, '->', type(v).__name__)
    except Exception as e:
        print(k, '-> not found')
