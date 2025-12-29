# AGL_daily_tick.ps1
# Simple daily tick for AGL: runs benchmark (learned_facts) and Taskmaster tick.

$AGL_ROOT = "D:/AGL/repo-copy"
$PYTHON = "D:/AGL/.venv/Scripts/python.exe"

Set-Location $AGL_ROOT
$env:PYTHONPATH = $AGL_ROOT

# Use real mode (not FAST_MODE) so learning persists
$env:AGL_FAST_MODE = "0"
$env:AGL_DEEP_COT = "1"
$env:AGL_DYNAMIC_COGNITION = "1"

Write-Host "=== [AGL] Daily QA Benchmark & Learning ==="
# Run the benchmark which appends to collective_memory and learned_facts
& $PYTHON tools/zero_shot_qa_eval.py

Write-Host "=== [AGL] Taskmaster Tick (Long-Term Projects) ==="
$code = @"
from Self_Improvement.taskmaster import run_taskmaster_tick
from Self_Improvement.projects import ProjectStore

ticks = run_taskmaster_tick(store=ProjectStore(), max_projects=2)
print(f"ticks_done={ticks}")
"@

& $PYTHON -c $code

Write-Host "=== [AGL] Daily tick completed. ==="
