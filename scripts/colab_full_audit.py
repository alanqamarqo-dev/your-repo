#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════
🛡️ AGL Security Tool — Cloud Bounty Audit Runner
أداة AGL للتدقيق الأمني — مُشغّل المكافآت السحابي

يعمل على Google Colab / GitHub Codespaces / أي خادم سحابي
Works on Google Colab / GitHub Codespaces / any cloud server

Usage (Colab):
    !python scripts/colab_full_audit.py --target <repo_or_dir> [--mode deep]

Usage (Local):
    python scripts/colab_full_audit.py --target ./my-project --mode deep

═══════════════════════════════════════════════════════════════════════
"""

import subprocess
import sys
import os
import json
import time
import argparse
import shutil
from pathlib import Path
from datetime import datetime


# ─── Configuration ────────────────────────────────────────────────
BOUNTY_PLATFORMS = {
    "immunefi": "https://immunefi.com/explore/",
    "code4rena": "https://code4rena.com/contests",
    "sherlock": "https://audits.sherlock.xyz/contests",
    "hats": "https://hats.finance/",
    "cantina": "https://cantina.xyz/",
}

# Popular targets for practice
PRACTICE_TARGETS = {
    "damn-vulnerable-defi": "https://github.com/tinchoabbate/damn-vulnerable-defi",
    "ethernaut": "https://github.com/OpenZeppelin/ethernaut",
    "capture-the-ether": "https://github.com/cmichel/capture-the-ether-solutions",
}


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║   🛡️  AGL Security Tool — Full Power Cloud Audit           ║
║   أداة AGL للتدقيق الأمني — فحص سحابي بالقوة الكاملة         ║
║                                                              ║
║   12 Analysis Layers | 22 Detectors | External Tools         ║
║   Z3 + Slither + Semgrep + Mythril + Attack Simulation       ║
╚══════════════════════════════════════════════════════════════╝
""")


def check_and_install_dependencies():
    """تثبيت جميع الاعتمادات — Install all dependencies."""
    print("\n📦 [1/4] Installing dependencies / تثبيت الاعتمادات...")

    # Python packages
    packages = [
        "z3-solver",
        "requests",
        "slither-analyzer",
        "semgrep",
        "solc-select",
        "pytest",
    ]

    for pkg in packages:
        print(f"  📥 {pkg}...", end=" ", flush=True)
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", pkg, "-q"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("✅")
        else:
            print(f"⚠️ (may still work)")

    # Install solc
    print("  📥 solc 0.8.19...", end=" ", flush=True)
    subprocess.run(["solc-select", "install", "0.8.19"], capture_output=True)
    subprocess.run(["solc-select", "use", "0.8.19"], capture_output=True)
    print("✅")

    # Optional: Mythril (heavy, skip if fails)
    print("  📥 mythril (optional, heavy)...", end=" ", flush=True)
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "mythril", "-q"],
        capture_output=True, text=True, timeout=300
    )
    if result.returncode == 0:
        print("✅")
    else:
        print("⚠️ skipped (tool works without it)")

    print("  ✅ All dependencies ready / جميع الاعتمادات جاهزة\n")


def verify_tools():
    """التحقق من الأدوات — Verify all tools are available."""
    print("🔧 [2/4] Verifying tools / التحقق من الأدوات...")
    tools = {
        "solc": ["solc", "--version"],
        "slither": ["slither", "--version"],
        "semgrep": ["semgrep", "--version"],
        "myth": ["myth", "version"],
        "z3": [sys.executable, "-c", "import z3; print(f'z3 {z3.get_version_string()}')"],
    }
    available = {}
    for name, cmd in tools.items():
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            ver = result.stdout.strip().split('\n')[0][:60]
            available[name] = True
            print(f"  ✅ {name}: {ver}")
        except Exception:
            available[name] = False
            print(f"  ⚠️ {name}: not available (optional)")

    print(f"\n  🔧 {sum(available.values())}/{len(available)} tools ready\n")
    return available


def clone_target(target: str, work_dir: str) -> str:
    """
    استنساخ الهدف — Clone or copy the target project.
    Handles: git URLs, local paths, GitHub shorthand (owner/repo)
    """
    print(f"📂 [3/4] Preparing target / تحضير الهدف: {target}")

    # If it's a local directory
    if os.path.isdir(target):
        print(f"  📂 Using local directory: {target}")
        return os.path.abspath(target)

    # If it's a local .sol file
    if os.path.isfile(target) and target.endswith('.sol'):
        print(f"  📄 Using local file: {target}")
        return os.path.abspath(target)

    # If it's a GitHub shorthand (owner/repo)
    if '/' in target and not target.startswith('http'):
        target = f"https://github.com/{target}"

    # Clone from git
    repo_name = target.rstrip('/').split('/')[-1].replace('.git', '')
    clone_path = os.path.join(work_dir, repo_name)

    if os.path.exists(clone_path):
        print(f"  ♻️ Already cloned: {clone_path}")
        return clone_path

    print(f"  🌐 Cloning {target}...")
    result = subprocess.run(
        ["git", "clone", "--depth", "1", target, clone_path],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        print(f"  ❌ Clone failed: {result.stderr[:200]}")
        sys.exit(1)

    print(f"  ✅ Cloned to {clone_path}")
    return clone_path


def find_solidity_files(project_path: str) -> list:
    """البحث عن ملفات Solidity — Find all .sol files in project."""
    sol_files = []
    exclude_dirs = {'node_modules', '.git', 'lib', 'forge-std', 'openzeppelin',
                    'test', 'tests', 'mock', 'mocks', 'script', 'scripts'}

    for root, dirs, files in os.walk(project_path):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d.lower() not in exclude_dirs]
        for f in files:
            if f.endswith('.sol') and not f.startswith('.'):
                sol_files.append(os.path.join(root, f))

    return sol_files


def run_full_audit(target_path: str, mode: str = "deep", output_dir: str = "audit_reports"):
    """
    تشغيل الفحص الكامل — Run the full audit with all 12 layers.
    """
    print(f"\n🔍 [4/4] Running {mode.upper()} audit / بدء الفحص {'العميق' if mode == 'deep' else 'القياسي'}...")
    print(f"  Target: {target_path}")
    print(f"  Mode: {mode}")
    print(f"  Layers: ALL 12 (Z3 + Slither + Semgrep + Mythril + State + Attack + Search + Exploit)")
    print()

    # Setup paths
    script_dir = Path(__file__).parent.resolve()
    project_root = script_dir.parent
    sys.path.insert(0, str(project_root))

    from agl_security_tool import AGLSecurityAudit, __version__
    print(f"  🛡️ AGL Security Tool v{__version__} loaded")

    # Configure for maximum power
    config = {
        "skip_llm": True,           # Skip LLM (not available on free Colab)
        "mythril_timeout": 300,     # 5 min per contract for Mythril
        "generate_poc": True,       # Generate proof-of-concept code
        "suite": {
            "severity_filter": ["critical", "high", "medium", "low"],
            "confidence_threshold": 0.3,  # Lower threshold to catch more
        },
    }

    audit = AGLSecurityAudit(config)
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Determine if it's a file or project
    is_file = os.path.isfile(target_path) and target_path.endswith('.sol')
    is_project = os.path.isdir(target_path)

    all_results = []

    if is_project:
        # ── Project-level scan ──
        sol_files = find_solidity_files(target_path)
        print(f"\n  📊 Found {len(sol_files)} Solidity files (excluding tests/mocks/libs)")

        if not sol_files:
            print("  ❌ No Solidity files found!")
            return

        # First: try project-level scan
        print(f"\n  ═══════════════════════════════════════════════")
        print(f"  🔬 Phase 1: Project-level analysis / تحليل على مستوى المشروع")
        print(f"  ═══════════════════════════════════════════════")
        try:
            project_result = audit.scan_project(
                target_path,
                mode=mode,
                output_format="dict",
                exclude_tests=True,
                exclude_mocks=True,
                scan_dependencies=False,
            )
            all_results.append({
                "type": "project",
                "target": target_path,
                "result": project_result,
            })
            _print_findings_summary(project_result, "Project Scan")
        except Exception as e:
            print(f"  ⚠️ Project scan error: {e}")

        # Then: scan critical files individually for deeper analysis
        print(f"\n  ═══════════════════════════════════════════════")
        print(f"  🔬 Phase 2: Individual file deep scan / فحص عميق لكل ملف")
        print(f"  ═══════════════════════════════════════════════")

        for i, sol_file in enumerate(sol_files, 1):
            rel_path = os.path.relpath(sol_file, target_path)
            print(f"\n  [{i}/{len(sol_files)}] 📄 {rel_path}")

            try:
                t0 = time.time()
                if mode == "deep":
                    result = audit.deep_scan(sol_file)
                else:
                    result = audit.scan(sol_file)
                duration = time.time() - t0

                findings_count = result.get("total_findings", len(result.get("findings", [])))
                critical = result.get("severity_summary", {}).get("CRITICAL", 0)
                high = result.get("severity_summary", {}).get("HIGH", 0)

                all_results.append({
                    "type": "file",
                    "target": rel_path,
                    "result": result,
                })

                icon = "🔴" if critical > 0 else "🟠" if high > 0 else "✅"
                print(f"    {icon} {findings_count} findings | "
                      f"C:{critical} H:{high} | "
                      f"{duration:.1f}s | "
                      f"Layers: {len(result.get('layers_used', []))}")

                # Print critical/high findings immediately
                for f in result.get("all_findings_unified", result.get("findings", [])):
                    sev = f.get("severity", "").upper()
                    if sev in ["CRITICAL", "HIGH"]:
                        title = f.get("title", f.get("text", ""))[:80]
                        line = f.get("line", "?")
                        conf = f.get("confidence", 0)
                        print(f"      🚨 [{sev}] L{line}: {title} (conf: {conf:.0%})")

            except Exception as e:
                print(f"    ⚠️ Error: {str(e)[:100]}")
                all_results.append({
                    "type": "file",
                    "target": rel_path,
                    "error": str(e),
                })

    elif is_file:
        # ── Single file scan ──
        print(f"\n  🔬 Deep scanning single file: {target_path}")
        try:
            t0 = time.time()
            if mode == "deep":
                result = audit.deep_scan(target_path)
            else:
                result = audit.scan(target_path)
            duration = time.time() - t0

            all_results.append({
                "type": "file",
                "target": target_path,
                "result": result,
            })

            _print_findings_summary(result, os.path.basename(target_path))
        except Exception as e:
            print(f"  ❌ Scan error: {e}")
            return

    # ── Generate reports ──
    print(f"\n{'='*70}")
    print(f"📝 Generating reports / إنشاء التقارير...")
    print(f"{'='*70}")

    # JSON report
    json_path = os.path.join(output_dir, f"audit_{timestamp}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)
    print(f"  📄 JSON: {json_path}")

    # Markdown report (bounty-ready)
    md_path = os.path.join(output_dir, f"audit_{timestamp}.md")
    _generate_bounty_report(all_results, md_path, target_path, mode)
    print(f"  📝 Markdown: {md_path}")

    # Summary report
    _print_final_summary(all_results, target_path)

    return all_results


def _print_findings_summary(result: dict, label: str):
    """طباعة ملخص النتائج — Print findings summary."""
    summary = result.get("severity_summary", {})
    total = result.get("total_findings", 0)
    layers = result.get("layers_used", [])

    print(f"\n    📊 {label}: {total} findings")
    print(f"    🔴 CRITICAL: {summary.get('CRITICAL', 0)} | "
          f"🟠 HIGH: {summary.get('HIGH', 0)} | "
          f"🟡 MEDIUM: {summary.get('MEDIUM', 0)} | "
          f"🔵 LOW: {summary.get('LOW', 0)}")
    print(f"    🔧 Layers used: {len(layers)} — {', '.join(layers[:6])}")


def _print_final_summary(all_results: list, target_path: str):
    """الملخص النهائي — Final summary."""
    total_findings = 0
    total_critical = 0
    total_high = 0
    files_scanned = 0
    errors = 0

    for r in all_results:
        if "error" in r:
            errors += 1
            continue
        result = r.get("result", {})
        total_findings += result.get("total_findings", 0)
        summary = result.get("severity_summary", {})
        total_critical += summary.get("CRITICAL", 0)
        total_high += summary.get("HIGH", 0)
        if r["type"] == "file":
            files_scanned += 1

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    📊 AUDIT COMPLETE / اكتمل الفحص          ║
╠══════════════════════════════════════════════════════════════╣
║  Target:     {target_path[:48]:48s} ║
║  Files:      {files_scanned:<48d} ║
║  Findings:   {total_findings:<48d} ║
║  🔴 CRITICAL: {total_critical:<47d} ║
║  🟠 HIGH:     {total_high:<47d} ║
║  Errors:     {errors:<48d} ║
╠══════════════════════════════════════════════════════════════╣
║  Reports: audit_reports/                                     ║
╚══════════════════════════════════════════════════════════════╝
""")

    if total_critical > 0 or total_high > 0:
        print("🎯 BOUNTY POTENTIAL: Found critical/high issues!")
        print("   Next steps / الخطوات التالية:")
        print("   1. Review the Markdown report / راجع التقرير")
        print("   2. Validate findings manually / تحقق يدوياً")
        print("   3. Write PoC exploit / اكتب إثبات مفهوم")
        print("   4. Submit to bounty platform / أرسل للمنصة")
        print(f"\n   Platforms / المنصات:")
        for name, url in BOUNTY_PLATFORMS.items():
            print(f"     🔗 {name}: {url}")


def _generate_bounty_report(all_results: list, output_path: str,
                             target_path: str, mode: str):
    """
    إنشاء تقرير احترافي جاهز للإرسال كـ Bug Bounty
    Generate professional bounty-ready report.
    """
    lines = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

    lines.append("# 🛡️ Security Audit Report — AGL Security Tool\n")
    lines.append(f"**Target:** `{target_path}`  ")
    lines.append(f"**Date:** {timestamp}  ")
    lines.append(f"**Mode:** {mode.upper()} (All 12 Analysis Layers)  ")
    lines.append(f"**Tool:** AGL Security Tool v1.1.0\n")

    lines.append("## Executive Summary\n")

    # Collect all findings
    all_findings = []
    for r in all_results:
        result = r.get("result", {})
        target = r.get("target", "?")
        for f in result.get("all_findings_unified", result.get("findings", [])):
            f["_source_file"] = target
            all_findings.append(f)

    # Deduplicate by title+line
    seen = set()
    unique_findings = []
    for f in all_findings:
        key = (f.get("title", ""), f.get("line", 0), f.get("_source_file", ""))
        if key not in seen:
            seen.add(key)
            unique_findings.append(f)

    # Count by severity
    by_sev = {"CRITICAL": [], "HIGH": [], "MEDIUM": [], "LOW": []}
    for f in unique_findings:
        sev = f.get("severity", "LOW").upper()
        if sev in by_sev:
            by_sev[sev].append(f)

    total = len(unique_findings)
    lines.append(f"Total unique findings: **{total}**\n")
    lines.append(f"| Severity | Count |")
    lines.append(f"|----------|-------|")
    lines.append(f"| 🔴 CRITICAL | **{len(by_sev['CRITICAL'])}** |")
    lines.append(f"| 🟠 HIGH | **{len(by_sev['HIGH'])}** |")
    lines.append(f"| 🟡 MEDIUM | **{len(by_sev['MEDIUM'])}** |")
    lines.append(f"| 🔵 LOW | **{len(by_sev['LOW'])}** |")
    lines.append("")

    # Analysis layers used
    used_layers = set()
    for r in all_results:
        result = r.get("result", {})
        used_layers.update(result.get("layers_used", []))

    lines.append("## Analysis Methodology\n")
    lines.append("This audit was performed using AGL Security Tool's 12-layer pipeline:\n")
    for layer in sorted(used_layers):
        lines.append(f"- ✅ {layer}")
    lines.append("")

    # Detailed findings by severity
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        findings = by_sev[sev]
        if not findings:
            continue

        sev_icons = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵"}
        lines.append(f"\n## {sev_icons[sev]} {sev} Findings ({len(findings)})\n")

        for i, f in enumerate(findings, 1):
            title = f.get("title", f.get("text", "Unknown"))
            desc = f.get("description", "")
            line_num = f.get("line", "?")
            source_file = f.get("_source_file", "?")
            category = f.get("category", "")
            confidence = f.get("confidence", 0)
            confirmed_by = f.get("confirmed_by", [])
            proven = f.get("mathematically_proven", False)
            fix = f.get("fix", "")
            poc = f.get("poc", "")

            lines.append(f"### {sev[0]}-{i:02d}: {title}\n")
            lines.append(f"**File:** `{source_file}` | **Line:** {line_num} | "
                        f"**Category:** {category} | **Confidence:** {confidence:.0%}")
            if confirmed_by:
                lines.append(f"**Confirmed by:** {', '.join(confirmed_by)}")
            if proven:
                lines.append(f"**⚡ Mathematically proven by Z3 SMT solver**")
            lines.append(f"\n**Description:**\n{desc}\n")

            if fix:
                lines.append("**Recommended Fix:**")
                lines.append(f"```solidity\n{fix}\n```\n")

            if poc:
                lines.append("**Proof of Concept:**")
                lines.append(f"```solidity\n{poc}\n```\n")

            lines.append("---\n")

    # Appendix
    lines.append("\n## Appendix\n")
    lines.append(f"- **Files scanned:** {sum(1 for r in all_results if r['type'] == 'file')}")
    lines.append(f"- **Errors:** {sum(1 for r in all_results if 'error' in r)}")
    lines.append(f"- **External tools:** Slither, Semgrep, Z3" +
                (" + Mythril" if shutil.which("myth") else ""))
    lines.append(f"- **Internal detectors:** 22 (reentrancy×4, access×4, defi×5, common×6, token×3)")
    lines.append("\n---\n*Generated by AGL Security Tool v1.1.0*")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ─── Main ────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="🛡️ AGL Security Tool — Cloud Bounty Audit Runner"
    )
    parser.add_argument(
        "--target", "-t",
        required=True,
        help="Target: local path, git URL, or GitHub owner/repo"
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["scan", "quick", "deep"],
        default="deep",
        help="Scan mode: quick (fast), scan (standard), deep (all layers)"
    )
    parser.add_argument(
        "--output", "-o",
        default="audit_reports",
        help="Output directory for reports"
    )
    parser.add_argument(
        "--skip-install",
        action="store_true",
        help="Skip dependency installation"
    )
    parser.add_argument(
        "--work-dir",
        default="/tmp/agl_audit" if os.name != 'nt' else os.path.join(os.environ.get('TEMP', '.'), 'agl_audit'),
        help="Working directory for cloned repos"
    )

    args = parser.parse_args()

    print_banner()

    # Step 1: Install dependencies
    if not args.skip_install:
        check_and_install_dependencies()

    # Step 2: Verify tools
    verify_tools()

    # Step 3: Prepare target
    os.makedirs(args.work_dir, exist_ok=True)
    target_path = clone_target(args.target, args.work_dir)

    # Step 4: Run audit
    run_full_audit(target_path, mode=args.mode, output_dir=args.output)


if __name__ == "__main__":
    main()
