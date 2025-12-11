import os
import shutil
import importlib


def setup_env(tmp_path):
    # Ensure FAST_MODE and artifacts dir are set before importing rag_index
    os.environ['AGL_FAST_MODE'] = '1'
    art = tmp_path / 'artifacts'
    os.environ['AGL_ARTIFACTS_DIR'] = str(art)
    if art.exists():
        shutil.rmtree(art)
    art.mkdir(parents=True, exist_ok=True)
    return art


def test_rag_index_search_and_retrieve(tmp_path):
    art = setup_env(tmp_path)

    # import after env set
    import Self_Improvement.rag_index as rag_index

    # add documents
    rag_index.add_document('d1', 'Bananas are yellow and rich in potassium and fiber.')
    rag_index.add_document('d2', 'Apples contain fiber and vitamin C.')

    res = rag_index.search('which fruits have potassium', k=2)
    texts = '\n'.join(d.get('text', '') for d in res)
    assert 'potassium' in texts.lower() or 'banana' in texts.lower()


def test_agl_pipeline_prefers_rag_for_knowledge(tmp_path):
    art = setup_env(tmp_path)

    # import modules after env configured
    import Self_Improvement.rag_index as rag_index
    import Self_Improvement.rag_adapter as rag_adapter
    import Self_Improvement.hosted_llm_adapter as hosted_mod
    from Self_Improvement.Knowledge_Graph import agl_pipeline
    from Self_Improvement.Knowledge_Graph import CognitiveIntegrationEngine

    # add a high-quality fact that RAG should retrieve
    rag_index.add_document('f_capital', 'The capital of Testland is Testville.')

    # build a CIE with RAG + hosted adapters
    cie = CognitiveIntegrationEngine()
    cie.adapters = [rag_adapter.RAGAdapter(), hosted_mod.HostedLLMAdapter()]
    # prevent CIE default connect_engines from overriding our adapters for the test
    try:
        cie.connect_engines = lambda: None
    except Exception:
        pass

    # run pipeline with explicit CIE
    q = 'What is the capital of Testland?'
    out = agl_pipeline(q, cie=cie)

    # provenance should prefer rag as winner for factual question
    prov = out.get('provenance') or {}
    winner = prov.get('winner') or {}
    assert winner.get('engine') == 'rag' or 'Testville' in (out.get('answer') or ''), f"unexpected winner: {winner}"
