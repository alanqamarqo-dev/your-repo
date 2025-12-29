import os
import subprocess

print("Running Phase-5 benchmark (zero_shot_qa_eval) using sample_medical_bench.json")
cmd = (
    "cd D:/AGL/repo-copy; "
    "$env:PYTHONPATH='D:/AGL/repo-copy'; "
    "$env:AGL_ENGINES='hosted_llm'; "
    "$env:AGL_COT_SAMPLES='1'; "
    "$env:AGL_BENCHMARK_PATH='benchmarks/sample_medical_bench.json'; "
    "D:/AGL/.venv/Scripts/python.exe tools/zero_shot_qa_eval.py"
)
print("Command to run (PowerShell):")
print(cmd)
print("\nYou can paste this into PowerShell to execute the Phase-5 benchmark.")
