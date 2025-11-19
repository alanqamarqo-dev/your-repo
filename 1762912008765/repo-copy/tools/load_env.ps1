<#
loads a .env file from the repository root into the current PowerShell session

Usage:
  # from project root
  .\tools\load_env.ps1

This script reads a `.env` file (simple KEY=VALUE lines) and sets each pair as
an environment variable in the current session. It intentionally does NOT write
the key anywhere persistent in source control.
#>
param(
    [string]$EnvPath = "./.env"
)

if (-not (Test-Path $EnvPath)) {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
    Write-Error "Env file not found at $EnvPath. Create one by copying .env.template and filling your OPENAI_API_KEY."
    exit 2
}

Get-Content $EnvPath | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith('#')) { return }
    $parts = $line -split('=',2)
    if ($parts.Length -lt 2) { return }
    $k = $parts[0].Trim()
    $v = $parts[1].Trim()
    # remove surrounding quotes if present
    if ($v.StartsWith('"') -and $v.EndsWith('"')) { $v = $v.Substring(1, $v.Length-2) }
    if ($v.StartsWith("'") -and $v.EndsWith("'")) { $v = $v.Substring(1, $v.Length-2) }
    Write-Output "Setting env: $k"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
    Set-Item -Path Env:\$k -Value $vsk-proj-KajgJ59bnTAwEyRCPeD8JLJNiZh5MXWKsX5dPyfR-DMsMBaEPwH_wuPAen5FmwwMMckwdr5MD9T3BlbkFJA3p14NYFCdVhNkcqF-dflVrA8gPWD4c-JFZp14xczgQ-UAJAonrJ93JMgGaOIuWUEHlNi00G0A
}

Write-Output "Loaded .env into session. (Not written to disk in repo.)"
