<#
run_all.ps1 — Full repo automation wrapper
Purpose: Create/ensure .venv, install requirements, run tests, start long-running ops (ops_full_run.ps1), then run smoke/meta scripts.
Usage:
  pwsh -ExecutionPolicy Bypass -File .\run_all.ps1            # normal run (interactive)
  pwsh -ExecutionPolicy Bypass -File .\run_all.ps1 -DryRun   # show steps, don't execute long-running actions

This script is conservative: it uses the repo's .venv if present, otherwise attempts to create one using the first available python (py, python). It logs key steps into artifacts/logs.
#>
param(
    [switch]$DryRun
)

$Root = (Resolve-Path $PSScriptRoot).Path
Set-Location $Root

$Artifacts = Join-Path $Root 'artifacts'
$Logs = Join-Path $Artifacts 'logs'
if (-not (Test-Path $Logs)) { New-Item -ItemType Directory -Force -Path $Logs | Out-Null }
$logFile = Join-Path $Logs "run_all.log"
function Log { param($s) $s | Out-File -FilePath $logFile -Append -Encoding utf8; Write-Output $s }

# Find / prepare python executable
$venvPy = Join-Path $Root '.venv\Scripts\python.exe'
$pyCandidates = @($venvPy, 'py.exe', 'python.exe')
function Find-Python { foreach ($c in $pyCandidates) { if (Test-Path $c) { return $c } try { $ver = & $c -V 2>&1; if ($LASTEXITCODE -eq 0 -or $ver) { return $c } } catch {} } return $null }
$py = Find-Python

if (-not $py) {
    Log "No python executable detected on PATH or .venv. Attempting to use 'py' to create .venv."
    if ($DryRun) { Log "DryRun: would run: py -3 -m venv .venv" } else {
        try { & py -3 -m venv .venv; $py = $venvPy } catch { Log "Failed to create .venv automatically. Please install Python or create .venv manually."; exit 1 }
    }
}
if (-not $py -and (Test-Path $venvPy)) { $py = $venvPy }

if (-not $py) { Log "No Python available; aborting."; exit 1 }
Log "Using Python: $py"

# Install requirements if any
$reqPinned = Join-Path $Root 'requirements-pinned.txt'
$req = Join-Path $Root 'requirements.txt'
if (Test-Path $reqPinned) { $reqToUse = $reqPinned } elseif (Test-Path $req) { $reqToUse = $req } else { $reqToUse = $null }
if ($reqToUse) {
    if ($DryRun) { Log "DryRun: would run: & $py -m pip install -r $reqToUse" } else {
        Log "Installing requirements from: $reqToUse"
        & $py -m pip install --upgrade pip setuptools wheel | Out-Null
        & $py -m pip install -r $reqToUse | Tee-Object -FilePath $logFile -Append
    }
} else { Log "No requirements file found; skipping pip install." }

# Run tests if pytest installed
$pytestExists = $false
try { & $py -m pytest -q --version > $null 2>&1; if ($LASTEXITCODE -eq 0) { $pytestExists = $true } } catch {}
if ($pytestExists) {
    if ($DryRun) { Log "DryRun: would run: & $py -m pytest -q" } else {
        Log "Running pytest..."
        & $py -m pytest -q | Tee-Object -FilePath $logFile -Append
    }
} else { Log "pytest not available in environment; skipping test run." }

# ---------------- Integration tests / system cohesion check ----------------
Log "Looking for integration tests (tests/test_integration_*.py)"
$integPattern = Join-Path $Root 'tests\test_integration_*.py'
# Collect integration test files using the pattern we just formed
$integFiles = Get-ChildItem -Path (Split-Path $integPattern) -Filter (Split-Path $integPattern -Leaf) -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName }
$integFiles = Get-ChildItem -Path (Join-Path $Root 'tests') -Filter 'test_integration_*.py' -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName }
if ($integFiles -and $integFiles.Count -gt 0) {
    $integLog = Join-Path $Logs 'integration_tests.log'
    if ($DryRun) {
        Log "DryRun: would run integration tests: & $py -m pytest $($integFiles -join ' ') | Tee-Object -FilePath $integLog -Append"
    } else {
        Log "Running integration tests: $($integFiles -join ', ')"
        # Run pytest for integration files and capture output
        try {
            & $py -m pytest $integFiles 2>&1 | Tee-Object -FilePath $integLog -Append
            $rc = $LASTEXITCODE
        } catch {
            Log "Error running pytest: $($_)"
            $rc = 2
        }

        # Parse pytest summary from the log to compute simple cohesion metric
        $summary = Get-Content $integLog -Tail 200 -ErrorAction SilentlyContinue | Select-String -Pattern "=+ .* in .*s" -AllMatches | ForEach-Object { $_.ToString() }
        $summaryText = $summary -join "`n"
        # Try to extract numbers: X passed, Y failed, Z skipped, W errors
        $passed = 0; $failed = 0; $errors = 0; $skipped = 0
        if ($summaryText) {
            if ($summaryText -match '(\d+) passed') { $passed = [int]$Matches[1] }
            if ($summaryText -match '(\d+) failed') { $failed = [int]$Matches[1] }
            if ($summaryText -match '(\d+) errors') { $errors = [int]$Matches[1] }
            if ($summaryText -match '(\d+) skipped') { $skipped = [int]$Matches[1] }
        }
        $totalRun = $passed + $failed + $errors
        if ($totalRun -eq 0) { $cohesion = 0 } else { $cohesion = [math]::Round(($passed / $totalRun) * 100, 1) }
        Log "Integration tests result: passed=$passed failed=$failed errors=$errors skipped=$skipped -> cohesion=$cohesion% (based on passed/(passed+failed+errors))"

        # If cohesion low, abort starting long-running services
        $threshold = 80.0
        if ($cohesion -lt $threshold) {
            Log "Cohesion ($cohesion%) below threshold $threshold% — aborting ops runner start. Check $integLog for details."
            Write-Output "Integration cohesion check failed: $cohesion% (< $threshold%). See $integLog"
            exit 1
        }
    }
} else {
    Log "No integration test files found (tests/test_integration_*.py); skipping integration test step."
}

# Start ops runner (ops_full_run.ps1) — it manages server/harvester/cron jobs.
$opsRunner = Join-Path $Root 'ops_full_run.ps1'
if (Test-Path $opsRunner) {
    if ($DryRun) { Log "DryRun: would start ops runner: pwsh -ExecutionPolicy Bypass -File $opsRunner -Mode start" } else {
        Log "Starting ops runner (server + harvester + cron) via ops_full_run.ps1"
        try { & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $opsRunner -Mode start | Tee-Object -FilePath $logFile -Append } catch { Log "Failed to invoke ops runner: $_" }
    }
} else { Log "ops_full_run.ps1 not found; skipping ops runner start." }

# ---- Start AGL-V expansion/integration (if present) ----
$aglV = Join-Path $Root 'scripts\AGL_V_Expansion.ps1'
if (Test-Path $aglV) {
    if ($DryRun) { Log "DryRun: would run AGL-V expansion: powershell.exe -NoProfile -ExecutionPolicy Bypass -File $aglV" } else {
        Log "Invoking AGL-V expansion script: $aglV"
        try { & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $aglV | Tee-Object -FilePath $logFile -Append } catch { Log "AGL-V expansion failed: $_" }
    }
} else {
    Log "AGL-V expansion script not found; skipping." 
}

# Invoke strategic planner automation if present
$strategicRunner = Join-Path $Root 'scripts\run_strategic_planner.ps1'
if (Test-Path $strategicRunner) {
    if ($DryRun) { Log "DryRun: would run strategic planner: pwsh -ExecutionPolicy Bypass -File $strategicRunner -UseMock -Stakeholders configs/sample_stakeholders.json -MCIterations 100 -UseRag" } else {
        Log "Running strategic planner automation"
        try { & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $strategicRunner -UseMock -Stakeholders configs/sample_stakeholders.json -MCIterations 100 -UseRag | Tee-Object -FilePath $logFile -Append } catch { Log "Strategic planner run failed: $_" }
    }
} else {
    Log "Strategic planner automation not found; skipping."
}

# Run smoke/self/meta scripts
$scriptsToRun = @(
    'scripts\run_smoke_self_engine.py',
    'scripts\run_meta_reasoner.py',
    'scripts\test_meta_learning_autonomy.py'
)
foreach ($s in $scriptsToRun) {
    $path = Join-Path $Root $s
    if (Test-Path $path) {
        if ($DryRun) { Log "DryRun: would run: & $py $path" } else {
            Log "Running: $s"
            try { & $py $path 2>&1 | Tee-Object -FilePath $logFile -Append } catch { Log ("Error running {0}: {1}" -f $s, $($_)) }
        }
    } else { Log "Script missing, skipping: $s" }
}

Log "run_all.ps1 completed (DryRun=$DryRun). See $logFile for details."
if ($DryRun) { exit 0 } else { exit 0 }
