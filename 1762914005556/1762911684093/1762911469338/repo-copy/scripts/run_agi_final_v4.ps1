param(
    [string]$AGL_SUT = "tests.fixtures.local_sut:generate",
    [string]$PY = "D:\\AGL\\.venv\\Scripts\\python.exe"
)

# Script to run the AGI Final v4 pytest with environment defaults (PowerShell)
# Usage:
#   .\scripts\run_agi_final_v4.ps1               # uses local shim
#   .\scripts\run_agi_final_v4.ps1 -AGL_SUT 'tests.fixtures.http_sut:call'

$root = Resolve-Path -Relative "."
Write-Host "Running AGI Final v4 test from: $root"

$env:PYTHONPATH = "D:\AGL\repo-copy"
$env:AGL_TEST_SCAFFOLD_FORCE = '1'
$env:AGL_LLM_PROVIDER = 'offline'
$env:AGL_SUT = $AGL_SUT

Write-Host "Using AGL_SUT=$env:AGL_SUT"

# Run pytest for the specific test file
& $PY -m pytest tests\agi\test_final_v4.py -q -s

$exitCode = $LASTEXITCODE
if ($exitCode -ne 0) {
    Write-Error "pytest exited with code $exitCode"
    exit $exitCode
}

Write-Host "Finished. Artifacts written to artifacts\agi_final_v4\"
exit 0
