"""Simple integration test for the KnowledgeOrchestrator.

This script enables the orchestrator, configures the external provider to use the
OpenAI adapter (or mock if AGL_OPENAI_KB_MOCK=1) and runs a sample question.
"""
import os
import json
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Core_Engines.KnowledgeOrchestrator import KnowledgeOrchestrator


def main():
    # env toggles: prefer ollama adapter for local testing and disable cache for fresh results
    os.environ['AGL_EXTERNAL_INFO_IMPL'] = os.environ.get('AGL_EXTERNAL_INFO_IMPL','ollama_engine')
    # prefer disabling cache in test runs unless explicitly enabled
    os.environ['AGL_OLLAMA_KB_CACHE_ENABLE'] = os.environ.get('AGL_OLLAMA_KB_CACHE_ENABLE','0')
    # default to the local pulled model if not provided
    if not os.environ.get('AGL_EXTERNAL_INFO_MODEL'):
        os.environ['AGL_EXTERNAL_INFO_MODEL'] = 'qwen2.5:7b-instruct'

    # instantiate orchestrator (it will auto-detect retriever/external provider)
    orch = KnowledgeOrchestrator()

    q = 'أعطني ملخصًا مختصرًا لأحدث تطورات مهمة ناسا Artemis في أكتوبر 2025 مع مصادر رسمية'
    res = orch.orchestrate(q)
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
