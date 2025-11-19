$env:AGL_TEST_SCAFFOLD_FORCE = "1"
$env:PYTHONUTF8 = "1"
$env:PYTHONPATH = "repo-copy"
py -3 -m pytest -q tests/test_agi_advanced_eval.py -x --maxfail=1
py -3 -m pytest -q tests/test_agi_eval_weights.py
py -3 -m pytest -q tests/test_registry_adapter.py
