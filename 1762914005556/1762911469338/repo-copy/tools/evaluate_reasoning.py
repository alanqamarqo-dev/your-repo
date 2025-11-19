import json, os

OUT = 'artifacts/reasoning_eval.json'

def compute_metrics():
    # simple metrics based on artifacts files
    hyp_ok = 'artifacts/hypotheses.jsonl'
    hyp_bad = 'artifacts/hypotheses_rejected.jsonl'
    graph = 'artifacts/causal_graph.json'
    stats = {}
    ok = 0
    bad = 0
    if os.path.exists(hyp_ok):
        with open(hyp_ok, 'r', encoding='utf-8') as f:
            ok = sum(1 for _ in f)
    if os.path.exists(hyp_bad):
        with open(hyp_bad, 'r', encoding='utf-8') as f:
            bad = sum(1 for _ in f)
    cc = 0
    nodes = 0
    if os.path.exists(graph):
        with open(graph, 'r', encoding='utf-8') as f:
            g = json.load(f)
            nodes = len(g.get('nodes', {}))
            edges = g.get('edges', [])
            cc = sum(1 for n in g.get('nodes', {}) if any(e.get('src') == n or e.get('dst') == n for e in edges))
    metrics = {
        'hypotheses_generated': ok + bad,
        'hypotheses_accepted': ok,
        'hypotheses_rejected': bad,
        'causal_nodes': nodes,
        'causal_covered_nodes': cc,
        'causal_coverage_pct': (cc / nodes * 100.0) if nodes else 0.0
    }
    os.makedirs('artifacts', exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as out:
        json.dump(metrics, out, ensure_ascii=False, indent=2)
    print('WROTE', OUT)
    print(metrics)

if __name__ == '__main__':
    compute_metrics()
