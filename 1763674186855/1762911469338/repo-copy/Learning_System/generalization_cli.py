# -*- coding: utf-8 -*-
"""
CLI لتشغيل مصفوفة التعميم وحفظ النتائج
"""
from __future__ import annotations
import argparse, os, json
from .GeneralizationMatrix import run_generalization

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kb", default="Knowledge_Base/Learned_Patterns.json", help="مسار ملف الأنماط")
    ap.add_argument("--out", default="artifacts/generalization", help="مجلد الإخراج")
    args = ap.parse_args()

    res = run_generalization(args.kb, args.out)
    print(f"wrote {os.path.join(args.out,'generalization_bundle.json')}")
    print(json.dumps({"count": res.get("count",0), "out": args.out}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
