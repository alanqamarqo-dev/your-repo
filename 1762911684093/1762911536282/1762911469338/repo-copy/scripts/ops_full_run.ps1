# Full run ops (PowerShell)
# Usage: run from project root in PowerShell

# 1. Init environment
$env:PYTHONIOENCODING = "utf-8"; $env:PYTHONPATH = (Get-Location).Path

# 2. Restore KB from lock (if needed) and normalize
Copy-Item Knowledge_Base\Learned_Patterns.lock.json Knowledge_Base\Learned_Patterns.json -Force
.\.venv\Scripts\python.exe tools\normalize_kb.py

# 3. Refine power data and retrain
.\.venv\Scripts\python.exe tools\power_data_refine.py --in data\training\C_freefall_A.csv --x "s[m]" --y "t[s]" --out data\training\C_freefall_A_refined.csv
.\.venv\Scripts\python.exe tools\power_data_refine.py --in data\training\C_freefall_B.csv --x "s[m]" --y "t[s]" --out data\training\C_freefall_B_refined.csv
.\.venv\Scripts\python.exe -m Learning_System.self_learning_cli --base power --data data\training\C_freefall_A_refined.csv --out artifacts\models\power_refined_A
.\.venv\Scripts\python.exe -m Learning_System.self_learning_cli --base power --data data\training\C_freefall_B_refined.csv --out artifacts\models\power_refined_B

# 4. (Optional) Promote refined results
# Copy-Item artifacts\models\power_refined_A\results.json artifacts\models\freefall_C_A\results.json -Force
# Copy-Item artifacts\models\power_refined_B\results.json artifacts\models\freefall_C_B\results.json -Force

# 5. Promote winners into KB and save RC tau
.\.venv\Scripts\python.exe scripts\phase_g_save_patterns.py
.\.venv\Scripts\python.exe scripts\save_rc_to_kb.py
Copy-Item Knowledge_Base\Learned_Patterns.json Knowledge_Base\Learned_Patterns.lock.json -Force

# 6. Generate reports, self-optimize and safety
.\.venv\Scripts\python.exe scripts\generate_all_reports.py
.\.venv\Scripts\python.exe scripts\self_optimize.py --out reports\self_optimization
.\.venv\Scripts\python.exe -m scripts.safety_suite --out reports\safety_suite

# 7. Update report manifest
$json = '{"html":["models_report.html","models_visual.html","full_system_report.html","auto_reports/ohm_report.html","auto_reports/power_report.html","auto_reports/rc_step_report.html","safety_suite/safety_report.html"],"json":["safety_suite/safety_report.json","self_optimization/self_optimization.json","last_success.json"]}'; $json | Set-Content -Encoding utf8 reports\report_manifest.json

# 8. Start static server (manual step recommended)
Write-Output "To serve reports: python -m http.server 8000 (run manually to keep session interactive)"

# 9. Manual checks: view safety report and export PDF
Write-Output "Check safety report: Get-Content reports\safety_suite\safety_report.json"
Write-Output "To export PDF (headless Chrome): & \"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe\" --headless --disable-gpu --print-to-pdf=\"reports\\AGL_report.pdf\" \"http://localhost:8000/reports/models_report.html\""

# 10. Run critical tests
.\.venv\Scripts\python.exe -m unittest -v tests.test_inference_engine tests.test_orchestrator_inference tests.test_kb_integrity

# 11. Git commit
Write-Output "To commit: git add Knowledge_Base/Learned_Patterns.json Knowledge_Base/Learned_Patterns.lock.json reports/ ; git commit -m 'Refine power data, retrain, regenerate reports, update KB & safety'"
