# PowerShell helper to create venv, install deps and run uvicorn for MedicalAssistant_v1
param(
    [int]$Port = 8080
)

$Root = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $Root

if (-Not (Test-Path -Path .\.venv)) {
    python -m venv .venv
}

# Activate the venv in the current session
. .\.venv\Scripts\Activate.ps1

# Upgrade pip and install requirements
python -m pip install --upgrade pip
if (Test-Path requirements.txt) {
    pip install -r requirements.txt
}

# Run uvicorn in the foreground; user can Ctrl+C to stop
Write-Host "Starting uvicorn on port $Port (press Ctrl+C to stop)..."
uvicorn api:app --host 0.0.0.0 --port $Port
