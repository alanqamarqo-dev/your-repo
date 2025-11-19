#!/usr/bin/env python3
# Simple evaluation harness for RAG answers
import json
import os
from Integration_Layer.retriever import SimpleFactsRetriever
from Integration_Layer.rag import answer_with_rag

SAMPLE_QUERIES = [
    'ما هو الانصهار النووي؟',
    'ما الفرق بين الذرة والجزيء؟',
    'كيف تعمل خلايا الوقود؟',
    'ما هي أعراض نقص فيتامين د؟',
    'اشرح مبدأ عمل محرك الاحتراق الداخلي.'
]

# controlled by AGL_RETRIEVER_K (default 5)
try:
    _AGL_RETRIEVER_K = int(os.environ.get('AGL_RETRIEVER_K', '5'))
except Exception:
    _AGL_RETRIEVER_K = 5

def run(queries=None, out_path='artifacts/rag_eval.jsonl'):
    queries = queries or SAMPLE_QUERIES
    retriever = SimpleFactsRetriever()
    prov = None
    try:
        # Real provider when OPENAI_API_KEY present, otherwise uses mock if set
        from Core_Engines.External_InfoProvider import ExternalInfoProvider
        prov = ExternalInfoProvider()
    except Exception as e:
        print('Provider init failed, ensure OPENAI_API_KEY or mock mode:', e)
        return
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as out:
        for q in queries:
            # use module-level knob controlled by AGL_RETRIEVER_K
            res = answer_with_rag(q, retriever=retriever, provider=prov, k=_AGL_RETRIEVER_K)
            out.write(json.dumps({'query': q, 'result': res}, ensure_ascii=False) + '\n')
            print('WROTE:', q)

if __name__ == '__main__':
    run()
