import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ['AGL_REASONER_MODE']='dkn'
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
mo = registry.get('meta_orchestrator')
print('meta_orchestrator ->', type(mo).__name__)
print('has consensus_and_emit?', hasattr(mo, 'consensus_and_emit'))
try:
    attr = getattr(mo, 'consensus_and_emit')
    print('callable(consensus_and_emit)?', callable(attr))
    print('repr:', repr(attr))
except Exception as e:
    print('getattr error', e)
try:
    print('calling consensus_and_emit ->')
    r = mo.consensus_and_emit()
    print('returned type', type(r).__name__)
except Exception as e:
    print('call raised', e)
print('meta_orchestrator module:', getattr(mo, '__class__').__module__)
print('meta_orchestrator dir (first 60):', sorted([d for d in dir(mo) if not d.startswith('_')])[:60])
