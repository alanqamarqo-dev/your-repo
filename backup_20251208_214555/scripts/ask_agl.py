# -*- coding: utf-8 -*-
"""
Simple interactive script to ask a single question to the AGL unified interface.

Usage (PowerShell):
  $env:PYTHONPATH = (Resolve-Path .).Path
  py -3 scripts/ask_agl.py

This will prompt for a question and print the formatted final answer.
"""
import os
import sys
import argparse
from Self_Improvement.Knowledge_Graph import CognitiveIntegrationEngine, agl_pipeline


def _get_question_from_sources(cli_q: str | None) -> str:
    # 1) CLI --question has highest priority
    if cli_q:
        return cli_q.strip()
    # 2) env var QUESTION
    env_q = os.getenv("QUESTION", "").strip()
    if env_q:
        return env_q
    # 3) stdin (pipe)
    try:
        if not sys.stdin.isatty():
            data = sys.stdin.read()
            if data and data.strip():
                return data.strip()
    except Exception:
        pass
    # 4) interactive prompt
    try:
        return input("🧠 اكتب سؤالك: ").strip()
    except Exception:
        return ""


def main(argv=None):
    p = argparse.ArgumentParser(description="Ask a single question to AGL (CognitiveIntegrationEngine)")
    p.add_argument("--question", "-q", help="Question string (also read from env QUESTION or stdin pipe)")
    p.add_argument("--lang", "-l", default=os.getenv("QUESTION_LANG", "ar"), help="Language code (default from QUESTION_LANG or 'ar')")
    args = p.parse_args(argv)

    q = _get_question_from_sources(args.question)
    if not q:
        print("No question provided. Exiting.")
        return 1

    # Use central agl_pipeline wrapper
    try:
        out = agl_pipeline(q, mode="default", language=args.lang)
    except Exception:
        # fallback to older API
        cie = CognitiveIntegrationEngine()
        try:
            cie.connect_engines()
        except Exception:
            pass
        out = cie.answer_question(q, context="", language=args.lang)

    print("\n=== الجواب المنسق ===\n")
    # support both legacy shape (formatted_answer) and new agl_pipeline (answer)
    fa = out.get('answer') if out.get('answer') is not None else out.get('formatted_answer')
    # make sure printed output is a readable string
    try:
        if isinstance(fa, dict):
            import json
            print(json.dumps(fa, ensure_ascii=False, indent=2))
        else:
            print(str(fa))
    except Exception:
        print(repr(fa))

    print("\n=== provenance (winner + top) ===\n")
    prov = out.get('provenance') if out.get('provenance') is not None else out.get('cie_result')
    try:
        import json
        print(json.dumps(prov, ensure_ascii=False, indent=2))
    except Exception:
        print(repr(prov))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
