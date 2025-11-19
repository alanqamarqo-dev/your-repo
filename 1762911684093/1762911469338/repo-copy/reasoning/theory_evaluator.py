import statistics as stats
from typing import List, Dict, Any

def evaluate(narratives: List[Dict[str, Any]], links: List[Dict[str, Any]]):
    if not narratives:
        return {"coherence":0, "consistency":0, "falsifiability":0, "coverage":0}

    confs = [n.get("confidence", 0.5) for n in narratives]
    link_density = len(links) / max(1, len(narratives))
    coherence = min(1.0, 0.7*stats.fmean(confs) + 0.3*min(1.0, link_density))

    consistency = 1.0

    falsi_hits = sum(1 for n in narratives if ("قد" in n.get("text","") or "إذا" in n.get("text","")))
    falsifiability = min(1.0, falsi_hits / max(1, len(narratives)))

    domains = {n.get("domain") for n in narratives}
    coverage = min(1.0, len(domains) / 4)

    return {
        "coherence": round(coherence,3),
        "consistency": round(consistency,3),
        "falsifiability": round(falsifiability,3),
        "coverage": round(coverage,3),
        "links_count": len(links),
        "narratives_count": len(narratives),
        "domains_count": len(domains),
    }
