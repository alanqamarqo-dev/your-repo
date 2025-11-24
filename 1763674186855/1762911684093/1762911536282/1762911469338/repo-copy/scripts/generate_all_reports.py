import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import subprocess, datetime, json
from Learning_System.io_utils import read_json_with_fallback

KB_PATH = "Knowledge_Base/Learned_Patterns.json"
REPORT_DIR = "reports/auto_reports"

os.makedirs(REPORT_DIR, exist_ok=True)

# Use fallback reader so we can tolerate missing canonical KB and use lock/.new
kb = read_json_with_fallback(KB_PATH)

patterns = kb.get("patterns", [])
print(f"Found {len(patterns)} patterns to report")

for p in patterns:
    base = p.get("base")
    if not base:
        continue
    out_path = os.path.join(REPORT_DIR, f"{base}_report.html")
    print(f"Generating report for {base} → {out_path}")
    # Call the report generator; ensure encoding env set
    cmd = [sys.executable, os.path.join("scripts", "infer_report.py"), "--base", base, "--out", out_path]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = env.get("PYTHONIOENCODING", "utf-8")
    subprocess.run(cmd, check=False, env=env)

timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
print(f"\nCompleted all reports at {timestamp}")
print(f"Saved under: {REPORT_DIR}")
