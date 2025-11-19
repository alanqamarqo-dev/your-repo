import argparse
import csv
import json
import os
from pathlib import Path

from Learning_System.Self_Learning import SelfLearning


def infer_mapping_from_row(row: dict):
    # prefer explicit law_name mapping
    law = row.get('law_name', '').strip().lower()
    if law == 'hooke':
        return ('F', 'x')
    if law == 'ohm':
        return ('V', 'I')
    # fallback heuristics
    if 'F' in row and 'x' in row:
        return ('F', 'x')
    if 'V' in row and 'I' in row:
        return ('V', 'I')
    # generic: pick last as x, first numeric as y
    keys = list(row.keys())
    if len(keys) >= 2:
        return (keys[0], keys[1])
    return (keys[0], keys[0])


def read_samples(csv_path: str, prefer_y: str = None, prefer_x: str = None): # type: ignore
    samples = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        r = csv.DictReader(f)
        first_row = None
        for row in r:
            if first_row is None:
                first_row = row
            # normalize units per-row if unit columns present
            row = dict(row)
            # Hooke: unit_x may be 'cm' or 'm'
            if 'unit_x' in row and row.get('unit_x'):
                try:
                    ux = row.get('unit_x','').strip().lower()
                    if ux == 'cm':
                        # convert x from cm to m
                        row['x'] = str(float(row.get('x', 0)) * 0.01)
                        row['unit_x'] = 'm'
                except Exception:
                    pass
            # Ohm: unit_I may be 'mA' or 'A'; unit_V may be 'mV' or 'V'
            if 'unit_i' in {k.lower() for k in row.keys()} or 'unit_I' in row:
                # normalize case-insensitive keys
                ui_key = None
                for k in row.keys():
                    if k.lower() == 'unit_i':
                        ui_key = k
                        break
                if ui_key:
                    try:
                        ui = row.get(ui_key,'').strip().lower()
                        if ui == 'ma':
                            row_key = ui_key.replace('unit_', '')
                            # attempt to find numeric key name (I)
                            if 'I' in row:
                                row['I'] = str(float(row.get('I', 0)) * 0.001)
                                row[ui_key] = 'A'
                    except Exception:
                        pass
            if 'unit_v' in {k.lower() for k in row.keys()} or 'unit_V' in row:
                uv_key = None
                for k in row.keys():
                    if k.lower() == 'unit_v':
                        uv_key = k
                        break
                if uv_key:
                    try:
                        uv = row.get(uv_key,'').strip().lower()
                        if uv == 'mv':
                            if 'V' in row:
                                row['V'] = str(float(row.get('V', 0)) * 0.001)
                                row[uv_key] = 'V'
                    except Exception:
                        pass
            samples.append(row)
    if not samples:
        return [], None, None
    # allow callers to hint which columns are y/x by providing simple names
    yname = None
    xname = None
    if prefer_y and first_row:
        # match header by substring (case-insensitive)
        for k in first_row.keys():
            if prefer_y.lower() in k.lower():
                yname = k
                break
    if prefer_x and first_row:
        for k in first_row.keys():
            if prefer_x.lower() in k.lower():
                xname = k
                break
    if not yname or not xname:
        yname, xname = infer_mapping_from_row(first_row) # type: ignore
    # construct sample dicts with order y then x to satisfy SelfLearning.evaluate heuristic
    out = []
    for row in samples:
        try:
            xv = float(row.get(xname, row.get('x', 0)))
        except Exception:
            try:
                xv = float(row.get('x', 0))
            except Exception:
                xv = None
        try:
            yv = float(row.get(yname, row.get('F', 0)))
        except Exception:
            try:
                yv = float(row.get('F', 0))
            except Exception:
                yv = None
        out.append({yname: yv, xname: xv})
    return out, yname, xname


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--data', required=True, help='CSV file with samples')
    p.add_argument('--out', required=True, help='Output directory for artifacts')
    p.add_argument('--base', required=False, help='Base formula/law name (e.g. hooke, ohm)')
    p.add_argument('--y', required=False, help='Preferred dependent variable column name or substring (e.g. s or V)')
    p.add_argument('--x', required=False, help='Preferred independent variable column name or substring (e.g. t or I)')
    args = p.parse_args()

    samples, yname, xname = read_samples(args.data, prefer_y=args.y, prefer_x=args.x)
    if not samples:
        print('No samples found in', args.data)
        return

    base = args.base or Path(args.data).stem.split('_')[0]
    # load optional coverage_boost config
    cfg = {}
    from Learning_System.io_utils import read_json
    try:
        if os.path.exists('config/coverage_boost.json'):
            cfg = read_json('config/coverage_boost.json')
    except Exception:
        cfg = {}

    use_cv = cfg.get('cv', {}).get('folds', 0) >= 3
    use_robust = 'robust' in cfg

    # apply robust outlier masking if requested
    if use_robust:
        import numpy as _np
        from Learning_System.robust_fit import zscore_mask
        ys = _np.array([s.get(yname) for s in samples], dtype=float)
        mask = zscore_mask(ys, z=cfg.get('robust', {}).get('outlier_z', 3.0))
        # filter samples
        new_samples = []
        for m, s in zip(mask, samples):
            if bool(m):
                new_samples.append(s)
        if new_samples:
            samples = new_samples

    sl = SelfLearning()
    # pass along config flags where supported (SelfLearning.run may ignore extras)
    # Note: pass only supported args to SelfLearning.run (it may ignore extra cfg)
    results = sl.run(base, samples, max_candidates=4)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    res_path = out_dir / 'results.json'
    with open(res_path, 'w', encoding='utf-8') as f:
        json.dump({'base': base, 'yname': yname, 'xname': xname, 'results': results}, f, ensure_ascii=False, indent=2)

    print('Wrote results to', str(res_path))


if __name__ == '__main__':
    main()
