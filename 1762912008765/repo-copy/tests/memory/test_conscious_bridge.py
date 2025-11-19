from Core_Memory.Conscious_Bridge import ConsciousBridge


def test_bridge_put_link_query():
    cb = ConsciousBridge(stm_capacity=4)
    t = "trace-xyz"
    a = cb.put("goal", {"text":"ارفع الاحتفاظ"}, trace_id=t, ttl_s=60)
    b = cb.put("metric", {"retention":0.62}, trace_id=t)
    assert cb.link(a, b, "measured_by")
    q = cb.query(trace_id=t)
    assert len(q) >= 2
