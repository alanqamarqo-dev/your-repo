import os
os.environ['AGL_FAST_MODE'] = '1'
from Self_Improvement.Knowledge_Graph import agl_pipeline, CognitiveIntegrationEngine

# monkeypatch by direct assign
orig = getattr(CognitiveIntegrationEngine, 'collaborative_solve', None)
def _raise(self, *a, **k):
    raise RuntimeError('simulated failure for testing')
CognitiveIntegrationEngine.collaborative_solve = _raise

print('Calling agl_pipeline with patched CognitiveIntegrationEngine.collaborative_solve...')
res = agl_pipeline('ما هي أعراض الإنفلونزا؟')
import json
print('RESULT:')
print(json.dumps(res, ensure_ascii=False, indent=2))
print('PROV:', json.dumps(res.get('provenance', {}), ensure_ascii=False, indent=2))

# restore
if orig:
    CognitiveIntegrationEngine.collaborative_solve = orig
print('done')
