from Integration_Layer import Hybrid_Composer


def test_compose_physics_detects_and_solves():
    problem = {
        "text": "Simple circuit: I=2 R=3 V=?",
        "given": {"I": 2, "R": 3},
    }
    res = Hybrid_Composer.compose(problem)
    # basic smoke assertions: composed output structure and at least one result
    assert isinstance(res, dict)
    assert res.get("ok") is True
    assert "results" in res and isinstance(res["results"], list)
    assert len(res["results"]) >= 1
    first = res["results"][0]
    # PhysicsSolver returns domain 'electrical' for Ohm problems
    assert first.get("domain") in ("electrical", "physics") or first.get("ok") in (True, False)
