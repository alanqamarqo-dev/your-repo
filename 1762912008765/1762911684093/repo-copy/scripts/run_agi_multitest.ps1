<#
PowerShell helper to run the AGI multidimensional pytest harness.

Usage examples:
  # run permissive (no strict assertion)
  .\scripts\run_agi_multitest.ps1

  # run with strict mode (will set AGI_STRICT=1)
  .\scripts\run_agi_multitest.ps1 -Strict

  # pass custom provider/model/baseurl
  .\scripts\run_agi_multitest.ps1 -Provider ollama -Model 'qwen2.5:7b-instruct' -BaseUrl 'http://127.0.0.1:11434'
#>

param(
    [switch]$Strict,
    [string]$Provider = $(if ($env:AGL_LLM_PROVIDER) { $env:AGL_LLM_PROVIDER } else { 'ollama' }),
    [string]$Model = $(if ($env:AGL_LLM_MODEL) { $env:AGL_LLM_MODEL } else { 'qwen2.5:7b-instruct' }),
    [string]$BaseUrl = $(if ($env:AGL_LLM_BASEURL) { $env:AGL_LLM_BASEURL } else { '' })
)

Write-Host "Running AGI multidimensional test with provider=$Provider model=$Model baseUrl=$BaseUrl strict=$Strict"

# export env vars for the process
$env:AGL_LLM_PROVIDER = $Provider
$env:AGL_LLM_MODEL = $Model
if ($BaseUrl) { $env:AGL_LLM_BASEURL = $BaseUrl }

if ($Strict.IsPresent) { $env:AGI_STRICT = '1' } else { $env:AGI_STRICT = '0' }

# Find a python executable
$pythonCmd = $null
try {
    $pythonCmd = (Get-Command python -ErrorAction SilentlyContinue).Source
} catch { }
if (-not $pythonCmd) {
    try { $pythonCmd = (Get-Command py -ErrorAction SilentlyContinue).Source } catch { }
}
if (-not $pythonCmd) {
    Write-Error "Python not found on PATH. Please ensure Python is installed and available as 'python' or 'py'."
    exit 2
}

# Run the pytest file that was added to the repo
Write-Host "Executing test with: $pythonCmd -m pytest -q tests/test_agi_multidimensional.py"
& $pythonCmd -m pytest -q tests/test_agi_multidimensional.py
$exitCode = $LASTEXITCODE

# Show artifact path if created
$artifact = Join-Path -Path (Get-Item -Path .).FullName -ChildPath "artifacts/agi_multitest_result.json"
if (Test-Path $artifact) {
    Write-Host "Artifact written: $(Resolve-Path $artifact)"
} else {
    Write-Warning "No artifact found at artifacts/agi_multitest_result.json"
}

exit $exitCode
