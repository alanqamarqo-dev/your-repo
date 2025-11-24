# === AGL auto-injected knobs (idempotent) ===
try:
    import os
    def _to_int(name, default):
        try:
            return int(os.environ.get(name, str(default)))
        except Exception:
            return default
except Exception:
    def _to_int(name, default): return default
_AGL_TOP_K = _to_int('AGL_TOP_K', 5)

try:
    import os
    def _to_int(name, default):
        try:
            return int(os.environ.get(name, str(default)))
        except Exception:
            return default
except Exception:
    def _to_int(name, default): return default
import os
import sqlite3
import json
import pytest
def test_export_import_roundtrip(tmp_path):
    from Core_Memory.Conscious_Bridge import ConsciousBridge
    br = ConsciousBridge()
    ids = []
    for i in range(5):
        ids.append(br.put('sample_event', {'i': i}, to='ltm'))
    db_path = str(tmp_path / 'memory.sqlite')
    written = br.export_ltm_to_db(db_path)
    assert written >= 5
    br.ltm.clear()
    assert len(br.ltm) == 0
    loaded = br.import_ltm_from_db(db_path)
    assert loaded >= 5
    for eid in ids:
        assert eid in br.ltm
def test_semantic_index_and_search_if_available():
    import importlib
    st_spec = importlib.util.find_spec('sentence_transformers')
    faiss_spec = importlib.util.find_spec('faiss')
    if not st_spec or not faiss_spec:
        pytest.skip('sentence-transformers/faiss not available in environment')
    from Core_Memory.Conscious_Bridge import ConsciousBridge
    br = ConsciousBridge()
    br.ltm.clear()
    br.put('doc', {'text': 'apple fruit red'}, to='ltm')
    br.put('doc', {'text': 'banana fruit yellow'}, to='ltm')
    br.put('doc', {'text': 'carrot vegetable orange'}, to='ltm')
    n = br.build_semantic_index()
    assert n >= 3
    res = br.semantic_search('fruit', top_k=_AGL_TOP_K)
    assert isinstance(res, list)
    assert len(res) >= 1
