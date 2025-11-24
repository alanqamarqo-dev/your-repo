param()

$repo = (Resolve-Path "$PSScriptRoot\..").Path
Set-Location $repo

Write-Output "[orchestrate] ensure artifacts dir"
if (-not (Test-Path artifacts)) { New-Item -ItemType Directory -Path artifacts | Out-Null }

Write-Output "[orchestrate] running harvester (mock safe by default)"
$env:AGL_EXTERNAL_INFO_MOCK='1'
if (Test-Path ".venv\Scripts\python.exe") { & .\.venv\Scripts\python.exe .\workers\knowledge_harvester.py } else { python .\workers\knowledge_harvester.py }

Write-Output "[orchestrate] running reasoning cycle"
if (Test-Path ".venv\Scripts\python.exe") { & .\.venv\Scripts\python.exe .\workers\reasoning_cycle.py } else { python .\workers\reasoning_cycle.py }

Write-Output "[orchestrate] evaluating reasoning"
if (Test-Path ".venv\Scripts\python.exe") { & .\.venv\Scripts\python.exe .\tools\evaluate_reasoning.py } else { python .\tools\evaluate_reasoning.py }

Write-Output "[orchestrate] done"
