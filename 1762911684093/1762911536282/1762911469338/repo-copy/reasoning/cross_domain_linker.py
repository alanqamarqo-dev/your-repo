import json, math
from collections import defaultdict
from typing import List, Dict, Any

def _norm(t: str) -> str:
    return "".join(ch for ch in t.lower() if ch.isalnum() or ch.isspace())

def jaccard(a: set, b: set) -> float:
    i = len(a & b); u = len(a | b) or 1
    return i / u

def link(narratives: List[Dict[str, Any]], min_score: float = 0.18):
    by_domain = defaultdict(list)
    for n in narratives:
        toks = set(_norm(n.get("text", "")).split())
        by_domain[n.get("domain")].append((n, toks))

    links = []
    domains = list(by_domain.keys())
    for i in range(len(domains)):
        for j in range(i+1, len(domains)):
            d1, d2 = domains[i], domains[j]
            for n1, t1 in by_domain[d1]:
                for n2, t2 in by_domain[d2]:
                    score = jaccard(t1, t2)
                    if score >= min_score:
                        links.append({
                            "a": {"id": n1["id"], "domain": d1},
                            "b": {"id": n2["id"], "domain": d2},
                            "score": round(score, 3)
                        })
    return links
