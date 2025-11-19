param(
    [Parameter(Mandatory = $true)][ValidateSet('Baseline', 'SelfEngineer', 'MergeAuto')] [string]$Command
)

Set-Location -Path (Resolve-Path "$(Split-Path -Parent $MyInvocation.MyCommand.Definition)").Path | Out-Null
Set-Location -Path (Resolve-Path "..").Path | Out-Null

$env:PYTHONPATH = (Get-Location).Path
$env:PYTHONIOENCODING = 'utf-8'

function Ensure-KB {
    if (Test-Path Knowledge_Base\Learned_Patterns.lock.json) {
        Copy-Item Knowledge_Base\Learned_Patterns.lock.json Knowledge_Base\Learned_Patterns.json -Force
    }
}

switch ($Command) {
    'Baseline' {
        Ensure-KB
        .\.venv\Scripts\python.exe scripts\generate_all_reports.py
        .\.venv\Scripts\python.exe -m scripts.safety_suite --out reports\safety_suite
    }
    'SelfEngineer' {
        Ensure-KB
        .\.venv\Scripts\python.exe scripts\self_engineer_run.py --rules configs\self_engineer_rules.json --out reports\self_engineer --sandbox artifacts\self_engineer_runs --loop --max-iters 3 --auto-promote
    }
    'MergeAuto' {
        git checkout -b feat/auto-self-edit
        if (Test-Path reports\self_engineer\patch.diff) {
            git apply --reject --whitespace=fix reports\self_engineer\patch.diff
            git add -A
            git commit -m "Self-Engineer: apply proposed patch (auto)"
        }
    }
}
# Oriented: PowerShell quick-ops for AGL dashboard
# Usage: From project root in PowerShell, run: .\scripts\ops_commands.ps1

# Set environment for scripts
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONPATH = (Get-Location).Path

Write-Output "Generating reports..."
.\.venv\Scripts\python.exe scripts\generate_all_reports.py
.\.venv\Scripts\python.exe scripts\make_models_report.py
.\.venv\Scripts\python.exe scripts\make_visual_report.py
.\.venv\Scripts\python.exe scripts\self_optimize.py --out reports\self_optimization
.\.venv\Scripts\python.exe -m scripts.safety_suite --out reports\safety_suite

Write-Output "Wrote manifest (optional)"
'{"html":["models_report.html","auto_reports/ohm_report.html","auto_reports/power_report.html","safety_suite/safety_report.html"],"json":["safety_suite/safety_report.json","self_optimization/self_optimization.json","last_success.json"]}' | Set-Content -Encoding utf8 reports\report_manifest.json

Write-Output "Starting simple static server on :8000"
python -m http.server 8000
