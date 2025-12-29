from Core_Memory.bridge_singleton import get_bridge
from Core_Engines import Reasoning_Layer
import uuid, json
br = get_bridge()
trace = str(uuid.uuid4())
print('trace:', trace)
res = Reasoning_Layer.run({'query':'اختبار تتبع الفكرة: اذكر خطوات ربط','trace_id': trace})
print('run res ok:', res.get('ok'))
print('run res keys:', list(res.keys()))
rats = br.query_by_trace_and_type(trace, 'rationale', scope = 'stm')
print('rationale count:', len(rats))
print('rationale ids:', [r['id'] for r in rats])
print('bridge stm len:', len(br.stm))
print('bridge index_by_trace has trace:', trace in br.index_by_trace)
