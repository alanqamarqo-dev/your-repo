import os
os.environ['AGL_FAST_MODE'] = '0'
from Self_Improvement import hosted_llm_adapter
from Self_Improvement.Knowledge_Graph import agl_pipeline

# monkeypatch by direct assignment
original = getattr(hosted_llm_adapter.HostedLLMAdapter, 'process_task', None)
def fake_broken(self, task, timeout_s=200.0):
    raise RuntimeError('simulated failure for testing')
setattr(hosted_llm_adapter.HostedLLMAdapter, 'process_task', fake_broken)

print('Calling agl_pipeline with monkeypatched HostedLLMAdapter.process_task...')
res = agl_pipeline('ما هي أعراض الإنفلونزا؟')
import json
print('RESULT PROVENANCE:')
print(json.dumps(res.get('provenance', {}), ensure_ascii=False, indent=2))
print('RUNTIME CONTEXT:', res.get('provenance', {}).get('runtime_context'))

# restore
if original:
    setattr(hosted_llm_adapter.HostedLLMAdapter, 'process_task', original)
print('done')
