# Very small RAG wrapper that uses a retriever and the ExternalInfoProvider to compose hints
from typing import Any, Dict, List
from .retriever import SimpleFactsRetriever
from Core_Engines.External_InfoProvider import ExternalInfoProvider


def answer_with_rag(question: str, retriever: SimpleFactsRetriever | None = None, provider: ExternalInfoProvider | None = None, k: int = 5) -> Dict[str, Any]:
    retriever = retriever or SimpleFactsRetriever()
    provider = provider or ExternalInfoProvider()
    # Step 1: retrieve candidate facts
    ctx_facts = retriever.retrieve(question, k=k)
    hints = [f"{f['text']} (source: {f['source']}, conf: {f['confidence']})" for f in ctx_facts]
    # Step 2: call provider with hints
    prov = provider.fetch_facts(question, hints=hints)
    out = {'provider': prov, 'retrieved': ctx_facts}
    # If provider returned answer, attach cited sources from retrieved list that match
    if prov.get('ok'):
        out['answer'] = prov.get('answer')
        out['facts'] = prov.get('facts', [])
    return out
