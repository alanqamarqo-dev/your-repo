#!/usr/bin/env python
"""CLI for running self-optimization and producing HTML/JSON reports."""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import argparse
from Learning_System.Self_Optimizer import run_self_optimization

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="artifacts/models")
    ap.add_argument("--kb", default="Knowledge_Base/Learned_Patterns.json")
    ap.add_argument("--fusion", default="config/fusion_weights.json")
    ap.add_argument("--out", default="reports/self_optimization")
    args = ap.parse_args()
    rep = run_self_optimization(out_dir=args.out, models_root=args.models, kb_path=args.kb, fusion_cfg=args.fusion)
    print("Self-Optimization complete")
    print("KB version:", rep.get("kb_version"))
    print("Patterns:", rep.get("kb_count"))
    print("Weights:", rep.get("fusion_weights"))

if __name__ == "__main__":
    main()
