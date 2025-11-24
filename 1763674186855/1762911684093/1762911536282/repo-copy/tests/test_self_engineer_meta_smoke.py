def test_meta_improvement_cycle_smoke():
    from Learning_System.Self_Engineer import SelfEngineer
    se = SelfEngineer()
    out = se.meta_improvement_cycle(test_reports=[{"type": "pytest", "payload": {"failures": []}}], max_candidates=2)
    assert isinstance(out, list)
