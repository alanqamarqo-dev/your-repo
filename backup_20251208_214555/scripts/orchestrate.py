import argparse, json, sys, os
import importlib.util
ie_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Integration_Layer", "Task_Orchestrator.py"))
spec = importlib.util.spec_from_file_location("taskorch_mod", ie_path)
if spec and spec.loader:
    task_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(task_mod)  # type: ignore
    TaskOrchestrator = task_mod.TaskOrchestrator
else:
    raise ImportError(f"cannot load Task_Orchestrator from {ie_path}")

def main():
    ap = argparse.ArgumentParser("AGL Orchestrate CLI")
    ap.add_argument("--task", required=True, choices=["predict","derive"])
    ap.add_argument("--base", required=True)
    ap.add_argument("--x", nargs="*", help="قيمة/قيم x (اختياري لـ derive)")
    ap.add_argument("--run-engines", action="store_true", help="Run the engines compiler aggregator before routing")
    ap.add_argument("--engines-live", action="store_true", help="When running engines, enable live ExternalInfoProvider (requires OPENAI_API_KEY in session)")
    args = ap.parse_args()

    orch = TaskOrchestrator()

    # Optionally run the engines compiler aggregator before performing the orchestrator task
    engines_report = None
    if args.run_engines:
        try:
            import subprocess
            # Try to use the resource guard when available to protect long-running engine runs
            try:
                from tools.resource_guard import ResourceGuard
            except Exception:
                ResourceGuard = None

            eng_script = os.path.join(os.path.dirname(__file__), 'engines_compiler.py')
            cmd = [sys.executable, eng_script, '--out', os.path.join('artifacts', 'engines_compiler_from_orch_report.json')]
            if args.engines_live:
                cmd.append('--live')

            if ResourceGuard:
                with ResourceGuard():
                    subprocess.run(cmd, check=True)
            else:
                subprocess.run(cmd, check=True)
            # read report if present
            rep_path = os.path.join('artifacts', 'engines_compiler_from_orch_report.json')
            if os.path.exists(rep_path):
                try:
                    with open(rep_path, 'r', encoding='utf-8') as fh:
                        engines_report = json.load(fh)
                except Exception:
                    engines_report = {"error": "failed_to_read_report"}
        except Exception as e:
            engines_report = {"error": str(e)}

    if args.task == "predict":
        if not args.x:
            print("ERROR: provide --x for predict", file=sys.stderr)
            sys.exit(2)
        xs = [float(v) for v in args.x]
        x = xs[0] if len(xs) == 1 else xs
        out = orch.route("predict", {"base": args.base, "x": x})
    else:
        out = orch.route("derive", {"base": args.base})

    result = {"orchestrator": out}
    if engines_report is not None:
        result["engines_report"] = engines_report

    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    sys.exit(main())
