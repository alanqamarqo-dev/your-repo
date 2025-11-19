import os
import subprocess
import json


def test_run_agi_final_via_script():
    """Run the PowerShell script that executes the AGI final v4 test and assert artifacts are produced."""
    script = os.path.join("scripts", "run_agi_final_v4.ps1")
    assert os.path.exists(script), f"Runner script not found: {script}"

    # Run the script using PowerShell
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        script,
    ]
    proc = subprocess.run(cmd, cwd=os.getcwd(), capture_output=True, text=True)

    print(proc.stdout)
    print(proc.stderr)

    assert proc.returncode == 0, f"Runner script failed (code {proc.returncode})\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"

    # Check artifacts
    json_path = os.path.join("artifacts", "agi_final_v4", "result.json")
    assert os.path.exists(json_path), f"Result JSON not found at {json_path}"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "total" in data
