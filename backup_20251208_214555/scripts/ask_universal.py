# -*- coding: utf-8 -*-
"""
Simple CLI to ask the universal solver and pass results to the existing RAG formatter.

Usage (PowerShell):
  $env:PYTHONPATH = (Resolve-Path ..).Path
  py -3 scripts/ask_universal.py "سؤالك هنا"

The script loads `solve_universal` from `agl_universal`, builds a problem,
calls the CIE, then uses `rag_answer` as the answer formatter.
"""
import json
import os
import sys
from typing import Any, Dict

try:
    from agl_universal import solve_universal, build_answer_context, DEFAULT_UNIVERSAL_SYSTEM_PROMPT
    from Integration_Layer.rag_wrapper import rag_answer
except Exception:
    # Fallback for direct imports when running from repo root with PYTHONPATH set
    from ..agl_universal import solve_universal, build_answer_context, DEFAULT_UNIVERSAL_SYSTEM_PROMPT  # type: ignore
    from Integration_Layer.rag_wrapper import rag_answer  # type: ignore


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    if not argv:
        print("Usage: py -3 scripts/ask_universal.py \"<question text>\"")
        return 1

    question_text = argv[0]
    story_text = None
    if len(argv) > 1:
        story_text = argv[1]

    problem: Dict[str, Any] = {
        "mode": "qa",
        "language": "ar",
        "question": question_text,
        "context": story_text,
    }

    print("[ask_universal] running solve_universal...")
    bundle = solve_universal(problem, domains_needed=("language", "analysis", "knowledge"), fanout_all=True)

    # Build a context using the same builder (keeps parity with universal pipeline)
    context = build_answer_context(problem=problem, collab_result=bundle.get("cie_result", {}), health_snapshot=bundle.get("health"))

    # Call existing RAG pipeline as the Answer Formatter
    try:
        formatted = rag_answer(question=question_text, context=context, system_prompt=DEFAULT_UNIVERSAL_SYSTEM_PROMPT)
    except TypeError:
        # fallback signatures
        try:
            formatted = rag_answer(question_text, context)
        except Exception as exc:
            formatted = {"_error": "rag_failed", "exc": str(exc)}

    out = {
        "question": question_text,
        "formatted_answer": formatted,
        "bundle": bundle,
        "context": context,
    }

    os.makedirs("artifacts", exist_ok=True)
    out_path = os.path.join("artifacts", "ask_universal_output.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)

    print("[ask_universal] formatted answer:\n")
    print(formatted)
    print(f"[ask_universal] bundle saved to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
