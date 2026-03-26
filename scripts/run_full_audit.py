#!/usr/bin/env python3
"""
🛡️ AGL Full Pipeline Audit — فحص شامل لكل العقود
Runs the complete AGL security pipeline on all project contracts.
Works in CI, WSL, and native Linux environments.

Usage:
    python scripts/run_full_audit.py                          # Scan default contracts
    python scripts/run_full_audit.py --target contract.sol    # Scan specific file
    python scripts/run_full_audit.py --target contracts/      # Scan directory

WSL Usage:
    bash scripts/run_audit_wsl.sh                             # Auto-setup + scan
    bash scripts/run_audit_wsl.sh /path/to/contracts/         # Scan custom path
"""

import sys
import os
import json
import time
import argparse
import platform
from pathlib import Path
from datetime import datetime, timezone

# Setup paths
REPO_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(REPO_ROOT))

from agl_security_tool.core import AGLSecurityAudit
from agl_security_tool.detectors.solidity_parser import SoliditySemanticParser
from agl_security_tool.detectors import DetectorRunner
from agl_security_tool.z3_symbolic_engine import Z3SymbolicEngine
from agl_security_tool.exploit_reasoning import ExploitReasoningEngine

# ═══ Configuration ═══
SKIP_LLM = True  # No Ollama in CI — skip LLM layers

# ═══════════════════════════════════════════════════════════
#  Default contracts to audit
# ═══════════════════════════════════════════════════════════
DEFAULT_CONTRACTS = [
    REPO_ROOT / "vulnerable.sol",
    REPO_ROOT / "test_project" / "src" / "Vault.sol",
    REPO_ROOT / "test_project" / "src" / "VaultToken.sol",
    REPO_ROOT / "test_project" / "src" / "RewardDistributor.sol",
    REPO_ROOT / "test_project" / "src" / "VaultFactory.sol",
    REPO_ROOT / "test_project" / "src" / "interfaces" / "IVault.sol",
]


def is_wsl() -> bool:
    """Detect if running inside WSL."""
    try:
        with open("/proc/version", "r") as f:
            return "microsoft" in f.read().lower()
    except Exception:
        return False


def resolve_contracts(target: str = None) -> list:
    """Resolve target to list of .sol files.

    Args:
        target: Path to a .sol file or a directory containing .sol files.
                If None, returns DEFAULT_CONTRACTS.
    """
    if target is None:
        return [p for p in DEFAULT_CONTRACTS if p.exists()]

    target_path = Path(target).resolve()
    if target_path.is_file() and target_path.suffix == ".sol":
        return [target_path]
    elif target_path.is_dir():
        sols = sorted(target_path.rglob("*.sol"))
        # Exclude test files and node_modules
        sols = [
            s for s in sols
            if "node_modules" not in str(s)
            and ".t.sol" not in s.name
        ]
        return sols
    else:
        print(f"⚠️  Target not found or not .sol: {target}")
        return []


def read_source(path: Path) -> str:
    """Read Solidity source safely."""
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def run_layer1_quick_scan(audit: AGLSecurityAudit, path: Path) -> dict:
    """Layer 1: Quick scan (pattern engine only — no Ollama/LLM)."""
    try:
        result = audit.quick_scan(str(path))
        return result
    except Exception as e:
        return {"error": str(e), "findings": []}


def run_layer2_detectors(parser: SoliditySemanticParser, runner: DetectorRunner, source: str, filename: str) -> list:
    """Layer 2: 22 AGL semantic detectors."""
    try:
        contracts = parser.parse(source, filename)
        if not contracts:
            return []
        findings = runner.run(contracts)
        return [f.to_dict() for f in findings]
    except Exception as e:
        return [{"error": str(e)}]


def run_layer3_z3(engine: Z3SymbolicEngine, source: str, filename: str) -> list:
    """Layer 3: Z3 symbolic execution engine."""
    try:
        results = engine.analyze(source, filename)
        findings = engine.findings
        return [
            {
                "title": getattr(f, "title", str(f)),
                "severity": getattr(f, "severity", "unknown"),
                "category": getattr(f, "category", "unknown"),
                "line": getattr(f, "line", 0),
                "function": getattr(f, "function", ""),
                "confidence": getattr(f, "confidence", 0),
                "is_proven": getattr(f, "is_proven", False),
                "description": getattr(f, "description", "")[:200],
            }
            for f in findings
        ]
    except Exception as e:
        return [{"error": str(e)}]


def run_layer4_exploit_reasoning(source: str, findings: list) -> list:
    """Layer 4: Exploit reasoning engine."""
    try:
        engine = ExploitReasoningEngine()
        results = engine.analyze(source, findings)
        return [
            {
                "title": getattr(r, "title", str(r)),
                "exploitable": getattr(r, "exploitable", False),
                "severity": getattr(r, "severity", "unknown"),
                "proof_summary": getattr(r, "proof_summary", "")[:200] if hasattr(r, "proof_summary") else "",
                "confidence": getattr(r, "confidence", 0),
            }
            for r in results
        ] if results else []
    except Exception as e:
        return [{"error": str(e)}]


def severity_color(sev: str) -> str:
    """Color code for severity."""
    colors = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🔵",
        "info": "⚪",
    }
    return colors.get(str(sev).lower(), "⚫")


def main():
    # ── CLI Arguments ──
    parser_cli = argparse.ArgumentParser(
        description="🛡️ AGL Full Pipeline Audit — فحص خط الأنابيب الكامل"
    )
    parser_cli.add_argument(
        "--target", "-t",
        help="Path to a .sol file or directory to scan (default: project contracts)",
        default=None,
    )
    parser_cli.add_argument(
        "--skip-llm",
        action="store_true",
        default=True,
        help="Skip LLM/Ollama layers (default: True)",
    )
    args = parser_cli.parse_args()

    # ── Environment Detection ──
    env_label = "WSL" if is_wsl() else platform.system()

    print("=" * 70)
    print("🛡️  AGL FULL PIPELINE AUDIT — فحص خط الأنابيب الكامل")
    print(f"📅  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"🖥️  Environment: {env_label} | Python {platform.python_version()}")
    print("=" * 70)

    # ── Resolve contracts ──
    contracts = resolve_contracts(args.target)
    if not contracts:
        print("❌ No .sol contracts found to scan!")
        sys.exit(1)

    # Initialize engines
    print("\n⚙️  Initializing engines...")
    t0 = time.time()

    audit = AGLSecurityAudit(config={"skip_llm": args.skip_llm or SKIP_LLM})
    sol_parser = SoliditySemanticParser()
    detector_runner = DetectorRunner()

    # Z3 is optional — handle gracefully if not installed
    z3_engine = None
    try:
        z3_engine = Z3SymbolicEngine()
    except Exception as e:
        print(f"   ⚠️  Z3 engine unavailable: {e} — Layer 3 will be skipped")

    print(f"   ✅ All engines loaded in {time.time() - t0:.1f}s")
    print(f"   📋 Detectors registered: {len(detector_runner.detectors)}")
    print(f"   📂 Contracts to scan: {len(contracts)}")

    # Track aggregates
    all_results = {}
    total_findings = 0
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}

    for contract_path in contracts:
        filename = contract_path.name
        try:
            rel_path = contract_path.relative_to(REPO_ROOT)
        except ValueError:
            rel_path = contract_path  # External path — use absolute

        if not contract_path.exists():
            print(f"\n⚠️  Skipping {rel_path} — file not found")
            continue

        source = read_source(contract_path)
        if not source.strip():
            print(f"\n⚠️  Skipping {rel_path} — empty file")
            continue

        print(f"\n{'─' * 70}")
        print(f"📄 Scanning: {rel_path}")
        print(f"{'─' * 70}")
        contract_start = time.time()

        contract_result = {
            "file": str(rel_path),
            "deep_scan": {},
            "detectors": [],
            "z3_symbolic": [],
            "exploit_reasoning": [],
        }

        # ── Layer 1: Quick Scan (Pattern Engine) ──
        print("   🔬 Layer 1: Pattern Engine (Quick Scan)...")
        t1 = time.time()
        deep = run_layer1_quick_scan(audit, contract_path)
        deep_findings = deep.get("findings", [])
        contract_result["deep_scan"] = {
            "total_findings": deep.get("total_findings", len(deep_findings)),
            "severity_summary": deep.get("severity_summary", {}),
            "duration_s": round(time.time() - t1, 1),
        }
        print(f"      → {len(deep_findings)} findings ({time.time() - t1:.1f}s)")

        # ── Layer 2: 22 Detectors ──
        print("   🔍 Layer 2: 22 Semantic Detectors...")
        t2 = time.time()
        det_findings = run_layer2_detectors(sol_parser, detector_runner, source, filename)
        det_clean = [f for f in det_findings if "error" not in f]
        contract_result["detectors"] = det_clean
        print(f"      → {len(det_clean)} findings ({time.time() - t2:.1f}s)")

        # ── Layer 3: Z3 Symbolic ──
        print("   ⚡ Layer 3: Z3 Symbolic Execution...")
        t3 = time.time()
        z3_clean = []
        proven = 0
        if z3_engine is not None:
            z3_engine.findings = []  # Reset
            z3_findings = run_layer3_z3(z3_engine, source, filename)
            z3_clean = [f for f in z3_findings if "error" not in f]
            proven = sum(1 for f in z3_clean if f.get("is_proven"))
            print(f"      → {len(z3_clean)} findings ({proven} proven) ({time.time() - t3:.1f}s)")
        else:
            print(f"      → skipped (Z3 not available)")
        contract_result["z3_symbolic"] = z3_clean

        # ── Layer 4: Exploit Reasoning ──
        print("   💀 Layer 4: Exploit Reasoning Engine...")
        t4 = time.time()
        # Combine findings for exploit analysis
        combined_findings_for_exploit = []
        for f in deep_findings:
            combined_findings_for_exploit.append(f)
        for f in det_clean:
            combined_findings_for_exploit.append({
                "title": f.get("title", ""),
                "severity": f.get("severity", "medium"),
                "category": f.get("detector", ""),
                "line": f.get("line", 0),
                "description": f.get("description", ""),
                "source": "agl_22_detectors",
            })
        for f in z3_clean:
            combined_findings_for_exploit.append({
                "title": f.get("title", ""),
                "severity": f.get("severity", "medium"),
                "category": f.get("category", ""),
                "line": f.get("line", 0),
                "description": f.get("description", ""),
                "source": "z3_symbolic",
                "is_proven": f.get("is_proven", False),
            })

        exploit_results = run_layer4_exploit_reasoning(source, combined_findings_for_exploit)
        exploit_clean = [r for r in exploit_results if "error" not in r]
        exploitable = [r for r in exploit_clean if r.get("exploitable")]
        contract_result["exploit_reasoning"] = exploit_clean
        print(f"      → {len(exploit_clean)} analyzed, {len(exploitable)} exploitable ({time.time() - t4:.1f}s)")

        # ── Summary for this contract ──
        contract_total = len(deep_findings) + len(det_clean) + len(z3_clean)
        total_findings += contract_total
        contract_result["total"] = contract_total
        contract_result["duration_s"] = round(time.time() - contract_start, 1)

        # Count severities
        for f in deep_findings:
            sev = str(f.get("severity", "info")).lower()
            if sev in severity_counts:
                severity_counts[sev] += 1
        for f in det_clean:
            sev = str(f.get("severity", "info")).lower()
            if sev in severity_counts:
                severity_counts[sev] += 1
        for f in z3_clean:
            sev = str(f.get("severity", "info")).lower()
            if sev in severity_counts:
                severity_counts[sev] += 1

        # Print per-contract summary
        print(f"\n   📊 Contract Summary: {contract_total} total findings")
        print(f"      Deep: {len(deep_findings)} | Detectors: {len(det_clean)} | Z3: {len(z3_clean)} | Exploitable: {len(exploitable)}")
        print(f"      ⏱️  Duration: {contract_result['duration_s']}s")

        # Print critical/high findings
        crit_high = []
        for f in det_clean:
            if f.get("severity") in ("critical", "high"):
                crit_high.append(f)
        for f in z3_clean:
            if f.get("severity") in ("critical", "high") and f.get("is_proven"):
                crit_high.append(f)

        if crit_high:
            print(f"\n   🚨 Critical/High Findings:")
            for f in crit_high[:10]:
                sev = f.get("severity", "?")
                title = f.get("title", "?")
                line = f.get("line", "?")
                print(f"      {severity_color(sev)} [{sev.upper()}] {title} (line {line})")

        all_results[str(rel_path)] = contract_result

    # ═══════════════════════════════════════════════
    #  Global Summary
    # ═══════════════════════════════════════════════
    total_time = time.time() - t0
    print(f"\n{'═' * 70}")
    print(f"📊  AUDIT COMPLETE — ملخص التدقيق الكامل")
    print(f"{'═' * 70}")
    print(f"   📂 Contracts scanned: {len(all_results)}")
    print(f"   🔍 Total findings: {total_findings}")
    print(f"   🔴 Critical: {severity_counts['critical']}")
    print(f"   🟠 High: {severity_counts['high']}")
    print(f"   🟡 Medium: {severity_counts['medium']}")
    print(f"   🔵 Low: {severity_counts['low']}")
    print(f"   ⚪ Info: {severity_counts['info']}")
    print(f"   ⏱️  Total time: {total_time:.1f}s")

    # Save JSON report
    report = {
        "audit_metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pipeline_version": "1.1.0",
            "engines": ["deep_scan", "22_detectors", "z3_symbolic", "exploit_reasoning"],
            "total_duration_s": round(total_time, 1),
        },
        "summary": {
            "contracts_scanned": len(all_results),
            "total_findings": total_findings,
            "severity_counts": severity_counts,
        },
        "contracts": all_results,
    }

    report_path = REPO_ROOT / "reports" / "full_pipeline_audit.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n💾 JSON report saved: {report_path.relative_to(REPO_ROOT)}")

    # Generate Markdown report
    md_path = REPO_ROOT / "reports" / "FULL_AUDIT_REPORT.md"
    generate_markdown_report(report, md_path)
    print(f"📝 Markdown report saved: {md_path.relative_to(REPO_ROOT)}")

    return report


def generate_markdown_report(report: dict, path: Path):
    """Generate a readable Markdown audit report."""
    summary = report["summary"]
    meta = report["audit_metadata"]
    contracts = report["contracts"]

    lines = [
        "# 🛡️ AGL Full Pipeline Security Audit Report",
        "",
        f"**Date:** {meta['timestamp']}",
        f"**Pipeline Version:** {meta['pipeline_version']}",
        f"**Duration:** {meta['total_duration_s']}s",
        f"**Engines:** {', '.join(meta['engines'])}",
        "",
        "## 📊 Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Contracts Scanned | {summary['contracts_scanned']} |",
        f"| Total Findings | {summary['total_findings']} |",
        f"| 🔴 Critical | {summary['severity_counts']['critical']} |",
        f"| 🟠 High | {summary['severity_counts']['high']} |",
        f"| 🟡 Medium | {summary['severity_counts']['medium']} |",
        f"| 🔵 Low | {summary['severity_counts']['low']} |",
        f"| ⚪ Info | {summary['severity_counts']['info']} |",
        "",
        "---",
        "",
    ]

    for contract_path, data in contracts.items():
        lines.append(f"## 📄 {contract_path}")
        lines.append("")
        lines.append(f"**Total findings:** {data.get('total', 0)} | **Duration:** {data.get('duration_s', 0)}s")
        lines.append("")

        # Deep scan
        ds = data.get("deep_scan", {})
        lines.append(f"### Layer 1 — Deep Scan")
        lines.append(f"- Findings: {ds.get('total_findings', 0)}")
        sev_sum = ds.get("severity_summary", {})
        if sev_sum:
            lines.append(f"- Severity: {json.dumps(sev_sum)}")
        lines.append("")

        # Detectors
        det = data.get("detectors", [])
        lines.append(f"### Layer 2 — 22 Semantic Detectors ({len(det)} findings)")
        lines.append("")
        if det:
            lines.append("| Severity | Detector | Title | Line | Function |")
            lines.append("|----------|----------|-------|------|----------|")
            for f in det:
                sev = f.get("severity", "?")
                det_id = f.get("detector", "?")
                title = f.get("title", "?")
                line_num = f.get("line", "?")
                func = f.get("function", "?")
                lines.append(f"| {severity_color(sev)} {sev} | {det_id} | {title} | {line_num} | {func} |")
            lines.append("")

        # Z3
        z3 = data.get("z3_symbolic", [])
        lines.append(f"### Layer 3 — Z3 Symbolic ({len(z3)} findings)")
        lines.append("")
        if z3:
            lines.append("| Severity | Category | Title | Line | Proven | Confidence |")
            lines.append("|----------|----------|-------|------|--------|------------|")
            for f in z3:
                sev = f.get("severity", "?")
                cat = f.get("category", "?")
                title = f.get("title", "?")[:60]
                line_num = f.get("line", "?")
                proven = "✅" if f.get("is_proven") else "❌"
                conf = f.get("confidence", 0)
                lines.append(f"| {severity_color(sev)} {sev} | {cat} | {title} | {line_num} | {proven} | {conf} |")
            lines.append("")

        # Exploit reasoning
        exploit = data.get("exploit_reasoning", [])
        exploitable = [e for e in exploit if e.get("exploitable")]
        lines.append(f"### Layer 4 — Exploit Reasoning ({len(exploitable)} exploitable / {len(exploit)} total)")
        lines.append("")
        if exploitable:
            for e in exploitable:
                lines.append(f"- 💀 **{e.get('title', '?')}** — {e.get('severity', '?')} (confidence: {e.get('confidence', 0)})")
                if e.get("proof_summary"):
                    lines.append(f"  > {e['proof_summary'][:200]}")
            lines.append("")

        lines.append("---")
        lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
