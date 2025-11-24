#!/usr/bin/env python3
"""Detect weak models from reports/self_optimization/self_optimization.json,
attempt data refine (where applicable) and retrain, then re-run self_optimization
and update ensemble summary.

Policy used here:
 - Consider a model "weak" when rmse > 0.12 or confidence < 0.3.
 - If base == 'power' try to find data/training/*{base}*.csv and run tools/power_data_refine.py
 - Retrain with Learning_System.self_learning_cli into artifacts/models/{base}_refined_auto
 - Re-run self_optimize and regenerate summary.
"""
import os, json, glob, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)

PY = os.environ.get('PYTHON', os.path.join('.venv','Scripts','python.exe'))

def run_cmd(cmd, check=True):
    print('>', ' '.join(cmd))
    return subprocess.run(cmd, check=check)

def read_self_optimization():
    p = ROOT / 'reports' / 'self_optimization' / 'self_optimization.json'
    if not p.exists():
        print('self_optimization.json not found — run scripts/self_optimize.py first')
        return None
    with open(p, 'r', encoding='utf-8-sig') as f:
        return json.load(f)

def find_training_csvs_for_base(base):
    # look under data/training for files containing base in filename
    return sorted(glob.glob(str(ROOT / 'data' / 'training' / f'*{base}*.csv')))

def refine_power_csv(src_csv, out_csv):
    cmd = [PY, 'tools/power_data_refine.py', '--in', src_csv, '--x', 's[m]', '--y', 't[s]', '--out', out_csv]
    try:
        run_cmd(cmd)
    except subprocess.CalledProcessError:
        print('Refine failed for', src_csv)
        return False
    return True

def retrain_on_csv(csv_path, base):
    out_dir = ROOT / 'artifacts' / 'models' / f"{base}_refined_auto"
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [PY, '-m', 'Learning_System.self_learning_cli', '--data', str(csv_path), '--out', str(out_dir), '--base', base]
    try:
        run_cmd(cmd)
    except subprocess.CalledProcessError:
        print('Retrain failed for', csv_path)
        return False
    return True

def run_self_optimize():
    cmd = [PY, 'scripts/self_optimize.py', '--out', 'reports/self_optimization']
    run_cmd(cmd)

def regenerate_summary():
    cmd = [PY, 'scripts/inject_blended_and_summary.py']
    run_cmd(cmd)

def main():
    so = read_self_optimization()
    if not so:
        return
    model_signals = so.get('model_signals', {})
    weak = []
    for base, s in model_signals.items():
        rmse = s.get('rmse', 9999)
        conf = s.get('confidence', 0.0)
        if rmse > 0.12 or conf < 0.3:
            weak.append((base, rmse, conf))

    if not weak:
        print('No weak models detected (threshold rmse>0.12 or conf<0.3).')
        return

    print('Detected weak models:', weak)

    for base, rmse, conf in weak:
        print('\n--- Handling weak base:', base, 'rmse=', rmse, 'conf=', conf)
        csvs = find_training_csvs_for_base(base)
        if not csvs:
            print('No training CSVs found for base', base)
            continue
        # Try refine for known bases
        for csv in csvs:
            print('Processing training CSV:', csv)
            if base == 'power':
                out_csv = str(Path(csv).with_name(Path(csv).stem + '_refined.csv'))
                ok = refine_power_csv(csv, out_csv)
                if ok:
                    retrain_on_csv(out_csv, base)
                else:
                    print('Refine failed — skipping retrain for', csv)
            else:
                # For other bases, attempt retrain on the raw csv
                retrain_on_csv(csv, base)

    print('\nRe-running self_optimization to refresh signals and fusion weights...')
    run_self_optimize()

    print('Regenerating ensemble summary and manifest...')
    regenerate_summary()

    print('Done. Check reports/ensemble_summary.html and artifacts/models/*_refined_auto')

if __name__ == '__main__':
    main()
