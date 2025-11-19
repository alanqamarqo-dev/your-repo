from pathlib import Path
import json, datetime as dt
from typing import Dict

def synthesize(hypotheses_path: Path, facts_index: Dict[str, str], max_items=50):
    """Merge latest accepted hypotheses + supporting facts into short Arabic paragraphs.

    If you want improved fluency, set env AGL_USE_LLM_FOR_NARRATIVE=1 and implement
    an LLM-based refine step.
    """
    hyps = []
    if not hypotheses_path.exists():
        return {"narratives": [], "generated_at": dt.datetime.utcnow().isoformat() + "Z"}
    with hypotheses_path.open('r', encoding='utf-8') as f:
        for line in f:
            try:
                obj = json.loads(line)
                hyps.append(obj)
            except Exception:
                continue
    hyps = hyps[-max_items:]

    narratives = []
    for h in hyps:
        support = h.get("support", [])
        snippets = [facts_index.get(s, "") for s in support if s in facts_index]
        paragraph = (
            f"فرضية: {h.get('hypothesis','')}\n"
            f"الدعم: " + ("؛ ".join(s for s in snippets if s) or "—")
        )
        narratives.append({
            "id": h.get("id"),
            "domain": h.get("domain"),
            "text": paragraph,
            "confidence": h.get("confidence", 0.5),
            "ts": h.get("ts")
        })
    return {"narratives": narratives, "generated_at": dt.datetime.utcnow().isoformat() + "Z"}
