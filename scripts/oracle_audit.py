#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════
🛡️ AGL Security Tool — Oracle Cloud Audit Runner (24GB RAM)
أداة AGL للتدقيق الأمني — مُشغّل أوراكل السحابي (24 جيجا رام)

مُحسّن لخوادم أوراكل ذات الذاكرة الكبيرة — يشغّل كل الطبقات بلا قيود
Optimized for Oracle Cloud high-memory servers — runs ALL layers unrestricted

Usage:
    python3 scripts/oracle_audit.py <target> [options]

Examples:
    # Scan a GitHub repo (deep mode — all 12 layers)
    python3 scripts/oracle_audit.py https://github.com/owner/defi-protocol

    # Scan with GitHub shorthand
    python3 scripts/oracle_audit.py tinchoabbate/damn-vulnerable-defi

    # Scan a local file
    python3 scripts/oracle_audit.py /path/to/contract.sol

    # Scan a local project folder
    python3 scripts/oracle_audit.py /path/to/project/

    # Quick scan (fast, patterns only)
    python3 scripts/oracle_audit.py <target> --mode quick

    # Standard scan
    python3 scripts/oracle_audit.py <target> --mode scan

    # Scan specific solc version
    python3 scripts/oracle_audit.py <target> --solc 0.8.24

═══════════════════════════════════════════════════════════════════════
"""

import subprocess
import sys
import os
import json
import time
import argparse
import shutil
import resource
import traceback
from pathlib import Path
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed


# ─── Constants ────────────────────────────────────────────────────
BOUNTY_PLATFORMS = {
    "immunefi":  "https://immunefi.com/explore/",
    "code4rena": "https://code4rena.com/contests",
    "sherlock":  "https://audits.sherlock.xyz/contests",
    "hats":      "https://hats.finance/",
    "cantina":   "https://cantina.xyz/",
}

# Directories to skip when scanning projects
EXCLUDE_DIRS = {
    'node_modules', '.git', 'lib', 'forge-std', 'openzeppelin',
    '@openzeppelin', 'test', 'tests', 'mock', 'mocks', 'script',
    'scripts', 'deploy', 'migrations', '.deps', 'artifacts',
    'cache', 'out', 'build', 'typechain', 'typechain-types',
}


def print_banner():
    mem = _get_memory_gb()
    cpus = os.cpu_count() or 1
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║   🛡️  AGL Security Tool — Oracle Cloud Full Power Audit        ║
║   أداة AGL للتدقيق الأمني — فحص بالقوة الكاملة على أوراكل       ║
║                                                                  ║
║   💾 RAM: {mem:.1f} GB  |  🖥 CPUs: {cpus}  |  12 Layers  |  22 Detectors  ║
║   Z3 + Slither + Semgrep + Mythril + State + Attack + Search    ║
╚══════════════════════════════════════════════════════════════════╝
""")


def _get_memory_gb() -> float:
    """Get total system memory in GB."""
    try:
        with open('/proc/meminfo') as f:
            for line in f:
                if line.startswith('MemTotal:'):
                    return int(line.split()[1]) / (1024 * 1024)
    except:
        pass
    return 0.0


def _get_available_memory_gb() -> float:
    """Get available system memory in GB."""
    try:
        with open('/proc/meminfo') as f:
            for line in f:
                if line.startswith('MemAvailable:'):
                    return int(line.split()[1]) / (1024 * 1024)
    except:
        pass
    return 0.0


def verify_tools() -> dict:
    """التحقق من الأدوات — Verify all tools are available."""
    print("🔧 Verifying tools / التحقق من الأدوات...")
    tools = {
        "solc":    ["solc", "--version"],
        "slither": ["slither", "--version"],
        "semgrep": ["semgrep", "--version"],
        "myth":    ["myth", "version"],
        "z3":      [sys.executable, "-c", "import z3; print(f'z3 {z3.get_version_string()}')"],
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

    print(f"  🔧 {sum(available.values())}/{len(available)} tools ready\n")
    return available


def prepare_target(target: str, work_dir: str) -> str:
    """
    تحضير الهدف — Prepare the target (clone if needed).
    """
    print(f"📂 Preparing target / تحضير الهدف: {target}")

    if os.path.isdir(target):
        print(f"  📂 Local directory: {os.path.abspath(target)}")
        return os.path.abspath(target)

    if os.path.isfile(target) and target.endswith('.sol'):
        print(f"  📄 Local file: {os.path.abspath(target)}")
        return os.path.abspath(target)

    # GitHub shorthand → full URL
    if '/' in target and not target.startswith('http'):
        target = f"https://github.com/{target}"

    repo_name = target.rstrip('/').split('/')[-1].replace('.git', '')
    clone_path = os.path.join(work_dir, repo_name)

    if os.path.exists(clone_path):
        print(f"  ♻️ Already cloned: {clone_path}")
        return clone_path

    print(f"  🌐 Cloning {target}...")
    result = subprocess.run(
        ["git", "clone", "--depth", "1", target, clone_path],
        capture_output=True, text=True, timeout=300
    )
    if result.returncode != 0:
        print(f"  ❌ Clone failed: {result.stderr[:300]}")
        sys.exit(1)

    # Install npm deps if package.json exists (for Hardhat projects)
    pkg_json = os.path.join(clone_path, "package.json")
    if os.path.exists(pkg_json):
        print(f"  📦 Installing npm deps...")
        subprocess.run(["npm", "install"], cwd=clone_path,
                       capture_output=True, timeout=120)

    print(f"  ✅ Target ready: {clone_path}")
    return clone_path


def find_solidity_files(project_path: str, scan_deps: bool = False) -> list:
    """البحث عن ملفات Solidity."""
    sol_files = []
    for root, dirs, files in os.walk(project_path):
        if not scan_deps:
            dirs[:] = [d for d in dirs if d.lower() not in EXCLUDE_DIRS]
        for f in files:
            if f.endswith('.sol') and not f.startswith('.'):
                full = os.path.join(root, f)
                sol_files.append(full)
    return sorted(sol_files)


def set_solc_version(version: str):
    """تعيين إصدار solc."""
    print(f"  ⚙️ Setting solc to {version}...")
    subprocess.run(["solc-select", "install", version], capture_output=True)
    subprocess.run(["solc-select", "use", version], capture_output=True)


def detect_solc_version(sol_files: list) -> str:
    """كشف إصدار solc من pragma."""
    for f in sol_files[:5]:
        try:
            with open(f) as fh:
                for line in fh:
                    if 'pragma solidity' in line:
                        # Extract version like ^0.8.19 or >=0.8.0
                        import re
                        m = re.search(r'(\d+\.\d+\.\d+)', line)
                        if m:
                            return m.group(1)
        except:
            pass
    return "0.8.19"


def scan_single_file(args_tuple):
    """
    فحص ملف واحد في عملية منفصلة (للتوازي).
    Worker function for parallel scanning.
    """
    sol_file, project_root, mode, config = args_tuple
    rel_path = os.path.relpath(sol_file, project_root)

    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))
        from agl_security_tool import AGLSecurityAudit

        audit = AGLSecurityAudit(config)
        t0 = time.time()

        if mode == "deep":
            result = audit.deep_scan(sol_file)
        elif mode == "quick":
            result = audit.quick_scan(sol_file)
        else:
            result = audit.scan(sol_file)

        duration = time.time() - t0
        return {
            "file": rel_path,
            "status": "success",
            "result": result,
            "duration": round(duration, 1),
        }

    except Exception as e:
        return {
            "file": rel_path,
            "status": "error",
            "error": str(e)[:500],
            "duration": 0,
        }


def run_audit(target_path: str, mode: str = "deep", output_dir: str = "audit_reports",
              parallel: int = 1, solc_ver: str = None, scan_deps: bool = False):
    """
    تشغيل الفحص الكامل بالقوة الكاملة — Run full audit at maximum power.
    Optimized for 24GB RAM Oracle Cloud instances.
    """
    t0_global = time.time()

    # Setup
    script_dir = Path(__file__).parent.resolve()
    project_root = script_dir.parent
    sys.path.insert(0, str(project_root))

    from agl_security_tool import AGLSecurityAudit, __version__
    from agl_security_tool.detectors import DetectorRunner

    dr = DetectorRunner()
    print(f"  🛡️ AGL Security Tool v{__version__} | {len(dr.detectors)} detectors")

    # Oracle Cloud optimized config — no memory limits!
    config = {
        "skip_llm": True,
        "mythril_timeout": 600,      # 10 min per contract (24GB can handle it)
        "generate_poc": True,
        "suite": {
            "severity_filter": ["critical", "high", "medium", "low"],
            "confidence_threshold": 0.3,
        },
    }

    audit = AGLSecurityAudit(config)
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    is_file = os.path.isfile(target_path) and target_path.endswith('.sol')
    is_project = os.path.isdir(target_path)

    all_results = []

    if is_file:
        # ── Single file ──
        print(f"\n  🔬 Deep scanning: {target_path}")
        try:
            if mode == "deep":
                result = audit.deep_scan(target_path)
            elif mode == "quick":
                result = audit.quick_scan(target_path)
            else:
                result = audit.scan(target_path)

            all_results.append({"type": "file", "target": target_path, "result": result})
            _print_result(result, os.path.basename(target_path))

        except Exception as e:
            print(f"  ❌ Error: {e}")
            traceback.print_exc()

    elif is_project:
        # ── Project ──
        sol_files = find_solidity_files(target_path, scan_deps=scan_deps)
        print(f"\n  📊 Found {len(sol_files)} Solidity files")

        if not sol_files:
            print("  ❌ No .sol files found! Check the path.")
            return

        # Detect & set solc version
        if solc_ver:
            set_solc_version(solc_ver)
        else:
            detected = detect_solc_version(sol_files)
            print(f"  ⚙️ Auto-detected solc: {detected}")
            set_solc_version(detected)

        # Phase 1: Project-level scan
        print(f"\n{'═'*65}")
        print(f"  🔬 Phase 1: Project-level analysis / تحليل على مستوى المشروع")
        print(f"{'═'*65}")
        try:
            project_result = audit.scan_project(
                target_path, mode=mode, output_format="dict",
                exclude_tests=True, exclude_mocks=True,
                scan_dependencies=scan_deps,
            )
            all_results.append({
                "type": "project", "target": target_path, "result": project_result
            })
            _print_result(project_result, "PROJECT SCAN")
        except Exception as e:
            print(f"  ⚠️ Project scan error: {e}")

        # Phase 2: Individual file scans
        print(f"\n{'═'*65}")
        print(f"  🔬 Phase 2: Individual file deep scan ({len(sol_files)} files)")
        print(f"{'═'*65}")

        avail_mem = _get_available_memory_gb()
        effective_parallel = min(parallel, max(1, int(avail_mem / 4)))  # ~4GB per worker

        if effective_parallel > 1 and len(sol_files) > 2:
            print(f"  ⚡ Parallel scanning with {effective_parallel} workers "
                  f"({avail_mem:.1f}GB available)")
            _scan_parallel(sol_files, target_path, mode, config,
                          effective_parallel, all_results)
        else:
            _scan_sequential(sol_files, target_path, mode, audit, all_results)

    # ── Generate reports ──
    total_duration = time.time() - t0_global

    print(f"\n{'═'*65}")
    print(f"📝 Generating reports / إنشاء التقارير...")
    print(f"{'═'*65}")

    # JSON report
    json_path = os.path.join(output_dir, f"audit_{timestamp}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "meta": {
                "target": target_path,
                "mode": mode,
                "timestamp": timestamp,
                "duration_seconds": round(total_duration, 1),
                "ram_gb": _get_memory_gb(),
                "cpus": os.cpu_count(),
            },
            "results": all_results,
        }, f, indent=2, ensure_ascii=False, default=str)
    print(f"  📄 JSON: {json_path}")

    # Markdown bounty report
    md_path = os.path.join(output_dir, f"audit_{timestamp}.md")
    _generate_bounty_report(all_results, md_path, target_path, mode, total_duration)
    print(f"  📝 Markdown: {md_path}")

    # SARIF report (for GitHub integration)
    sarif_path = os.path.join(output_dir, f"audit_{timestamp}.sarif")
    _generate_sarif(all_results, sarif_path, target_path)
    print(f"  🔗 SARIF: {sarif_path}")

    # Final summary
    _print_final_summary(all_results, target_path, total_duration)

    return all_results


def _scan_sequential(sol_files, target_path, mode, audit, all_results):
    """فحص تسلسلي — Sequential scan."""
    for i, sol_file in enumerate(sol_files, 1):
        rel = os.path.relpath(sol_file, target_path)
        print(f"\n  [{i}/{len(sol_files)}] 📄 {rel}")

        try:
            t0 = time.time()
            if mode == "deep":
                result = audit.deep_scan(sol_file)
            elif mode == "quick":
                result = audit.quick_scan(sol_file)
            else:
                result = audit.scan(sol_file)
            dur = time.time() - t0

            all_results.append({"type": "file", "target": rel, "result": result})
            _print_compact_result(result, dur)

        except Exception as e:
            print(f"    ⚠️ Error: {str(e)[:120]}")
            all_results.append({"type": "file", "target": rel, "error": str(e)})


def _scan_parallel(sol_files, target_path, mode, config, workers, all_results):
    """فحص متوازي — Parallel scan."""
    tasks = [(f, target_path, mode, config) for f in sol_files]

    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(scan_single_file, t): t[0] for t in tasks}
        done = 0
        for future in as_completed(futures):
            done += 1
            r = future.result()
            rel = r["file"]
            print(f"  [{done}/{len(sol_files)}] 📄 {rel}", end="")

            if r["status"] == "success":
                result = r["result"]
                all_results.append({"type": "file", "target": rel, "result": result})
                sev = result.get("severity_summary", {})
                c, h = sev.get("CRITICAL", 0), sev.get("HIGH", 0)
                total = result.get("total_findings", 0)
                icon = "🔴" if c else "🟠" if h else "✅"
                print(f" {icon} {total} findings (C:{c} H:{h}) [{r['duration']}s]")
            else:
                print(f" ⚠️ {r.get('error', 'unknown')[:80]}")
                all_results.append({"type": "file", "target": rel, "error": r.get("error")})


def _print_result(result: dict, label: str):
    """طباعة نتيجة."""
    sev = result.get("severity_summary", {})
    total = result.get("total_findings", 0)
    layers = result.get("layers_used", [])
    t = result.get("time_seconds", 0)

    print(f"\n    📊 {label}: {total} findings in {t:.1f}s")
    print(f"    🔴 C:{sev.get('CRITICAL',0)} | 🟠 H:{sev.get('HIGH',0)} | "
          f"🟡 M:{sev.get('MEDIUM',0)} | 🔵 L:{sev.get('LOW',0)}")
    print(f"    🔧 {len(layers)} layers: {', '.join(layers[:8])}")

    # Print critical/high findings
    for f in result.get("all_findings_unified", result.get("findings", [])):
        s = f.get("severity", "").upper()
        if s in ["CRITICAL", "HIGH"]:
            title = f.get("title", f.get("text", ""))[:90]
            line = f.get("line", "?")
            conf = f.get("confidence", 0)
            proven = "⚡" if f.get("mathematically_proven") else ""
            print(f"    🚨 [{s}] L{line}: {title} ({conf:.0%}) {proven}")


def _print_compact_result(result: dict, duration: float):
    """طباعة مختصرة."""
    sev = result.get("severity_summary", {})
    c, h = sev.get("CRITICAL", 0), sev.get("HIGH", 0)
    total = result.get("total_findings", 0)
    layers = len(result.get("layers_used", []))
    icon = "🔴" if c else "🟠" if h else "✅"
    print(f"    {icon} {total} findings | C:{c} H:{h} | {layers} layers | {duration:.1f}s")

    for f in result.get("all_findings_unified", result.get("findings", [])):
        s = f.get("severity", "").upper()
        if s == "CRITICAL":
            print(f"      🚨 [{s}] L{f.get('line','?')}: "
                  f"{f.get('title', f.get('text',''))[:80]}")


def _print_final_summary(all_results: list, target_path: str, total_duration: float):
    """الملخص النهائي."""
    total_findings = 0
    total_c = total_h = total_m = total_l = 0
    files_ok = files_err = 0
    all_layers = set()

    for r in all_results:
        if "error" in r:
            files_err += 1
            continue
        result = r.get("result", {})
        total_findings += result.get("total_findings", 0)
        sev = result.get("severity_summary", {})
        total_c += sev.get("CRITICAL", 0)
        total_h += sev.get("HIGH", 0)
        total_m += sev.get("MEDIUM", 0)
        total_l += sev.get("LOW", 0)
        all_layers.update(result.get("layers_used", []))
        if r["type"] == "file":
            files_ok += 1

    bounty_worthy = total_c + total_h

    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║                   📊 AUDIT COMPLETE / اكتمل الفحص               ║
╠══════════════════════════════════════════════════════════════════╣
║  🎯 Target:      {os.path.basename(target_path)[:44]:44s}  ║
║  📄 Files:       {files_ok} scanned, {files_err} errors{' '*(34-len(str(files_ok))-len(str(files_err)))}  ║
║  🔧 Layers:      {len(all_layers)}/12{' '*44}  ║
║  ⏱️ Duration:    {total_duration:.0f}s{' '*(44-len(f'{total_duration:.0f}'))}  ║
║                                                                  ║
║  📊 FINDINGS:    {total_findings} total{' '*(39-len(str(total_findings)))}  ║
║  🔴 CRITICAL:    {total_c}{' '*(47-len(str(total_c)))}  ║
║  🟠 HIGH:        {total_h}{' '*(47-len(str(total_h)))}  ║
║  🟡 MEDIUM:      {total_m}{' '*(47-len(str(total_m)))}  ║
║  🔵 LOW:         {total_l}{' '*(47-len(str(total_l)))}  ║
║                                                                  ║
║  🎯 BOUNTY-WORTHY: {bounty_worthy} findings (CRITICAL + HIGH){' '*(18-len(str(bounty_worthy)))}  ║
╚══════════════════════════════════════════════════════════════════╝
""")

    if bounty_worthy > 0:
        print("🏆 BOUNTY POTENTIAL FOUND! / تم إيجاد ثغرات محتملة للمكافأة!")
        print("   الخطوات التالية / Next steps:")
        print("   1. راجع التقرير في audit_reports/ → Review the report")
        print("   2. تحقق يدوياً من كل ثغرة    → Validate each finding manually")
        print("   3. اكتب إثبات مفهوم (PoC)     → Write Proof-of-Concept")
        print("   4. أرسل للمنصة               → Submit to bounty platform")
        print(f"\n   📋 Bug Bounty Platforms / منصات المكافآت:")
        for name, url in BOUNTY_PLATFORMS.items():
            print(f"     🔗 {name}: {url}")
    else:
        print("✅ No critical/high issues found. The code looks relatively safe.")
        print("   Consider running with --mode deep if you haven't already.")


def _generate_bounty_report(all_results, output_path, target_path, mode, duration):
    """إنشاء تقرير احترافي جاهز لمنصات Bug Bounty."""
    lines = []
    ts = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

    lines.append("# 🛡️ Security Audit Report\n")
    lines.append(f"**Target:** `{os.path.basename(target_path)}`  ")
    lines.append(f"**Date:** {ts}  ")
    lines.append(f"**Mode:** {mode.upper()} — All 12 Analysis Layers  ")
    lines.append(f"**Tool:** AGL Security Tool v1.1.0  ")
    lines.append(f"**Duration:** {duration:.0f}s  ")
    lines.append(f"**Platform:** Oracle Cloud ({_get_memory_gb():.0f}GB RAM)\n")

    # Collect unique findings
    all_findings = []
    for r in all_results:
        result = r.get("result", {})
        target = r.get("target", "?")
        for f in result.get("all_findings_unified", result.get("findings", [])):
            f["_file"] = target
            all_findings.append(f)

    # Deduplicate
    seen = set()
    unique = []
    for f in all_findings:
        key = (f.get("title", ""), f.get("line", 0), f.get("_file", ""))
        if key not in seen:
            seen.add(key)
            unique.append(f)

    by_sev = {"CRITICAL": [], "HIGH": [], "MEDIUM": [], "LOW": []}
    for f in unique:
        s = f.get("severity", "LOW").upper()
        if s in by_sev:
            by_sev[s].append(f)

    lines.append("## Executive Summary\n")
    lines.append(f"| Severity | Count |")
    lines.append(f"|----------|-------|")
    for s in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        icons = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵"}
        lines.append(f"| {icons[s]} {s} | **{len(by_sev[s])}** |")
    lines.append(f"| **Total** | **{len(unique)}** |\n")

    # Layers used
    used_layers = set()
    for r in all_results:
        used_layers.update(r.get("result", {}).get("layers_used", []))

    lines.append("## Methodology\n")
    lines.append(f"12-layer analysis pipeline ({len(used_layers)} active):\n")
    for l in sorted(used_layers):
        lines.append(f"- ✅ {l}")
    lines.append("")

    # Detailed findings
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        findings = by_sev[sev]
        if not findings:
            continue

        icons = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵"}
        lines.append(f"\n## {icons[sev]} {sev} Findings ({len(findings)})\n")

        for i, f in enumerate(findings, 1):
            title = f.get("title", f.get("text", "Unknown"))
            desc = f.get("description", "")
            line_num = f.get("line", "?")
            src = f.get("_file", "?")
            cat = f.get("category", "")
            conf = f.get("confidence", 0)
            confirmed = f.get("confirmed_by", [])
            proven = f.get("mathematically_proven", False)
            fix = f.get("fix", "")
            poc = f.get("poc", "")

            lines.append(f"### {sev[0]}-{i:02d}: {title}\n")
            lines.append(f"| Property | Value |")
            lines.append(f"|----------|-------|")
            lines.append(f"| File | `{src}` |")
            lines.append(f"| Line | {line_num} |")
            lines.append(f"| Category | {cat} |")
            lines.append(f"| Confidence | {conf:.0%} |")
            if confirmed:
                lines.append(f"| Confirmed by | {', '.join(confirmed)} |")
            if proven:
                lines.append(f"| Z3 Proven | ⚡ Yes |")
            lines.append("")

            if desc:
                lines.append(f"**Description:**\n\n{desc}\n")
            if fix:
                lines.append(f"**Recommended Fix:**\n```solidity\n{fix}\n```\n")
            if poc:
                lines.append(f"**Proof of Concept:**\n```solidity\n{poc}\n```\n")
            lines.append("---\n")

    lines.append("\n---\n*Generated by AGL Security Tool v1.1.0 on Oracle Cloud*\n")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _generate_sarif(all_results, output_path, target_path):
    """إنشاء تقرير SARIF (قياسي لـ GitHub/Azure DevOps)."""
    sarif = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/main/sarif-2.1/schema/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {
                "driver": {
                    "name": "AGL Security Tool",
                    "version": "1.1.0",
                    "informationUri": "https://github.com/alanqamarqo-dev/your-repo",
                }
            },
            "results": []
        }]
    }

    sev_map = {"CRITICAL": "error", "HIGH": "error", "MEDIUM": "warning", "LOW": "note"}

    for r in all_results:
        result = r.get("result", {})
        src = r.get("target", "?")
        for f in result.get("all_findings_unified", result.get("findings", [])):
            sarif["runs"][0]["results"].append({
                "ruleId": f.get("category", "unknown"),
                "level": sev_map.get(f.get("severity", "").upper(), "note"),
                "message": {"text": f.get("title", f.get("text", ""))},
                "locations": [{
                    "physicalLocation": {
                        "artifactLocation": {"uri": src},
                        "region": {"startLine": f.get("line", 1)}
                    }
                }]
            })

    with open(output_path, "w") as f:
        json.dump(sarif, f, indent=2)


# ─── Main ────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="🛡️ AGL Security Tool — Oracle Cloud Full Power Audit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scripts/oracle_audit.py https://github.com/owner/protocol
  python3 scripts/oracle_audit.py tinchoabbate/damn-vulnerable-defi
  python3 scripts/oracle_audit.py ./contracts/ --mode deep --parallel 4
  python3 scripts/oracle_audit.py contract.sol --solc 0.8.24
        """
    )
    parser.add_argument("target",
        help="Git URL, GitHub shorthand (owner/repo), local dir, or .sol file")
    parser.add_argument("--mode", "-m",
        choices=["quick", "scan", "deep"], default="deep",
        help="Scan mode (default: deep — all 12 layers)")
    parser.add_argument("--output", "-o",
        default="audit_reports",
        help="Output directory (default: audit_reports/)")
    parser.add_argument("--parallel", "-p",
        type=int, default=1,
        help="Parallel workers for file scanning (default: 1, auto-limited by RAM)")
    parser.add_argument("--solc",
        default=None,
        help="Force specific solc version (e.g. 0.8.24)")
    parser.add_argument("--scan-deps",
        action="store_true",
        help="Also scan dependency files (node_modules, lib, etc.)")
    parser.add_argument("--work-dir",
        default=os.path.expanduser("~/agl-audit/targets"),
        help="Directory for cloned repos")

    args = parser.parse_args()

    print_banner()
    verify_tools()

    os.makedirs(args.work_dir, exist_ok=True)
    target_path = prepare_target(args.target, args.work_dir)

    run_audit(
        target_path,
        mode=args.mode,
        output_dir=args.output,
        parallel=args.parallel,
        solc_ver=args.solc,
        scan_deps=args.scan_deps,
    )


if __name__ == "__main__":
    main()
