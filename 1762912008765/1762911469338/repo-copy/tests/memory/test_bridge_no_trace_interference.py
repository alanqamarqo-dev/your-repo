from Core_Memory.bridge_singleton import get_bridge


def _clear_bridge(br):
    try:
        if hasattr(br, 'stm') and hasattr(br.stm, '_od'):
            for k in list(br.stm._od.keys()):
                br.stm.delete(k)
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


def test_no_interference_across_traces():
    br = get_bridge()
    assert br is not None
    _clear_bridge(br)

    t1, t2 = "trace_A", "trace_B"
    # put two events of same type X in different traces
    br.put("X", {"a": 1}, trace_id=t1, pinned=True)
    br.put("X", {"b": 2}, trace_id=t2, pinned=True)

    # query with strict AND should return only events from t1
    r_and = br.query_by_trace_and_type(t1, "X", scope = "stm")
    assert all(ev.get("trace_id") == t1 for ev in r_and)
    assert not any(ev.get("trace_id") == t2 for ev in r_and)
