import importlib, os


def _reload_with_env(val: str | None):
    # prepare environment
    if val is None:
        os.environ.pop("AGL_TEST_SCAFFOLD_FORCE", None)
    else:
        os.environ["AGL_TEST_SCAFFOLD_FORCE"] = val
    # reload module after env change
    if "agi_eval" in list(importlib.sys.modules.keys()):
        del importlib.sys.modules["agi_eval"]
    import agi_eval
    return agi_eval


def test_weights_baseline_when_scaffold_off():
    mod = _reload_with_env(None)  # env var not set
    W = mod.WEIGHTS
    # ensure it's not the scaffold weights (fewshot should be non-zero)
    assert W["fewshot"] != 0.00, "Baseline weights expected (fewshot should be non-zero)."


def test_weights_scaffold_when_on():
    mod = _reload_with_env("1")
    W = mod.WEIGHTS
    # ensure it's the scaffold weights (values per config)
    assert W["fewshot"] == 0.00 and abs(W["flex"] - 0.43) < 1e-6
