from Learning_System.Self_Engineer import SelfEngineer, quick_smoke


def test_quick_smoke_no_promotion():
    out = quick_smoke()
    assert 'winner' in out or 'runs' in out


def test_rule_based_suggest_task():
    se = SelfEngineer()
    diag = se.diagnose({}, {})
    assert 'suggested_task' in diag
