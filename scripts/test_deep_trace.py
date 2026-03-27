"""Deep connection trace: offensive_security <-> agl_security <-> smart_contract_analyzer"""
import sys
sys.path.insert(0, r'd:\AGL\AGL_NextGen\src')

print('='*60)
print('DEEP CONNECTION TRACE')
print('='*60)

# Test 1: Import chain from offensive_security
print('\n[1] Import chain from offensive_security:')
try:
    from agl.engines.offensive_security import (
        OffensiveSecurityEngine, SECURITY_SUITE_AVAILABLE, 
        AGLSecuritySuite, SmartContractAnalyzer
    )
    print(f'   SECURITY_SUITE_AVAILABLE: {SECURITY_SUITE_AVAILABLE}')
    print(f'   AGLSecuritySuite: {AGLSecuritySuite}')
    print(f'   SmartContractAnalyzer: {SmartContractAnalyzer}')
except Exception as e:
    print(f'   ERROR: {e}')

# Test 2: Direct import of agl_security
print('\n[2] Direct import agl_security:')
try:
    from agl.engines.agl_security import AGLSecuritySuite as DirectSuite
    print(f'   OK: {DirectSuite}')
except Exception as e:
    print(f'   ERROR: {e}')

# Test 3: Direct import smart_contract_analyzer
print('\n[3] Direct import smart_contract_analyzer:')
try:
    from agl.engines.smart_contract_analyzer import SmartContractAnalyzer as DA
    print(f'   OK: {DA}')
    print(f'   analyze(): {hasattr(DA, "analyze")}')
    print(f'   analyze_project(): {hasattr(DA, "analyze_project")}')
    print(f'   analyze_file(): {hasattr(DA, "analyze_file")}')
    print(f'   _pattern_scan(): {hasattr(DA, "_pattern_scan")}')
except Exception as e:
    print(f'   ERROR: {e}')

# Test 4: Engine instance
print('\n[4] Engine instance connections:')
engine = OffensiveSecurityEngine()
print(f'   security_suite type: {type(engine.security_suite).__name__}')
print(f'   smart_analyzer type: {type(engine.smart_analyzer).__name__}')
print(f'   security_suite is AGLSecuritySuite: {isinstance(engine.security_suite, AGLSecuritySuite) if engine.security_suite else "N/A"}')

# Test 5: Run agl_security.scan_file
print('\n[5] AGLSecuritySuite.scan_file(vulnerable.sol):')
if engine.security_suite:
    r = engine.security_suite.scan_file(r'd:\AGL\vulnerable.sol')
    findings = r.get('findings', [])
    print(f'   Findings: {len(findings)}')
    for f in findings:
        print(f'     [{f["severity"]}] L{f["line"]}: {f["title"]}')
    print(f'   Tools used: {r.get("tools_used", ["agl"])}')
else:
    print('   SKIP: suite not available')

# Test 6: Does SmartContractAnalyzer.analyze find same things?
print('\n[6] SmartContractAnalyzer.analyze() directly:')
if engine.smart_analyzer:
    code = open(r'd:\AGL\vulnerable.sol', 'r').read()
    r = engine.smart_analyzer.analyze(code)
    findings = r.get('findings', [])
    print(f'   Findings: {len(findings)}')
    for f in findings:
        print(f'     [{f["severity"]}] L{f["line"]}: {f["title"]}')
    print(f'   Contracts: {[c["name"] for c in r.get("contracts", [])]}')
    print(f'   Functions: {[f["name"] for f in r.get("functions", [])]}')
else:
    print('   SKIP: analyzer not available')

# Test 7: Compare with offensive_security._analyze_smart_contracts
print('\n[7] Comparing pipelines (what does offensive_security ADD on top?):')
import time
t0 = time.time()
full_result = engine.process_task('smart_contract_audit', r'd:\AGL\vulnerable.sol')
t1 = time.time()

vulns = full_result.get('vulnerabilities', [])
proven = full_result.get('math_proven_count', 0)
false_pos_filtered = full_result.get('false_positives_filtered', 0)
evm = full_result.get('evm_simulation', {})

print(f'   Time: {t1-t0:.1f}s')
print(f'   Total vulnerabilities: {len(vulns)}')
print(f'   Math proven (Z3): {proven}')
print(f'   False positives filtered: {false_pos_filtered}')
print(f'   EVM chains analyzed: {len(evm.get("call_chains", []))}')
print(f'   Has quantum_findings: {"quantum_findings" in full_result}')

# Count what came from suite vs heuristic
suite_count = sum(1 for v in vulns if v.get('source') == 'agl-security-suite')
heuristic_count = sum(1 for v in vulns if v.get('source') != 'agl-security-suite')
print(f'   From Security Suite: {suite_count}')
print(f'   From Heuristic Engine: {heuristic_count}')

print('\n' + '='*60)
print('TRACE COMPLETE')
