from scripts._bootstrap import ensure_project_root
root = ensure_project_root()

import json, time
from pathlib import Path
from Integration_Layer import rag_wrapper as rw

q = (
    "اشرح باختصار أثر صدمة نفطية على اقتصاد يعتمد على الاستيراد، مع ذكر عاملين كابحين للتضخم."
)

t0 = time.perf_counter()
resp = rw.rag_answer(q)
dt = time.perf_counter() - t0


def _get(k: str):
    if isinstance(resp, dict):
        return resp.get(k)
    return getattr(resp, k, None)


out = {
    "question": q,
    "elapsed_seconds": round(dt, 3),
    "engine": _get("engine"),
    "sources": _get("sources"),
    "answer": _get("answer"),
}

out_dir = Path(root) / "artifacts" / "rag_health"
out_dir.mkdir(parents=True, exist_ok=True)
out_file = out_dir / "health.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print(f"✅ RAG OK in {out['elapsed_seconds']}s via {out['engine']}. Saved: {out_file}")
