"""Quick usability test for agl_security_tool"""

import sys, os, time

_PROJECT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
os.chdir(_PROJECT_ROOT)
sys.path.insert(0, _PROJECT_ROOT)

# Suppress noisy stderr
import io

old_stderr = sys.stderr
sys.stderr = io.StringIO()

try:
    from agl_security_tool import AGLSecurityAudit, __version__

    print(f"[OK] Import works — version {__version__}")
except Exception as e:
    print(f"[FAIL] Import: {e}")
    sys.exit(1)

# Test 1: Instantiation
try:
    audit = AGLSecurityAudit()
    print(f"[OK] AGLSecurityAudit() created")
except Exception as e:
    print(f"[FAIL] Init: {e}")
    sys.exit(1)

# Test 2: Quick scan
try:
    t0 = time.time()
    r = audit.quick_scan("vulnerable.sol")
    t1 = time.time()
    findings = r.get("findings", [])
    print(
        f"[OK] quick_scan: {len(findings)} findings in {t1-t0:.2f}s — status={r.get('status')}"
    )
except Exception as e:
    print(f"[FAIL] quick_scan: {e}")

# Test 3: Full scan
try:
    t0 = time.time()
    r = audit.scan("vulnerable.sol")
    t1 = time.time()
    layers = r.get("layers_used", [])
    det = len(r.get("detector_findings", []))
    sym = len(r.get("symbolic_findings", []))
    uni = len(r.get("all_findings_unified", []))
    ss = r.get("severity_summary", {})
    print(f"[OK] scan: {uni} unified findings in {t1-t0:.2f}s")
    print(f"     Layers active: {layers}")
    print(f"     Detectors: {det} | Symbolic(Z3): {sym}")
    print(
        f"     CRITICAL={ss.get('CRITICAL',0)} HIGH={ss.get('HIGH',0)} MEDIUM={ss.get('MEDIUM',0)} LOW={ss.get('LOW',0)}"
    )
    # Show top 5 findings
    for i, f in enumerate(r.get("all_findings_unified", [])[:5]):
        sev = f.get("severity", "?").upper()
        title = str(f.get("title", f.get("description", "")))[:90]
        line = f.get("line", "?")
        print(f"     [{sev}] L{line}: {title}")
except Exception as e:
    print(f"[FAIL] scan: {e}")

# Test 4: State Extraction
try:
    t0 = time.time()
    r = audit.extract_state("vulnerable.sol")
    t1 = time.time()
    if "error" in r:
        print(f"[WARN] extract_state: {r['error']}")
    else:
        entities = len(r.get("entities", []))
        relations = len(r.get("relationships", []))
        print(
            f"[OK] extract_state: {entities} entities, {relations} relationships in {t1-t0:.2f}s"
        )
except Exception as e:
    print(f"[FAIL] extract_state: {e}")

# Test 5: Project scanner
try:
    from agl_security_tool import ProjectScanner

    if os.path.isdir("test_project"):
        scanner = ProjectScanner("test_project")
        info = scanner.discover()
        print(
            f"[OK] ProjectScanner: type={info.project_type}, files={info.total_sol_files}, contracts={info.total_contracts}"
        )
    else:
        print(f"[SKIP] ProjectScanner: no test_project/ dir")
except Exception as e:
    print(f"[FAIL] ProjectScanner: {e}")

# Test 6: Detectors
try:
    from agl_security_tool.detectors import DetectorRunner

    dr = DetectorRunner()
    print(f"[OK] DetectorRunner: {len(dr.detectors)} detectors loaded")
    for d in dr.detectors:
        print(f"     - {d.DETECTOR_ID}")
except Exception as e:
    print(f"[FAIL] DetectorRunner: {e}")

# Test 7: Z3 symbolic
try:
    from agl_security_tool.z3_symbolic_engine import Z3SymbolicEngine

    z3e = Z3SymbolicEngine()
    with open("vulnerable.sol", "r") as f:
        code = f.read()
    findings = z3e.analyze(code, "vulnerable.sol")
    print(f"[OK] Z3SymbolicEngine: {len(findings)} proven findings")
    for sf in findings[:3]:
        print(f"     [{sf.severity.upper()}] {sf.title[:80]}")
except Exception as e:
    print(f"[FAIL] Z3: {e}")

# Test 8: Exploit Reasoning
try:
    from agl_security_tool.exploit_reasoning import ExploitReasoningEngine

    print(f"[OK] ExploitReasoningEngine importable")
except Exception as e:
    print(f"[FAIL] ExploitReasoning: {e}")

# Test 9: Report generation
try:
    r = audit.scan("vulnerable.sol")
    text_report = audit.generate_report(r, "text")
    md_report = audit.generate_report(r, "markdown")
    json_report = audit.generate_report(r, "json")
    print(
        f"[OK] Reports: text={len(text_report)} chars, md={len(md_report)} chars, json={len(json_report)} chars"
    )
except Exception as e:
    print(f"[FAIL] Reports: {e}")

sys.stderr = old_stderr
print("\n=== USABILITY TEST COMPLETE ===")
