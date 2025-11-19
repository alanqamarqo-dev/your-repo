#!/usr/bin/env python3
# Run RAG evaluation over the queries in tools/rag_queries.txt
import json
import os
import sys
# ensure project root is importable
sys.path.append(os.getcwd())
from Integration_Layer.retriever import SimpleFactsRetriever
from Integration_Layer.rag import answer_with_rag

# env-driven evidence limit for reporting/hydration (keep default behavior)
_AGL_EVIDENCE_LIMIT = int(os.environ.get('AGL_EVIDENCE_LIMIT', '3'))

QUERIES_FILE = os.path.join('tools', 'rag_queries.txt')
OUT_PATH = os.path.join('artifacts', 'rag_eval.jsonl')

def load_queries():
    if not os.path.exists(QUERIES_FILE):
        return []
    with open(QUERIES_FILE, 'r', encoding='utf-8') as f:
        return [l.strip() for l in f.readlines() if l.strip()]

def run_all():
    queries = load_queries()
    retriever = SimpleFactsRetriever()
    # provider will be created inside answer_with_rag (uses ExternalInfoProvider)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    stats = {'total': 0, 'answered_local': 0, 'has_sources': 0}
    with open(OUT_PATH, 'w', encoding='utf-8') as out:
        for q in queries:
            res = answer_with_rag(q, retriever=retriever)
            # Ensure top-level result includes provider facts for stats/UI
            provider_out = res.get('provider') or {}
            retrieved = res.get('retrieved') or []
            # If retrieved is empty but provider supplied facts (common in MOCK), hydrate retrieved for reporting
            if not retrieved and provider_out.get('facts'):
                retrieved = [
                    {
                        'text': f.get('text',''),
                        'source': f.get('source','mock-provider'),
                        'confidence': f.get('confidence', 0.5)
                    } for f in provider_out.get('facts', [])[:_AGL_EVIDENCE_LIMIT]
                ]

            row = {
                'query': q,
                'result': {
                    'provider': provider_out,
                    'retrieved': retrieved,
                    'answer': provider_out.get('answer'),
                    'facts': provider_out.get('facts', [])
                }
            }
            out.write(json.dumps(row, ensure_ascii=False) + '\n')
            stats['total'] += 1
            if row['result'].get('answer'):
                stats['answered_local'] += 1
            # has_sources now considers either retrieved or facts
            has_sources = False
            if row['result'].get('retrieved'):
                has_sources = True
            elif row['result'].get('facts'):
                has_sources = True
            if has_sources:
                stats['has_sources'] += 1
    print('WROTE', OUT_PATH)
    print('STATS:', stats)

if __name__ == '__main__':
    run_all()
