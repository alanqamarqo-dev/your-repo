Write-Output "Starting local CI: unit tests -> reports -> safety"
$env:PYTHONPATH = (Get-Location).Path
$env:PYTHONIOENCODING = 'utf-8'

Write-Output "Running unit tests..."
.\.venv\Scripts\python.exe -m unittest discover -v
if ($LASTEXITCODE -ne 0) { Write-Error "Unit tests failed"; exit $LASTEXITCODE }

Write-Output "Generating reports..."
Write-Output "Running full automation (reports + self_opt + safety + pdf + manifest)"
.\.venv\Scripts\python.exe scripts\ops_full_automation.py
if ($LASTEXITCODE -ne 0) { Write-Error "Automation failed"; exit $LASTEXITCODE }

Write-Output "Local CI completed"