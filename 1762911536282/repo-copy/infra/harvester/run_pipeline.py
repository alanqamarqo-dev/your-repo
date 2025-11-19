import os
import subprocess
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)
PY = os.path.join('.venv', 'Scripts', 'python.exe')

def run(cmd, **kwargs):
    print('>',' '.join(cmd))
    return subprocess.run(cmd, check=False, capture_output=True, text=True, **kwargs)

def main():
    # 1) run one harvester iteration in mock mode
    env = os.environ.copy()
    env['AGL_EXTERNAL_INFO_MOCK'] = '1'
    env['AGL_EXTERNAL_INFO_ENABLED'] = '1'
    print('Running harvester (mock)')
    r = run([PY, 'workers/knowledge_harvester.py'], env=env)
    print(r.stdout)
    print(r.stderr)

    # 2) supervisor routes facts
    print('Running supervisor to route facts')
    r = run([PY, 'infra/harvester/supervisor.py'])
    print(r.stdout)
    print(r.stderr)

    # 3) attempt refine & retrain weak models (may be no-ops)
    print('Running refine_and_retrain_weak_models.py')
    r = run([PY, 'scripts/refine_and_retrain_weak_models.py'])
    print(r.stdout)
    print(r.stderr)

    # 4) run safety suite
    print('Running safety_suite.py')
    r = run([PY, 'scripts/safety_suite.py', '--out', 'reports/safety_pipeline'])
    print(r.stdout)
    print(r.stderr)

    # 5) summarize
    summary = {'harvester_rc': r.returncode}
    with open('artifacts/pipeline_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print('Pipeline complete. Summary written to artifacts/pipeline_summary.json')

if __name__ == '__main__':
    main()
