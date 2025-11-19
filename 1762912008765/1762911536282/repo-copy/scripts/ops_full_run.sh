#!/usr/bin/env bash
# Full run ops (bash)
# Usage: run from project root in a bash shell

# 1. Init environment
export PYTHONIOENCODING=utf-8
export PYTHONPATH="$(pwd)"

# 2. Restore KB from lock (if needed) and normalize
cp Knowledge_Base/Learned_Patterns.lock.json Knowledge_Base/Learned_Patterns.json
python3 tools/normalize_kb.py

# 3. Refine power data and retrain
python3 tools/power_data_refine.py --in data/training/C_freefall_A.csv --x "s[m]" --y "t[s]" --out data/training/C_freefall_A_refined.csv
python3 tools/power_data_refine.py --in data/training/C_freefall_B.csv --x "s[m]" --y "t[s]" --out data/training/C_freefall_B_refined.csv
python3 -m Learning_System.self_learning_cli --base power --data data/training/C_freefall_A_refined.csv --out artifacts/models/power_refined_A
python3 -m Learning_System.self_learning_cli --base power --data data/training/C_freefall_B_refined.csv --out artifacts/models/power_refined_B

# 4. (Optional) Promote refined results
# cp artifacts/models/power_refined_A/results.json artifacts/models/freefall_C_A/results.json
# cp artifacts/models/power_refined_B/results.json artifacts/models/freefall_C_B/results.json

# 5. Promote winners into KB and save RC tau
python3 scripts/phase_g_save_patterns.py
python3 scripts/save_rc_to_kb.py
cp Knowledge_Base/Learned_Patterns.json Knowledge_Base/Learned_Patterns.lock.json

# 6. Generate reports, self-optimize and safety
python3 scripts/generate_all_reports.py
python3 scripts/self_optimize.py --out reports/self_optimization
python3 -m scripts.safety_suite --out reports/safety_suite

# 7. Update report manifest
printf '{"html":["models_report.html","models_visual.html","full_system_report.html","auto_reports/ohm_report.html","auto_reports/power_report.html","auto_reports/rc_step_report.html","safety_suite/safety_report.html"],"json":["safety_suite/safety_report.json","self_optimization/self_optimization.json","last_success.json"]}' > reports/report_manifest.json

# 8. Start static server (manual step recommended)
echo "To serve reports: python3 -m http.server 8000 (run manually to keep session interactive)"

# 9. Manual checks
echo "Check safety report: cat reports/safety_suite/safety_report.json"
echo "To export PDF (headless Chrome): google-chrome --headless --disable-gpu --print-to-pdf=\"reports/AGL_report.pdf\" \"http://localhost:8000/reports/models_report.html\""

# 10. Run critical tests
python3 -m unittest -v tests.test_inference_engine tests.test_orchestrator_inference tests.test_kb_integrity

# 11. Git commit
echo "To commit: git add Knowledge_Base/Learned_Patterns.json Knowledge_Base/Learned_Patterns.lock.json reports/ ; git commit -m 'Refine power data, retrain, regenerate reports, update KB & safety'"
