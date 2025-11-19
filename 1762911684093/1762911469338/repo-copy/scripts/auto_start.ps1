<#
scripts/auto_start.ps1 — Unified launcher for server, harvester and UI

Purpose: Ensure environment is configured, then start the ops runner (server+harvester+cron)
and optionally start the local UI. Supports DryRun to preview actions without executing long-running processes.

Usage examples:
  # Dry-run to see actions
  pwsh -ExecutionPolicy Bypass -File .\scripts\auto_start.ps1 -DryRun

  # Start everything (ops runner + UI)
  pwsh -ExecutionPolicy Bypass -File .\scripts\auto_start.ps1 -Mode start -WithUI

  # Stop ops and UI started by this script
  pwsh -ExecutionPolicy Bypass -File .\scripts\auto_start.ps1 -Mode stop
#>

param(
  [ValidateSet('start','stop','status')]
  [string]$Mode = 'start',
  [switch]$WithUI,
  [switch]$DryRun
)

$Root = (Resolve-Path $PSScriptRoot).Path
Set-Location $Root

function Log { param($s) $s | Out-File -FilePath (Join-Path $Root 'artifacts\logs\auto_start.log') -Append -Encoding utf8; Write-Output $s }

# Ensure logs dir
if (-not (Test-Path (Join-Path $Root 'artifacts\logs'))) { New-Item -ItemType Directory -Force -Path (Join-Path $Root 'artifacts\logs') | Out-Null }

# discover python similarly to run_all
$venvPy = Join-Path $Root '.venv\Scripts\python.exe'
$pyCandidates = @($venvPy, 'py.exe', 'python.exe')
function Find-Python { foreach ($c in $pyCandidates) { if (Test-Path $c) { return $c } try { $ver = & $c -V 2>&1; if ($LASTEXITCODE -eq 0 -or $ver) { return $c } } catch {} } return $null }
$py = Find-Python
if (-not $py) { Log 'No python found; please create .venv or ensure python on PATH'; if ($DryRun) { exit 0 } else { exit 1 } }

# Base environment for ops
$envVars = @{
  'AGL_USE_ORCHESTRATOR' = '1'
  'AGL_EXTERNAL_INFO_IMPL' = 'openai_engine'
  'AGL_OPENAI_KB_CACHE_ENABLE' = '0'
  'AGL_EXTERNAL_INFO_ENABLED' = '1'
  'PYTHONUTF8' = '1'
  'PYTHONIOENCODING' = 'utf-8'
}

if ($DryRun) { Log 'DryRun mode: will not start processes. Showing environment to set:' }
foreach ($k in $envVars.Keys) {
  if ($DryRun) {
    Log "  $k = $($envVars[$k])"
  } else {
    # Use Set-Item to set environment variables dynamically
    try {
      $p = "env:$k"
      Set-Item -Path $p -Value $envVars[$k] -Force
      Log "Set $k"
    } catch {
      $err = if ($_.Exception) { $_.Exception.Message } else { $_ }
      Log ("Failed to set env var {0}: {1}" -f $k, $err)
    }
  }
}

$opsRunner = Join-Path $Root 'ops_full_run.ps1'

switch ($Mode) {
  'start' {
    Log "Starting AGL (Mode=start) [DryRun=$DryRun] using Python: $py"
    if (-not (Test-Path $opsRunner)) { Log "ops_full_run.ps1 not found at $opsRunner; aborting"; exit 1 }

    if ($DryRun) {
      Log "DryRun: would start ops runner: pwsh -ExecutionPolicy Bypass -File $opsRunner -Mode start"
    } else {
      Log "Launching ops runner..."
      Start-Process -FilePath 'pwsh' -ArgumentList ('-NoProfile','-ExecutionPolicy','Bypass','-File',"$opsRunner",'-Mode','start') -WindowStyle Hidden | Out-Null
      Log "Ops runner started (check artifacts/logs/ops_main.log and logs/* for details)"
    }

    if ($WithUI) {
      $uiScript = Join-Path $Root 'AGL_UI\main.py'
      if (-not (Test-Path $uiScript)) { Log "UI script not found at $uiScript; skipping UI start" } else {
        if ($DryRun) { Log "DryRun: would run UI: & $py $uiScript" } else {
          Log "Starting local UI (AGL_UI/main.py)"
          # Start UI in its own process so ops runner continues
          Start-Process -FilePath $py -ArgumentList "$uiScript" -WorkingDirectory $Root | Out-Null
          Log "UI started (window may appear)."
        }
      }
    } else { Log "WithUI not set; skipping UI start." }
  }

  'stop' {
    Log "Stopping AGL jobs and UI (if started)"
    if ($DryRun) { Log "DryRun: would call ops_full_run.ps1 -Mode stop" } else {
      try { Start-Process -FilePath 'pwsh' -ArgumentList ('-NoProfile','-ExecutionPolicy','Bypass','-File',"$opsRunner",'-Mode','stop') -Wait -NoNewWindow | Out-Null } catch { Log "Failed to run ops stop: $_" }
      # try to kill any python process that runs AGL_UI\main.py (best-effort)
      Get-CimInstance Win32_Process -Filter "Name='python.exe'" | ForEach-Object {
        $cmd = $_.CommandLine
        if ($cmd -and $cmd -match 'AGL_UI\\main.py') {
          Log "Stopping UI process: $($_.ProcessId)"
          try { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } catch {}
        }
      }
      Log "Stop sequence issued."
    }
  }

  'status' {
    Log "AGL status:"; 
    if ($DryRun) { Log "DryRun: would show jobs and UI status" } else {
      Log "Jobs:"; Get-Job | Where-Object { $_.Name -like 'AGL_*' } | Format-Table -AutoSize | Out-String | Log
      Log "Python UI processes (AGL_UI/main.py):"
      Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -match 'AGL_UI\\main.py' } | Select-Object ProcessId,CommandLine | Format-Table -AutoSize | Out-String | Log
    }
  }
}

Log "auto_start.ps1 completed (Mode=$Mode, WithUI=$WithUI, DryRun=$DryRun)"
