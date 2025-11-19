<#
Run the enhanced strategic planner with sensible defaults and options.

Usage examples:
  # Mock RAG mode, 500 MC iterations, use sample stakeholders
  pwsh -ExecutionPolicy Bypass -File .\scripts\run_strategic_planner.ps1 -UseMock -Stakeholders configs/sample_stakeholders.json -MCIterations 500 -UseRag

  # Live RAG (requires OPENAI_API_KEY set in the session)
  pwsh -ExecutionPolicy Bypass -File .\scripts\run_strategic_planner.ps1 -Years 5 -Budget 12.5 -MCIterations 100 -Stakeholders configs/sample_stakeholders.json -UseRag
#>
param(
    [switch]$UseMock,
    [string]$Stakeholders = 'configs/sample_stakeholders.json',
    [int]$MCIterations = 0,
    [int]$Years = 5,
    [double]$Budget = 10.0,
    [switch]$UseRag,
    [string]$PythonExe = '.\.venv\Scripts\python.exe'
)

$Root = (Resolve-Path $PSScriptRoot).Path
Set-Location $Root

if ($UseMock) { $env:AGL_EXTERNAL_INFO_MOCK = '1' } else { Remove-Item env:AGL_EXTERNAL_INFO_MOCK -ErrorAction SilentlyContinue }

if ($UseRag -and -not $UseMock) {
    # Ensure OPENAI_API_KEY present for live RAG
    if (-not $env:OPENAI_API_KEY) {
        Write-Host "WARNING: --UseRag requested but OPENAI_API_KEY not set in session. RAG live will likely fail."
    }
}

# Build args

$plannerArgs = @()
$plannerArgs += '--objective'; $plannerArgs += 'تطوير نظام AGI متعدد المجالات'
$plannerArgs += '--years'; $plannerArgs += $Years.ToString()
$plannerArgs += '--budget'; $plannerArgs += $Budget.ToString()
if ($Stakeholders) { $plannerArgs += '--stakeholders-file'; $plannerArgs += $Stakeholders }
if ($MCIterations -gt 0) { $plannerArgs += '--mc-iterations'; $plannerArgs += $MCIterations.ToString() }
if ($UseRag) { $plannerArgs += '--use-rag' }

Write-Host "Running strategic planner with args: $($plannerArgs -join ' ')"
& $PythonExe '.\scripts\strategic_advanced_planner.py' @plannerArgs

if ($LASTEXITCODE -ne 0) { Write-Error "Strategic planner exited with code $LASTEXITCODE"; exit $LASTEXITCODE }
Write-Host "Strategic planner finished successfully. Check artifacts/reports for the generated report."
