# AGL_taskmaster_tick_only.ps1
# Run Taskmaster tick only (no benchmark, no external model calls)

$AGL_ROOT = "D:/AGL/repo-copy"
$PYTHON = "D:/AGL/.venv/Scripts/python.exe"

Set-Location $AGL_ROOT
$env:PYTHONPATH = $AGL_ROOT

# Use real mode but we are not running benchmark so this is just for consistency
$env:AGL_FAST_MODE = "0"
$env:AGL_DEEP_COT = "1"
$env:AGL_DYNAMIC_COGNITION = "1"

Write-Host "=== [AGL] Taskmaster Tick ONLY (no benchmark) ==="

# Call python directly with an inline command (avoid PowerShell interpolation issues)
& $PYTHON -c "from Self_Improvement.taskmaster import run_taskmaster_tick; from Self_Improvement.projects import ProjectStore; ticks = run_taskmaster_tick(store=ProjectStore(), max_projects=2); print('ticks_done=' + str(ticks))"

Write-Host "=== [AGL] Tick-only done. ==="
