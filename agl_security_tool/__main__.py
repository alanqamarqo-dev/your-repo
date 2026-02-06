#!/usr/bin/env python3
"""
AGL Security — نقطة الدخول عبر سطر الأوامر
Command-Line Interface for AGL Smart Contract Security Auditor

Usage:
    python -m agl_security_tool scan contract.sol
    python -m agl_security_tool scan contracts/ --recursive
    python -m agl_security_tool quick contract.sol
    python -m agl_security_tool deep contract.sol
    python -m agl_security_tool scan contract.sol --format markdown --output report.md
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
  %(prog)s scan contract.sol                    # Standard scan
  %(prog)s quick contract.sol                   # Fast pattern-only scan
  %(prog)s deep contract.sol                    # Full pipeline (Z3 + EVM + LLM)
  %(prog)s scan contracts/ --recursive          # Scan entire directory
  %(prog)s scan contract.sol -f markdown -o report.md
  %(prog)s scan contract.sol -f json -o result.json
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

    # ═══ version ═══
    parser.add_argument("--version", action="version", version="AGL Security 1.0.0")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # ═══ تهيئة المحرك ═══
    from agl_security_tool import AGLSecurityAudit

    print("🛡️ AGL Security Auditor v1.0.0")
    print("=" * 50)

    audit = AGLSecurityAudit()

    # ═══ تنفيذ الأمر ═══
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
    report = audit.generate_report(result, format=output_format)

    if getattr(args, "output", None):
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n💾 Report saved to: {output_path}")
    else:
        print(report)

    # ═══ Exit code based on severity ═══
    summary = result.get("severity_summary", {})
    if summary.get("CRITICAL", 0) > 0:
        sys.exit(2)  # CRITICAL findings
    elif summary.get("HIGH", 0) > 0:
        sys.exit(1)  # HIGH findings
    else:
        sys.exit(0)  # Clean


if __name__ == "__main__":
    main()
