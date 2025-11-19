#!/usr/bin/env python3
"""Inject controlled noise into model results and training CSVs for robustness testing.

This script will:
- copy some artifacts/models/*/results.json into artifacts/models/noisy/ with perturbed fit values
- create noisy copies of a few training CSVs by adding gaussian noise to numeric fields
"""
import os, json, random
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / 'artifacts' / 'models'
NOISY_DIR = MODELS / 'noisy'
DATA_TRAIN = ROOT / 'data' / 'training'
NOISY_DATA = DATA_TRAIN / 'noisy'
NOISY_DIR.mkdir(parents=True, exist_ok=True)
NOISY_DATA.mkdir(parents=True, exist_ok=True)

def perturb_results(src, dst, scale=0.2):
    j = json.loads(src.read_text(encoding='utf-8'))
    for r in j.get('results', []):
        fit = r.get('fit', {})
        for k in ('a','b','A','B'):
            if k in fit and isinstance(fit[k], (int,float)):
                orig = float(fit[k])
                noise = random.gauss(0, abs(orig)*scale + 1e-6)
                fit[k] = orig + noise
        # also perturb rmse upward slightly
        if 'rmse' in fit:
            fit['rmse'] = float(fit['rmse']) * (1.0 + abs(random.gauss(0, scale/2)))
    dst.write_text(json.dumps(j, ensure_ascii=False, indent=2), encoding='utf-8')

def noisy_csv(src, dst, noise_scale=0.1):
    # add gaussian noise to numeric y columns when present
    import csv
    with open(src, 'r', encoding='utf-8') as f_in, open(dst, 'w', encoding='utf-8', newline='') as f_out:
        r = csv.DictReader(f_in)
        w = csv.DictWriter(f_out, fieldnames=r.fieldnames)
        w.writeheader()
        for row in r:
            new = dict(row)
            for k,v in row.items():
                try:
                    val = float(v)
                    new[k] = val + random.gauss(0, abs(val)*noise_scale + 1e-6)
                except Exception:
                    # keep non-numeric as-is
                    pass
            w.writerow(new)

def main():
    # perturb some model results
    for p in MODELS.glob('*'):
        if p.is_dir():
            src = p / 'results.json'
            if src.exists():
                dst = NOISY_DIR / (p.name + '_noisy.json')
                print('Perturbing', src, '->', dst)
                perturb_results(src, dst, scale=0.25)

    # noisy copies of training CSVs (pick first 5)
    csvs = list(DATA_TRAIN.glob('*.csv'))[:5]
    for c in csvs:
        dst = NOISY_DATA / (c.stem + '_noisy.csv')
        print('Creating noisy CSV', c, '->', dst)
        noisy_csv(c, dst, noise_scale=0.15)

    print('Noisy artifacts written to', NOISY_DIR, 'and', NOISY_DATA)

if __name__ == '__main__':
    main()
