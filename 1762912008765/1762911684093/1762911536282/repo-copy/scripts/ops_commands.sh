#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="$ROOT"
export PYTHONIOENCODING="utf-8"

cmd=${1:-}
case "$cmd" in
  Baseline)
    cp Knowledge_Base/Learned_Patterns.lock.json Knowledge_Base/Learned_Patterns.json || true
    python3 scripts/generate_all_reports.py
    python3 -m scripts.safety_suite --out reports/safety_suite
    ;;
  SelfEngineer)
    mkdir -p artifacts/self_engineer_runs
    cp Knowledge_Base/Learned_Patterns.lock.json Knowledge_Base/Learned_Patterns.json || true
    python3 scripts/self_engineer_run.py configs/self_engineer_rules.json reports/self_engineer artifacts/self_engineer_runs
    ;;
  MergeAuto)
    git checkout -b feat/auto-self-edit || true
    if [ -f reports/self_engineer/patch.diff ]; then
      git apply --reject --whitespace=fix reports/self_engineer/patch.diff || true
      git add -A && git commit -m "Self-Engineer: apply proposed patch (auto)" || true
    fi
    ;;
  *)
    echo "Usage: $0 {Baseline|SelfEngineer|MergeAuto}"
    exit 2
    ;;
esac
#!/usr/bin/env bash
# Bash quick-ops for AGL dashboard
# Usage: from project root: chmod +x scripts/ops_commands.sh; ./scripts/ops_commands.sh

export PYTHONIOENCODING=utf-8
export PYTHONPATH="$(pwd)"

echo "Generating reports..."
python3 scripts/generate_all_reports.py
python3 scripts/make_models_report.py
python3 scripts/make_visual_report.py
python3 scripts/self_optimize.py --out reports/self_optimization
python3 -m scripts.safety_suite --out reports/safety_suite

echo "Writing manifest..."
printf '{"html":["models_report.html","auto_reports/ohm_report.html","auto_reports/power_report.html","safety_suite/safety_report.html"],"json":["safety_suite/safety_report.json","self_optimization/self_optimization.json","last_success.json"]}' > reports/report_manifest.json

echo "Starting static server on :8000"
python3 -m http.server 8000
