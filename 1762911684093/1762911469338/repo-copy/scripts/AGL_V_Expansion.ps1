param(
  [string]$Model = $env:AGL_EXTERNAL_INFO_MODEL
)

# AGL-V expansion helper (English-only, safe for PowerShell 5.1)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $MyInvocation.MyCommand.Path -Parent) | Out-Null
Set-Location ..  # change to repo root

# Environment flags
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:AGL_AUTO_TUNE = '1'
$env:AGL_MEMORY_PERSIST = '1'

# External info provider
$env:AGL_EXTERNAL_INFO_ENABLED = '1'
$env:AGL_EXTERNAL_INFO_MOCK = ''
if (-not $Model) { $Model = 'gpt-4o-mini' }
$env:AGL_EXTERNAL_INFO_MODEL = $Model

# Load domains config and export harvest target per domain if available
$domainsPath = "artifacts/domains_v5.json"
if (-not (Test-Path $domainsPath)) {
    Write-Output "domains file not found: $domainsPath - skipping harvest target export"
    return
}
try {
    $cfg = Get-Content $domainsPath -Raw | ConvertFrom-Json
    if ($cfg -and $cfg.targets_per_domain) { $env:AGL_HARVEST_TARGET_PER_DOMAIN = [string]$cfg.targets_per_domain }
} catch {
    Write-Output ("Failed to read {0}: {1}" -f $domainsPath, $_)
}

Write-Output "AGL-V expansion completed. Model=$Model; AGL_HARVEST_TARGET_PER_DOMAIN=$env:AGL_HARVEST_TARGET_PER_DOMAIN"
