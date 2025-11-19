<#
start_harvester.ps1
Helper to run the knowledge harvester in this repo on Windows PowerShell.

Usage:
  - Run interactively and the script will use $env:OPENAI_API_KEY if set.
  - Or pass -ApiKey 'sk-...'

Example:
  .\start_harvester.ps1 -ApiKey 'sk-...'

Security: this script sets the API key in the current session only. Do NOT commit keys.
#>
[CmdletBinding()]
param(
    [string]$ApiKey
    ,[switch]$OpsRecipe
)

Set-Location $PSScriptRoot
# use venv in repo root
$venv = Join-Path $PSScriptRoot ".venv\Scripts\Activate.ps1"
if (-Not (Test-Path $venv)) {
    Write-Error "Virtualenv activate script not found at $venv. Activate your venv manually or create one."
    exit 2
}

if (-not $ApiKey) {
    if ($env:OPENAI_API_KEY) {
        Write-Output "Using OPENAI_API_KEY from environment (session)."
    } else {
        Write-Host "OPENAI_API_KEY not found in environment. You can paste it now (input hidden)."
        $secure = Read-Host -AsSecureString "Enter OPENAI_API_KEY (input hidden)" -ErrorAction SilentlyContinue
        if ($secure -and $secure.Length -gt 0) {
            $ApiKey = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure))
        }
    }
}

if ($ApiKey) { $env:OPENAI_API_KEY = $ApiKey }

# Ensure UTF-8 runtime
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:AGL_EXTERNAL_INFO_ENABLED = '1'
$env:PYTHONPATH = (Get-Location).Path

# === تفعيل الحفظ التلقائي للذاكرة والتحسين التلقائي إذا لم تكن مُعرفة ===
if (-not $env:AGL_MEMORY_PERSIST) { $env:AGL_MEMORY_PERSIST = '1'; Write-Output "Setting AGL_MEMORY_PERSIST=1" }
if (-not $env:AGL_AUTO_TUNE) { $env:AGL_AUTO_TUNE = '1'; Write-Output "Setting AGL_AUTO_TUNE=1" }
# Optional: external provider model; leave unchanged if user set it before calling
if ($env:AGL_EXTERNAL_INFO_MODEL) { Write-Output "Using external info model: $env:AGL_EXTERNAL_INFO_MODEL" } else { Write-Output "AGL_EXTERNAL_INFO_MODEL not set; using default provider model" }

# Activate venv and run harvester in a loop, logging output
. $venv
$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$harvester = Join-Path $PSScriptRoot "workers\knowledge_harvester.py"
$log = Join-Path $PSScriptRoot "artifacts\harvester.log"

# Ensure only a single instance of this script runs at a time to avoid concurrent harvests
$mutexName = 'Global\AGL_Harvester_Mutex'
$mutex = New-Object System.Threading.Mutex($false, $mutexName)
$hasHandle = $false
try {
    try { $hasHandle = $mutex.WaitOne(0) } catch { $hasHandle = $false }
    if (-not $hasHandle) {
        Write-Output "Another harvester instance is already running (mutex='$mutexName'). Exiting."
        exit 0
    }
} catch {
    Write-Warning "Failed to acquire single-instance mutex: $_"
}

if (-not (Test-Path (Split-Path $log))) { New-Item -ItemType Directory -Path (Split-Path $log) -Force | Out-Null }

Write-Output "Starting harvester. Logging to $log"
Write-Output "Press Ctrl+C to stop."

# If enabled, start the watcher that triggers training/automation on new harvested facts
if ($env:AGL_AUTO_TRAIN -and $env:AGL_AUTO_TRAIN -ne '0') {
    $watcher = Join-Path $PSScriptRoot 'scripts\watch_and_train.py'
    if (Test-Path $watcher) {
        $autoLog = Join-Path $PSScriptRoot 'artifacts\auto_train.log'
        Write-Output "Starting background auto-train watcher (watch_and_train.py). Logs -> $autoLog"

        # Build an explicit --cmds argument from a set of known training/automation scripts if they exist
        $candidateScripts = @(
            'scripts\calibrate_fusion_weights.py',
            'scripts\phase_g_save_patterns.py',
            'scripts\refine_and_retrain_weak_models.py',
            'scripts\self_engineer_run.py',
            'scripts\fine_tune_self_engineer.py'
        )
        $foundCmds = @()
        foreach ($s in $candidateScripts) {
            $full = Join-Path $PSScriptRoot $s
            if (Test-Path $full) {
                # prefer invoking via the repo venv python executable for consistency
                $foundCmds += "`"$python`" `"$full`""
            }
        }

        if ($foundCmds.Count -gt 0) {
            $cmdsArg = [string]::Join("`n", $foundCmds)
            $cmdFile = Join-Path $PSScriptRoot 'artifacts\auto_train_cmds.txt'
            Write-Output "Writing watcher commands to $cmdFile"
            if (-not (Test-Path (Split-Path $cmdFile))) { New-Item -ItemType Directory -Path (Split-Path $cmdFile) -Force | Out-Null }
            Set-Content -Path $cmdFile -Value $cmdsArg -Encoding UTF8
            Write-Output "Watcher will run commands from file: $cmdFile"
            # Start watcher with explicit --cmds-file argument so it reads the prepared commands
            Start-Process -FilePath $python -ArgumentList @($watcher, '--cmds-file', $cmdFile) -NoNewWindow -WindowStyle Hidden
        } else {
            Write-Output "No candidate training scripts found under scripts/. Not starting auto-train watcher. To enable, add training scripts or set AGL_AUTO_TRAIN with an explicit cmds-file."
            Write-Output "Checked candidate scripts:" 
            foreach ($s in $candidateScripts) { Write-Output " - $s : " + (Test-Path (Join-Path $PSScriptRoot $s)) }
        }
    } else {
        Write-Output "watch_and_train.py not found at $watcher; auto-train disabled."
    }
}

# === خطوة 4: التقارير والتقييم ===
Write-Host "[AGL-V] generating reports"
if (Test-Path "scripts\generate_all_reports.py") {
    & $python (Join-Path $PSScriptRoot 'scripts\generate_all_reports.py')
}
& $python (Join-Path $PSScriptRoot 'tools\run_eval50.py')
& $python (Join-Path $PSScriptRoot 'tools\print_theory.py')
try {
    if ($OpsRecipe) {
        Write-Output "Running ops recipe: py scripts\ops_full_automation.py"
        & $python (Join-Path $PSScriptRoot 'scripts\ops_full_automation.py') 2>&1 | Tee-Object -FilePath $log -Append
        Write-Output "Ops recipe completed."
    } else {
        while ($true) {
            try {
                & $python $harvester 2>&1 | Tee-Object -FilePath $log -Append
                # === بعد كل دفعة حصاد: تقليل التكرار ورفع جدّة الحقائق ===
                try {
                    Write-Output "[AGL-V] post-harvest: running coverage_booster, cleanup_artifacts, make_visual_report"
                    $cov = Join-Path $PSScriptRoot 'scripts\coverage_booster.py'
                    if (Test-Path $cov) {
                        & $python $cov 2>&1 | Tee-Object -FilePath $log -Append
                    } else {
                        Write-Output "coverage_booster.py not found at $cov, skipping."
                    }
                } catch {
                    Write-Warning "coverage_booster failed: $_"
                }
                try {
                    $cleanup = Join-Path $PSScriptRoot 'scripts\cleanup_artifacts.py'
                    if (Test-Path $cleanup) {
                        & $python $cleanup '--dedup' 'strong' 2>&1 | Tee-Object -FilePath $log -Append
                    } else {
                        Write-Output "cleanup_artifacts.py not found at $cleanup, skipping."
                    }
                } catch {
                    Write-Warning "cleanup_artifacts failed: $_"
                }
                try {
                    $viz = Join-Path $PSScriptRoot 'scripts\make_visual_report.py'
                    if (Test-Path $viz) {
                        & $python $viz 2>&1 | Tee-Object -FilePath $log -Append
                    } else {
                        Write-Output "make_visual_report.py not found at $viz, skipping."
                    }
                } catch {
                    Write-Warning "make_visual_report failed: $_"
                }
                    try {
                        $cleaner = Join-Path $PSScriptRoot 'scripts\clean_harvested_facts.py'
                        if (Test-Path $cleaner) {
                            Write-Output "Running harvested facts cleaner: $cleaner"
                            & $python $cleaner 2>&1 | Tee-Object -FilePath $log -Append
                        } else {
                            Write-Output "clean_harvested_facts.py not found at $cleaner, skipping."
                        }
                    } catch {
                        Write-Warning "clean_harvested_facts failed: $_"
                    }
            } catch {
                Write-Error $_
            }
            Start-Sleep -Seconds 5
        }
    }
} finally {
        # === خطوة 5: ملخص نهائي ===
        Write-Host "`n==== AGL-V SUMMARY ===="
        if (Test-Path "artifacts\harvest_progress.json") {
            Get-Content artifacts\harvest_progress.json -Raw | Write-Output
        }
        if (Test-Path "artifacts\rag_eval.jsonl") {
            Write-Host "`nEval stats (rag_eval.jsonl tail):"
            Get-Content artifacts\rag_eval.jsonl -Tail 3 | Write-Output
        }
        if (Test-Path "reports\theory_report.html") {
            Write-Host "`nTheory report -> reports\theory_report.html"
        }
        Write-Host "Done."
    try {
        if ($hasHandle) { $mutex.ReleaseMutex() | Out-Null }
        if ($mutex) { $mutex.Dispose() }
    } catch {
        Write-Warning "Failed to release mutex: $_"
    }
}
