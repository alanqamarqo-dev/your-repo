"""
AGL Security Audit — النواة الرئيسية
Unified API wrapping the 4-layer analysis pipeline:
  Layer 1: smart_contract_analyzer (Lexer + CFG + Taint + 8 pattern detectors)
  Layer 2: agl_security suite (Slither/Mythril/Semgrep integration + filter/dedup)
  Layer 3: offensive_security engine (Heuristic + Z3 Formal + EVM Sim + Logic Gates + LLM)
  Layer 4: AGL Detectors (22 semantic detectors — reentrancy, access, DeFi, common, token)
"""

import os
import sys
import json
import time
from typing import Dict, Any, List, Optional
from pathlib import Path

# ═══════════════════════════════════════════════════════
# تهيئة مسارات الاستيراد — Setup import paths
# ═══════════════════════════════════════════════════════
_TOOL_DIR = Path(__file__).parent.resolve()
_ENGINES_DIR = _TOOL_DIR.parent / "AGL_NextGen" / "src" / "agl" / "engines"
_SRC_DIR = _TOOL_DIR.parent / "AGL_NextGen" / "src"

# إضافة المسارات إلى sys.path
for p in [str(_SRC_DIR), str(_ENGINES_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)


class AGLSecurityAudit:
    """
    واجهة موحدة لتحليل أمان العقود الذكية
    Unified smart contract security analysis interface.

    Usage:
        audit = AGLSecurityAudit()
        result = audit.scan("contract.sol")
        result = audit.scan("contracts/", recursive=True)
        result = audit.quick_scan("contract.sol")   # Fast pattern-only
        result = audit.deep_scan("contract.sol")    # Full pipeline + Z3 + EVM
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        تهيئة محرك التحليل مع كل الطبقات المتاحة.

        Args:
            config: إعدادات اختيارية — severity_filter, confidence_threshold, timeout...
        """
        self.config = config or {}
        self._engine = None
        self._suite = None
        self._analyzer = None
        self._detector_runner = None
        self._parser = None
        self._init_engines()

    def _init_engines(self):
        """تحميل المحركات المتاحة — أي محرك غير متوفر يتم تجاوزه بدون خطأ."""
        # Layer 1: SmartContractAnalyzer (pattern scan + Lexer + CFG)
        try:
            from agl.engines.smart_contract_analyzer import SmartContractAnalyzer
            self._analyzer = SmartContractAnalyzer()
        except Exception:
            pass

        # Layer 2: AGLSecuritySuite (Slither/Mythril wrapper)
        try:
            from agl.engines.agl_security import AGLSecuritySuite
            self._suite = AGLSecuritySuite(self.config.get("suite", {
                "severity_filter": ["critical", "high", "medium", "low"],
                "confidence_threshold": 0.5,
            }))
        except Exception:
            pass

        # Layer 3: OffensiveSecurityEngine (full pipeline)
        try:
            from agl.engines.offensive_security import OffensiveSecurityEngine
            self._engine = OffensiveSecurityEngine()
        except Exception:
            pass

        # Layer 4: AGL Semantic Detectors (22 detectors)
        try:
            from agl_security_tool.detectors import DetectorRunner
            from agl_security_tool.detectors.solidity_parser import SoliditySemanticParser
            self._detector_runner = DetectorRunner()
            self._parser = SoliditySemanticParser()
        except Exception:
            pass

    # ═══════════════════════════════════════════════════
    # الواجهة العامة — Public API
    # ═══════════════════════════════════════════════════

    def scan(self, target: str, recursive: bool = False) -> Dict[str, Any]:
        """
        فحص ذكي — يختار الطريقة المناسبة تلقائياً.

        Args:
            target: مسار ملف .sol أو مجلد
            recursive: فحص المجلدات الفرعية

        Returns:
            قاموس بالنتائج: findings, suite_findings, severity_summary, evm_simulation
        """
        target = str(Path(target).resolve())

        if not os.path.exists(target):
            return {"error": f"المسار غير موجود: {target}", "status": "ERROR"}

        if os.path.isfile(target):
            return self._scan_file(target)
        else:
            return self._scan_directory(target, recursive)

    def quick_scan(self, target: str) -> Dict[str, Any]:
        """
        فحص سريع — أنماط regex فقط بدون LLM أو Z3.
        مناسب للمسح السريع لمئات الملفات.

        Args:
            target: مسار ملف .sol

        Returns:
            قاموس بالنتائج: findings مع severity و line numbers
        """
        target = str(Path(target).resolve())
        if not os.path.isfile(target):
            return {"error": f"الملف غير موجود: {target}", "status": "ERROR"}

        t0 = time.time()

        # Use Layer 1 only (pattern scan)
        if self._analyzer:
            with open(target, "r", encoding="utf-8", errors="ignore") as f:
                code = f.read()
            result = self._analyzer.analyze(code)
            result["time_seconds"] = round(time.time() - t0, 2)
            result["scan_mode"] = "quick"
            result["file"] = target
            return result

        # Fallback to Layer 2
        if self._suite:
            result = self._suite.scan_file(target)
            result["time_seconds"] = round(time.time() - t0, 2)
            result["scan_mode"] = "quick"
            return result

        return {"error": "لا يوجد محرك تحليل متاح", "status": "ERROR"}

    def deep_scan(self, target: str) -> Dict[str, Any]:
        """
        فحص عميق — كل الطبقات: Pattern + Suite + Heuristic + Z3 + EVM + LLM.

        Args:
            target: مسار ملف .sol أو مجلد

        Returns:
            قاموس شامل بكل النتائج والإثباتات الرياضية
        """
        target = str(Path(target).resolve())
        if not os.path.exists(target):
            return {"error": f"المسار غير موجود: {target}", "status": "ERROR"}

        t0 = time.time()

        if self._engine:
            result = self._engine.process_task("smart_contract_audit", target)
            result["time_seconds"] = round(time.time() - t0, 2)
            result["scan_mode"] = "deep"
            return result

        # Fallback
        return self.scan(target)

    def generate_report(self, result: Dict[str, Any], format: str = "text") -> str:
        """
        توليد تقرير من نتائج الفحص.

        Args:
            result: نتائج من scan/quick_scan/deep_scan
            format: "text" أو "json" أو "markdown"

        Returns:
            التقرير كنص
        """
        if format == "json":
            return json.dumps(result, indent=2, ensure_ascii=False, default=str)

        if format == "markdown":
            return self._format_markdown(result)

        return self._format_text(result)

    # ═══════════════════════════════════════════════════
    # الدوال الداخلية — Internal methods
    # ═══════════════════════════════════════════════════

    def _scan_file(self, file_path: str) -> Dict[str, Any]:
        """فحص ملف واحد عبر كل الطبقات المتاحة."""
        t0 = time.time()
        combined = {
            "status": "COMPLETE",
            "file": file_path,
            "scan_mode": "standard",
            "layers_used": [],
            "findings": [],
            "suite_findings": [],
            "detector_findings": [],
            "severity_summary": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
        }

        # Layer 1: Pattern Scan
        if self._analyzer:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    code = f.read()
                r = self._analyzer.analyze(code)
                combined["findings"].extend(r.get("findings", []))
                combined["contracts"] = r.get("contracts", [])
                combined["functions"] = r.get("functions", [])
                combined["layers_used"].append("smart_contract_analyzer")
            except Exception as e:
                combined.setdefault("warnings", []).append(f"Layer 1 error: {e}")

        # Layer 2: Security Suite
        if self._suite:
            try:
                r = self._suite.scan_file(file_path)
                suite_f = r.get("findings", [])
                combined["suite_findings"].extend(suite_f)
                combined["layers_used"].append("agl_security_suite")
            except Exception as e:
                combined.setdefault("warnings", []).append(f"Layer 2 error: {e}")

        # Layer 4: AGL Semantic Detectors (22 detectors)
        if self._parser and self._detector_runner:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    code = f.read()
                contracts = self._parser.parse(code, file_path)
                det_findings = self._detector_runner.run(contracts)
                combined["detector_findings"].extend(
                    df.to_dict() for df in det_findings
                )
                combined["layers_used"].append("agl_detectors")
                combined["parsed_contracts"] = len(contracts)
            except Exception as e:
                combined.setdefault("warnings", []).append(f"Layer 4 (detectors) error: {e}")

        # Count severities
        for f in combined["findings"]:
            sev = f.get("severity", "low").upper()
            if sev in combined["severity_summary"]:
                combined["severity_summary"][sev] += 1

        for f in combined["suite_findings"]:
            sev = f.get("severity", "low").upper()
            if sev in combined["severity_summary"]:
                combined["severity_summary"][sev] += 1

        for f in combined["detector_findings"]:
            sev = f.get("severity", "low").upper()
            if sev in combined["severity_summary"]:
                combined["severity_summary"][sev] += 1

        combined["total_findings"] = (
            len(combined["findings"]) +
            len(combined["suite_findings"]) +
            len(combined["detector_findings"])
        )
        combined["time_seconds"] = round(time.time() - t0, 2)
        return combined

    def _scan_directory(self, dir_path: str, recursive: bool) -> Dict[str, Any]:
        """فحص مجلد كامل."""
        sol_files = []
        if recursive:
            for root, _, files in os.walk(dir_path):
                for f in files:
                    if f.endswith(".sol"):
                        sol_files.append(os.path.join(root, f))
        else:
            sol_files = [
                os.path.join(dir_path, f)
                for f in os.listdir(dir_path)
                if f.endswith(".sol")
            ]

        results = {
            "status": "COMPLETE",
            "directory": dir_path,
            "files_scanned": len(sol_files),
            "file_results": {},
            "total_findings": 0,
            "severity_summary": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
        }

        for f in sol_files:
            r = self._scan_file(f)
            results["file_results"][f] = r
            results["total_findings"] += r.get("total_findings", 0)
            for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
                results["severity_summary"][sev] += r.get("severity_summary", {}).get(sev, 0)

        return results

    def _format_text(self, result: Dict[str, Any]) -> str:
        """تنسيق النتائج كنص عادي."""
        lines = []
        lines.append("=" * 60)
        lines.append("  AGL Security Audit Report")
        lines.append("=" * 60)
        lines.append(f"  Status: {result.get('status', 'N/A')}")
        lines.append(f"  Mode: {result.get('scan_mode', 'N/A')}")
        lines.append(f"  Time: {result.get('time_seconds', 'N/A')}s")
        lines.append("")

        # Findings
        findings = result.get("findings", [])
        suite = result.get("suite_findings", [])
        detectors = result.get("detector_findings", [])

        if findings:
            lines.append(f"  📋 Pattern Findings ({len(findings)}):")
            for f in findings:
                sev = f.get("severity", "?").upper()
                title = f.get("title", f.get("text", "Unknown"))
                line = f.get("line", "?")
                lines.append(f"    [{sev}] L{line}: {title}")

        if suite:
            lines.append(f"\n  🛡️ Suite Findings ({len(suite)}):")
            for f in suite:
                sev = f.get("severity", "?").upper()
                title = f.get("title", "Unknown")
                line = f.get("line", "?")
                lines.append(f"    [{sev}] L{line}: {title}")

        if detectors:
            lines.append(f"\n  🔬 Detector Findings ({len(detectors)}):")
            for f in detectors:
                sev = f.get("severity", "?").upper()
                title = f.get("title", f.get("detector_id", "Unknown"))
                line = f.get("line", "?")
                lines.append(f"    [{sev}] L{line}: {title}")
                desc = f.get("description", "")
                if desc:
                    # Wrap description to 70 chars
                    lines.append(f"           {desc[:120]}{'...' if len(desc) > 120 else ''}")

        # Summary
        summary = result.get("severity_summary", {})
        lines.append(f"\n  📊 Summary:")
        lines.append(f"    CRITICAL: {summary.get('CRITICAL', 0)}")
        lines.append(f"    HIGH:     {summary.get('HIGH', 0)}")
        lines.append(f"    MEDIUM:   {summary.get('MEDIUM', 0)}")
        lines.append(f"    LOW:      {summary.get('LOW', 0)}")
        lines.append("=" * 60)
        return "\n".join(lines)

    def scan_project(self, project_path: str, **kwargs) -> Dict[str, Any]:
        """
        فحص مشروع كامل — Foundry / Hardhat / Truffle.
        يحلل البنية والتبعيات والتوارث ويفحص كل العقود.

        Args:
            project_path: مسار المجلد الجذري للمشروع
            **kwargs: إعدادات إضافية:
                mode: "scan" أو "quick" أو "deep" (default: "scan")
                output_format: "dict" أو "json" أو "markdown" أو "text" (default: "dict")
                exclude_tests: bool (default: True)
                exclude_mocks: bool (default: True)
                scan_dependencies: bool (default: False)

        Returns:
            تقرير شامل على مستوى المشروع
        """
        from agl_security_tool.project_scanner import ProjectScanner

        mode = kwargs.pop("mode", "scan")
        output_format = kwargs.pop("output_format", "dict")

        scanner = ProjectScanner(project_path, config={**self.config, **kwargs})

        if mode == "deep":
            return scanner.deep_scan(output_format=output_format)
        elif mode == "quick":
            return scanner.quick_scan(output_format=output_format)
        else:
            return scanner.full_scan(output_format=output_format)

    def _format_markdown(self, result: Dict[str, Any]) -> str:
        """تنسيق النتائج كـ Markdown."""
        lines = []
        lines.append("# 🛡️ AGL Security Audit Report\n")
        lines.append(f"**Status:** {result.get('status', 'N/A')}")
        lines.append(f"**Mode:** {result.get('scan_mode', 'N/A')}")
        lines.append(f"**Time:** {result.get('time_seconds', 'N/A')}s\n")

        findings = result.get("findings", [])
        suite = result.get("suite_findings", [])

        if findings:
            lines.append(f"## Pattern Findings ({len(findings)})\n")
            lines.append("| Severity | Line | Title |")
            lines.append("|----------|------|-------|")
            for f in findings:
                sev = f.get("severity", "?").upper()
                title = f.get("title", f.get("text", "Unknown"))
                line = f.get("line", "?")
                lines.append(f"| {sev} | {line} | {title} |")

        if suite:
            lines.append(f"\n## Suite Findings ({len(suite)})\n")
            lines.append("| Severity | Line | Title |")
            lines.append("|----------|------|-------|")
            for f in suite:
                sev = f.get("severity", "?").upper()
                title = f.get("title", "Unknown")
                line = f.get("line", "?")
                lines.append(f"| {sev} | {line} | {title} |")

        summary = result.get("severity_summary", {})
        lines.append("\n## Summary\n")
        lines.append(f"- 🔴 CRITICAL: **{summary.get('CRITICAL', 0)}**")
        lines.append(f"- 🟠 HIGH: **{summary.get('HIGH', 0)}**")
        lines.append(f"- 🟡 MEDIUM: **{summary.get('MEDIUM', 0)}**")
        lines.append(f"- 🔵 LOW: **{summary.get('LOW', 0)}**")

        return "\n".join(lines)
