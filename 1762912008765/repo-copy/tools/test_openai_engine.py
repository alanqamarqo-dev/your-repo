"""Small test runner for the OpenAIKnowledgeEngine added to Core_Engines.

Run locally:
  # mock run (no external calls)
  python tools/test_openai_engine.py --mock "سجل وقائع عن الثورة الصناعية؟"

  # real run (requires OPENAI_API_KEY in environment)
  python tools/test_openai_engine.py "ما هو قانون الحفظ للطاقة؟"
"""
import os
import argparse
import json

from Core_Engines.OpenAI_KnowledgeEngine import OpenAIKnowledgeEngine


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('question', nargs='?', default='ما هو الذكاء الاصطناعي؟')
    parser.add_argument('--mock', action='store_true', help='Run in mock mode (no external calls)')
    args = parser.parse_args()
    if args.mock:
        os.environ['AGL_OPENAI_KB_MOCK'] = '1'
    eng = OpenAIKnowledgeEngine()
    res = eng.ask(args.question)
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
