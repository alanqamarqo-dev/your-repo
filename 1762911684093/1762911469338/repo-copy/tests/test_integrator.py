import pytest


class DummyBridge:
    def __init__(self):
        self.writes = []

    def put(self, t, payload, to='ltm', **kwargs):
        self.writes.append((t, payload, to))


@pytest.fixture(autouse=True)
def patch_ask_engine(monkeypatch):
    """Monkeypatch engine ask helper and the bridge to deterministic stubs."""

    def fake_ask(engine_name, question):
        return {'ok': True, 'text': f"stub_{engine_name}", 'engine': engine_name}

    # Patch the test helper ask_engine if present (non-failing)
    monkeypatch.setattr('tests.helpers.engine_ask.ask_engine', fake_ask, raising=False)

    # Provide a dummy bridge for persistence calls
    dummy = DummyBridge()
    monkeypatch.setattr('Core_Memory.bridge_singleton.get_bridge', lambda: dummy, raising=False)

    yield


def test_integrator_runs_and_returns_structure():
    # import inside test to avoid import-time side effects
    from scripts.run_integrator import AGLIntegrator

    intg = AGLIntegrator()
    res = intg.integrate_query('short test question', timeout_per_engine=1)

    assert isinstance(res, dict)
    assert 'final_answer' in res
    assert 'supporting_evidence' in res
    assert isinstance(res.get('supporting_evidence'), list)
