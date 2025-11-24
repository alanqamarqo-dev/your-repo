import os, json, subprocess, sys, time, glob

CFG_PATH = 'config/coverage_boost.json'
from Learning_System.io_utils import read_json
CFG = read_json(CFG_PATH) if os.path.exists(CFG_PATH) else {}
PY = sys.executable

def run(cmd):
    return subprocess.run(cmd, text=True, capture_output=True)

def train_all():
    cmds = []
    # only add commands if data exists
    if os.path.exists('data/training/B_ohm_B.csv'):
        # Use a safe wrapper that checks existence and avoids crashing if file missing
        cmds.append([PY, "scripts/safe_self_learning.py", "--base", "ohm", "--data", "data/training/B_ohm_B.csv", "--out", "artifacts/models/ohm_B"])
    else:
        print('Skipping ohm training; data file missing: data/training/B_ohm_B.csv')
    if os.path.exists('data/phaseD/poly2_iv.csv'):
        cmds.append([PY,"-m","scripts.train_phaseD","--data","data/phaseD/poly2_iv.csv","--x","I","--y","V","--candidates","poly2","a*x**2","k*x","k*x + b","--out","artifacts/models/poly2_D"])
    else:
        print('Skipping phaseD training; data file missing: data/phaseD/poly2_iv.csv')
    for c in cmds:
        print('Running:', c)
        r = run(c)
        print(r.stdout or r.stderr)

def evaluate_and_update_fusion():
    best = {}
    for fp in glob.glob('artifacts/models/**/results.json', recursive=True):
        try:
            j = read_json(fp)
            if 'ensemble' in j and j['ensemble'].get('success'):
                r = j['ensemble']['result']
                base = j.get('base','?')
                best[base] = {'rmse': r.get('rmse', 1e9), 'confidence': r.get('confidence', 0.0)}
            elif 'results' in j and j['results']:
                r = sorted(j['results'], key=lambda k: k.get('fit', {}).get('rmse', 1e9))[0]
                base = j.get('base','?')
                best[base] = {'rmse': r.get('fit', {}).get('rmse', 1e9), 'confidence': r.get('fit', {}).get('confidence', 0.0)}
        except Exception:
            pass

    fusion_path = 'config/fusion_weights.json'
    fw = {'mathematical_brain':1.0, 'quantum_processor':0.6, 'code_generator':1.2, 'protocol_designer':0.6}
    if os.path.exists(fusion_path):
        try:
            fw = read_json(fusion_path)
        except Exception:
            pass

    def clamp(v):
        caps = CFG.get('fusion', {}).get('caps', {'min':0.4,'max':1.35})
        return max(caps['min'], min(caps['max'], v))

    avg_conf = sum(v['confidence'] for v in best.values())/max(1,len(best))
    grad = (avg_conf - 0.5) * CFG.get('fusion', {}).get('eta', 0.15)
    for k in list(fw.keys()):
        fw[k] = clamp(fw.get(k,1.0) + grad)

    # atomic write
    with open(fusion_path + '.tmp', 'w', encoding='utf-8') as f:
        json.dump(fw, f, ensure_ascii=False, indent=2)
    try:
        os.replace(fusion_path + '.tmp', fusion_path)
    except Exception:
        pass
    print('Updated fusion_weights:', fw)

def main():
    train_all()
    # run a few critical unit tests (best-effort)
    for t in ['tests.test_ensemble_selector','tests.test_reasoner','tests.test_generalization_matrix','tests.test_emergency_system_ar']:
        print('Running tests:', t)
        r = run([PY,'-m','unittest','-v',t])
        print(r.stderr or r.stdout)
    evaluate_and_update_fusion()
    # produce a combined report if available
    run([PY,'-m','scripts.report_summary','--out','reports/combined/full_system_report.html'])

if __name__ == '__main__':
    main()
