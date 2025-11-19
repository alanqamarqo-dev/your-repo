class GKGraph:
    def __init__(self, **kwargs):
        self.name = "GK_graph"

    @staticmethod
    def create_engine(config=None):
        return GKGraph()

    def process_task(self, payload: dict):
        return {"ok": True, "engine": "gk_graph:stub", "nodes": []}
import re
import os
from typing import List, Tuple, Dict, Any

# configurable node sampling size for displays and small diagnostics
try:
    _AGL_GK_GRAPH_NODE_SAMPLE = int(os.environ.get('AGL_GK_GRAPH_NODE_SAMPLE', '20'))
except Exception:
    _AGL_GK_GRAPH_NODE_SAMPLE = 20

try:
    _AGL_GK_GRAPH_MAX_NODES = int(os.environ.get('AGL_GK_GRAPH_MAX_NODES', '500'))
except Exception:
    _AGL_GK_GRAPH_MAX_NODES = 500

try:
    _AGL_GK_GRAPH_MAX_EDGES = int(os.environ.get('AGL_GK_GRAPH_MAX_EDGES', '2000'))
except Exception:
    _AGL_GK_GRAPH_MAX_EDGES = 2000


class GKGraph:
    def __init__(self):
        self.nodes = set()
        self.edges: List[Tuple[str, str, str, float]] = []
        # optional provenance/meta per edge index
        self.edge_meta: Dict[int, Dict[str, Any]] = {}

    def ingest_evidence(self, evidences: List[Any]) -> int:
        # simple SPO extraction: look for patterns "X is Y" (Arabic/English)
        count = 0
        for e in evidences:
            text = getattr(e, "text", "")
            # naive english "X is Y"
            m = re.search(r"([A-Za-z\u0600-\u06FF\s]{2,30})\s+(?:is|are|هي|هو)\s+([A-Za-z\u0600-\u06FF\s]{1,30})", text)
            if m:
                s = m.group(1).strip()
                o = m.group(2).strip()
                p = "is"
                self.nodes.add(s)
                self.nodes.add(o)
                self.edges.append((s, p, o, getattr(e, "score", 0.5)))
                count += 1
                # enforce max edges cap
                if len(self.edges) >= _AGL_GK_GRAPH_MAX_EDGES:
                    break
        return count

    def upsert_facts(self, facts: List[Any]) -> int:
        added = 0
        for f in facts:
            # support both object.field names and dict-like facts
            subj = getattr(f, "subject", None) if not isinstance(f, dict) else f.get("subject")
            pred = getattr(f, "predicate", None) if not isinstance(f, dict) else f.get("predicate")
            obj = getattr(f, "obj", None) if not isinstance(f, dict) else (f.get("object") or f.get("obj"))
            if subj and pred and obj:
                self.nodes.add(subj)
                self.nodes.add(obj)
                conf = getattr(f, "confidence", None) if not isinstance(f, dict) else f.get("confidence", 0.5)
                # store provenance as part of edge tuple if present (source, added_by, added_at)
                source = getattr(f, "source", None) if not isinstance(f, dict) else f.get("source")
                added_by = getattr(f, "added_by", None) if not isinstance(f, dict) else f.get("added_by")
                added_at = getattr(f, "added_at", None) if not isinstance(f, dict) else f.get("added_at")
                conf_val = conf if conf is not None else 0.5
                idx = len(self.edges)
                # enforce graph size caps
                if len(self.nodes) < _AGL_GK_GRAPH_MAX_NODES and len(self.edges) < _AGL_GK_GRAPH_MAX_EDGES:
                    self.edges.append((subj, pred, obj, conf_val))
                else:
                    # skip if we reached capacity
                    continue
                if source or added_by or added_at:
                    self.edge_meta[idx] = {"source": source, "added_by": added_by, "added_at": added_at}
                added += 1
        return added

    def link_text(self, text: str) -> Dict[str, Any]:
        # return simple mentions and naive links
        mentions = []
        for node in list(self.nodes)[:_AGL_GK_GRAPH_NODE_SAMPLE]:
            if node in text:
                mentions.append(node)
        return {"mentions": mentions, "links": []}


# ensure a create_engine exists and that the class exposes process_task
def _gk_process_task(self, payload: dict) -> dict:
    try:
        if payload.get('action') == 'ingest':
            cnt = self.ingest_evidence(payload.get('evidences', []))
            return {'ok': True, 'ingested': cnt}
        if payload.get('action') == 'link':
            return {'ok': True, 'result': self.link_text(payload.get('text',''))}
        if payload.get('action') == 'upsert':
            return {'ok': True, 'added': self.upsert_facts(payload.get('facts', []))}
        return {'ok': True, 'nodes': list(self.nodes)[:_AGL_GK_GRAPH_NODE_SAMPLE], 'edges': len(self.edges)}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


if not hasattr(GKGraph, 'process_task'):
    setattr(GKGraph, 'process_task', _gk_process_task)


def create_engine(config: dict | None = None):
    return GKGraph()
