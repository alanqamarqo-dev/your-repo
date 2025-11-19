# CI smoke script: deterministic cohesion check (CI-only)
$env:AGL_EXTERNAL_INFO_MOCK = '1'
$env:AGL_TEST_SCAFFOLD_FORCE = '1'
$env:AGL_REASONER_MODE = 'dkn'
$env:AGL_QUANTUM_MODE = 'simulate'
py -3 .\scripts\integration_cohesion_check.py
