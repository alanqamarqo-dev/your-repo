#!/usr/bin/env python3
"""
AGL Security — نقطة الدخول عبر سطر الأوامر
Command-Line Interface for AGL Smart Contract Security Auditor

Usage:
    python -m agl_security_tool scan contract.sol
    python -m agl_security_tool scan contracts/ --recursive
    python -m agl_security_tool quick contract.sol
    python -m agl_security_tool deep contract.sol
    python -m agl_security_tool project /path/to/foundry-project
    python -m agl_security_tool project /path/to/hardhat-project -m deep -f markdown -o report.md
    python -m agl_security_tool info /path/to/project
    python -m agl_security_tool graph /path/to/project -o deps.json
"""

import argparse
import sys
import os
import json
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        prog="agl-security",
        description="🛡️ AGL Smart Contract Security Auditor — أداة تحليل أمان العقود الذكية",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s scan contract.sol                        # Standard file scan
  %(prog)s quick contract.sol                       # Fast pattern-only scan
  %(prog)s deep contract.sol                        # Full pipeline (Z3 + EVM + LLM)
  %(prog)s scan contracts/ --recursive              # Scan entire directory

  %(prog)s project ./my-defi-project                # Scan full Foundry/Hardhat project
  %(prog)s project ./project -m deep -f markdown    # Deep scan + Markdown report
  %(prog)s project ./project --include-tests        # Include test files
  %(prog)s project ./project --include-deps         # Scan dependencies too

  %(prog)s info ./my-project                        # Project stats (no scan)
  %(prog)s graph ./my-project -o deps.json          # Dependency graph
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="الأمر المطلوب")

    # ═══ scan ═══
    scan_parser = subparsers.add_parser("scan", help="فحص قياسي — Standard scan")
    scan_parser.add_argument("target", help="مسار ملف .sol أو مجلد")
    scan_parser.add_argument("-r", "--recursive", action="store_true", help="فحص المجلدات الفرعية")
    scan_parser.add_argument("-f", "--format", choices=["text", "json", "markdown"], default="text", help="تنسيق الإخراج")
    scan_parser.add_argument("-o", "--output", help="حفظ النتيجة في ملف")

    # ═══ quick ═══
    quick_parser = subparsers.add_parser("quick", help="فحص سريع — Pattern-only scan")
    quick_parser.add_argument("target", help="مسار ملف .sol")
    quick_parser.add_argument("-f", "--format", choices=["text", "json", "markdown"], default="text")
    quick_parser.add_argument("-o", "--output", help="حفظ النتيجة في ملف")

    # ═══ deep ═══
    deep_parser = subparsers.add_parser("deep", help="فحص عميق — Full pipeline (Z3 + EVM + LLM)")
    deep_parser.add_argument("target", help="مسار ملف .sol أو مجلد")
    deep_parser.add_argument("-f", "--format", choices=["text", "json", "markdown"], default="text")
    deep_parser.add_argument("-o", "--output", help="حفظ النتيجة في ملف")

    # ═══ project ═══
    proj_parser = subparsers.add_parser("project", help="فحص مشروع كامل — Foundry/Hardhat/Truffle")
    proj_parser.add_argument("target", help="مسار المجلد الجذري للمشروع")
    proj_parser.add_argument("-m", "--mode", choices=["quick", "scan", "deep"], default="scan",
                             help="وضع الفحص (default: scan)")
    proj_parser.add_argument("-f", "--format", choices=["text", "json", "markdown"], default="text")
    proj_parser.add_argument("-o", "--output", help="حفظ النتيجة في ملف")
    proj_parser.add_argument("--include-tests", action="store_true", help="فحص ملفات الاختبار أيضاً")
    proj_parser.add_argument("--include-deps", action="store_true", help="فحص المكتبات المثبتة")
    proj_parser.add_argument("--include-mocks", action="store_true", help="فحص ملفات المحاكاة")

    # ═══ info ═══
    info_parser = subparsers.add_parser("info", help="معلومات المشروع — إحصائيات وبنية بدون فحص")
    info_parser.add_argument("target", help="مسار المجلد الجذري للمشروع")

    # ═══ graph ═══
    graph_parser = subparsers.add_parser("graph", help="شجرة التبعيات — Dependency graph")
    graph_parser.add_argument("target", help="مسار المجلد الجذري للمشروع")
    graph_parser.add_argument("-o", "--output", help="حفظ في ملف JSON")

    # ═══ version ═══
    parser.add_argument("--version", action="version", version="AGL Security 1.1.0")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # ═══ تهيئة المحركات ═══
    from agl_security_tool import AGLSecurityAudit, ProjectScanner

    print("🛡️ AGL Security Auditor v1.1.0")
    print("=" * 50)

    result = None

    # ═══ أوامر المشروع الكاملة ═══
    if args.command == "project":
        print(f"📁 Project scan: {args.target} (mode={args.mode})")
        config = {
            "exclude_tests": not getattr(args, "include_tests", False),
            "exclude_mocks": not getattr(args, "include_mocks", False),
            "scan_dependencies": getattr(args, "include_deps", False),
        }
        scanner = ProjectScanner(args.target, config=config)
        scanner.discover()

        # طباعة معلومات المشروع
        info = scanner.project_info
        print(f"  Type: {info.project_type}")
        print(f"  Contracts dir: {info.contracts_dir}")
        print(f"  Files found: {info.total_sol_files}")
        print(f"  Contracts: {info.total_contracts}")
        if info.remappings:
            print(f"  Remappings: {len(info.remappings)}")
        print()

        mode = getattr(args, "mode", "scan")
        output_format = getattr(args, "format", "text")

        if mode == "deep":
            result = scanner.deep_scan(output_format=output_format)
        elif mode == "quick":
            result = scanner.quick_scan(output_format=output_format)
        else:
            result = scanner.full_scan(output_format=output_format)

        # استخراج التقرير
        report_text = (
            result.get("report_text") or
            result.get("report_markdown") or
            result.get("report_json") or
            ""
        )

        if report_text:
            if getattr(args, "output", None):
                _save_report(args.output, report_text)
            else:
                print(report_text)
        else:
            # Fallback: JSON dump
            import json as _json
            out = _json.dumps(result, indent=2, ensure_ascii=False, default=str)
            if getattr(args, "output", None):
                _save_report(args.output, out)
            else:
                print(out)

    elif args.command == "info":
        print(f"📊 Project info: {args.target}")
        scanner = ProjectScanner(args.target)
        scanner.discover()
        stats = scanner.get_project_stats()
        import json as _json
        print(_json.dumps(stats, indent=2, ensure_ascii=False))
        sys.exit(0)

    elif args.command == "graph":
        print(f"🔗 Dependency graph: {args.target}")
        scanner = ProjectScanner(args.target)
        scanner.discover()
        graph = scanner.get_dependency_graph()
        import json as _json
        out = _json.dumps(graph, indent=2, ensure_ascii=False)
        if getattr(args, "output", None):
            _save_report(args.output, out)
            print(f"📊 Nodes: {len(graph['nodes'])}, Edges: {len(graph['edges'])}")
        else:
            print(out)
        sys.exit(0)

    else:
        # ═══ أوامر الملف الواحد ═══
        audit = AGLSecurityAudit()

        if args.command == "scan":
            print(f"📂 Scanning: {args.target}")
            result = audit.scan(args.target, recursive=getattr(args, "recursive", False))
        elif args.command == "quick":
            print(f"⚡ Quick scan: {args.target}")
            result = audit.quick_scan(args.target)
        elif args.command == "deep":
            print(f"🔬 Deep scan: {args.target}")
            result = audit.deep_scan(args.target)
        else:
            parser.print_help()
            sys.exit(1)

        # ═══ إخراج النتائج ═══
        output_format = getattr(args, "format", "text")
        report_text = audit.generate_report(result, format=output_format)

        if getattr(args, "output", None):
            _save_report(args.output, report_text)
        else:
            print(report_text)

    # ═══ Exit code based on severity ═══
    if result:
        summary = result.get("severity_summary", {})
        if summary.get("CRITICAL", 0) > 0:
            sys.exit(2)  # CRITICAL findings
        elif summary.get("HIGH", 0) > 0:
            sys.exit(1)  # HIGH findings

    sys.exit(0)


def _save_report(output_path: str, content: str):
    """حفظ التقرير في ملف."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n💾 Report saved to: {path}")


if __name__ == "__main__":
    main()
