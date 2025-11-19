from Core_Memory.bridge_singleton import get_bridge
from Core_Engines import prompt_composer_v2 as pc_v2
import uuid
br = get_bridge()
trace = str(uuid.uuid4())
print('trace:', trace)
# ensure there is a rationale first
from Core_Engines import Reasoning_Layer
rl = Reasoning_Layer.run({'query':'اختبار تتبع الفكرة: اذكر خطوات ربط','trace_id': trace})
print('reasoning ok', rl.get('ok'))
pc = pc_v2.PromptComposerV2()
# call process_task properly
pc_out = pc.process_task({'task': 'ربط', 'trace_id': trace})
print('prompt ok', pc_out.get('ok'))
pps = br.query_by_trace_and_type(trace, 'prompt_plan', scope = 'stm')
print('prompt_plan count', len(pps))
print('graph links:', br.graph)
 