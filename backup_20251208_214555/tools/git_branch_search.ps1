param(
    [string]$pattern = 'continual|agent|PlannerAdapter|DeliberationAdapter|multimodal|vision|Learning_System|continual_learning|executive_agent|internal_agents'
)

$refs = git for-each-ref --format='%(refname:short)' refs/heads refs/remotes
$out = Join-Path (Get-Location) 'git_branch_search_results.txt'
if (Test-Path $out) { Remove-Item $out -ErrorAction SilentlyContinue }

foreach ($r in $refs) {
    "$([DateTime]::UtcNow.ToString('o')) REF: $r" | Out-File -FilePath $out -Append -Encoding utf8
    try {
        $matches = git grep -n -E $pattern $r 2>$null
        if ($matches) {
            foreach ($m in $matches) {
                $m | Out-File -FilePath $out -Append -Encoding utf8
            }
        }
    } catch {
        # ignore
    }
}

if (Test-Path $out) {
    Get-Content $out -Raw
} else {
    Write-Output 'NO_MATCHES'
}
