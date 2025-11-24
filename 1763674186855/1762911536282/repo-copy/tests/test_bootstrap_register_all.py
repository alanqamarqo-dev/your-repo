import types
import sys


def test_bootstrap_register_all_dict_registry(monkeypatch):
    # تجهيز MODULE وهمي بمحرك بسيط
    fake_mod = types.ModuleType("Core_Engines.FakeEngine")
    class FakeEngine:
        def __init__(self, config=None):
            self.name = "FakeEngine"
            self._cfg = config
        def process_task(self, x):
            return {"ok": True, "in": x, "cfg": self._cfg}

    def create_engine(config=None):
        return FakeEngine(config=config)

    fake_mod.create_engine = create_engine
    sys.modules["Core_Engines.FakeEngine"] = fake_mod

    # حقن SPEC مؤقتًا
    import Core_Engines as CE
    original_specs = CE.ENGINE_SPECS.copy()
    try:
        CE.ENGINE_SPECS["FakeEngine"] = ("Core_Engines.FakeEngine", None)
        reg = {}
        out = CE.bootstrap_register_all_engines(registry=reg, config={"x": 1}, verbose=True)
        assert "FakeEngine" in out
        assert "FakeEngine" in reg
        assert reg["FakeEngine"].process_task({"a": 2})["cfg"] == {"x": 1}
    finally:
        CE.ENGINE_SPECS = original_specs
        # تنظيف
        sys.modules.pop("Core_Engines.FakeEngine", None)
