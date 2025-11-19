<#
Runs a full AGL cycle (harvest+reasoning+eval+reports+theory+save) and logs output.
Designed to be invoked by Task Scheduler once per hour.
#>
Push-Location (Split-Path -Path "$MyInvocation.MyCommand.Definition" -Parent) | Out-Null
Push-Location ".."  # go to repo root (D:\AGL)

$log = "artifacts\scheduler.log"
[void](New-Item -Path $log -ItemType File -Force)

function Log($msg) {
    $ts = (Get-Date).ToString('o')
    "$ts  $msg" | Out-File -FilePath $log -Append -Encoding utf8
}

Log "=== AGL hourly cycle start ==="

# Environment toggles you can edit before scheduling
$env:AGL_AUTO_TUNE = '1'
$env:AGL_THEORY_MIN_CONF = '0.7'
$env:AGL_THEORY_MIN_COH = '0.6'
$env:AGL_MEMORY_PERSIST = '1'

try {
    Log "Running orchestrator: scripts\run_agl4.py"
    & py scripts\run_agl4.py 2>&1 | ForEach-Object { Log $_ }

    Log "Running evaluation: tools\run_eval50.py"
    & py tools\run_eval50.py 2>&1 | ForEach-Object { Log $_ }

    Log "Generating reports: scripts\generate_all_reports.py"
    & py scripts\generate_all_reports.py 2>&1 | ForEach-Object { Log $_ }

    Log "Running theory pipeline: tools\run_theory.py"
    & py tools\run_theory.py 2>&1 | ForEach-Object { Log $_ }

    Log "Saving eligible theories to memory"
    & py -c "from infra.adaptive.AdaptiveMemory import save_theory_items; print('saved', save_theory_items('artifacts/theory_bundle.json', min_conf=0.7, min_coherence=0.6))" 2>&1 | ForEach-Object { Log $_ }

    Log "=== AGL hourly cycle complete ==="
} catch {
    Log "ERROR: $_"
}

Pop-Location; Pop-Location
