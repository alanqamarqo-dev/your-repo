import uuid
from Core_Memory.bridge_singleton import get_bridge


def _clear_bridge(br):
    # best-effort clear existing singleton state to avoid test pollution
    try:
        # clear STM entries
        if hasattr(br, 'stm') and hasattr(br.stm, '_od'):
            for k in list(br.stm._od.keys()):
                br.stm.delete(k)
        # clear LTM and indices/graph
        if hasattr(br, 'ltm'):
            br.ltm.clear()
        if hasattr(br, 'graph'):
            br.graph.clear()
        if hasattr(br, 'index_by_type'):
            br.index_by_type.clear()
        if hasattr(br, 'index_by_trace'):
            br.index_by_trace.clear()
    except Exception:
        pass


def test_bridge_query_match_and():
    br = get_bridge()
    assert br is not None
    _clear_bridge(br)

    trace_a, trace_b = str(uuid.uuid4()), str(uuid.uuid4())

    a1 = br.put("rationale", {"text": "A"}, trace_id=trace_a, pinned=True)
    b1 = br.put("rationale", {"text": "B"}, trace_id=trace_b, pinned=True)
    a2 = br.put("prompt_plan", {"text": "PP"}, trace_id=trace_a, pinned=True)

    # OR (القديم) قد يُرجع عناصر زائدة — لا نعتمد عليه في الروابط
    or_list = br.query(type="rationale", trace_id=trace_a, scope="stm", match="or")
    assert any(ev["trace_id"] == trace_a for ev in or_list)

    # AND: يجب أن يرجع فقط rationale ضمن trace_a
    and_list = br.query_by_trace_and_type(trace_a, "rationale", scope = "stm")
    assert all(ev["trace_id"] == trace_a and ev["type"] == "rationale" for ev in and_list)

    # latest helper
    pp = br.latest(trace_a, "prompt_plan", scope="stm")
    assert pp is not None and pp["trace_id"] == trace_a and pp["type"] == "prompt_plan"
