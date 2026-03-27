"""Quick test of the full detector pipeline through core.py"""
from agl_security_tool.core import AGLSecurityAudit

audit = AGLSecurityAudit()

# Test 1: vulnerable.sol through full pipeline
result = audit.scan("vulnerable.sol")
print("=" * 60)
print("Test: vulnerable.sol via AGLSecurityAudit.scan()")
print("=" * 60)
print(f"Status: {result['status']}")
print(f"Layers used: {result['layers_used']}")
print(f"Total findings: {result['total_findings']}")
print(f"Severity: {result['severity_summary']}")

# Detector findings detail
det = result.get("detector_findings", [])
print(f"\n--- Detector Findings ({len(det)}) ---")
for f in det:
    sev = f["severity"].upper()
    print(f"  [{sev}] {f['detector']}: {f['function']}")
    print(f"    {f['description'][:100]}")

# Test 2: Full test_project scan
import os
if os.path.exists("test_project/src"):
    print("\n" + "=" * 60)
    print("Test: test_project/ directory scan")
    print("=" * 60)
    result2 = audit.scan("test_project/src", recursive=True)
    print(f"Files scanned: {result2.get('files_scanned', 0)}")
    print(f"Total findings: {result2.get('total_findings', 0)}")
    print(f"Severity: {result2.get('severity_summary', {})}")

    for fpath, fr in result2.get("file_results", {}).items():
        dets = fr.get("detector_findings", [])
        if dets:
            print(f"\n  {os.path.basename(fpath)}: {len(dets)} detector findings")
            for d in dets:
                print(f"    [{d['severity'].upper()}] {d['detector']}")

# Test 3: List all registered detectors
from agl_security_tool.detectors import DetectorRunner
runner = DetectorRunner()
print(f"\n--- Registered Detectors ({len(runner.detectors)}) ---")
for info in runner.list_detectors():
    print(f"  {info['id']}: [{info['severity']}] {info['title']}")
