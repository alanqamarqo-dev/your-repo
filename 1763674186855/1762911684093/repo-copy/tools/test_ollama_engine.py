"""Small test runner for the OllamaAdapter / OllamaKnowledgeEngine.

Usage examples:
  py -3 tools/test_ollama_engine.py "ما هو قانون الحفظ للطاقة؟"
  py -3 tools/test_ollama_engine.py --mock "ما هي سرعة الضوء؟"

Before running in real mode ensure either:
 - `ollama` CLI is installed and on PATH, or
 - OLLAMA_API_URL is set to a compatible HTTP endpoint.
"""
import os
import argparse
import json

from Core_Engines.Ollama_Adapter import OllamaAdapter


def main():
    p = argparse.ArgumentParser()
    p.add_argument('question', nargs='?', default=None)
    p.add_argument('--mock', action='store_true')
    args = p.parse_args()
    if args.mock:
        os.environ['AGL_OLLAMA_KB_MOCK'] = '1'

    adapter = OllamaAdapter()
    q = args.question or 'ما هو الذكاء الاصطناعي؟'
    out = adapter.fetch_facts(q, hints=['اختبار'])
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
