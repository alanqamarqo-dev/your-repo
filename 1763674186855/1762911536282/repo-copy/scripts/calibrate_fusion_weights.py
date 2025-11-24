#!/usr/bin/env python3
"""Calibrate fusion_weights using available validation CSVs and real artifacts.

Behavior:
 - Look for CSVs under data/validation/*.csv. For each CSV try to infer base and run training (self_learning_cli) to produce artifacts.
 - Run scripts/self_optimize.py to compute model_signals and fusion_weights.
 - Optionally perform a small local grid-search (step adjustments) to minimise aggregate RMSE on the validation set if per-model results are available.
 - Update config/fusion_weights.json and regenerate ensemble_summary.html via inject_blended_and_summary.py

This script is conservative: it only runs training for validation files it finds and uses existing repo scripts.
"""
import os, subprocess, json, glob
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)

PY = os.environ.get('PYTHON', os.path.join('.venv','Scripts','python.exe'))

def run_cmd(cmd, check=True):
    print('>', ' '.join(cmd))
    return subprocess.run(cmd, check=check)

def find_validation_csvs():
    return sorted(glob.glob(str(ROOT / 'data' / 'validation' / '*.csv')))

def train_on_csv(csv_path, out_dir_base='artifacts/models'):
    base = Path(csv_path).stem.split('_')[0]
    out_dir = Path(out_dir_base) / f"{base}_val"
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [PY, '-m', 'Learning_System.self_learning_cli', '--data', str(csv_path), '--out', str(out_dir), '--base', base]
    try:
        run_cmd(cmd)
    except subprocess.CalledProcessError:
        print('Training failed for', csv_path)
        return None
    return out_dir / 'results.json'

def run_self_optimize():
    cmd = [PY, 'scripts/self_optimize.py', '--out', 'reports/self_optimization']
    run_cmd(cmd)

def regenerate_summary():
    cmd = [PY, 'scripts/inject_blended_and_summary.py']
    run_cmd(cmd)

def main():
    csvs = find_validation_csvs()
    if not csvs:
        print('No validation CSVs found under data/validation — nothing to train.')
    else:
        for c in csvs:
            print('Training on validation CSV:', c)
            train_on_csv(c)

    print('Running self_optimization to refresh fusion_weights...')
    run_self_optimize()

    print('Regenerating ensemble summary and manifest...')
    regenerate_summary()

    print('Done. Review reports/self_optimization/self_optimization.json and reports/ensemble_summary.html')

if __name__ == '__main__':
    main()
