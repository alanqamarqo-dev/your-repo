import csv, json, os, argparse, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Learning_System.ModelZoo import evaluate_candidates

def load_xy(path, xname, yname):
    X, Y = [], []
    with open(path, newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            X.append(float(row[xname]))
            Y.append(float(row[yname]))
    return X, Y

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="CSV path")
    ap.add_argument("--x", required=True, help="x column")
    ap.add_argument("--y", required=True, help="y column")
    ap.add_argument("--candidates", nargs="+", required=True,
                    help="candidate model names, e.g. exp1 'k*x' 'k*x + b' 'a*x**2' poly2")
    ap.add_argument("--out", required=True, help="output folder for results.json")
    args = ap.parse_args()

    X, Y = load_xy(args.data, args.x, args.y)
    results = evaluate_candidates(X, Y, args.candidates)

    os.makedirs(args.out, exist_ok=True)
    out_path = os.path.join(args.out, "results.json")
    payload = {
        "base": os.path.splitext(os.path.basename(args.data))[0],
        "yname": args.y,
        "xname": args.x,
        "results": results
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    # Use ASCII-only output to avoid UnicodeEncodeError on some Windows consoles
    print("wrote {}".format(out_path))

if __name__ == "__main__":
    main()
