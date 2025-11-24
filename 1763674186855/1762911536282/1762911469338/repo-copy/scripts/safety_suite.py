#!/usr/bin/env python
"""Run safety + emergency related tests and produce a small JSON+HTML report."""
from __future__ import annotations
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import argparse, json, os, subprocess, sys, tempfile
from datetime import datetime, timezone


def run_tests(test_modules: list) -> dict:
    out = {"tests": {}, "passed": True}
    for mod in test_modules:
        cmd = [sys.executable, "-m", "unittest", "-v", mod]
        p = subprocess.run(cmd, capture_output=True, text=True)
        out["tests"][mod] = {
            "returncode": p.returncode,
            "stdout": p.stdout,
            "stderr": p.stderr
        }
        if p.returncode != 0:
            out["passed"] = False
    return out


HTML_TPL = """<!doctype html>
<html><head><meta charset='utf-8'><title>Safety Suite Report</title></head><body>
<h1>Safety Suite Report</h1>
<div>Generated: {now}</div>
<div>Passed: {passed}</div>
<ul>
{items}
</ul>
</body></html>"""


def write_report(outdir: str, result: dict):
    os.makedirs(outdir, exist_ok=True)
    jpath = os.path.join(outdir, "safety_report.json")
    with open(jpath, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    items = []
    for k, v in result["tests"].items():
        items.append(f"<li><strong>{k}</strong> - rc={v['returncode']}<pre>{v['stdout']}</pre></li>")
    html = HTML_TPL.format(now=datetime.now(timezone.utc).isoformat(), passed=result.get('passed', False), items='\n'.join(items))
    hpath = os.path.join(outdir, "safety_report.html")
    with open(hpath, "w", encoding="utf-8") as f:
        f.write(html)
    return jpath, hpath


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reports/safety_suite")
    args = ap.parse_args()
    modules = [
        "tests.test_emergency_system_ar",
        "tests.test_copilot_sandbox",
        "tests.test_emergency_killswitch"
    ]
    res = run_tests(modules)
    j, h = write_report(args.out, res)
    print("wrote", j, h)


if __name__ == '__main__':
    main()
