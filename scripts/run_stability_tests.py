#!/usr/bin/env python3
"""Run mission_runner_direct multiple times, score each run, and aggregate stats.
Writes per-run artifacts into `artifacts/` and summary CSV `artifacts/mission_stability_summary.csv`.
"""
import subprocess
import os
import shutil
import time
import csv
import json
import statistics

HERE = os.path.dirname(__file__)
ART = os.path.join(HERE, '..', 'artifacts')
ART = os.path.abspath(ART)
os.makedirs(ART, exist_ok=True)

RUNS = 3

def run_once(i):
    print(f'=== Run {i} ===')
    # call mission runner
    r = subprocess.run(['python', os.path.join(HERE, 'mission_runner_direct.py')], cwd=os.path.abspath(HERE), capture_output=True, text=True)
    print(r.stdout)
    if r.returncode != 0:
        print('mission_runner_direct failed:', r.stderr)
        return False
    src = os.path.join(ART, 'mission_direct_results.json')
    dest = os.path.join(ART, f'mission_direct_results_run{i}.json')
    if os.path.exists(src):
        shutil.move(src, dest)
    else:
        print('Expected artifact not found after run')
        return False
    # score it
    out_csv = os.path.join(ART, f'mission_eval_with_scores_run{i}.csv')
    r2 = subprocess.run(['python', os.path.join(HERE, 'compute_semantic_scores.py'), '--artifact', dest, '--out', out_csv], cwd=os.path.abspath(HERE), capture_output=True, text=True)
    print(r2.stdout)
    if r2.returncode != 0:
        print('scoring failed:', r2.stderr)
        return False
    return True


def aggregate(runs):
    # collect per-question scores
    per_q = {}
    for i in range(1, runs+1):
        csvp = os.path.join(ART, f'mission_eval_with_scores_run{i}.csv')
        if not os.path.exists(csvp):
            continue
        with open(csvp, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                qid = row['id']
                score = float(row.get('semantic_score') or 0)
                rt = float(row.get('rt_s') or 0)
                per_q.setdefault(qid, {'scores': [], 'rts': []})
                per_q[qid]['scores'].append(score)
                per_q[qid]['rts'].append(rt)
    outp = os.path.join(ART, 'mission_stability_summary.csv')
    with open(outp, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(('id','mean_score','std_score','mean_rt','std_rt','n'))
        for qid, vals in sorted(per_q.items()):
            n = len(vals['scores'])
            mean_s = statistics.mean(vals['scores']) if n else 0
            std_s = statistics.pstdev(vals['scores']) if n else 0
            mean_rt = statistics.mean(vals['rts']) if n else 0
            std_rt = statistics.pstdev(vals['rts']) if n else 0
            w.writerow([qid, mean_s, std_s, mean_rt, std_rt, n])
    print('Wrote stability summary to', outp)


def main():
    for i in range(1, RUNS+1):
        ok = run_once(i)
        if not ok:
            print('Run', i, 'failed — aborting further runs')
            break
        # small delay to let services settle
        time.sleep(1)
    aggregate(RUNS)

if __name__ == '__main__':
    main()
