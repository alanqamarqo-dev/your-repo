#!/usr/bin/env python3
"""Generate a system report: exercise solvers, run unit tests, and emit JSON summary."""
import json
import os
import sys
import unittest
from datetime import datetime
from pathlib import Path

# ensure repo root is on sys.path so local packages (Solvers, Core_Engines, Integration_Layer) import correctly
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Solvers.QuantumSolver import QuantumSolver
from Solvers.PhysicsSolver import PhysicsSolver
from Solvers.AlgebraSolver import AlgebraSolver
from Solvers.ChemistrySolver import ChemistrySolver


def exercise_solvers():
    solvers = {
        "quantum": QuantumSolver(),
        "physics": PhysicsSolver(),
        "algebra": AlgebraSolver(),
        "chemistry": ChemistrySolver(),
    }

    samples = {
        "quantum": {"goal": "probability", "text": "probability of |1> after U", "given": {"psi": "|ψ>", "U": "U"}},
        "physics": {"goal": "I", "text": "Ohm example", "given": {"V": 12, "R": 4}},
        "algebra": {"goal": "determinant", "text": "matrix det", "given": {}},
        "chemistry": {"goal": "balance", "text": "H2 + O2 -> H2O", "given": {}},
    }

    results = {}
    for name, solver in solvers.items():
        try:
            res = solver.solve(samples[name])
            ok = bool(res.get("ok"))
            results[name] = {"ok": ok, "result": res.get("result"), "raw": res}
        except Exception as e:
            results[name] = {"ok": False, "error": str(e)}
    return results


def run_unittests():
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir="tests")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    out = {
        "testsRun": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(getattr(result, 'skipped', [])),
        "wasSuccessful": result.wasSuccessful(),
    }
    return out


def main():
    report = {"ts": datetime.utcnow().isoformat() + "Z"}
    print("[system_report] Exercising solvers...")
    sol = exercise_solvers()
    report["solvers"] = sol # type: ignore
    total = len(sol)
    ok_count = sum(1 for v in sol.values() if v.get("ok"))
    pct_ok = (ok_count / total) * 100 if total else 0.0
    report["solvers_summary"] = {"total": total, "ok": ok_count, "pct_ok": pct_ok} # type: ignore
    print(f"[system_report] Solvers OK: {ok_count}/{total} ({pct_ok:.1f}%)")

    print("[system_report] Running unit tests (discovery: tests/)...")
    tests = run_unittests()
    report["tests"] = tests # type: ignore
    print(f"[system_report] Tests run: {tests['testsRun']}, failures: {tests['failures']}, errors: {tests['errors']}, skipped: {tests['skipped']}")

    # Write JSON report
    out_dir = os.path.join("reports")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "system_report.json")
    with open(out_path, "w", encoding="utf8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"[system_report] Wrote {out_path}")


if __name__ == "__main__":
    main()
