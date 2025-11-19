"""Load fetched NASA pages and ask the OpenAIKnowledgeEngine to summarize them with sources.

This script expects artifacts/nasa_artemis_pages.json to exist (created by fetch_nasa_artemis.py).
It will read pages, build a short context list, and call Core_Engines.OpenAI_KnowledgeEngine.ask(..., context=...)
to generate a summary that cites sources.
"""
import os
import json
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Core_Engines.OpenAI_KnowledgeEngine import OpenAIKnowledgeEngine


def load_pages(path='artifacts/nasa_artemis_pages.json'):
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    with open(path, 'r', encoding='utf-8') as fh:
        return json.load(fh)


def build_context(pages):
    ctx = []
    for p in pages:
        if p.get('error'):
            continue
        text = p.get('text') or ''
        if not text:
            continue
        # limit each page to ~2000 chars to keep prompt size reasonable
        excerpt = text.strip()[:2000]
        src = p.get('url')
        ctx.append(f"SOURCE: {src}\n{excerpt}")
    return ctx


def main():
    pages = load_pages()
    if not pages:
        print('No pages found to summarize')
        return
    context = build_context(pages)
    print(f'Prepared context from {len(context)} pages (sending to model)')

    # create engine (will use OPENAI_API_KEY from environment)
    eng = OpenAIKnowledgeEngine()

    question = 'اكتب ملخصًا مختصرًا (عربي) لأحدث تطورات مهمة ناسا Artemis في أكتوبر 2025 واذكر المصادر كرابط لكل نقطة.'
    res = eng.ask(question, context=context)
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
