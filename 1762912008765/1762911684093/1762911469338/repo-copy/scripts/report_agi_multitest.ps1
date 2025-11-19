<#
Produce a human-readable report from the AGI multidimensional test artifact.

Usage:
  # default artifact path
  .\scripts\report_agi_multitest.ps1

  # specify artifact and open the markdown after generation
  .\scripts\report_agi_multitest.ps1 -ArtifactPath artifacts/agi_multitest_result.json -Open
#>

param(
    [string]$ArtifactPath = "artifacts/agi_multitest_result.json",
    [switch]$Open
)

if (-not (Test-Path $ArtifactPath)) {
    Write-Error "Artifact not found: $ArtifactPath. Run the test first (see scripts/run_agi_multitest.ps1)."
    exit 2
}

$jsonText = Get-Content -Raw -Path $ArtifactPath -ErrorAction Stop
try {
    $data = $jsonText | ConvertFrom-Json -ErrorAction Stop
} catch {
    Write-Error "Failed to parse JSON artifact: $_"
    exit 3
}

$outDir = Split-Path -Path $ArtifactPath -Parent
$mdPath = Join-Path $outDir "agi_multitest_report.md"
$txtPath = Join-Path $outDir "agi_multitest_report.txt"

function ScoreToPercent($s) {
    # input s is 0..10 -> return 0..100 string
    return [math]::Round(($s * 10.0), 2)
}

$md = @()
$md += "# AGI Multidimensional Test Report"
$md += ""
$md += "Generated: $(Get-Date -Format o)"
$md += ""
$md += "## Summary"
$md += "- Overall score: $($data.overall_score_percent) %"
$md += "- Weights: $(($data.weights | ConvertTo-Json -Depth 2))"
$md += ""
$md += "## Per-scenario results"

foreach ($k in $data.scores.PSObject.Properties.Name) {
    $s = $data.scores.$k
    $md += "### $k"
    $md += "- Duration: $([math]::Round($s.duration,2))s"
    $md += "- Score: $($s.score) / 10  (≈ $(ScoreToPercent $s.score)%)"
    $md += "- Keyword score: $($s.kw_score)"
    $md += "- Length score: $($s.len_score)"
    $md += "- Answer (truncated to 800 chars):"
    $ans = $s.text -as [string]
    if (-not $ans) { $ans = "(no text)" }
    $tr = if ($ans.Length -gt 800) { $ans.Substring(0,800) + '... (truncated)' } else { $ans }
    $md += '```'
    $md += $tr
    $md += '```'
    $md += ""
}

$md += "## Interactions (raw)"
$md += "$(ConvertTo-Json $data.interactions -Depth 4)"

# write markdown and plain text
[System.IO.File]::WriteAllText($mdPath, ($md -join "`n"), [System.Text.Encoding]::UTF8)
[System.IO.File]::WriteAllText($txtPath, ($md -join "`n"), [System.Text.Encoding]::UTF8)

Write-Host "Report written: $mdPath" -ForegroundColor Green
Write-Host "Also wrote plain text copy: $txtPath" -ForegroundColor Green

if ($Open.IsPresent) {
    try {
        Start-Process -FilePath $mdPath
    } catch {
        Write-Warning "Unable to open report automatically: $_"
    }
}

exit 0
