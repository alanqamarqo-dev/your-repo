# === AGL auto-injected knobs (idempotent) ===
try:
    import os
    def _to_int(name, default):
        try:
            return int(os.environ.get(name, str(default)))
        except Exception:
            return default
except Exception:
    def _to_int(name, default): return default
_AGL_PREVIEW_1000 = _to_int('AGL_PREVIEW_1000', 1000)

try:
    import os
    def _to_int(name, default):
        try:
            return int(os.environ.get(name, str(default)))
        except Exception:
            return default
except Exception:
    def _to_int(name, default): return default
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Integration_Layer.integration_registry import registry
import Core_Engines as CE
CE.bootstrap_register_all_engines(registry, allow_optional=True)
llm = registry.get('Ollama_KnowledgeEngine')
meta = registry.get('AdvancedMetaReasoner') or registry.get('Meta_Learning')
q = 'المشكلة: اختبار صغير للتحقق من مخرجات المحركات.'
print('LLM exists', llm is not None)
print('META exists', meta is not None)
if llm:
    try:
        r = llm.process_task({'query': q})
    except Exception:
        try:
            r = llm.ask(q)
        except Exception as e:
            r = {'error': str(e)}
    print('LLM.resp:', repr(r)[:_AGL_PREVIEW_1000])
if meta:
    try:
        r2 = meta.process_task({'prompt': q})
    except Exception as e:
        r2 = {'error': str(e)}
    print('META.resp:', repr(r2)[:_AGL_PREVIEW_1000])
