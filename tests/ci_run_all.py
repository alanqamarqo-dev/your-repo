"""
CI Test Runner — يشغل جميع اختبارات agl_security_tool ويخرج نتائج JSON
Runs all agl_security_tool tests and produces JSON results + exit code.

Usage:
    python tests/ci_run_all.py
"""

import subprocess, sys, os, time, json

# Resolve project root (parent of tests/)
PROJECT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
os.chdir(PROJECT_ROOT)

# ── Test definitions ──────────────────────────────────────
# Each entry: (file_path, timeout_seconds, requires_external_tools)
TESTS = [
    # Core tests — fast, no external tools needed
    ("tests/_test_state_engine.py",      120, False),
    ("tests/_test_temporal_model.py",    300, False),
    ("tests/_test_action_space.py",      120, False),
    ("tests/_test_attack_engine.py",     120, False),
    ("tests/_test_search_engine.py",     120, False),
    ("tests/_test_exploit_reasoning.py", 300, False),
    ("tests/_test_defi_detection.py",    300, False),
    ("test_detector_system.py",          120, False),

    # Full pipeline tests — need Slither/Semgrep, take longer
    ("tests/_test_l1_l4.py",            600, True),
    ("tests/_test_tool_usability.py",   600, True),
    ("tests/_test_final.py",            600, True),
]

# Skip tests that need fixtures not available in CI
CONDITIONAL_SKIP = {
    "tests/_test_fix.py":   "aave-v3-core/contracts/protocol/pool/Pool.sol",
    "tests/_test_speed.py": "aave-v3-core/contracts/protocol/pool/Pool.sol",
}

# ── Runner ────────────────────────────────────────────────
results = []
total_t0 = time.time()

print("=" * 70)
print("AGL SECURITY TOOL — CI TEST SUITE")
print(f"Python {sys.version.split()[0]} | CWD: {os.getcwd()}")
print("=" * 70)

for test_file, timeout, needs_external in TESTS:
    if not os.path.exists(test_file):
        results.append({
            "test": test_file,
            "status": "SKIP",
            "reason": "file not found",
            "duration": 0,
        })
        print(f"  ⊘ [SKIP   ] {test_file:45s} (file not found)")
        continue

    print(f"  ▶ Running {test_file} ...", end=" ", flush=True)
    t0 = time.time()

    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = PROJECT_ROOT + os.pathsep + env.get("PYTHONPATH", "")

        proc = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=PROJECT_ROOT,
            env=env,
        )
        duration = time.time() - t0

        output = proc.stdout + proc.stderr
        out_lower = output.lower()

        # Determine pass/fail
        if proc.returncode == 0:
            if "fail" in out_lower and "0 fail" not in out_lower:
                status = "FAIL"
            else:
                status = "PASS"
        else:
            status = "FAIL"

        # Extract last meaningful lines
        lines = [l.strip() for l in output.strip().split("\n") if l.strip()]
        summary = " | ".join(lines[-3:])[:200] if lines else "(no output)"

        results.append({
            "test": test_file,
            "status": status,
            "returncode": proc.returncode,
            "duration": round(duration, 1),
            "summary": summary,
        })

        icon = "✓" if status == "PASS" else "✗"
        print(f"{icon} {status} ({duration:.1f}s)")

    except subprocess.TimeoutExpired:
        duration = time.time() - t0
        results.append({
            "test": test_file,
            "status": "TIMEOUT",
            "duration": round(duration, 1),
            "reason": f"exceeded {timeout}s",
        })
        print(f"⏱ TIMEOUT ({timeout}s)")

    except Exception as e:
        duration = time.time() - t0
        results.append({
            "test": test_file,
            "status": "ERROR",
            "duration": round(duration, 1),
            "reason": str(e)[:200],
        })
        print(f"⚠ ERROR: {e}")

# ── Skipped conditional tests ─────────────────────────────
for test_file, fixture in CONDITIONAL_SKIP.items():
    if os.path.exists(fixture):
        # Fixture exists — run the test
        print(f"  ▶ Running {test_file} (fixture found) ...", end=" ", flush=True)
        t0 = time.time()
        try:
            env = os.environ.copy()
            env["PYTHONPATH"] = PROJECT_ROOT + os.pathsep + env.get("PYTHONPATH", "")
            proc = subprocess.run(
                [sys.executable, test_file],
                capture_output=True, text=True, timeout=600,
                cwd=PROJECT_ROOT, env=env,
            )
            duration = time.time() - t0
            status = "PASS" if proc.returncode == 0 else "FAIL"
            results.append({
                "test": test_file, "status": status,
                "duration": round(duration, 1),
            })
            icon = "✓" if status == "PASS" else "✗"
            print(f"{icon} {status} ({duration:.1f}s)")
        except subprocess.TimeoutExpired:
            results.append({
                "test": test_file, "status": "TIMEOUT",
                "duration": 600, "reason": "exceeded 600s",
            })
            print("⏱ TIMEOUT")
    else:
        results.append({
            "test": test_file,
            "status": "SKIP",
            "reason": f"fixture missing: {fixture}",
            "duration": 0,
        })
        print(f"  ⊘ [SKIP   ] {test_file:45s} (missing {fixture})")

# ── Summary ───────────────────────────────────────────────
total_duration = time.time() - total_t0
passed  = sum(1 for r in results if r["status"] == "PASS")
failed  = sum(1 for r in results if r["status"] == "FAIL")
skipped = sum(1 for r in results if r["status"] == "SKIP")
timeout = sum(1 for r in results if r["status"] == "TIMEOUT")
errors  = sum(1 for r in results if r["status"] == "ERROR")

print("\n" + "=" * 70)
print(f"RESULTS: {passed} passed, {failed} failed, {skipped} skipped, "
      f"{timeout} timeout, {errors} errors  [{total_duration:.0f}s]")
print("=" * 70)

for r in results:
    icons = {"PASS": "✓", "FAIL": "✗", "SKIP": "⊘", "TIMEOUT": "⏱", "ERROR": "⚠"}
    icon = icons.get(r["status"], "?")
    detail = r.get("summary", r.get("reason", ""))[:70]
    print(f"  {icon} [{r['status']:7s}] {r['test']:45s} {r['duration']:6.1f}s  {detail}")

# ── Write JSON results ────────────────────────────────────
json_path = os.path.join(PROJECT_ROOT, "tests", "ci_results.json")
with open(json_path, "w") as f:
    json.dump({
        "total_duration": round(total_duration, 1),
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "timeout": timeout,
        "errors": errors,
        "tests": results,
    }, f, indent=2, ensure_ascii=False)

print(f"\n📄 Results saved to {json_path}")

# ── Exit code ─────────────────────────────────────────────
if failed > 0 or errors > 0:
    print(f"\n❌ CI FAILED — {failed} test(s) failed, {errors} error(s)")
    sys.exit(1)
else:
    print(f"\n✅ CI PASSED — {passed}/{passed + skipped + timeout} tests passed")
    sys.exit(0)
