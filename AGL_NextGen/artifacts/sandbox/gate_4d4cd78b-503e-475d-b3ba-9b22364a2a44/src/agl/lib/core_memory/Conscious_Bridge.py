from __future__ import annotations
import time, uuid, typing as T
import re
from collections import OrderedDict
import os
import sqlite3
import json
from pathlib import Path
from typing import Any
import sqlite3
import json
import os
import math
from typing import Iterable
try:
    from sklearn.feature_extraction.text import TfidfVectorizer # type: ignore
    from sklearn.metrics.pairwise import cosine_similarity # type: ignore
except Exception:
    TfidfVectorizer = None
    cosine_similarity = None

Event = T.TypedDict("Event", {"id": str, "ts": float, "type": str, "payload": T.Dict[str,T.Any], "trace_id": str, "ttl_s": T.Optional[float], "pinned": bool, "emotion": T.Optional[str]})
Link  = T.Tuple[str, str, str]  # (src_id, rel, dst_id)

class LRUCache:
    def __init__(self, capacity:int=256):
        self.capacity = capacity
        self._od: OrderedDict[str, Event] = OrderedDict()
    def get(self, key:str)->T.Optional[Event]:
        if key in self._od:
            self._od.move_to_end(key)
            return self._od[key]
        return None
    def set(self, key:str, value:Event):
        self._od[key] = value
        self._od.move_to_end(key)
        if len(self._od) > self.capacity:
            self._od.popitem(last=False)
    def values(self): return list(self._od.values())
    def delete(self, key:str): self._od.pop(key, None)
    def __len__(self): return len(self._od)

class ConsciousBridge:
    """
    واجهة موحّدة بين STM (ذاكرة قصيرة) و LTM (طويلة) + رسم علاقات سببية/معنوية.
    API:
      - put(event): يعيد event_id
      - link(a,b,rel): يربط حدثين (a→rel→b)
      - query(criteria): بحث مبسط (حسب النوع/trace_id/نطاق زمني/نص)
      - evict(policy): سياسة تفريغ للـ STM
    """
    def __init__(self, stm_capacity:int=256):
        self.stm = LRUCache(capacity=stm_capacity)
        self.ltm: dict[str, Event] = {}
        self.graph: dict[str, list[Link]] = {}  # adjacency by src_id
        self.index_by_type: dict[str, set[str]] = {}
        self.index_by_trace: dict[str, set[str]] = {}
        self.index_by_emotion: dict[str, set[str]] = {}
        # persistence
        self._db_path = os.path.join(os.path.dirname(__file__), "memory.db")
        self._conn: sqlite3.Connection | None = None
        # semantic index placeholders
        self._vectorizer = None
        self._doc_matrix = None
        self._doc_ids: list[str] = []
        # processing helpers flags
        self._use_embeddings = False
        self._use_faiss = False
        self._use_tfidf = False
        self._embeddings = None
        self._faiss_index = None
        self._nn_index = None
        self._kw_index = None
        # initialize DB and load persisted LTM entries
        try:
            self._init_db()
            self._load_ltm_from_db()
        except Exception:
            # best-effort: ignore persistence errors
            pass

    def _new_event(self, type:str, payload:dict, trace_id:str|None=None, ttl_s:float|None=None, pinned:bool=False, emotion: str|None = None)->Event:
        eid = str(uuid.uuid4())
        return {"id": eid, "ts": time.time(), "type": type, "payload": payload or {}, "trace_id": trace_id or eid, "ttl_s": ttl_s, "pinned": pinned, "emotion": emotion}

    def put(self, type:str, payload:dict, *, to="stm", trace_id:str|None=None, ttl_s:float|None=None, pinned:bool=False, emotion: str|None = None)->str:
        ev = self._new_event(type, payload, trace_id, ttl_s, pinned, emotion)
        if to == "ltm":
            self.ltm[ev["id"]] = ev
            # persist to sqlite if available
            try:
                self._persist_event(ev)
            except Exception:
                pass
        else:
            self.stm.set(ev["id"], ev)
        # فهارس
        self.index_by_type.setdefault(ev["type"], set()).add(ev["id"])
        self.index_by_trace.setdefault(ev["trace_id"], set()).add(ev["id"])
        if ev.get('emotion'):
            self.index_by_emotion.setdefault(ev.get('emotion'), set()).add(ev['id'])
        return ev["id"]

    def link(self, src_id: str, dst_id: str, relation: str = "related_to") -> bool:
        """Create a directed link between two events."""
        if not (self._get(src_id) and self._get(dst_id)):
            return False
        self.graph.setdefault(src_id, []).append((src_id, relation, dst_id))
        return True

    def _get(self, eid: str) -> Event | None:
        """Helper to get event from STM or LTM."""
        return self.stm.get(eid) or self.ltm.get(eid)

    # Persistence helpers
    def _init_db(self):
        """Create/open sqlite DB and ensure events table exists."""
        try:
            self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
            cur = self._conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    ts REAL,
                    type TEXT,
                    payload TEXT,
                    emotion TEXT,
                    trace_id TEXT,
                    ttl_s REAL,
                    pinned INTEGER
                )
                """
            )
            self._conn.commit()
        except Exception:
            self._conn = None

    def _persist_event(self, ev: Event):
        if not self._conn:
            return
        cur = self._conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO events(id, ts, type, payload, emotion, trace_id, ttl_s, pinned) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (ev["id"], float(ev["ts"]), ev.get("type"), json.dumps(ev.get("payload", {}), ensure_ascii=False), ev.get("emotion"), ev.get("trace_id"), ev.get("ttl_s"), 1 if ev.get("pinned") else 0),
        )
        self._conn.commit()

    def _load_ltm_from_db(self):
        if not self._conn:
            return
        cur = self._conn.cursor()
        cur.execute("SELECT id, ts, type, payload, emotion, trace_id, ttl_s, pinned FROM events")
        rows = cur.fetchall()
        for r in rows:
            try:
                pid, ts, typ, payload_text, emotion, trace_id, ttl_s, pinned = r
                payload = json.loads(payload_text) if payload_text else {}
                ev: Event = {"id": pid, "ts": float(ts), "type": typ, "payload": payload, "trace_id": trace_id, "ttl_s": ttl_s, "pinned": bool(pinned), "emotion": emotion}
                self.ltm[pid] = ev
                self.index_by_type.setdefault(typ, set()).add(pid)
                self.index_by_trace.setdefault(trace_id or pid, set()).add(pid)
                if emotion:
                    self.index_by_emotion.setdefault(emotion, set()).add(pid)
            except Exception:
                continue

    def export_ltm_to_db(self, ids: Iterable[str]|None=None):
        """Persist current LTM entries to sqlite. If ids is None, persist all."""
        if ids is None:
            ids = list(self.ltm.keys())
        for i in ids:
            ev = self.ltm.get(i)
            if ev:
                try:
                    self._persist_event(ev)
                except Exception:
                    pass

    # Semantic indexing/search (TF-IDF fallback)
    def build_semantic_index(self, *, analyzer: str = 'char_wb', ngram_range=(3,5)) -> int:
        """Build a semantic index (TF-IDF or embeddings) over LTM event text representations.

        Applies enhanced preprocessing to each document before indexing. Returns
        the number of documents indexed.
        """
        docs = []
        ids = []
        for eid, ev in self.ltm.items():
            txt = f"{ev.get('type','')} {json.dumps(ev.get('payload',{}), ensure_ascii=False)}"
            processed = self._enhanced_text_preprocessing(txt)
            if processed is None:
                # skip very weak/auto-seed docs
                continue
            docs.append(processed)
            ids.append(eid)

        if not docs:
            self._vectorizer = None
            self._doc_matrix = None
            self._doc_ids = []
            return 0

        try:
            # prefer TF-IDF here (embedding path handled in the other build below)
            vec = self._optimized_tfidf_settings()
            self._vectorizer = vec.fit(docs)
            self._doc_matrix = self._vectorizer.transform(docs)
            self._doc_ids = ids
            self._use_tfidf = True
            self._use_embeddings = False
            return len(ids)
        except Exception:
            self._vectorizer = None
            self._doc_matrix = None
            self._doc_ids = []
            return 0

    def _enhanced_text_preprocessing(self, text: str):
        """Lightweight text preprocessing including Arabic normalization and filtering.

        Returns cleaned text or None to indicate the document should be skipped.
        """
        try:
            # apply explicit Arabic preprocess hook first
            def _pre_ar(s: str) -> str:
                if not isinstance(s, str):
                    s = str(s)
                s = s.lower()
                _AR_PUNCT = r"[ـ\u0610-\u061A\u064B-\u065F\u06D6-\u06ED]"
                s = re.sub(_AR_PUNCT, "", s)
                s = re.sub(r"[^\w\s\u0600-\u06FF]", " ", s)
                s = re.sub(r"\s+", " ", s).strip()
                return s

            text = _pre_ar(text)
            # collapse whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            if not text:
                return None
            if 'auto-seed event' in text.lower():
                return None
            # Arabic-specific normalizations
            if any('\u0600' <= c <= '\u06FF' for c in text):
                # remove diacritics
                text = re.sub(r'[\u064B-\u065F]', '', text)
                # unify common letter variants
                text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
            return text
        except Exception:
            return text

    def _optimized_tfidf_settings(self):
        """Return a configured TfidfVectorizer tuned for the repository.

        Tuned settings: larger vocabulary, ignore very rare/common terms, use unigrams+bigrams.
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer # type: ignore
            return TfidfVectorizer(
                max_features=20000,
                min_df=3,
                max_df=0.7,
                ngram_range=(1, 2),
                stop_words=None,
                analyzer='word'
            )
        except Exception:
            # fallback to a minimal vectorizer if sklearn missing
            try:
                from sklearn.feature_extraction.text import TfidfVectorizer # type: ignore
                return TfidfVectorizer(max_features=8192)
            except Exception:
                return None

    def semantic_search(self, query: str, top_k: int = 5) -> list[Event]:
        """Return top_k LTM events most similar to query using TF-IDF cosine similarity."""
        if TfidfVectorizer is None or self._vectorizer is None or self._doc_matrix is None:
            return []
        try:
            qv = self._vectorizer.transform([query])
            sims = cosine_similarity(qv, self._doc_matrix)[0]
            # get top_k indices
            idxs = sorted(range(len(sims)), key=lambda i: sims[i], reverse=True)[:top_k]
            out = []
            for i in idxs:
                eid = self._doc_ids[i]
                ev = self.ltm.get(eid)
                if ev:
                    out.append(ev)
            return out
        except Exception as e:
            # best-effort fallback: try simple keyword matching instead of failing silently
            try:
                proc_query = self._enhanced_text_preprocessing(query) if hasattr(self, '_enhanced_text_preprocessing') else (query or '')
                qwords = set((proc_query or '').lower().split())
                scores = {}
                for eid, ev in self.ltm.items():
                    txt = (ev.get('type', '') + ' ' + json.dumps(ev.get('payload', {}))).lower()
                    s = sum(1 for w in qwords if w in txt)
                    if s > 0:
                        scores[eid] = s
                pairs = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
                out = []
                for eid, sc in pairs:
                    ev = self.ltm.get(eid)
                    if ev:
                        ev_copy = dict(ev)
                        ev_copy['_score'] = float(sc)
                        out.append(ev_copy)
                return out
            except Exception:
                return []

    def link(self, a_id:str, b_id:str, rel:str)->bool:
        if not self._exists(a_id) or not self._exists(b_id):
            return False
        self.graph.setdefault(a_id, []).append((a_id, rel, b_id))
        return True

    def _exists(self, eid:str)->bool:
        return (self.stm.get(eid) is not None) or (eid in self.ltm)

    def _get(self, eid:str)->Event|None:
        return self.stm.get(eid) or self.ltm.get(eid)

    def query(self, *, type:str|None=None, trace_id:str|None=None, text:str|None=None, since:float|None=None, until:float|None=None, scope:str="all", match: str = "or")->list[Event]:
        """Query events from STM/LTM.

        Two matching modes are supported:
          - match='or' (default): historical/legacy behavior where an event is
            returned if it matches the provided `type` OR `trace_id` (or other
            filters).
          - match='and': strict intersection semantics where both `type` AND
            `trace_id` (when provided) must match.

        The function iterates the requested store(s) (STM/LTM) and applies the
        requested filters. Results are sorted by timestamp.
        """
        out: list[Event] = []

        def _iter_store_values(s: str):
            if s == 'stm':
                return list(self.stm.values())
            elif s == 'ltm':
                return list(self.ltm.values())
            else:  # all
                return list(self.stm.values()) + list(self.ltm.values())

        try:
            cand = _iter_store_values(scope if scope in ('stm','ltm') else 'all')
            for ev in cand:
                # basic type/trace matches
                t_ok = (type is None) or (ev.get('type') == type)
                tr_ok = (trace_id is None) or (ev.get('trace_id') == trace_id)

                accept = False
                if match == 'and':
                    if t_ok and tr_ok:
                        accept = True
                else:  # default OR to preserve legacy semantics
                    if (type is not None and t_ok) or (trace_id is not None and tr_ok) or (type is None and trace_id is None):
                        accept = True

                if not accept:
                    continue

                # time window filtering
                if since and ev.get('ts', 0) < since:
                    continue
                if until and ev.get('ts', 0) > until:
                    continue

                # text search
                if text:
                    blob = (ev.get('type', '') + ' ' + str(ev.get('payload', {})))
                    if text not in blob:
                        continue

                out.append(ev)

        except Exception:
            # best-effort: return empty list on unexpected errors
            return []

        out.sort(key=lambda e: e.get('ts', 0))
        return out

    def query_by_trace_and_type(self, trace_id: str, type_: str, scope: str = "stm") -> list[Event]:
        """Strict intersection query: return events that match both trace_id AND type within scope.

        This preserves the original `query` behavior (which is a union) for
        backwards compatibility while providing callers a clearer, less error-
        prone API when they need the intersection semantics.
        """
        out: list[Event] = []
        store = self.stm if scope == "stm" else self.ltm
        try:
            for ev in store.values():
                if ev.get('trace_id') == trace_id and ev.get('type') == type_:
                    out.append(ev)
            out.sort(key=lambda e: e.get('ts', 0))
        except Exception:
            # best-effort: return empty list on unexpected errors
            return []
        return out

    def latest(self, trace_id: str, type_: str, scope: str = "stm") -> T.Optional[Event]:
        """Return the latest event matching trace_id AND type within scope, or None."""
        xs = self.query(type=type_, trace_id=trace_id, scope=scope, match='and')
        return xs[-1] if xs else None

    def evict(self, policy:str="ttl_or_lru")->int:
        """يفرّغ من STM حسب TTL أو LRU مع احترام pinned."""
        removed = 0
        now = time.time()
        # TTL أولًا
        for ev in list(self.stm.values()):
            if ev["pinned"]: continue
            if ev["ttl_s"] is not None and (now - ev["ts"]) > ev["ttl_s"]:
                self.stm.delete(ev["id"]); removed += 1
        # إن تجاوز السعة تُترك LRU (يتم تلقائيًا داخل LRUCache عند set)
        return removed

    # مساعدين اختيارية
    def pin(self, eid:str, pinned:bool=True)->bool:
        ev = self._get(eid); 
        if not ev: return False
        ev["pinned"] = pinned; return True

    def move_to_ltm(self, eid:str)->bool:
        ev = self._get(eid); 
        if not ev: return False
        self.ltm[eid] = ev
        self.stm.delete(eid)
        return True

    # ---------------------------- Persistence & Indexing --------------------
    def _default_db_path(self) -> str:
        """Return a sensible default sqlite path inside the repo data folder.

        The path will be: <repo-root>/data/memory.sqlite where repo-root is
        two levels above this file (repo-copy/Core_Memory -> repo-copy).
        """
        try:
            this = Path(__file__).resolve()
            repo_root = this.parents[1]
            data_dir = repo_root / 'data'
            data_dir.mkdir(parents=True, exist_ok=True)
            return str((data_dir / 'memory.sqlite').resolve())
        except Exception:
            return os.path.abspath('memory.sqlite')

    def export_ltm_to_db(self, db_path: str | None = None) -> int:
        """Persist current LTM events to sqlite. Returns number of rows written.

        If db_path is None, uses a default under repo data/ directory.
        Existing rows are REPLACEd by id.
        """
        db = db_path or self._default_db_path()
        try:
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    ts REAL,
                    type TEXT,
                    payload TEXT,
                    emotion TEXT,
                    trace_id TEXT,
                    ttl_s REAL,
                    pinned INTEGER
                )
                """
            )
            written = 0
            for eid, ev in list(self.ltm.items()):
                payload = json.dumps(ev.get('payload', {}), ensure_ascii=False)
                cur.execute(
                    "REPLACE INTO events (id, ts, type, payload, emotion, trace_id, ttl_s, pinned) VALUES (?,?,?,?,?,?,?,?)",
                    (ev.get('id'), float(ev.get('ts', 0)), ev.get('type'), payload, ev.get('emotion'), ev.get('trace_id'), ev.get('ttl_s') or None, 1 if ev.get('pinned') else 0),
                )
                written += 1
            conn.commit()
            conn.close()
            return written
        except Exception:
            return 0

    def import_ltm_from_db(self, db_path: str | None = None) -> int:
        """Load rows from sqlite into in-memory LTM. Returns number of rows loaded."""
        db = db_path or self._default_db_path()
        try:
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            cur.execute("SELECT id, ts, type, payload, emotion, trace_id, ttl_s, pinned FROM events")
            rows = cur.fetchall()
            for r in rows:
                eid, ts, type_, payload_text, emotion, trace_id, ttl_s, pinned = r
                try:
                    payload = json.loads(payload_text or "{}")
                except Exception:
                    payload = {"raw": payload_text}
                ev = {"id": eid, "ts": ts, "type": type_, "payload": payload, "trace_id": trace_id, "ttl_s": ttl_s, "pinned": bool(pinned), "emotion": emotion}
                self.ltm[eid] = ev
            conn.close()
            return len(rows)
        except Exception:
            return 0

    def build_semantic_index(self) -> int:
        """Build a TF-IDF semantic index over LTM documents.

        Returns number of indexed documents. If sklearn is not available,
        falls back to a simple keyword index (stored in self._kw_index).
        """
        # collect documents (type + payload text) with preprocessing
        docs = []
        ids = []
        for ev in self.ltm.values():
            # create a textual representation
            txt = ev.get('type', '') + ' ' + json.dumps(ev.get('payload', {}), ensure_ascii=False)
            processed = self._enhanced_text_preprocessing(txt) if hasattr(self, '_enhanced_text_preprocessing') else txt
            if processed is None:
                continue
            docs.append(processed)
            ids.append(ev.get('id'))

        # Try embeddings-based pipeline first (sentence-transformers + faiss/sklearn NN fallbacks)
        try:
            from sentence_transformers import SentenceTransformer # type: ignore
            import numpy as _np
            model = SentenceTransformer('all-MiniLM-L6-v2')
            if docs:
                vecs = model.encode(docs, convert_to_numpy=True, show_progress_bar=False)
            else:
                vecs = _np.zeros((0, model.get_sentence_embedding_dimension()))

            # Try FAISS index (fast, in-memory)
            try:
                import faiss # type: ignore
                dim = int(vecs.shape[1]) if vecs.size else 0
                if dim == 0:
                    # nothing to index
                    self._use_embeddings = True
                    self._use_faiss = False
                    self._embeddings = _np.asarray(vecs, dtype='float32')
                    self._embed_model = model
                    self._doc_ids = ids
                    return len(ids)

                vecs32 = _np.asarray(vecs, dtype='float32')
                faiss.normalize_L2(vecs32)
                index = faiss.IndexFlatIP(vecs32.shape[1])
                index.add(vecs32)
                self._faiss_index = index
                self._embeddings = vecs32
                self._embed_model = model
                self._doc_ids = ids
                self._use_embeddings = True
                self._use_faiss = True
                return len(ids)
            except Exception:
                # FAISS not available, try sklearn NearestNeighbors
                try:
                    from sklearn.neighbors import NearestNeighbors # type: ignore
                    vecs32 = _np.asarray(vecs, dtype='float32')
                    nn = NearestNeighbors(metric='cosine', algorithm='brute')
                    if len(vecs32) > 0:
                        nn.fit(vecs32)
                    self._nn_index = nn
                    self._embeddings = vecs32
                    self._embed_model = model
                    self._doc_ids = ids
                    self._use_embeddings = True
                    self._use_faiss = False
                    return len(ids)
                except Exception:
                    # embeddings pipeline failed; fall through to TF-IDF
                    pass
        except Exception:
            # embedding libraries not available; fall back
            pass

        # TF-IDF fallback if embeddings not available
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer # type: ignore
            from sklearn.metrics.pairwise import linear_kernel # type: ignore

            vec = self._optimized_tfidf_settings() or TfidfVectorizer(max_features=16384)
            mat = vec.fit_transform(docs) if (docs and vec is not None) else None
            self._vectorizer = vec
            self._doc_matrix = mat
            self._doc_ids = ids
            self._use_tfidf = True
            self._use_embeddings = False
            return len(ids)
        except Exception:
            # fallback: build keyword inverted index
            kw_index: dict[str, list[str]] = {}
            for doc_id, doc in zip(ids, docs):
                for tok in set(doc.lower().split()):
                    kw_index.setdefault(tok, []).append(doc_id)
            self._kw_index = kw_index
            self._doc_ids = ids
            self._use_tfidf = False
            self._use_embeddings = False
            return len(ids)

    def semantic_search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Return top_k LTM events matching the query, with score.

        Returns a list of event dicts augmented with _score (float).
        """
        out: list[dict[str, Any]] = []
        try:
            # normalize the query using the same preprocessing used for documents
            try:
                proc_query = self._enhanced_text_preprocessing(query) if hasattr(self, '_enhanced_text_preprocessing') else (query or '')
            except Exception:
                proc_query = query or ''

            if not proc_query:
                return []
            # 1) Embeddings-based path (if available)
            if getattr(self, '_use_embeddings', False) and getattr(self, '_embed_model', None) is not None:
                try:
                    import numpy as _np

                    qv = self._embed_model.encode([proc_query], convert_to_numpy=True, show_progress_bar=False)
                    qv32 = _np.asarray(qv, dtype='float32')

                    # FAISS search
                    if getattr(self, '_use_faiss', False) and getattr(self, '_faiss_index', None) is not None:
                        try:
                            import faiss # type: ignore
                            qn = qv32.copy()
                            faiss.normalize_L2(qn)
                            D, I = self._faiss_index.search(qn, top_k)
                            for idx, score in zip(I[0], D[0]):
                                if idx < 0:
                                    continue
                                doc_id = self._doc_ids[idx]
                                ev = self.ltm.get(doc_id) or self.stm.get(doc_id)
                                if ev:
                                    ev_copy = dict(ev)
                                    ev_copy['_score'] = float(score)
                                    out.append(ev_copy)
                            return out
                        except Exception:
                            # FAISS present but failed for some reason
                            pass

                    # sklearn NearestNeighbors fallback
                    if getattr(self, '_nn_index', None) is not None and getattr(self, '_embeddings', None) is not None:
                        dists, idxs = self._nn_index.kneighbors(
                            qv32, n_neighbors=min(top_k, max(1, len(self._embeddings)))
                        )
                        for dist_row, idx_row in zip(dists, idxs):
                            for dist, idx in zip(dist_row, idx_row):
                                doc_id = self._doc_ids[idx]
                                ev = self.ltm.get(doc_id) or self.stm.get(doc_id)
                                if ev:
                                    ev_copy = dict(ev)
                                    ev_copy['_score'] = float(1.0 - dist)
                                    out.append(ev_copy)
                        return out
                except Exception:
                    # embedding pipeline failed; continue to other methods
                    pass

            # 2) TF-IDF path
            if getattr(self, '_use_tfidf', False) and getattr(self, '_vectorizer', None) is not None:
                qv = self._vectorizer.transform([proc_query])
                from sklearn.metrics.pairwise import linear_kernel # type: ignore

                sims = linear_kernel(qv, self._doc_matrix).flatten() if self._doc_matrix is not None else []
                pairs = sorted(enumerate(sims), key=lambda x: x[1], reverse=True)[:top_k]
                for idx, score in pairs:
                    doc_id = self._doc_ids[idx]
                    ev = self.ltm.get(doc_id) or self.stm.get(doc_id)
                    if ev:
                        ev_copy = dict(ev)
                        ev_copy['_score'] = float(score)
                        out.append(ev_copy)
                return out

            # 3) Keyword fallback scoring
            qwords = set((proc_query or '').lower().split())
            scores: dict[str, int] = {}
            for eid, ev in self.ltm.items():
                # use ensure_ascii=False so non-ASCII (Arabic) text remains readable for substring checks
                txt = (ev.get('type', '') + ' ' + json.dumps(ev.get('payload', {}), ensure_ascii=False)).lower()
                s = sum(1 for w in qwords if w in txt)
                if s > 0:
                    scores[eid] = s
            sorted_ids = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
            for eid, score in sorted_ids:
                ev = self.ltm.get(eid)
                ev_copy = dict(ev)
                ev_copy['_score'] = float(score)
                out.append(ev_copy)
            return out
        except Exception:
            return []

    # ---------------------- Contextual / Emotion helpers -------------------
    def tag_emotion(self, eid: str, emotion: str) -> bool:
        """Attach or update an emotion tag to an event (STM or LTM).

        Best-effort: updates indexes and persists if event is in LTM.
        """
        ev = self._get(eid)
        if not ev:
            return False
        old = ev.get('emotion')
        ev['emotion'] = emotion
        # update indexes
        if old and eid in self.index_by_emotion.get(old, set()):
            self.index_by_emotion.get(old, set()).discard(eid)
        self.index_by_emotion.setdefault(emotion, set()).add(eid)
        # persist if LTM
        if eid in self.ltm and self._conn:
            try:
                cur = self._conn.cursor()
                cur.execute("UPDATE events SET emotion = ? WHERE id = ?", (emotion, eid))
                self._conn.commit()
            except Exception:
                pass
        return True

    def semantic_search_by_context(self, query: str | None = None, *, emotions: list[str] | None = None, smell: str | None = None, expand_links_depth: int = 1, top_k: int = 5) -> list[Event]:
        """Context-aware semantic search.

        - query: textual query (can be None to search by smell/emotion only)
        - emotions: list of emotion strings to prefer/match
        - smell: a textual cue (e.g., 'rose', 'sea', 'cinnamon') to seed retrieval
        - expand_links_depth: how far to walk outgoing links from seed docs
        Returns up to top_k events ordered by heuristic score (semantic + emotion + proximity).
        """
        seeds: dict[str, float] = {}

        # 1) base semantic candidates
        if query:
            sem = self.semantic_search(query, top_k=top_k * 3)
            for i, ev in enumerate(sem):
                seeds[ev['id']] = max(seeds.get(ev['id'], 0.0), ev.get('_score', 0.0))

        # 2) smell-based seeding (substring match in type/payload)
        if smell:
            s = smell.lower()
            for eid, ev in self.ltm.items():
                # use ensure_ascii=False so non-ASCII (Arabic) text remains readable for substring checks
                txt = (ev.get('type', '') + ' ' + json.dumps(ev.get('payload', {}), ensure_ascii=False)).lower()
                if s in txt:
                    seeds[eid] = max(seeds.get(eid, 0.0), 0.5)

        # 3) emotion boost / direct matches
        if emotions:
            for emo in emotions:
                for eid in self.index_by_emotion.get(emo, set()):
                    seeds[eid] = max(seeds.get(eid, 0.0), seeds.get(eid, 0.0) + 0.25)

        # 4) expand via graph links (breadth-first)
        def expand_from(eids: list[str], depth: int):
            seen = set()
            frontier = list(eids)
            for d in range(depth):
                next_frontier: list[str] = []
                for src in frontier:
                    if src in seen: continue
                    seen.add(src)
                    for link in self.graph.get(src, []):
                        _, _, dst = link
                        if dst not in seeds:
                            # proximity score decays with depth
                            seeds[dst] = max(seeds.get(dst, 0.0), 0.4 / (d+1))
                        next_frontier.append(dst)
                frontier = next_frontier

        if seeds:
            expand_from(list(seeds.keys()), expand_links_depth)

        # 5) rank by combined heuristic: base seed score + recency bonus + emotion bonus
        scored: list[tuple[str, float]] = []
        now = time.time()
        for eid, base in seeds.items():
            ev = self.ltm.get(eid) or self.stm.get(eid)
            if not ev:
                continue
            age_hours = max(0.0, (now - ev.get('ts', now)) / 3600.0)
            recency_bonus = max(0.0, 1.0 - min(1.0, age_hours / 24.0))
            emo = ev.get('emotion')
            emo_bonus = 0.0
            if emotions and emo in emotions:
                emo_bonus = 0.35
            score = base * 0.6 + recency_bonus * 0.3 + emo_bonus * 0.1
            scored.append((eid, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        out: list[Event] = []
        seen_ids = set()
        for eid, _s in scored[:top_k]:
            ev = self.ltm.get(eid) or self.stm.get(eid)
            if ev and eid not in seen_ids:
                out.append(ev)
                seen_ids.add(eid)
        return out

    def selective_forget(self, *, age_days_threshold: float = 90.0, emotion_keep: list[str] | None = None, max_removals: int | None = None) -> list[str]:
        """Selectively remove old/low-value LTM events.

        - age_days_threshold: base age in days beyond which items are eligible
        - emotion_keep: list of emotions to protect from forgetting (e.g., ['positive','nostalgic'])
        - max_removals: cap number of deletions this run (None = unlimited)
        Returns list of removed event ids.
        """
        emotion_keep = emotion_keep or ['positive', 'nostalgic', 'important']
        now = time.time()
        removed: list[str] = []
        candidates = list(self.ltm.items())
        # Sort by age (oldest first) to apply threshold deterministically
        candidates.sort(key=lambda kv: kv[1].get('ts', 0))
        for eid, ev in candidates:
            if max_removals is not None and len(removed) >= max_removals:
                break
            if ev.get('pinned'):
                continue
            emo = ev.get('emotion')
            age_days = (now - ev.get('ts', now)) / 86400.0
            # Protected by emotion
            if emo and emo in emotion_keep:
                continue
            # skip relatively recent
            if age_days < age_days_threshold:
                continue
            # Best-effort: delete from in-memory and DB
            try:
                self.ltm.pop(eid, None)
                # clean indexes
                self.index_by_type.get(ev.get('type'), set()).discard(eid)
                self.index_by_trace.get(ev.get('trace_id') or eid, set()).discard(eid)
                if emo:
                    self.index_by_emotion.get(emo, set()).discard(eid)
                # remove graph edges referencing eid
                self.graph.pop(eid, None)
                for src, links in list(self.graph.items()):
                    self.graph[src] = [l for l in links if l[2] != eid]
                # remove from sqlite if present
                if self._conn:
                    try:
                        cur = self._conn.cursor()
                        cur.execute("DELETE FROM events WHERE id = ?", (eid,))
                        self._conn.commit()
                    except Exception:
                        pass
                removed.append(eid)
            except Exception:
                continue
        return removed
