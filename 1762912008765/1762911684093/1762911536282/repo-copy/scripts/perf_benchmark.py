"""Small perf harness: run the smoke self-engine and record elapsed time + outputs to artifacts/logs/perf_benchmark.log"""
import time, subprocess, sys, os
from datetime import datetime
ROOT = os.path.abspath(os.path.dirname(__file__) + os.sep + '..')
script = os.path.join(ROOT, 'scripts', 'run_smoke_self_engine.py')
py = sys.executable
start = time.time()
proc = subprocess.run([py, script], capture_output=True, text=True)
end = time.time()
elapsed = end - start
os.makedirs(os.path.join(ROOT, 'artifacts', 'logs'), exist_ok=True)
logpath = os.path.join(ROOT, 'artifacts', 'logs', 'perf_benchmark.log')
with open(logpath, 'a', encoding='utf-8') as f:
    f.write(f"[{datetime.utcnow().isoformat()}Z] elapsed_seconds={elapsed:.3f} returncode={proc.returncode}\n")
    f.write("--- STDOUT ---\n")
    f.write(proc.stdout + "\n")
    f.write("--- STDERR ---\n")
    f.write(proc.stderr + "\n\n")
print(f"elapsed_seconds={elapsed:.3f}")
# propagate return code of target so CI can detect failures
sys.exit(proc.returncode)
