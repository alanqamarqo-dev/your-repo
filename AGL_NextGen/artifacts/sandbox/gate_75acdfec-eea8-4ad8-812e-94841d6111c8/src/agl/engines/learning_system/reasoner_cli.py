# CLI thin wrapper for the Reasoner
from __future__ import annotations
import argparse
import json
from pathlib import Path
from agl.engines.learning_system.Reasoner import Reasoner

def main():
    p = argparse.ArgumentParser(prog="reasoner_cli", description="Query the learned knowledge base (Reasoner)")
    p.add_argument("question", nargs="+", help="The question to ask (wrap in quotes)")
    p.add_argument("--kb", default="Knowledge_Base/Learned_Patterns.json", help="Path to KB JSON")
    args = p.parse_args()

    q = " ".join(args.question)
    r = Reasoner(kb_path=Path(args.kb))
    ans = r.query(q)
    print(json.dumps({
        "ok": ans.ok,
        "question": ans.question,
        "result": ans.result,
        "reasoning": ans.reasoning,
        "ts": ans.ts_iso
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()

