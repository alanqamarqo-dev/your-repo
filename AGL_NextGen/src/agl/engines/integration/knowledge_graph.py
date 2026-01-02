from collections import defaultdict
from typing import Dict, List
from .dkn_types import Claim
import json
import os
from difflib import SequenceMatcher


class KnowledgeGraph:
    def __init__(self):
        # keyed by kind of claim (e.g. 'answer_piece','constraint','metric')
        self.nodes: Dict[str, List[Claim]] = defaultdict(list)
        # optional edges between claims (for later use)
        self.edges: List[Dict] = []
        # episodic storage: append dict snapshots
        self.episodic: List[Dict] = []

    def add_claim(self, claim: Claim):
        try:
            self.nodes[claim.kind].append(claim)
        except Exception:
            # defensive: ignore bad claim shapes
            return

    def recent(self, kind: str, k: int = 5) -> List[Claim]:
        return sorted(self.nodes.get(kind, []), key=lambda c: c.ts, reverse=True)[:k]

    def snapshot(self) -> Dict:
        # small snapshot useful for RAG/archiving
        snap = {k: [dict(content=x.content, confidence=x.confidence, source=x.source, ts=x.ts) for x in v]
                for k, v in self.nodes.items()}
        return snap

    def append_episode(self, record: Dict):
        self.episodic.append(record)

    def snapshot_to_file(self, path: str):
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'a', encoding='utf-8') as f:
                json.dump(self.snapshot(), f, ensure_ascii=False)
                f.write('\n')
        except Exception:
            # non-fatal: ignore IO errors
            pass

    def retrieve_similar(self, prompt: str, k: int = 5) -> List[Claim]:
        """Retrieve up to k claims whose textual content is most similar to prompt.

        This is a lightweight fallback: it concatenates textual fields from claims
        and ranks by SequenceMatcher ratio. For better performance add an
        embedding-based retriever later.
        """
        scored = []
        if not prompt:
            return []
        for kind, claims in self.nodes.items():
            for c in claims:
                # extract representative text
                txt = ''
                try:
                    if isinstance(c.content, dict):
                        # look for common text keys
                        for key in ('text', 'answer', 'summary'):
                            if key in c.content and isinstance(c.content[key], str):
                                txt = c.content[key]
                                break
                        if not txt:
                            # fallback: stringify content
                            txt = json.dumps(c.content, ensure_ascii=False)
                    else:
                        txt = str(c.content)
                except Exception:
                    txt = str(c.content)

                try:
                    sim = SequenceMatcher(None, prompt, txt).ratio()
                except Exception:
                    sim = 0.0
                scored.append((sim, c))

        scored.sort(key=lambda x: -x[0])
        return [c for s, c in scored[:k] if s > 0.0]
