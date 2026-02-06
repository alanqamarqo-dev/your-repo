"""
تحقق شامل: فحص كل طبقة من الأداة بعد الإصلاحات
Comprehensive verification after fixes
"""
import sys
sys.path.insert(0, r'd:\AGL\AGL_NextGen\src')

TARGET = r'd:\AGL\vulnerable.sol'

print('='*70)
print('  COMPREHENSIVE VERIFICATION TEST — POST-FIX')
print('='*70)

# ═══════════════════════════════════════════════════════════════════
# LAYER 1: smart_contract_analyzer._pattern_scan (الطبقة الأعمق)
# ═══════════════════════════════════════════════════════════════════
print('\n📋 [LAYER 1] smart_contract_analyzer._pattern_scan():')
from agl.engines.smart_contract_analyzer import SmartContractAnalyzer

analyzer = SmartContractAnalyzer()
with open(TARGET, 'r') as f:
    code = f.read()

result = analyzer.analyze(code)
findings_l1 = result.get('findings', [])
print(f'   Total findings: {len(findings_l1)}')
for f in findings_l1:
    icon = '💀' if f['severity'] == 'critical' else '🔴' if f['severity'] == 'high' else '🟡'
    print(f'   {icon} [{f["severity"].upper()}] L{f["line"]}: {f["title"]}')

# Check: Reentrancy should now be detected
has_reentrancy = any('reentrancy' in f.get('title', '').lower() or 'reentrancy' in f.get('category', '').lower() for f in findings_l1)
print(f'\n   ✅ Reentrancy detected: {has_reentrancy}' if has_reentrancy else f'\n   ❌ Reentrancy STILL MISSING!')
has_tx_origin = any('tx.origin' in f.get('title', '').lower() for f in findings_l1)
print(f'   ✅ tx.origin detected: {has_tx_origin}' if has_tx_origin else f'   ❌ tx.origin MISSING!')

# ═══════════════════════════════════════════════════════════════════
# LAYER 2: AGLSecuritySuite.scan_file (الطبقة الوسطى)
# ═══════════════════════════════════════════════════════════════════
print('\n📋 [LAYER 2] AGLSecuritySuite.scan_file():')
from agl.engines.agl_security import AGLSecuritySuite

suite = AGLSecuritySuite({'severity_filter': ['critical', 'high', 'medium', 'low']})
result2 = suite.scan_file(TARGET)
findings_l2 = result2.get('findings', [])
print(f'   Total findings: {len(findings_l2)}')
for f in findings_l2:
    icon = '💀' if f['severity'] == 'critical' else '🔴' if f['severity'] == 'high' else '🟡'
    print(f'   {icon} [{f["severity"].upper()}] L{f["line"]}: {f["title"]}')

has_reentrancy_l2 = any('reentrancy' in f.get('title', '').lower() for f in findings_l2)
print(f'\n   ✅ Reentrancy detected: {has_reentrancy_l2}' if has_reentrancy_l2 else f'\n   ❌ Reentrancy MISSING in suite!')

# ═══════════════════════════════════════════════════════════════════
# LAYER 3: offensive_security full pipeline (الطبقة العليا)
# ═══════════════════════════════════════════════════════════════════
print('\n📋 [LAYER 3] offensive_security.process_task("smart_contract_audit"):')
from agl.engines.offensive_security import OffensiveSecurityEngine
import time

engine = OffensiveSecurityEngine()
t0 = time.time()
result3 = engine.process_task('smart_contract_audit', TARGET)
t1 = time.time()

print(f'\n   ⏱️  Time: {t1-t0:.1f}s')
print(f'   📊 Status: {result3.get("status")}')
print(f'   📁 Files scanned: {result3.get("files_scanned")}')

# Heuristic findings (from findings list)
heuristic_findings = result3.get('findings', [])
total_heuristic_issues = 0
for hf in heuristic_findings:
    issues = hf.get('issues', [])
    total_heuristic_issues += len(issues)
    print(f'\n   📄 File: {hf.get("file")}')
    print(f'      Logic Gates: {hf.get("strict_logic_enabled")}')
    print(f'      Formal Verification: {hf.get("formal_verification_enabled")}')
    for issue in issues:
        sev = issue.get('severity', 'UNKNOWN')
        proven = '🔬 PROVEN' if issue.get('mathematically_proven') else ''
        status = issue.get('validation_status', 'N/A')
        icon = '💀' if sev == 'CRITICAL' else '🔴' if sev == 'HIGH' else '🟡'
        print(f'      {icon} [{sev}] ({status}) {proven}: {issue.get("text", "")[:80]}')

# Suite findings
suite_findings = result3.get('suite_findings', [])
print(f'\n   🛡️ Security Suite findings: {len(suite_findings)}')
for sf in suite_findings:
    icon = '💀' if sf['severity'] == 'critical' else '🔴' if sf['severity'] == 'high' else '🟡'
    print(f'      {icon} [{sf["severity"].upper()}] L{sf["line"]}: {sf["title"]}')

# Severity summary
summary = result3.get('severity_summary', {})
print(f'\n   📊 SEVERITY SUMMARY:')
print(f'      CRITICAL:    {summary.get("CRITICAL", 0)}')
print(f'      HIGH:        {summary.get("HIGH", 0)}')
print(f'      MEDIUM:      {summary.get("MEDIUM", 0)}')
print(f'      MATH PROVEN: {summary.get("MATHEMATICALLY_PROVEN", 0)}')
print(f'      Total:       {result3.get("total_findings", 0)}')

# EVM Simulation
evm = result3.get('evm_simulation', {})
if evm:
    chains = evm.get('call_chains', [])
    dangerous = [c for c in chains if c.get('z3_proven_dangerous')]
    print(f'\n   🔧 EVM Simulation:')
    print(f'      Call chains: {len(chains)}')
    print(f'      Z3 proven dangerous: {len(dangerous)}')

# ═══════════════════════════════════════════════════════════════════
# FINAL SCORECARD
# ═══════════════════════════════════════════════════════════════════
print('\n' + '='*70)
print('  SCORECARD: vulnerable.sol has 4 known vulnerabilities')
print('='*70)

known_vulns = {
    'Reentrancy': False,
    'tx.origin': False,
    'Unchecked call': False,
    'Block timestamp': False
}

# Check in all layers
all_texts = []
for f in findings_l1:
    all_texts.append(f.get('title', '').lower())
for f in findings_l2:
    all_texts.append(f.get('title', '').lower())
for hf in heuristic_findings:
    for issue in hf.get('issues', []):
        all_texts.append(issue.get('text', '').lower())
for sf in suite_findings:
    all_texts.append(sf.get('title', '').lower())

for text in all_texts:
    if 'reentrancy' in text or 'reentranc' in text:
        known_vulns['Reentrancy'] = True
    if 'tx.origin' in text:
        known_vulns['tx.origin'] = True
    if 'unchecked' in text or 'low-level call' in text:
        known_vulns['Unchecked call'] = True
    if 'timestamp' in text:
        known_vulns['Block timestamp'] = True

score = sum(known_vulns.values())
for vuln, found in known_vulns.items():
    icon = '✅' if found else '❌'
    print(f'   {icon} {vuln}: {"DETECTED" if found else "MISSED"}')

print(f'\n   🎯 DETECTION RATE: {score}/4 ({score*100//4}%)')
print(f'   📊 Total unique findings across all layers: L1={len(findings_l1)}, L2={len(findings_l2)}, Heuristic={total_heuristic_issues}, Suite={len(suite_findings)}')
print('='*70)
