# Learning_System/generalize_cli.py
import argparse, json, os, sys
from .Generalizer import Generalizer

def parse_kv_list(items):
    out = {}
    for it in items or []:
        if "=" not in it: raise ValueError(f"Bad sample '{it}', use key=value")
        k,v = it.split("=",1)
        try:
            out[k] = float(v)
        except:
            out[k] = v
    return out

def main():
    ap = argparse.ArgumentParser(description="AGL Generalizer CLI")
    ap.add_argument("--results", required=True, help="path to results.json")
    ap.add_argument("--relation", default=None, help="force relation name (optional)")
    ap.add_argument("--samples", nargs="*", help="sample values like x=0.2 I=2.0")
    ap.add_argument("--out", default=None, help="output JSON path (optional)")
    args = ap.parse_args()

    g = Generalizer()
    samples = parse_kv_list(args.samples)
    out = g.derive(args.results, relation_hint=args.relation, **samples)

    txt = json.dumps(out, ensure_ascii=False, indent=2)
    if args.out:
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f: f.write(txt)
        print(f"✅ wrote {args.out}")
    else:
        print(txt)

if __name__ == "__main__":
    sys.exit(main())
