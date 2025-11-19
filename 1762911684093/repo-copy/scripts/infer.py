import argparse, json, sys, os
import importlib.util
ie_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Learning_System", "Inference_Engine.py"))
spec = importlib.util.spec_from_file_location("inference_engine_mod", ie_path)
if spec and spec.loader:
    inference_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(inference_mod)  # type: ignore
    InferenceEngine = inference_mod.InferenceEngine
else:
    raise ImportError(f"cannot load Inference_Engine from {ie_path}")

def main():
    ap = argparse.ArgumentParser("AGL Inference CLI")
    ap.add_argument("--base", required=True, help="مثل: ohm, hooke, rc_step, poly2, power")
    ap.add_argument("--x", nargs="+", required=True, help="قيمة أو قيم x (مثلا I أو t أو x)")
    ap.add_argument("--kb", default="Knowledge_Base/Learned_Patterns.json")
    args = ap.parse_args()

    xs = [float(v) for v in args.x]
    x = xs[0] if len(xs) == 1 else xs

    eng = InferenceEngine(args.kb)
    out = eng.predict(args.base, x)
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    sys.exit(main())
