"""Soak-run harness: performs many tick() cycles and reports STM/LTM growth and evolution log alerts."""
import os, time, json
from pathlib import Path

from Self_Improvement.Knowledge_Graph import CognitiveIntegrationEngine


def read_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def stm_size(path):
    try:
        if not Path(path).exists():
            return 0
        j = read_json(path)
        if isinstance(j, list):
            return len(j)
        if isinstance(j, dict):
            return sum(1 for _ in j)
        return 0
    except Exception:
        return 0


def ltm_size(path):
    return stm_size(path)


def run_soak(iterations=100, snapshot_every=20):
    cie = CognitiveIntegrationEngine()
    cie.connect_engines()
    memroot = os.getenv('AGL_MEMORY_ROOT', 'artifacts/memory')
    stm = Path(memroot) / 'stm.json'
    ltm = Path(memroot) / 'ltm.json'

    for i in range(iterations):
        if i % 10 == 0:
            cie.pbus.push('sensor', {'tick': i, 'v': i % 7}, f't{i}')
        cie.pbus.push('vision', {'objects': ['pill', 'box', f'obj{i}']}, f't{i}')
        cie.pbus.push('audio', {'text': f'temp {36 + (i%5)}C'}, f't{i}')
        try:
            res = cie.tick(goal={'task': 'bg-health', 'step': i})
        except Exception as e:
            print('tick error at', i, e)
            break
        if i % snapshot_every == 0:
            print(f'iter {i}: stm={stm_size(stm)}, ltm={ltm_size(ltm)}, winner={(res.get("winner") or {}).get("engine")}')
    print('soak-run finished')


if __name__ == '__main__':
    run_soak(100, 20)
