import json, time, pathlib, sys, os
# ensure repository root is on sys.path so Core_Engines is importable when running this script directly
sys.path.append(os.getcwd())
from Core_Engines.Hypothesis_Generator import HypothesisGenerator
from Core_Engines.Consistency_Checker import ConsistencyChecker
from Core_Engines.Causal_Graph import CausalGraph
try:
    from infra.adaptive.AdaptiveMemory import suggest_reasoning_pairs
except Exception:
    suggest_reasoning_pairs = None

# tracing
try:
    from infra.monitoring.trace import emit as _emit
except Exception:
    _emit = lambda *a, **k: None

FACTS_PATH = pathlib.Path("artifacts/harvested_facts.jsonl")
HYP_OK = pathlib.Path("artifacts/hypotheses.jsonl")
HYP_BAD = pathlib.Path("artifacts/hypotheses_rejected.jsonl")

def read_facts(limit=500):
    if not FACTS_PATH.exists(): return []
    facts=[]
    with FACTS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            try: facts.append(json.loads(line))
            except: pass
    return facts[-limit:]

def append_jsonl(path, items):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False)+"\n")

def main():
    facts = read_facts()
    if not facts:
        print("[reasoning] no facts, exit.")
        return

    gen = HypothesisGenerator()
    # if memory provides seed pairs, pass them to the generator if it accepts seeds
    seed_pairs = []
    if suggest_reasoning_pairs is not None:
        try:
            seed_pairs = suggest_reasoning_pairs(max_pairs=10)
        except Exception:
            seed_pairs = []
    try:
        hyps = gen.propose(facts, seed_pairs=seed_pairs) # type: ignore
    except TypeError:
        # older generator interface: ignore seed_pairs
        hyps = gen.propose(facts)

    try:
        import uuid
        reasoning_id = str(uuid.uuid4())
    except Exception:
        reasoning_id = None

    try:
        _emit('reasoning.propose', {
            'n_facts': len(facts),
            'n_hyps': len(hyps) if hyps is not None else 0,
            'decision_id': reasoning_id,
            'rationale': 'generate_hypotheses',
            'confidence': None,
        })
    except Exception:
        pass

    graph = CausalGraph()
    checker = ConsistencyChecker()
    res = checker.check(graph, facts, hyps)

    # compute a simple consistency confidence: 1 - contradictions/(accepted+rejected+1)
    accepted = 0
    rejected = 0
    contradictions = 0
    consistency_conf = None
    try:
        accepted = len(res.get('accepted_hypotheses', []))
        rejected = len(res.get('rejected_hypotheses', []))
        contradictions = len(res.get('contradictions', []))
        total = accepted + rejected + 1
        consistency_conf = max(0.0, min(1.0, 1.0 - (contradictions / float(total))))
    except Exception:
        consistency_conf = None

    try:
        _emit('reasoning.check', {
            'accepted': accepted,
            'rejected': rejected,
            'contradictions': contradictions,
            'decision_id': reasoning_id,
            'rationale': 'consistency_check',
            'confidence': consistency_conf,
        })
    except Exception:
        pass

    # Upsert accepted into graph
    graph.upsert_from_hypotheses(res.get("accepted_hypotheses", []))
    graph.save()

    try:
        _emit('reasoning.upsert', {
            'n_upserted': len(res.get('accepted_hypotheses', [])),
            'decision_id': reasoning_id,
            'rationale': 'upsert_accepted',
            'confidence': consistency_conf,
        })
    except Exception:
        pass

    # Stamp
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    for h in res.get("accepted_hypotheses", []):
        h["ts"] = now
    for h in res.get("rejected_hypotheses", []):
        h["ts"] = now

    append_jsonl(HYP_OK,  res.get("accepted_hypotheses", []))
    append_jsonl(HYP_BAD, res.get("rejected_hypotheses", []))

    print(f"[reasoning] accepted={len(res.get('accepted_hypotheses', []))} "
          f"rejected={len(res.get('rejected_hypotheses', []))} "
          f"contradictions={len(res.get('contradictions', []))}")

if __name__ == "__main__":
    main()
