#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║              AGL Security Tool — سكربت الإدارة والتشغيل              ║
║                   Management & Operations Script                     ║
╚══════════════════════════════════════════════════════════════════════╝

Usage:
    python manage.py install          # تثبيت المتطلبات
    python manage.py check            # فحص صحة البيئة
    python manage.py test             # تشغيل الاختبارات
    python manage.py scan <path>      # فحص ملف أو مجلد
    python manage.py deep <path>      # فحص عميق (Z3 + EVM + LLM)
    python manage.py quick <path>     # فحص سريع (أنماط فقط)
    python manage.py report <path>    # فحص + تقرير Markdown
    python manage.py benchmark        # اختبار أداء على ملف تجريبي
    python manage.py status           # حالة المحركات
    python manage.py clean            # تنظيف الكاش والملفات المؤقتة
"""

import os
import sys
import time
import subprocess
import argparse
import json
from pathlib import Path

# ═══════════════════════════════════════════════════
# المسارات الأساسية
# ═══════════════════════════════════════════════════
ROOT_DIR = Path(__file__).parent.resolve()
ENGINES_DIR = ROOT_DIR / "AGL_NextGen" / "src" / "agl" / "engines"
TOOL_DIR = ROOT_DIR / "agl_security_tool"
ARTIFACTS_DIR = ROOT_DIR / "artifacts"
TEST_SOL = ROOT_DIR / "vulnerable.sol"

# ألوان الطرفية
class C:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_header(text):
    print(f"\n{C.BOLD}{C.BLUE}{'═' * 60}{C.END}")
    print(f"{C.BOLD}{C.BLUE}  {text}{C.END}")
    print(f"{C.BOLD}{C.BLUE}{'═' * 60}{C.END}\n")


def print_ok(text):
    print(f"  {C.GREEN}✅ {text}{C.END}")


def print_warn(text):
    print(f"  {C.YELLOW}⚠️  {text}{C.END}")


def print_err(text):
    print(f"  {C.RED}❌ {text}{C.END}")


# ═══════════════════════════════════════════════════
# الأوامر
# ═══════════════════════════════════════════════════

def cmd_install():
    """تثبيت المتطلبات"""
    print_header("Installing Dependencies — تثبيت المتطلبات")

    req_file = ROOT_DIR / "requirements_security.txt"
    if not req_file.exists():
        print_err(f"requirements_security.txt not found at {req_file}")
        return False

    print(f"  📦 Installing from {req_file}...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
        capture_output=True, text=True
    )

    if result.returncode == 0:
        print_ok("All dependencies installed successfully")
    else:
        print_err(f"Installation failed:\n{result.stderr[:500]}")
        return False

    # Try installing z3 separately (it's special)
    print("\n  🔬 Checking Z3 SMT Solver...")
    try:
        import z3
        print_ok(f"Z3 already installed: v{z3.get_version_string()}")
    except ImportError:
        print("  📦 Installing z3-solver...")
        subprocess.run([sys.executable, "-m", "pip", "install", "z3-solver"], capture_output=True)
        try:
            import z3
            print_ok(f"Z3 installed: v{z3.get_version_string()}")
        except ImportError:
            print_warn("Z3 installation failed — formal verification will be disabled")

    return True


def cmd_check():
    """فحص صحة البيئة"""
    print_header("Environment Health Check — فحص صحة البيئة")

    all_ok = True

    # Python version
    v = sys.version_info
    if v.major >= 3 and v.minor >= 10:
        print_ok(f"Python {v.major}.{v.minor}.{v.micro}")
    else:
        print_err(f"Python {v.major}.{v.minor}.{v.micro} — Need 3.10+")
        all_ok = False

    # Core files
    core_files = {
        "offensive_security.py": ENGINES_DIR / "offensive_security.py",
        "agl_security.py": ENGINES_DIR / "agl_security.py",
        "smart_contract_analyzer.py": ENGINES_DIR / "smart_contract_analyzer.py",
        "formal_verifier.py": ENGINES_DIR / "formal_verifier.py",
        "solidity_context_aggregator.py": ENGINES_DIR / "solidity_context_aggregator.py",
        "strict_logic/logic_gates.py": ENGINES_DIR / "strict_logic" / "logic_gates.py",
        "holographic_llm.py": ENGINES_DIR / "holographic_llm.py",
    }

    print(f"\n  📁 Core Files:")
    for name, path in core_files.items():
        if path.exists():
            size = path.stat().st_size
            print_ok(f"{name} ({size:,} bytes)")
        else:
            print_err(f"{name} — NOT FOUND")
            all_ok = False

    # Dependencies
    print(f"\n  📦 Dependencies:")
    deps = {
        "z3": "z3-solver (Formal Verification)",
        "requests": "requests (HTTP)",
        "re": "re (Regex — built-in)",
    }

    for module, desc in deps.items():
        try:
            __import__(module)
            print_ok(desc)
        except ImportError:
            print_warn(f"{desc} — NOT INSTALLED")

    # Optional dependencies
    print(f"\n  🔧 Optional Tools:")
    for tool in ["slither", "mythril", "semgrep"]:
        from shutil import which
        if which(tool):
            print_ok(f"{tool} — available")
        else:
            print_warn(f"{tool} — not found (optional, improves detection)")

    # Engine loading test
    print(f"\n  ⚙️ Engine Loading:")
    sys.path.insert(0, str(ROOT_DIR / "AGL_NextGen" / "src"))
    try:
        from agl.engines.offensive_security import OffensiveSecurityEngine
        print_ok("OffensiveSecurityEngine loads successfully")
    except Exception as e:
        print_err(f"OffensiveSecurityEngine failed: {e}")
        all_ok = False

    if all_ok:
        print(f"\n  {C.GREEN}{C.BOLD}🎯 All checks passed — ready to scan!{C.END}")
    else:
        print(f"\n  {C.YELLOW}{C.BOLD}⚠️ Some issues found — run 'python manage.py install' first{C.END}")

    return all_ok


def cmd_status():
    """حالة المحركات"""
    print_header("Engine Status — حالة المحركات")

    sys.path.insert(0, str(ROOT_DIR / "AGL_NextGen" / "src"))

    engines = [
        ("SmartContractAnalyzer", "agl.engines.smart_contract_analyzer", "SmartContractAnalyzer"),
        ("AGLSecuritySuite", "agl.engines.agl_security", "AGLSecuritySuite"),
        ("OffensiveSecurityEngine", "agl.engines.offensive_security", "OffensiveSecurityEngine"),
        ("FormalVerificationEngine", "agl.engines.formal_verifier", "FormalVerificationEngine"),
        ("HolographicLLM", "agl.engines.holographic_llm", "HolographicLLM"),
        ("AdvancedMetaReasoner", "agl.engines.advanced_meta_reasoner", "AdvancedMetaReasonerEngine"),
        ("ResonanceOptimizer", "agl.engines.resonance_optimizer", "ResonanceOptimizer"),
        ("QuantumNeuralCore", "agl.engines.quantum_neural", "QuantumNeuralCore"),
        ("Logic Gates (AND/OR/NOT)", "agl.engines.strict_logic", "ANDGate"),
    ]

    for name, module_path, class_name in engines:
        try:
            mod = __import__(module_path, fromlist=[class_name])
            cls = getattr(mod, class_name)
            print_ok(f"{name}")
        except Exception as e:
            print_warn(f"{name} — {e}")


def cmd_test():
    """تشغيل الاختبارات"""
    print_header("Running Tests — تشغيل الاختبارات")

    if not TEST_SOL.exists():
        print_err(f"Test file not found: {TEST_SOL}")
        return False

    # Quick API test
    sys.path.insert(0, str(ROOT_DIR))
    sys.path.insert(0, str(ROOT_DIR / "AGL_NextGen" / "src"))

    from agl_security_tool import AGLSecurityAudit

    audit = AGLSecurityAudit()

    # Test 1: Quick scan
    print("  🧪 Test 1: Quick scan (pattern only)...")
    t0 = time.time()
    r = audit.quick_scan(str(TEST_SOL))
    t1 = time.time()
    findings = len(r.get("findings", []))
    print_ok(f"Quick scan: {findings} findings in {t1-t0:.2f}s") if findings > 0 else print_err("Quick scan: 0 findings!")

    # Test 2: Standard scan
    print("  🧪 Test 2: Standard scan (L1 + L2)...")
    t0 = time.time()
    r = audit.scan(str(TEST_SOL))
    t1 = time.time()
    total = r.get("total_findings", 0)
    print_ok(f"Standard scan: {total} findings in {t1-t0:.2f}s") if total > 0 else print_err("Standard scan: 0 findings!")

    # Test 3: Report generation
    print("  🧪 Test 3: Report generation...")
    text_report = audit.generate_report(r, format="text")
    md_report = audit.generate_report(r, format="markdown")
    json_report = audit.generate_report(r, format="json")
    print_ok(f"Text: {len(text_report)} chars, MD: {len(md_report)} chars, JSON: {len(json_report)} chars")

    # Test 4: Known vulnerability detection
    print("  🧪 Test 4: Known vulnerability detection (vulnerable.sol has 4)...")
    all_texts = []
    for f in r.get("findings", []):
        all_texts.append(f.get("title", "").lower())
    for f in r.get("suite_findings", []):
        all_texts.append(f.get("title", "").lower())

    detected = {
        "Reentrancy": any("reentrancy" in t for t in all_texts),
        "tx.origin": any("tx.origin" in t for t in all_texts),
        "Timestamp": any("timestamp" in t for t in all_texts),
    }

    for vuln, found in detected.items():
        if found:
            print_ok(f"{vuln}: DETECTED")
        else:
            print_err(f"{vuln}: MISSED")

    print(f"\n  📊 Detection rate: {sum(detected.values())}/{len(detected)}")
    return all(detected.values())


def cmd_scan(target, format="text", output=None, mode="scan"):
    """فحص ملف أو مجلد"""
    sys.path.insert(0, str(ROOT_DIR))
    sys.path.insert(0, str(ROOT_DIR / "AGL_NextGen" / "src"))

    from agl_security_tool import AGLSecurityAudit

    print_header(f"{'🔬 Deep' if mode == 'deep' else '⚡ Quick' if mode == 'quick' else '🛡️ Standard'} Scan")

    audit = AGLSecurityAudit()

    if mode == "deep":
        result = audit.deep_scan(target)
    elif mode == "quick":
        result = audit.quick_scan(target)
    else:
        result = audit.scan(target)

    report = audit.generate_report(result, format=format)

    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w", encoding="utf-8") as f:
            f.write(report)
        print_ok(f"Report saved to: {output}")
    else:
        print(report)

    # Summary
    summary = result.get("severity_summary", {})
    total = sum(summary.values())
    if total > 0:
        print(f"\n  🎯 Total: {total} findings (CRITICAL: {summary.get('CRITICAL', 0)}, HIGH: {summary.get('HIGH', 0)})")
    else:
        print(f"\n  ✅ No vulnerabilities found")


def cmd_benchmark():
    """اختبار أداء"""
    print_header("Benchmark — اختبار الأداء")

    if not TEST_SOL.exists():
        print_err(f"Test file not found: {TEST_SOL}")
        return

    sys.path.insert(0, str(ROOT_DIR))
    sys.path.insert(0, str(ROOT_DIR / "AGL_NextGen" / "src"))
    from agl_security_tool import AGLSecurityAudit

    audit = AGLSecurityAudit()

    # Quick scan
    print("  ⚡ Quick scan benchmark...")
    times = []
    for i in range(5):
        t0 = time.time()
        audit.quick_scan(str(TEST_SOL))
        times.append(time.time() - t0)
    avg = sum(times) / len(times)
    print_ok(f"Quick scan: avg {avg*1000:.0f}ms ({min(times)*1000:.0f}ms - {max(times)*1000:.0f}ms)")

    # Standard scan
    print("  🛡️ Standard scan benchmark...")
    t0 = time.time()
    audit.scan(str(TEST_SOL))
    t1 = time.time()
    print_ok(f"Standard scan: {(t1-t0)*1000:.0f}ms")


def cmd_clean():
    """تنظيف الملفات المؤقتة"""
    print_header("Clean — تنظيف")

    cleaned = 0
    # __pycache__
    for root, dirs, files in os.walk(ROOT_DIR):
        for d in dirs:
            if d == "__pycache__":
                import shutil
                p = os.path.join(root, d)
                shutil.rmtree(p, ignore_errors=True)
                print(f"  🗑️ {p}")
                cleaned += 1

    # .pyc files
    for root, dirs, files in os.walk(ROOT_DIR):
        for f in files:
            if f.endswith(".pyc"):
                p = os.path.join(root, f)
                os.remove(p)
                cleaned += 1

    print_ok(f"Cleaned {cleaned} cache entries")


# ═══════════════════════════════════════════════════
# Entry Point
# ═══════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        prog="manage.py",
        description="🛡️ AGL Security Tool — سكربت الإدارة",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  install    تثبيت المتطلبات
  check      فحص صحة البيئة
  status     حالة المحركات
  test       تشغيل الاختبارات
  scan       فحص قياسي
  quick      فحص سريع (أنماط فقط)
  deep       فحص عميق (Z3 + EVM + LLM)
  report     فحص + تقرير Markdown
  benchmark  اختبار أداء
  clean      تنظيف الكاش
        """
    )

    parser.add_argument("command", choices=[
        "install", "check", "status", "test",
        "scan", "quick", "deep", "report",
        "benchmark", "clean"
    ])
    parser.add_argument("target", nargs="?", help="مسار ملف .sol أو مجلد")
    parser.add_argument("-f", "--format", choices=["text", "json", "markdown"], default="text")
    parser.add_argument("-o", "--output", help="حفظ النتيجة في ملف")

    args = parser.parse_args()

    if args.command == "install":
        cmd_install()
    elif args.command == "check":
        cmd_check()
    elif args.command == "status":
        cmd_status()
    elif args.command == "test":
        cmd_test()
    elif args.command in ("scan", "quick", "deep"):
        if not args.target:
            print_err(f"Usage: python manage.py {args.command} <path-to-contract.sol>")
            sys.exit(1)
        cmd_scan(args.target, format=args.format, output=args.output, mode=args.command)
    elif args.command == "report":
        if not args.target:
            print_err("Usage: python manage.py report <path-to-contract.sol>")
            sys.exit(1)
        out = args.output or f"report_{Path(args.target).stem}.md"
        cmd_scan(args.target, format="markdown", output=out, mode="scan")
    elif args.command == "benchmark":
        cmd_benchmark()
    elif args.command == "clean":
        cmd_clean()


if __name__ == "__main__":
    main()
