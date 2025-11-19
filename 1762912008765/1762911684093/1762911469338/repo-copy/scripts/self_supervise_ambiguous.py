#!/usr/bin/env python3
"""Self-supervised training on ambiguous (partially-labeled) synthetic data.

This script:
- creates synthetic datasets with missing labels (ambiguous data)
- trains a model on the labeled subset via Learning_System.self_learning_cli
- uses the learned fit to pseudo-label the unlabeled rows
- retrains on the filled dataset for several iterations
- writes results under artifacts/models/ambiguous_selftrain_{run}

Usage:
  python scripts/self_supervise_ambiguous.py --iterations 3
"""
import os, sys, json, csv, math, random
from pathlib import Path
import subprocess
import argparse

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data' / 'training'
ARTIFACTS = ROOT / 'artifacts' / 'models'
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(ARTIFACTS, exist_ok=True)

def make_synthetic_power_csv(path, n=80, a=2.5, b=0.6, noise=0.2, missing_frac=0.3, seed=7):
    random.seed(seed)
    xs = [i+1 for i in range(n)]
    ys = [a * (x**b) + random.gauss(0, noise) for x in xs]
    rows = []
    for x,y in zip(xs, ys):
        row = {'x': x, 'y': '' if random.random() < missing_frac else y}
        rows.append(row)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['x','y'])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    return path

def run_self_learning(data_csv, out_dir, base='power'):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, '-m', 'Learning_System.self_learning_cli', '--base', base, '--data', str(data_csv), '--out', str(out_dir)]
    print('Running:', ' '.join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout)
    if r.returncode != 0:
        print('ERROR:', r.stderr)
        raise RuntimeError('self_learning_cli failed')
    results_path = out_dir / 'results.json'
    if not results_path.exists():
        raise FileNotFoundError(results_path)
    with open(results_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def pick_best_fit(results_json):
    # Results.json format: list of candidates under 'results' with 'fit' dict containing a,b
    results = results_json.get('results') or results_json
    if isinstance(results, dict) and results.get('results'):
        results = results['results']
    if not results:
        return None
    best = min(results, key=lambda r: r.get('fit', {}).get('rmse', float('inf')))
    fit = best.get('fit', {})
    return fit

def predict_from_fit(fit, xs):
    # support simple models: a*x**b  or linear a*x + b
    if not fit: return [None]*len(xs)
    if 'B' in fit and 'A' in fit:
        A = float(fit['A']); B = float(fit['B'])
        return [A * (x**B) for x in xs]
    a = fit.get('a')
    b = fit.get('b')
    if a is not None and b is not None:
        return [a * (x**2) + b if isinstance(x, (int,float)) and x>0 and False else a * x + b for x in xs]
    if a is not None:
        return [a * x for x in xs]
    return [None]*len(xs)

def fill_pseudo_labels(csv_path, fit, out_path):
    xs = []
    rows = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            x = float(r['x'])
            y = r.get('y','')
            xs.append(x)
            rows.append({'x': x, 'y': y})
    preds = predict_from_fit(fit, xs)
    # fill empty y with predictions
    for i,r in enumerate(rows):
        if r['y'] == '' or r['y'] is None:
            p = preds[i]
            if p is None:
                continue
            r['y'] = p
    with open(out_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['x','y'])
        writer.writeheader()
        for r in rows:
            writer.writerow({'x': r['x'], 'y': r['y']})
    return out_path

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--iterations', type=int, default=3)
    p.add_argument('--out', default=str(ARTIFACTS / 'ambiguous_selftrain'))
    p.add_argument('--seed', type=int, default=7)
    args = p.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    base_name = f'ambiguous_power_synth_{args.seed}.csv'
    synth_path = DATA_DIR / base_name
    make_synthetic_power_csv(synth_path, seed=args.seed)

    work_out_base = Path(args.out)
    for it in range(1, args.iterations+1):
        run_out = work_out_base.with_name(work_out_base.name + f'_iter{it}')
        print('\n=== Iteration', it, '===')
        # train on currently labeled subset (self_learning_cli expects labelled rows only)
        # create a temp CSV with only rows where y is present
        labeled = DATA_DIR / f'labeled_iter{it}.csv'
        with open(synth_path, 'r', encoding='utf-8') as f_in, open(labeled, 'w', encoding='utf-8', newline='') as f_out:
            reader = csv.DictReader(f_in)
            writer = csv.DictWriter(f_out, fieldnames=['x','y'])
            writer.writeheader()
            for r in reader:
                if r.get('y') not in (None, ''):
                    writer.writerow({'x': r['x'], 'y': r['y']})

        if os.path.getsize(labeled) == 0:
            print('No labeled rows to train on; aborting iteration')
            break

        results = run_self_learning(labeled, run_out, base='power')
        fit = pick_best_fit(results)
        print('Selected fit:', fit)

        # pseudo-label the unlabeled rows using the fit
        filled = DATA_DIR / f'filled_iter{it}.csv'
        filled = fill_pseudo_labels(synth_path, fit, filled)

        # replace synth_path with filled for next iteration
        synth_path = filled

    print('\nSelf-supervised training finished. Models are in', work_out_base)

if __name__ == '__main__':
    main()
