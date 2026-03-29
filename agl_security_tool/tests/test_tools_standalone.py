"""Quick test: does Slither/Mythril work standalone?"""
import subprocess, json, sys

target = r"d:\AGL\agl_security_tool\test_contracts\vulnerable\unchecked_call.sol"

# Test Slither
print("=== SLITHER ===")
try:
    r = subprocess.run(
        ["slither", target, "--json", "-"],
        capture_output=True, text=True, timeout=60
    )
    if r.stdout:
        d = json.loads(r.stdout)
        dets = d.get("results", {}).get("detectors", [])
        print(f"  success={d.get('success')}, detectors={len(dets)}")
        for det in dets[:5]:
            print(f"    - {det.get('check','?')}: {det.get('impact','?')} / {det.get('confidence','?')}")
    else:
        print(f"  No stdout.")
    print(f"  stderr (first 1000 chars):\n{r.stderr[:1000]}")
    print(f"  returncode={r.returncode}")
except Exception as e:
    print(f"  Error: {e}")

# Test Mythril
print("\n=== MYTHRIL ===")
try:
    r = subprocess.run(
        ["myth", "analyze", target, "-o", "json", "--execution-timeout", "30"],
        capture_output=True, text=True, timeout=120
    )
    print(f"  returncode={r.returncode}")
    if r.stdout:
        d = json.loads(r.stdout)
        issues = d.get("issues", [])
        print(f"  issues={len(issues)}")
        for iss in issues[:5]:
            print(f"    - {iss.get('title','?')}: {iss.get('severity','?')}")
    else:
        print(f"  No stdout. stderr={r.stderr[:500]}")
except Exception as e:
    print(f"  Error: {e}")
