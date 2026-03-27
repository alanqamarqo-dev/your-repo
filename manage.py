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
    python manage.py project <path>   # فحص مشروع كامل (Foundry/Hardhat/Truffle)
    python manage.py info <path>      # إحصائيات المشروع بدون فحص
    python manage.py graph <path>     # شجرة التبعيات
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


def cmd_project(target, mode="scan", format="text", output=None, command="project",
                include_tests=False, include_deps=False, include_mocks=False):
    """فحص مشروع كامل (Foundry/Hardhat/Truffle)"""
    sys.path.insert(0, str(ROOT_DIR))
    sys.path.insert(0, str(ROOT_DIR / "AGL_NextGen" / "src"))

    from agl_security_tool.project_scanner import ProjectScanner

    config = {
        "exclude_tests": not include_tests,
        "exclude_mocks": not include_mocks,
        "scan_dependencies": include_deps,
    }

    scanner = ProjectScanner(target, config=config)

    # ── info: إحصائيات فقط ──
    if command == "info":
        print_header("Project Info — معلومات المشروع")
        scanner.discover()
        stats = scanner.get_project_stats()

        print(f"  📁 Root:       {stats['root_dir']}")
        print(f"  🔧 Type:       {stats['project_type']}")
        print(f"  📂 Contracts:  {stats['contracts_dir']}")
        print(f"  📄 .sol files: {stats['total_sol_files']}")
        print(f"  📋 Contracts:  {stats['total_contracts']}")
        print(f"  🔌 Interfaces: {stats['total_interfaces']}")
        print(f"  📚 Libraries:  {stats['total_libraries']}")
        print(f"  📝 LOC:        {stats['total_loc']:,}")
        print(f"  ⚙️  Functions:  {stats['total_functions']}")
        print(f"  🔗 Ext Calls:  {stats['total_external_calls']}")
        print(f"  📊 State Vars: {stats['total_state_variables']}")

        if stats.get("compiler_versions"):
            print(f"\n  🔨 Compiler Versions:")
            for v, count in stats["compiler_versions"].items():
                print(f"     {v}: {count} files")

        if stats.get("remappings"):
            print(f"\n  🔄 Remappings ({len(stats['remappings'])}):")
            for k, v in list(stats["remappings"].items())[:10]:
                print(f"     {k} → {v}")

        if stats.get("largest_files"):
            print(f"\n  📐 Largest Files (by LOC):")
            for f in stats["largest_files"][:5]:
                print(f"     {f['loc']:>5} LOC  {f['file']}  ({', '.join(f['contracts'])})")

        if stats.get("highest_attack_surface"):
            print(f"\n  ⚠️  Highest Attack Surface:")
            for f in stats["highest_attack_surface"][:5]:
                print(f"     {f['external_calls']:>3} ext calls  {f['file']}")

        return

    # ── graph: شجرة التبعيات ──
    if command == "graph":
        print_header("Dependency Graph — شجرة التبعيات")
        scanner.discover()
        graph = scanner.get_dependency_graph()

        print(f"  📊 Nodes: {len(graph['nodes'])}")
        print(f"  🔗 Edges: {len(graph['edges'])}")
        print(f"  🌳 Root contracts: {', '.join(graph['roots'][:10])}")
        print(f"  🍃 Leaf contracts: {', '.join(graph['leaves'][:10])}")

        out = json.dumps(graph, indent=2, ensure_ascii=False)
        if output:
            Path(output).parent.mkdir(parents=True, exist_ok=True)
            with open(output, "w", encoding="utf-8") as f:
                f.write(out)
            print_ok(f"Graph saved to: {output}")
        else:
            print(f"\n{out}")
        return

    # ── project: فحص كامل ──
    mode_label = {"quick": "⚡ Quick", "scan": "🛡️ Standard", "deep": "🔬 Deep"}
    print_header(f"{mode_label.get(mode, '🛡️')} Project Scan")
    print(f"  📁 Target: {target}")
    print(f"  🔧 Mode: {mode}")
    print()

    scanner.discover()
    info = scanner.project_info

    print(f"  🔍 Detected: {info.project_type} project")
    print(f"  📄 Files: {info.total_sol_files}")
    print(f"  📋 Contracts: {info.total_contracts}")
    if info.remappings:
        print(f"  🔄 Remappings: {len(info.remappings)}")
    print(f"\n  ⏳ Scanning...")

    if mode == "deep":
        result = scanner.deep_scan(output_format=format)
    elif mode == "quick":
        result = scanner.quick_scan(output_format=format)
    else:
        result = scanner.full_scan(output_format=format)

    # استخراج التقرير
    report_text = (
        result.get("report_text") or
        result.get("report_markdown") or
        result.get("report_json") or
        ""
    )

    if report_text:
        if output:
            Path(output).parent.mkdir(parents=True, exist_ok=True)
            with open(output, "w", encoding="utf-8") as f:
                f.write(report_text)
            print_ok(f"Report saved to: {output}")
        else:
            print(report_text)
    else:
        out = json.dumps(result, indent=2, ensure_ascii=False, default=str)
        if output:
            Path(output).parent.mkdir(parents=True, exist_ok=True)
            with open(output, "w", encoding="utf-8") as f:
                f.write(out)
            print_ok(f"Report saved to: {output}")
        else:
            print(out)

    # ملخص نهائي
    summary = result.get("severity_summary", {})
    total = sum(summary.values())
    if total > 0:
        print(f"\n  🎯 Total: {total} findings across {result.get('files_with_findings', '?')} files")
        print(f"     CRITICAL: {summary.get('CRITICAL', 0)}, HIGH: {summary.get('HIGH', 0)}, "
              f"MEDIUM: {summary.get('MEDIUM', 0)}, LOW: {summary.get('LOW', 0)}")
    else:
        print(f"\n  ✅ No vulnerabilities found across {result.get('files_scanned', '?')} files")


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
        "project", "info", "graph",
        "benchmark", "clean"
    ])
    parser.add_argument("target", nargs="?", help="مسار ملف .sol أو مجلد أو مشروع")
    parser.add_argument("-f", "--format", choices=["text", "json", "markdown"], default="text")
    parser.add_argument("-o", "--output", help="حفظ النتيجة في ملف")
    parser.add_argument("-m", "--mode", choices=["quick", "scan", "deep"], default="scan",
                        help="وضع الفحص (لأمر project)")
    parser.add_argument("--include-tests", action="store_true", help="فحص ملفات الاختبار")
    parser.add_argument("--include-deps", action="store_true", help="فحص المكتبات المثبتة")
    parser.add_argument("--include-mocks", action="store_true", help="فحص ملفات المحاكاة")

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
    elif args.command in ("project", "info", "graph"):
        if not args.target:
            print_err(f"Usage: python manage.py {args.command} <path-to-project>")
            sys.exit(1)
        cmd_project(args.target, mode=args.mode, format=args.format,
                    output=args.output, command=args.command,
                    include_tests=args.include_tests,
                    include_deps=args.include_deps,
                    include_mocks=args.include_mocks)


if __name__ == "__main__":
    main()
