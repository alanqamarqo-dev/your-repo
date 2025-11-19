@'

# Local Scaffold Smoke

Set-Location D:\AGL\repo-copy
$env:AGL_TEST_SCAFFOLD_FORCE="1"
$env:PYTHONUTF8="1"
$env:PYTHONPATH="repo-copy"

# Run the advanced smoke + guard tests

py -3 -m pytest -q tests/test_agi_advanced_eval.py -x --maxfail=1
py -3 -m pytest -q tests/test_agi_eval_weights.py
py -3 -m pytest -q tests/test_registry_adapter.py

# Turn scaffold OFF to use baseline weights/behavior

# Remove-Item Env:\AGL_TEST_SCAFFOLD_FORCE

'@ | Set-Content docs\LOCAL_SCAFFOLD_SMOKE.md
