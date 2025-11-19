"""Small example: call the local Ollama model via the OllamaAdapter and print the result.

Usage (PowerShell):
  $env:PYTHONPATH='D:\\AGL'
  $env:AGL_OLLAMA_KB_CACHE_ENABLE='0'    # optional: disable adapter cache for live runs
  $env:AGL_EXTERNAL_INFO_MODEL='qwen2.5:7b-instruct'
  py -3 tools\ollama_example.py "سؤالك هنا"

The script prints a JSON envelope with keys {ok, answer, facts}.
"""
import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Core_Engines.Ollama_Adapter import OllamaAdapter


def main():
    q = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else 'ما هو قانون نيوتن الثاني؟'

    # Ensure defaults for a local test
    os.environ.setdefault('AGL_EXTERNAL_INFO_MODEL', 'qwen2.5:7b-instruct')
    os.environ.setdefault('AGL_OLLAMA_KB_CACHE_ENABLE', '0')

    adapter = OllamaAdapter()
    res = adapter.fetch_facts(q, hints=['example'])
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
