import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

ARTIFACTS_DIR = Path(os.getenv("AGL_ARTIFACTS_DIR", "artifacts"))
LEARNED_FACTS_PATH = ARTIFACTS_DIR / "learned_facts.jsonl"

# When FAST_MODE is enabled for CI/test runs, tests may choose to avoid
# recording learned facts during specific benchmarks. Keep FAST_MODE flag
# available for callers, but do not force record/load behaviour here.
FAST_MODE = os.getenv("AGL_FAST_MODE", "0") == "1"


def _ensure_artifacts_dir():
    try:
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        # best-effort: if mkdir fails (permissions), we'll let callers handle failures
        pass


def record_learned_fact(problem: dict, answer: str, score: float, source: str = "qa_eval", min_score: float = 0.75) -> bool:
    """Record a learned fact as a JSONL row when answer quality passes threshold.

    - problem: dict containing title/question/etc as provided by AGL pipeline or benchmark
    - answer: final answer text
    - score: quality score (from benchmark or manual review)
    - source: origin tag (e.g., "zero_shot_qa_eval")
    - min_score: minimum score required to persist the fact
    """
    try:
        if score is None:
            return False
        if float(score) < float(min_score):
            return False
    except Exception:
        return False

    _ensure_artifacts_dir()

    # allow extra metadata (context_relations, hypothesis_variants, media_ctx)
    row = {
        "ts": float(datetime.utcnow().timestamp()),
        "source": source,
        "score": float(score),
        "title": (problem.get("title") or "") if isinstance(problem, dict) else "",
        "question": (problem.get("question") or "") if isinstance(problem, dict) else str(problem),
        "answer": answer or "",
    }
    try:
        # accept optional metadata passed via problem or outer calls
        if isinstance(problem, dict):
            if problem.get('context_relations'):
                row['context_relations'] = problem.get('context_relations')
            if problem.get('hypothesis_variants'):
                row['hypothesis_variants'] = problem.get('hypothesis_variants')
            if problem.get('media_ctx'):
                row['media_ctx'] = problem.get('media_ctx')
    except Exception:
        pass

    try:
        with LEARNED_FACTS_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return True
    except Exception:
        return False


def load_learned_facts(max_items: Optional[int] = None):
    """Load learned facts from the JSONL file.

    Returns a list of parsed rows (newest-first is not guaranteed; consumers can sort by `ts`).
    """
    if not LEARNED_FACTS_PATH.exists():
        return []

    rows = []
    try:
        with LEARNED_FACTS_PATH.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
                if max_items is not None and len(rows) >= max_items:
                    break
    except Exception:
        return []

    return rows


def load_learned_facts_as_context(max_items: int = 20) -> str:
    """Convert learned facts into a short textual context suitable for prepending
    to prompts sent to the LLM. Returns an empty string if no facts available.
    """
    facts = load_learned_facts(max_items=max_items)
    if not facts:
        return ""
    lines = []
    for f in facts:
        q = f.get("question") or f.get("problem_title") or ""
        a = f.get("answer") or f.get("final_answer") or ""
        if not a:
            continue
        # concise line, keep it human-readable and short
        lines.append(f"- لسؤال سابق «{q}» كانت خلاصة الجواب:\n {a}")
    return "\n".join(lines)
