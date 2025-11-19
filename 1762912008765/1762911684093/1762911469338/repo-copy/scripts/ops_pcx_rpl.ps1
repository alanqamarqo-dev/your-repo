# PCX / RPL operations PowerShell sheet
# Usage: run from project root in PowerShell

# 1) Ensure environment
$env:PYTHONPATH = (Get-Location).Path

# 1.a Optional: open configs/fusion_weights.json to confirm the new weights
Write-Output "Ensure configs/fusion_weights.json contains perception_context and reasoning_planner weights"
if (-Not (Test-Path configs\fusion_weights.json)) {
    Write-Output "configs/fusion_weights.json not found; creating default with PCX/RPL weights..."
    '{"mathematical_brain":1.5,"quantum_processor":0.95,"code_generator":1.5,"protocol_designer":0.6,"perception_context":1.0,"reasoning_planner":1.2}' | Set-Content -Encoding utf8 configs\fusion_weights.json
}

# 1.b Run self optimization to allow automatic weight tuning
Write-Output "Running self_optimize.py to refresh fusion weights and signals..."
.\.venv\Scripts\python.exe scripts\self_optimize.py --out reports\self_optimization

# 2) Generate reports and update the manifest
Write-Output "Generating all reports..."
.\.venv\Scripts\python.exe scripts\generate_all_reports.py
# Optional: generate PCX/RPL specific reports if script exists
if (Test-Path scripts\make_pcx_rpl_reports.py) {
    .\.venv\Scripts\python.exe scripts\make_pcx_rpl_reports.py
}

Write-Output "Updating report manifest to include PCX/RPL reports"
'{
 "html":[
   "models_report.html",
   "models_visual.html",
   "full_system_report.html",
   "auto_reports/ohm_report.html",
   "auto_reports/power_report.html",
   "auto_reports/rc_step_report.html",
   "auto_reports/poly2_report.html",
   "auto_reports/pcx_report.html",
   "auto_reports/rpl_report.html"
 ],
 "json":[
   "safety_suite/safety_report.json",
   "self_optimization/self_optimization.json",
   "last_success.json"
 ]
}' | Set-Content -Encoding utf8 reports\report_manifest.json

# 3) Run safety suite and print its JSON
Write-Output "Running safety suite..."
.\.venv\Scripts\python.exe -m scripts.safety_suite --out reports\safety_suite

Write-Output "Safety report (tail):"
Get-Content reports\safety_suite\safety_report.json -Raw | Select-String -Pattern '.' -Context 0, 200

# 4) Export PDF via Chrome headless (serve files first if needed)
Write-Output "Start a simple static server on :8000 if not running (python -m http.server 8000)"
Write-Output "Exporting models_report.html to reports\AGL_report.pdf using Chrome headless"
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --headless --disable-gpu --print-to-pdf="reports\AGL_report.pdf" "http://localhost:8000/reports/models_report.html"

# 5) Optional: commit updated reports and configs
Write-Output "Staging reports and config changes"
& git add reports/ reports/report_manifest.json configs/fusion_weights.json
if ($LASTEXITCODE -ne 0) {
    Write-Output "git add failed or git not available"
}

Write-Output "You can now commit: git commit -m 'Wire PCX/RPL into reports + self-optimization; refresh safety & manifest'"

# Acceptance checklist (manual):
Write-Output "\n--- Acceptance checklist (verify manually) ---"
Write-Output "[ ] PCX/RPL links appear in the dashboard left list (report_manifest includes pcx_report/rpl_report)"
Write-Output "[ ] Safety report present and readable: reports/safety_suite/safety_report.json"
Write-Output "[ ] PDF generated: reports/AGL_report.pdf"
Write-Output "[ ] self_optimization contains perception_context & reasoning_planner weights: reports/self_optimization/self_optimization.json"
Write-Output "[ ] Tests: run .\.venv\Scripts\python.exe -m unittest -v tests.test_perception_context tests.test_reasoning_planner tests.test_task_orchestrator_paths"
