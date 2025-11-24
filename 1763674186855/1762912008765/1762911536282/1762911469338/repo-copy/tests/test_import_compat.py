def test_legacy_import_knowledge_graph():
    import importlib
    importlib.invalidate_caches()
    importlib.import_module("Knowledge_Graph")
