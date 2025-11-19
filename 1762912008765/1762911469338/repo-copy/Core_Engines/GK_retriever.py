import os
from typing import List, Dict, Any

# blending knob (0.0 = TF-IDF only, 1.0 = embeddings only)
def _to_float(k, d):
    try:
        return float(os.environ.get(k, str(d)))
    except Exception:
        return d

_AGL_RETRIEVER_BLEND_ALPHA = _to_float("AGL_RETRIEVER_BLEND_ALPHA", 0.0)

# make small numeric limits configurable via env while keeping conservative defaults
# controlled by AGL_RETRIEVER_TOP_K (default 8)
try:
    _AGL_RETRIEVER_TOP_K = int(os.environ.get('AGL_RETRIEVER_TOP_K', '8'))
except Exception:
    _AGL_RETRIEVER_TOP_K = 8

try:
    _AGL_EVIDENCE_LIMIT = int(os.environ.get('AGL_EVIDENCE_LIMIT', '10'))
except Exception:
    _AGL_EVIDENCE_LIMIT = 10
# controlled by AGL_EVIDENCE_LIMIT (default 10)


class GKRetriever:
    def __init__(self, kb_adapters: Dict[str, Any]):
        self.kb = kb_adapters

    def retrieve(self, query) -> List[Any]:
        e1 = []
        try:
            e1 = self.kb["local"].search_text(query.text, top_k=_AGL_RETRIEVER_TOP_K)
        except Exception:
            e1 = []
        e2 = []
        if self.kb.get("vector"):
            try:
                e2 = self.kb.get("vector").search(query.text, top_k=_AGL_RETRIEVER_TOP_K)  # type: ignore
            except Exception:
                e2 = []
        # If both sources provide scored results (dicts with '_score'), blend them.
        def _get_id(item, src_idx):
            if isinstance(item, dict):
                return item.get('id') or item.get('payload', {}).get('id') or item.get('_id')
            return f"src{src_idx}:{str(item)[:200]}"

        tfidf_map = {}
        for it in e1:
            key = _get_id(it, 1)
            if key is None:
                key = f"tf_{len(tfidf_map)}"
            tfidf_map[key] = {'item': it, 'tfidf_score': float(it.get('_score', 0.0) if isinstance(it, dict) else 0.0)}

        emb_map = {}
        for it in e2:
            key = _get_id(it, 2)
            if key is None:
                key = f"emb_{len(emb_map)}"
            emb_map[key] = {'item': it, 'emb_score': float(it.get('_score', 0.0) if isinstance(it, dict) else 0.0)}

        # merge keys
        merged_keys = set(list(tfidf_map.keys()) + list(emb_map.keys()))
        merged = []
        for k in merged_keys:
            tf = tfidf_map.get(k, {}).get('tfidf_score', 0.0)
            em = emb_map.get(k, {}).get('emb_score', 0.0)
            item = tfidf_map.get(k, {}).get('item') or emb_map.get(k, {}).get('item')
            # apply blend
            a = _AGL_RETRIEVER_BLEND_ALPHA
            blended = (1.0 - a) * tf + a * em
            merged.append((blended, item))

        # If blending is a no-op (alpha == 0) and both lists are plain items, keep original order
        if _AGL_RETRIEVER_BLEND_ALPHA == 0.0 and not any(isinstance(x, dict) for x in (e1 + e2)):
            evidences = (e1 + e2)[:_AGL_EVIDENCE_LIMIT]
            return evidences

        # sort by blended score desc and return items
        merged.sort(key=lambda x: x[0], reverse=True)
        evidences = [it for _, it in merged][:_AGL_EVIDENCE_LIMIT]
        return evidences


def create_engine(config: Dict[str, Any] | None = None):
    """Factory used by bootstrap_register_all_engines.

    Creates a lightweight GKRetriever with harmless, no-network adapters if
    real knowledge backends are not configured. This prevents bootstrap from
    skipping GK_retriever due to missing constructor args.
    """
    # Minimal local adapter that returns no results but has the expected API
    class _LocalKB:
        def search_text(self, text, top_k=_AGL_RETRIEVER_TOP_K):
            return []

    kb_adapters: Dict[str, Any] = {"local": _LocalKB()}

    # Adapter wrapper to expose the minimal engine interface expected by
    # bootstrap_register_all_engines (process_task + name).
    class _GKRetrieverEngine(GKRetriever):
        def __init__(self, kb):
            super().__init__(kb)
            self.name = "GK_retriever"

        def process_task(self, task: Any):
            # Accept either a simple query string or a dict with 'query'
            q = None
            if isinstance(task, dict):
                q = task.get("query") or task.get("text")
            elif isinstance(task, str):
                q = task
            if q is None:
                return {"ok": True, "evidences": []}

            class _Q:
                def __init__(self, text):
                    self.text = text

            evidences = self.retrieve(_Q(q))
            return {"ok": True, "evidences": evidences}

    return _GKRetrieverEngine(kb_adapters)
