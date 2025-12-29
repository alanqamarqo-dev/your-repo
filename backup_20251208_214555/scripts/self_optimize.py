#!/usr/bin/env python
"""CLI for running self-optimization and producing HTML/JSON reports."""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import argparse
from Learning_System.Self_Optimizer import run_self_optimization

try:
    from Self_Improvement.safety_log import log_safety_event # type: ignore
except Exception:
    def log_safety_event(source, level, message, extra=None):
        return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="artifacts/models")
    ap.add_argument("--kb", default="Knowledge_Base/Learned_Patterns.json")
    ap.add_argument("--fusion", default="config/fusion_weights.json")
    ap.add_argument("--out", default="reports/self_optimization")
    ap.add_argument("--approve", action="store_true", help="تطبيق التغييرات المقترحة فعليًا")
    args = ap.parse_args()
    rep = run_self_optimization(out_dir=args.out, models_root=args.models, kb_path=args.kb, fusion_cfg=args.fusion)
    print("Self-Optimization complete")
    print("KB version:", rep.get("kb_version"))
    print("Patterns:", rep.get("kb_count"))
    print("Weights:", rep.get("fusion_weights"))
    # human approval gate: by default it's a dry-run, only apply if --approve provided
    if not args.approve:
        print("لن يتم تطبيق أي تغيير لأن --approve لم يُستخدم.")
        try:
            log_safety_event("run_self_optimization", "info", "dry-run awaiting human approval", {"summary": rep.get("summary")})
        except Exception:
            pass
        return 0

    # if approval provided, perform apply step (implementation-specific)
    print("تطبيق التغييرات بعد الموافقة...")
    try:
        log_safety_event("run_self_optimization", "info", "applied changes with approval", {"summary": rep.get("summary")})
    except Exception:
        pass
    return 0
if __name__ == "__main__":
    main()
