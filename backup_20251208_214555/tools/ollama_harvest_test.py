"""Run the project's harvester a few times using the OllamaAdapter as the external provider.

This script sets env vars to enable the external provider, points it at the local
`qwen2.5:7b-instruct` model, and invokes `workers/knowledge_harvester.py` main() N times.

Usage:
  py -3 tools\ollama_harvest_test.py --iterations 3

It prints a brief summary of each run to stdout.
"""
import sys
import os
import json
import time
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def run_harvester_once():
    # run the harvester main function in-process for faster feedback
    try:
        from workers import knowledge_harvester as kh
        # ensure env configured for live Ollama adapter
        os.environ['AGL_EXTERNAL_INFO_ENABLED'] = '1'
        os.environ['AGL_EXTERNAL_INFO_IMPL'] = 'ollama_engine'
        os.environ['AGL_EXTERNAL_INFO_MODEL'] = os.environ.get('AGL_EXTERNAL_INFO_MODEL', 'qwen2.5:7b-instruct')
        # disable adapter-level caching for fresh fetches
        os.environ['AGL_OLLAMA_KB_CACHE_ENABLE'] = os.environ.get('AGL_OLLAMA_KB_CACHE_ENABLE', '0')

        # call main() (it prints its own messages); capture exceptions
        kh.main()
        return True, None
    except SystemExit as se:
        # script may call sys.exit; treat non-zero as failure
        return False, f"SystemExit: {se}"
    except Exception as e:
        return False, str(e)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--iterations', type=int, default=2, help='Number of harvester iterations to run')
    args = p.parse_args()

    summary = []
    for i in range(args.iterations):
        print(f"[test] iteration {i+1}/{args.iterations} - invoking harvester...")
        ok, err = run_harvester_once()
        summary.append({'iteration': i+1, 'ok': ok, 'error': err})
        time.sleep(1)

    print('\n[test] summary:')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
