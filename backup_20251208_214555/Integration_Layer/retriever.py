# Simple keyword-based retriever over cached external facts
import os
import json
from typing import List, Dict, Any, Tuple

CACHE_DIR = os.path.join('artifacts', 'external_info_cache')

class SimpleFactsRetriever:
    def __init__(self, cache_dir: str | None = None):
        self.cache_dir = cache_dir or CACHE_DIR
        self._index = []  # list of tuples (text, source, confidence, meta_path)
        self._path_meta = {}  # path -> metadata (tags, num_facts, has_answer)
        self._load_cache()

    def _load_cache(self):
        self._index = []
        self._path_meta = {}
        try:
            if not os.path.isdir(self.cache_dir):
                return
            for fn in os.listdir(self.cache_dir):
                if not fn.endswith('.json'):
                    continue
                p = os.path.join(self.cache_dir, fn)
                try:
                    # Use a context manager and utf-8-sig to correctly handle BOM and
                    # ensure file handles are closed (avoids ResourceWarning).
                    with open(p, encoding='utf-8-sig') as fh:
                        j = json.load(fh)
                except Exception:
                    continue
                facts = j.get('facts') or []
                ans = j.get('answer')
                # file-level metadata: simple tag detection
                text_blob = json.dumps(j, ensure_ascii=False)
                tags = []
                if 'نيوتن' in text_blob or 'قانون' in text_blob:
                    tags.append('newton')
                if 'الطاقة' in text_blob or 'تنفي' in text_blob or 'تتحول' in text_blob:
                    tags.append('energy')
                self._path_meta[p] = {'tags': tags, 'num_facts': len(facts), 'has_answer': bool(ans)}
                for f in facts:
                    self._index.append((f.get('text', ''), f.get('source', ''), float(f.get('confidence', 0) or 0), p))
                if ans:
                    # treat cached answer as low-confidence fact too
                    self._index.append((str(ans), 'cached_answer', 0.3, p))
        except Exception:
            self._index = []
            self._path_meta = {}

    def refresh(self):
        self._load_cache()

    def retrieve(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        q = (query or '').lower()
        scored: List[Tuple[float, Dict[str, Any]]] = []
        for text, source, conf, path in self._index:
            t = (text or '').lower()
            # basic token sets
            qtokens = set(q.split()) if q else set()
            ttokens = set(t.split()) if t else set()
            # filter out very common short tokens and punctuation-like tokens to avoid spurious overlap
            STOPWORDS = {'في', 'على', 'من', 'إلى', 'ما', 'هو', 'هي', 'لماذا', 'كيف', 'متى', 'كم', 'هل', 'ان', 'عن', 'و', 'ب'}
            qtokens = set([tok for tok in qtokens if len(tok) > 2 and tok not in STOPWORDS])
            ttokens = set([tok for tok in ttokens if len(tok) > 2 and tok not in STOPWORDS])

            # normalized token overlap (fraction of query tokens covered)
            overlap_frac = 0.0
            if qtokens:
                overlap_frac = len(qtokens & ttokens) / float(len(qtokens))

            # require at least some lexical overlap OR a substring match to consider this candidate
            if overlap_frac == 0.0 and (q not in t):
                continue

            # scoring: prefer substring matches, then normalized overlap, then confidence (downweighted)
            score = 0.0
            if q in t and q:
                score += 2.0
            score += overlap_frac * 1.5
            # downweight cached confidence so it doesn't override relevance
            try:
                score += float(conf or 0.0) * 0.2
            except Exception:
                score += 0.0

            # Path-level safety rules: if the source path is dominated by a specific tag
            # (e.g., 'newton' or 'energy') and the query doesn't mention that tag and
            # overlap is small, skip or penalize heavily to avoid spurious answers.
            pmeta = self._path_meta.get(path, {})
            p_tags = set(pmeta.get('tags', []))
            if p_tags:
                # if path has a tag but query doesn't include the keyword, require stronger overlap
                tag_keywords = {'newton': 'نيوتن', 'energy': 'طاقة'}
                skip = False
                for tag in p_tags:
                    keyword = tag_keywords.get(tag)
                    if keyword and keyword not in q and overlap_frac < 0.6:
                        # penalize / skip
                        skip = True
                if skip:
                    # reduce chance of selection
                    score *= 0.01

            # deprioritize top-level cached answers (they're often generic)
            if source == 'cached_answer':
                score *= 0.4

            scored.append((score, {'text': text, 'source': source, 'confidence': conf, 'path': path, 'overlap': overlap_frac}))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scored[:k]]
