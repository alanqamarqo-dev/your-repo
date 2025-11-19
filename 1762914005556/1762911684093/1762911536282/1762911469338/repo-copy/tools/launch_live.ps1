<#
launch_live.ps1
A helper to move the workspace from MOCK -> LIVE, run the harvester a few rounds,
run the evaluation, and optionally start the local server.

Usage examples:
  # dry run (shows actions)
  .\tools\launch_live.ps1 -DryRun

  # clear cache, harvest 5 times, run eval, start server
  .\tools\launch_live.ps1 -ClearCache -HarvestCount 5 -StartServer

Security: The script prompts for OPENAI API key as a secure string and sets it only in the current session.
It validates the key exists, is ASCII, and starts with 'sk-'. The key is not logged.
#>

param(
    [switch]$ClearCache,
    [int]$HarvestCount = 1,
    [switch]$StartServer,
    [switch]$DryRun
)

function Write-Info($m){ Write-Host "[launch_live] $m" }

# Choose python executable (prefer venv)
$pyExe = "py"
$venvPy = Join-Path -Path (Get-Location) -ChildPath ".venv\Scripts\python.exe"
if (Test-Path $venvPy) { $pyExe = $venvPy }

Write-Info "Using Python: $pyExe"

# Try loading OPENAI key from common root files before prompting the user
if (-not $env:OPENAI_API_KEY) {
    $repoRoot = (Get-Location).Path
    $possibleFiles = @('openai.key','OPENAI_API_KEY.txt','openai_api_key.txt','.env')
    foreach ($f in $possibleFiles) {
        $path = Join-Path $repoRoot $f
        if (Test-Path $path) {
            Write-Host "Found key file '$f' at repo root; loading into session (value will not be printed)."
            try {
                if ($f -eq '.env') {
                    # Parse .env looking for OPENAI_API_KEY=VALUE
                    $lines = Get-Content -Path $path -ErrorAction SilentlyContinue
                    foreach ($ln in $lines) {
                        if ($ln -match "^\s*OPENAI_API_KEY\s*=\s*(.+)\s*$") {
                            $val = $Matches[1].Trim("'\"`")
                            if ($val) { $env:OPENAI_API_KEY = $val; break }
                        }
                    }
                } else {
                    $raw = Get-Content -Path $path -Raw -ErrorAction SilentlyContinue -Encoding UTF8
                    if ($raw) { $env:OPENAI_API_KEY = $raw.Trim() }
                }
            } catch {
                Write-Warning "Unable to read key file '$f': $_"
            }
            break
        }
    }

    # If still not set, ask interactively (secure input)
    if (-not $env:OPENAI_API_KEY) {
        Write-Host "OPENAI API key not found in environment or root files. Please enter it now (will not be saved to disk):"
        $secureKey = Read-Host -AsSecureString "OPENAI API KEY"
        $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
        $unsecure = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)
        if ($unsecure -and ($unsecure -is [string]) -and ($unsecure.Length -gt 0)) {
            $env:OPENAI_API_KEY = $unsecure
        } else {
            Write-Error "No OPENAI API key provided. Exiting."
            exit 1
        }
    }
}

# Basic validation: ASCII and starts with sk-
$okKey = $false
try {
    if ($env:OPENAI_API_KEY -and $env:OPENAI_API_KEY.StartsWith('sk-')) {
        $bytes = [System.Text.Encoding]::ASCII.GetBytes($env:OPENAI_API_KEY)
        if ($bytes.Length -eq $env:OPENAI_API_KEY.Length) { $okKey = $true }
    }
} catch { $okKey = $false }

if (-not $okKey) {
    Write-Host "OPENAI_API_KEY appears invalid (must be ASCII and start with 'sk-'). Aborting."; exit 1
}

# Confirm with user before proceeding
$confirm = Read-Host "Proceed to launch LIVE mode? Type YES to continue"
if ($confirm -ne 'YES') { Write-Host 'Aborted by user.'; exit 0 }

# Set runtime env vars for live mode
$env:AGL_EXTERNAL_INFO_ENABLED = '1'
$env:AGL_EXTERNAL_INFO_MOCK = ''
if (-not $env:AGL_EXTERNAL_INFO_MODEL) { $env:AGL_EXTERNAL_INFO_MODEL = 'gpt-4o-mini' }

Write-Info "AGL_EXTERNAL_INFO_ENABLED=1, AGL_EXTERNAL_INFO_MOCK disabled, model=$env:AGL_EXTERNAL_INFO_MODEL"

if ($DryRun) {
    Write-Info "Dry-run mode: no commands will be executed."; exit 0
}

# Optionally clear caches
if ($ClearCache) {
    Write-Info "Clearing artifact caches..."
    Remove-Item artifacts\external_info_cache\* -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item artifacts\harvested_facts.jsonl -ErrorAction SilentlyContinue
    Remove-Item artifacts\rag_eval.jsonl -ErrorAction SilentlyContinue
    Write-Info "Cache cleared."
}

# Run harvester HarvestCount times (small sleeps between runs)
for ($i=0; $i -lt $HarvestCount; $i++) {
    Write-Info "Running harvester (iteration $($i+1)/$HarvestCount)..."
    $rc = (& $pyExe "workers\knowledge_harvester.py")
    if ($LASTEXITCODE -ne 0) { Write-Host "harvester returned exit code $LASTEXITCODE" }
    Start-Sleep -Seconds 1
}

# Run evaluation
Write-Info "Running evaluation (run_eval50.py)..."
& $pyExe "tools\run_eval50.py"

# Optionally start server
if ($StartServer) {
    Write-Info "Starting server with uvicorn on 127.0.0.1:8000"
    $uvArgs = "-m uvicorn server:app --host 127.0.0.1 --port 8000"
    # start in new window so it doesn't block the script
    Start-Process -FilePath $pyExe -ArgumentList $uvArgs -WindowStyle Normal
    Write-Info "Server started (check http://127.0.0.1:8000). Use a separate PowerShell to view logs: Get-Content artifacts\server_run.log -Wait"
}

Write-Info "Launch sequence finished. Check artifacts/harvested_facts.jsonl and artifacts/rag_eval.jsonl for results."
