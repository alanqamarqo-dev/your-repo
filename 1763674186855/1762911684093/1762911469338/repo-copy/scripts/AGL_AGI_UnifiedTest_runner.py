#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run the unified AGI test multiple times (different seeds), compute mean and bootstrap 95% CI.
Produces aggregated report in artifacts/reports/AGL_AGI_UnifiedReport_aggregated.json
"""
import importlib.util, os, json, statistics, random
from pathlib import Path

MOD_PATH = Path(__file__).with_name('AGL_AGI_UnifiedTest.py')
spec = importlib.util.spec_from_file_location('agl_unified', str(MOD_PATH))
mod = importlib.util.module_from_spec(spec) # type: ignore
spec.loader.exec_module(mod) # type: ignore # type: ignore

OUT_DIR = Path('artifacts/reports')
OUT_DIR.mkdir(parents=True, exist_ok=True)

def run_one(seed:int):
    os.environ['AGL_AGI_SEED'] = str(seed)
    # Each run returns per-metric fractions
    try:
        w = mod._winograd_eval(mod.reasoning_eval)
        a = mod._arc_eval(mod.arc_infer)
        t = mod._tom_eval(mod.tom_infer)
        si = mod.self_improvement()
    except Exception as e:
        return {'error': str(e)}
    return {'winograd': w, 'arc': a, 'tom': t, 'self_improvement': si}

def baseline_random_for_tests():
    # simple random baseline: for each test pick random from expected answers pool
    # Winograd pool
    win_pool = list({ans for (_,_,ans) in mod.WINOGRAD})
    tom_pool = list({ans for (_,ans) in mod.TOM})
    arc_pool = [y for (_,_,y) in mod.ARC]

    def win_random():
        ok=0
        for s,q,ans in mod.WINOGRAD:
            guess = random.choice(win_pool)
            if guess==ans: ok+=1
        return ok/len(mod.WINOGRAD)
    def tom_random():
        ok=0
        for story,ans in mod.TOM:
            guess = random.choice(tom_pool)
            if guess==ans: ok+=1
        return ok/len(mod.TOM)
    def arc_random():
        ok=0
        for _,seq,y in mod.ARC:
            guess = random.choice(arc_pool)
            if guess==y: ok+=1
        return ok/len(mod.ARC)

    return {'winograd': win_random(), 'arc': arc_random(), 'tom': tom_random()}

def bootstrap_ci(values, nboot=1000, alpha=0.05):
    if not values:
        return (None, None)
    boot=[]
    for _ in range(nboot):
        sample = [random.choice(values) for _ in range(len(values))]
        boot.append(statistics.mean(sample))
    boot.sort()
    lo = boot[int((alpha/2)*len(boot))]
    hi = boot[int((1-alpha/2)*len(boot))-1]
    return (lo,hi)

def main(seeds=10):
    seeds_list = list(range(1, seeds+1))
    results = []
    errors = []
    for s in seeds_list:
        r = run_one(s)
        if 'error' in r:
            errors.append({'seed': s, 'error': r['error']})
        else:
            results.append(r)

    # collect per-metric lists
    win = [r['winograd'] for r in results]
    arc = [r['arc'] for r in results]
    tom = [r['tom'] for r in results]

    aggregated = {
        'runs': len(results),
        'errors': errors,
        'metrics': {
            'winograd': {
                'mean': statistics.mean(win) if win else None,
                '95ci': bootstrap_ci(win)
            },
            'arc': {
                'mean': statistics.mean(arc) if arc else None,
                '95ci': bootstrap_ci(arc)
            },
            'tom': {
                'mean': statistics.mean(tom) if tom else None,
                '95ci': bootstrap_ci(tom)
            }
        },
        'baseline_random': baseline_random_for_tests()
    }

    out_path = OUT_DIR / 'AGL_AGI_UnifiedReport_aggregated.json'
    with open(out_path, 'w', encoding='utf-8') as fh:
        json.dump(aggregated, fh, ensure_ascii=False, indent=2)
    print(f'Aggregated report saved to {out_path}')
    print(json.dumps(aggregated, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main( seeds=int(os.environ.get('AGL_AGI_RUNS', '10')) )
