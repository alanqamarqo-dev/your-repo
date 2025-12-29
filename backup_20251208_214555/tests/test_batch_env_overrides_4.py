import os, sys, importlib, types
sys.path.insert(0, r'D:\AGL\repo-copy')

def _reload(mod, env):
    for k,v in env.items():
        if v is None: os.environ.pop(k, None)
        else: os.environ[k] = str(v)
    if mod in sys.modules: del sys.modules[mod]
    return importlib.import_module(mod)


def test_hosted_llm_defaults_and_override():
    m = _reload('Core_Engines.Hosted_LLM', {'AGL_HOSTED_LLM_TOP_K': None, 'AGL_HOSTED_LLM_MAX_TOKENS': None})
    assert getattr(m,'_AGL_HOSTED_LLM_TOP_K', None) == 3
    assert getattr(m,'_AGL_HOSTED_LLM_MAX_TOKENS', None) == 512
    m = _reload('Core_Engines.Hosted_LLM', {'AGL_HOSTED_LLM_TOP_K': 7, 'AGL_HOSTED_LLM_MAX_TOKENS': 256})
    assert m._AGL_HOSTED_LLM_TOP_K == 7
    assert m._AGL_HOSTED_LLM_MAX_TOKENS == 256


def test_openai_knobs():
    m = _reload('Core_Engines.OpenAI_KnowledgeEngine', {'AGL_OPENAI_TOP_K': None, 'AGL_OPENAI_MAX_TOKENS': None})
    assert m._AGL_OPENAI_TOP_K == 3 and m._AGL_OPENAI_MAX_TOKENS == 512
    m = _reload('Core_Engines.OpenAI_KnowledgeEngine', {'AGL_OPENAI_TOP_K': 9, 'AGL_OPENAI_MAX_TOKENS': 128})
    assert m._AGL_OPENAI_TOP_K == 9 and m._AGL_OPENAI_MAX_TOKENS == 128


def test_ollama_topk():
    m = _reload('Core_Engines.Ollama_KnowledgeEngine', {'AGL_OLLAMA_TOP_K': None})
    assert m._AGL_OLLAMA_TOP_K == 3
    m = _reload('Core_Engines.Ollama_KnowledgeEngine', {'AGL_OLLAMA_TOP_K': 6})
    assert m._AGL_OLLAMA_TOP_K == 6


def test_gk_graph_caps():
    m = _reload('Core_Engines.GK_graph', {'AGL_GK_GRAPH_MAX_NODES': None, 'AGL_GK_GRAPH_MAX_EDGES': None})
    assert m._AGL_GK_GRAPH_MAX_NODES == 500 and m._AGL_GK_GRAPH_MAX_EDGES == 2000
    m = _reload('Core_Engines.GK_graph', {'AGL_GK_GRAPH_MAX_NODES': 50, 'AGL_GK_GRAPH_MAX_EDGES': 100})
    assert m._AGL_GK_GRAPH_MAX_NODES == 50 and m._AGL_GK_GRAPH_MAX_EDGES == 100
