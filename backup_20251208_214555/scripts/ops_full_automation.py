#!/usr/bin/env python3
"""Orchestrate full generation: tests -> reports -> self_optimize -> safety -> PDFs -> manifest

This script is safe to call from PowerShell (ci_local.ps1) and will try to export PDFs
using WeasyPrint if available; otherwise it will skip PDF export but still update manifest.
"""
import os, sys, subprocess, json, datetime

ROOT = os.path.dirname(os.path.dirname(__file__))
PY = sys.executable

def run_cmd(cmd, env=None, check=True):
    print("RUN:", cmd)
    res = subprocess.run(cmd, env=env, shell=False)
    if check and res.returncode != 0:
        raise SystemExit(res.returncode)
    return res.returncode

def run_unit_tests():
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    run_cmd([PY, "-m", "unittest", "discover", "-v"], env=env)

def generate_reports():
    run_cmd([PY, os.path.join("scripts", "generate_all_reports.py")])

def run_self_optimize():
    run_cmd([PY, os.path.join("scripts", "self_optimize.py"), "--out", os.path.join("reports","self_optimization")])

def run_safety():
    run_cmd([PY, "-m", "scripts.safety_suite", "--out", os.path.join("reports","safety_suite")])

def export_pdfs(manifest_htmls):
    try:
        from weasyprint import HTML # type: ignore
    except Exception:
        print("WeasyPrint not available; skipping PDF export. To enable, pip install weasyprint")
        return []
    out_files = []
    for h in manifest_htmls:
        src = os.path.join("reports", h)
        if not os.path.exists(src):
            print(f"skip missing {src}")
            continue
        dst = os.path.splitext(src)[0] + ".pdf"
        print(f"Exporting {src} -> {dst}")
        try:
            HTML(filename=src).write_pdf(dst)
            out_files.append(dst)
        except Exception as e:
            print("PDF export failed for", src, e)
    return out_files

def update_manifest(htmls, jsons):
    os.makedirs("reports", exist_ok=True)
    manifest = {"html": htmls, "json": jsons, "ts": datetime.datetime.now().isoformat()}
    with open(os.path.join("reports","report_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print("Wrote reports/report_manifest.json")

def main():
    # 1. tests
    run_unit_tests()
    # 2. reports
    generate_reports()
    # 3. self optimize
    run_self_optimize()
    # 4. safety
    run_safety()
    # 5. manifest and pdf
    # choose a set of default htmls (existing in repo conventions)
    htmls = [
        "models_report.html",
        "auto_reports/ohm_report.html",
        "auto_reports/power_report.html",
        "safety_suite/safety_report.html",
    ]
    jsons = [
        "safety_suite/safety_report.json",
        "self_optimization/self_optimization.json",
        "last_success.json",
    ]
    update_manifest(htmls, jsons)
    exported = export_pdfs(htmls)
    if exported:
        print("Exported PDFs:", exported)

if __name__ == '__main__':
    main()
