# -*- coding: utf-8 -*-
import uuid
from Core_Memory.bridge_singleton import get_bridge
from Core_Engines import prompt_composer_v2 as pc_v2
from Core_Engines import micro_planner
from Core_Engines import analogy_mapping
from Core_Engines import Reasoning_Layer


def test_trace_linkage_chain():
    br = get_bridge()
    # fresh trace id
    trace = str(uuid.uuid4())

    # 1) produce a rationale via Reasoning_Layer.run
    payload = {'query': 'اختبار تتبع الفكرة: اذكر خطوات ربط', 'trace_id': trace}
    rl_res = Reasoning_Layer.run(payload)
    assert rl_res.get('ok') is True

    # ensure rationale persisted
    rats = [e for e in br.query_by_trace_and_type(trace, 'rationale', scope = 'stm') if e.get('type') == 'rationale']
    assert len(rats) >= 1, 'rationale not recorded in bridge'
    rationale_id = rats[-1]['id']

    # 2) generate a prompt plan with the same trace
    pc_out = pc_v2.PromptComposerV2().process_task({'task': 'ربط', 'trace_id': trace})
    assert pc_out.get('ok') is True
    pps = [e for e in br.query_by_trace_and_type(trace, 'prompt_plan', scope = 'stm') if e.get('type') == 'prompt_plan']
    assert len(pps) >= 1, 'prompt_plan not recorded'
    prompt_plan_id = pps[-1]['id']

    # check link rationale -> prompt_plan
    linked = False
    for links in br.graph.values():
        for l in links:
            if l[0] == rationale_id and l[2] == prompt_plan_id:
                linked = True
    assert linked, 'rationale not linked to prompt_plan'

    # 3) micro-plan
    mp_out = micro_planner.MicroPlanner().process_task({'task': 'تنفيذ', 'trace_id': trace})
    assert mp_out.get('ok') is True
    plans = [e for e in br.query_by_trace_and_type(trace, 'plan', scope = 'stm') if e.get('type') == 'plan']
    assert len(plans) >= 1, 'plan not recorded'
    plan_id = plans[-1]['id']

    # check link prompt_plan -> plan
    linked_pp = False
    for links in br.graph.values():
        for l in links:
            if l[0] == prompt_plan_id and l[2] == plan_id:
                linked_pp = True
    assert linked_pp, 'prompt_plan not linked to plan'

    # 4) analogy map
    am_out = analogy_mapping.AnalogyMappingEngine().process_task({'text': 'تعليمي', 'trace_id': trace})
    assert am_out.get('ok') is True
    ams = [e for e in br.query_by_trace_and_type(trace, 'analogy_map', scope = 'stm') if e.get('type') == 'analogy_map']
    assert len(ams) >= 1, 'analogy_map not recorded'
    am_id = ams[-1]['id']

    # check chain plan -> analogy_map (Analogy_Mapping links rationale -> analogy in its code; ensure we have some link from plan or rationale to analogy)
    found = False
    for links in br.graph.values():
        for l in links:
            if l[2] == am_id and (l[0] == rationale_id or l[0] == prompt_plan_id or l[0] == plan_id):
                found = True
    assert found, 'analogy_map not linked to chain'
    # explicit edge assertions for stronger CI checks
    edges = [(s, rel, t) for links in br.graph.values() for (s, rel, t) in links]
    assert (rationale_id, 'informs_prompt', prompt_plan_id) in edges
    assert (prompt_plan_id, 'expanded_into_plan', plan_id) in edges
