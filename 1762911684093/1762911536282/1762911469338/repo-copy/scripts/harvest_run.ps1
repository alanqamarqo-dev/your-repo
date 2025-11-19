<#
One-shot harvest run script: Run -> Verify -> Store -> Report
Usage: .\scripts\harvest_run.ps1
#>
param()

# Environment
$env:AGL_EXTERNAL_INFO_ENABLED='1'
$env:AGL_EXTERNAL_INFO_MOCK=''
$env:AGL_EXTERNAL_INFO_MODEL='qwen2.5:7b-instruct'
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'

$repo = (Resolve-Path "$PSScriptRoot\..").Path
Set-Location $repo

$log = Join-Path $repo 'artifacts\harvester.log'
$logsDir = Join-Path $repo 'artifacts\logs'
$progressFile = Join-Path $repo 'artifacts\harvest_progress.json'
$harvested = Join-Path $repo 'artifacts\harvested_facts.jsonl'
$reviewFile = Join-Path $repo 'artifacts\harvest_review.jsonl'

# Rotate daily
if (-not (Test-Path $logsDir)) { New-Item -ItemType Directory -Path $logsDir | Out-Null }
$d = Get-Date -Format "yyyyMMdd_HHmm"
if (Test-Path $log) {
    Copy-Item $log (Join-Path $logsDir "harvester_$d.log") -Force
    Clear-Content $log
}

# Run harvester (single iteration)
Write-Output "[run] Starting harvester (model=$($env:AGL_EXTERNAL_INFO_MODEL))"
$harvCmd = "& '$repo\.venv\Scripts\python.exe' '$repo\workers\knowledge_harvester.py'"
# Run and capture exit code
Invoke-Expression $harvCmd
$rc = $LASTEXITCODE
if ($rc -ne 0) {
    Add-Content -Path (Join-Path $repo 'artifacts\alerts.log') -Value "$(Get-Date) HARVEST_FAIL rc=$rc"
    Write-Output "[run] Harvester exited with code $rc"
}

# Verify / Validate - try to run existing verification tools if they exist
Write-Output "[verify] Running verifiers and progress tools"
$toolsRan = @()
if (Test-Path "$repo\tools\harvest_progress.py") {
    & .\.venv\Scripts\python.exe "$repo\tools\harvest_progress.py" --last 5; $toolsRan += 'harvest_progress'
}
if (Test-Path "$repo\tools\print_tail.py") {
    & .\.venv\Scripts\python.exe "$repo\tools\print_tail.py" "$harvested" 5; $toolsRan += 'print_tail'
}
if (Test-Path "$repo\tools\run_eval50.py") {
    & .\.venv\Scripts\python.exe "$repo\tools\run_eval50.py"; $toolsRan += 'run_eval50'
}

# Postprocess: apply quality gates and write accepted/rejected records
Write-Output "[postprocess] Applying quality gates"
if (Test-Path "$repo\tools\harvest_postprocess.py") {
    & .\.venv\Scripts\python.exe "$repo\tools\harvest_postprocess.py" --min-confidence 0.7; $toolsRan += 'postprocess'
} else {
    Write-Output '[postprocess] tools/harvest_postprocess.py not found'
}

# Summarize accepted/rejected facts from the last run
Write-Output "[report] Summarizing last run"

# Prefer the progress file written by postprocess if it exists (avoid overwriting postprocess counts)
$proposed = 0; $accepted = 0; $rejected = 0; $topSources = @{}
$progressFromPost = $null
if (Test-Path $progressFile) {
    try {
        $raw = Get-Content $progressFile -Raw -ErrorAction Stop
        $progressFromPost = ConvertFrom-Json $raw -ErrorAction Stop
    } catch {
        $progressFromPost = $null
    }
}

if ($progressFromPost) {
    Write-Output "[report] Using progress produced by postprocess"
    $proposed = [int]($progressFromPost.proposed_last -as [int])
    $accepted = [int]($progressFromPost.accepted_last -as [int])
    $rejected = [int]($progressFromPost.rejected_last -as [int])
    # top_sources may be a mapping; copy into a hashtable
    if ($progressFromPost.top_sources) {
        try {
            foreach ($k in $progressFromPost.top_sources.Keys) {
                $topSources[$k] = $progressFromPost.top_sources[$k]
            }
        } catch { }
    }
} else {
    # Fallback: scan recent harvested_facts.jsonl to approximate counts
    if (Test-Path $harvested) {
        $lines = Get-Content $harvested -ErrorAction SilentlyContinue
        # look at last N lines (default 200)
        $last = $lines | Select-Object -Last 200
        foreach ($l in $last) {
            try {
                $j = ConvertFrom-Json $l -ErrorAction Stop
                $proposed += 1
                if ($j.accepted -eq $true -or ($j.PSObject.Properties.Name -contains 'accepted' -and $j.accepted -eq $true)) { $accepted += 1 } else { $rejected += 1 }
                $s = ($j.source -replace '\s+', ' ') -as [string]
                if ($s) { if ($topSources.ContainsKey($s)) { $topSources[$s] += 1 } else { $topSources[$s] = 1 } }
            } catch { }
        }
    }

    # Write a small progress file when postprocess didn't run
    $progress = @{
        ts = (Get-Date).ToString('s')
        proposed_last = $proposed
        accepted_last = $accepted
        rejected_last = $rejected
        top_sources = $topSources.GetEnumerator() | Sort-Object -Property Value -Descending | Select-Object -First 5 | ForEach-Object @{Name='k';Expression={$_.Name}} | ForEach-Object { $_ }
    }
    $progress | ConvertTo-Json -Depth 5 | Out-File -Encoding utf8 $progressFile
}

# Short textual report
Write-Output "[report] proposed=$proposed accepted=$accepted rejected=$rejected"
Write-Output "[report] Top sources:"; $topSources.GetEnumerator() | Sort-Object -Property Value -Descending | Select-Object -First 5 | ForEach-Object { Write-Output "  $($_.Name): $($_.Value)" }

# Tail the log
if (Test-Path $log) { Write-Output "[log tail]"; Get-Content $log -Tail 80 }

Write-Output "[done] harvest_run finished"
