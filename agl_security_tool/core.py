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
        Initialize the analysis engine with all available layers.
        تهيئة محرك التحليل مع كل الطبقات المتاحة.

        Args:
            config: Optional settings — severity_filter, confidence_threshold, timeout...
                    إعدادات اختيارية
        """
        self.config = config or {}
        self._engine = None
        self._suite = None
        self._analyzer = None
        self._detector_runner = None
        self._parser = None
        self._flattener = None
        self._symbolic_engine = None
        self._state_engine = None
        self._init_engines()

    def _init_engines(self):
        """Load available engines — any unavailable engine is silently skipped.
        تحميل المحركات المتاحة — أي محرك غير متوفر يتم تجاوزه بدون خطأ."""
        # Layer 0: Solidity Flattener + Inheritance Resolver
        try:
            from agl_security_tool.solidity_flattener import SolidityFlattener

            self._flattener = SolidityFlattener()
        except Exception:
            pass

        # Layer 0.5: Z3 Symbolic Execution Engine (internal Mythril)
        try:
            from agl_security_tool.z3_symbolic_engine import Z3SymbolicEngine

            self._symbolic_engine = Z3SymbolicEngine()
        except Exception:
            pass

        # Layer 1: SmartContractAnalyzer (pattern scan + Lexer + CFG)
        try:
            from agl.engines.smart_contract_analyzer import SmartContractAnalyzer

            self._analyzer = SmartContractAnalyzer()
        except Exception:
            pass

        # Layer 2: AGLSecuritySuite (Slither/Mythril wrapper — fallback)
        try:
            from agl.engines.agl_security import AGLSecuritySuite

            self._suite = AGLSecuritySuite(
                self.config.get(
                    "suite",
                    {
                        "severity_filter": ["critical", "high", "medium", "low"],
                        "confidence_threshold": 0.5,
                    },
                )
            )
        except Exception:
            pass

        # Layer 2+: Security Orchestrator (parallel Slither + Mythril + Semgrep + Z3)
        self._orchestrator = None
        try:
            from agl.engines.security_orchestrator import (
                AGLSecurityOrchestrator,
                AnalysisConfig,
            )

            _orch_cfg = AnalysisConfig(
                enable_slither=True,
                enable_mythril=True,
                enable_semgrep=True,
                enable_z3=True,
                enable_llm=True,
                mythril_timeout=self.config.get("mythril_timeout", 300),
                generate_poc=self.config.get("generate_poc", True),
            )
            self._orchestrator = AGLSecurityOrchestrator(_orch_cfg)
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
            from agl_security_tool.detectors.solidity_parser import (
                SoliditySemanticParser,
            )

            self._detector_runner = DetectorRunner()
            self._parser = SoliditySemanticParser()
        except Exception:
            pass

        # Layer 1 (State Extraction): Financial State Graph Engine
        try:
            from agl_security_tool.state_extraction import StateExtractionEngine

            self._state_engine = StateExtractionEngine(
                self.config.get("state_extraction", {})
            )
        except Exception:
            pass

    # ═══════════════════════════════════════════════════
    # الواجهة العامة — Public API
    # ═══════════════════════════════════════════════════

    def scan(self, target: str, recursive: bool = False) -> Dict[str, Any]:
        """
        Smart scan — automatically selects the appropriate method.
        فحص ذكي — يختار الطريقة المناسبة تلقائياً.

        Args:
            target: Path to .sol file or directory / مسار ملف .sol أو مجلد
            recursive: Scan subdirectories / فحص المجلدات الفرعية

        Returns:
            Dict with: findings, suite_findings, severity_summary, evm_simulation
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
        Quick scan — regex patterns only, no LLM or Z3.
        Suitable for rapid scanning of hundreds of files.
        فحص سريع — أنماط regex فقط بدون LLM أو Z3.
        مناسب للمسح السريع لمئات الملفات.

        Args:
            target: Path to .sol file / مسار ملف .sol

        Returns:
            Dict with: findings including severity and line numbers
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
        Deep scan — all layers combined:
        فحص عميق — كل الطبقات مجتمعة:
        Flattener → Z3 Symbolic → Pattern Scan → Orchestrator(Slither/Mythril/Semgrep) →
        22 AGL Detectors → Exploit Reasoning → LLM Enrichment →
        OffensiveSecurityEngine(EVM Sim + Quantum + Meta-Reasoner + Formal Proofs)

        Args:
            target: مسار ملف .sol أو مجلد

        Returns:
            قاموس شامل بكل النتائج والإثباتات الرياضية من جميع المحركات
        """
        import re as _re_deep

        target = str(Path(target).resolve())
        if not os.path.exists(target):
            return {"error": f"المسار غير موجود: {target}", "status": "ERROR"}

        t0 = time.time()

        # ═══ الخطوة 1: تشغيل كل الطبقات الأساسية (Layer 0 → 5) ═══
        if os.path.isfile(target):
            combined = self._scan_file(target)
        else:
            combined = self._scan_directory(target, recursive=True)

        # ═══ الخطوة 2: تشغيل محرك الأمان الهجومي (Layer 3) ═══
        # يضيف: EVM Simulation + Quantum Deep Audit + Meta-Reasoner +
        #        Holographic LLM + Strict Logic Gates + Formal Z3 Proofs
        if self._engine:
            try:
                offensive = self._engine.process_task(
                    "smart_contract_audit",
                    target,
                    context={"skip_suite": True},  # Orchestrator already ran tools
                )

                # دمج محاكاة EVM الديناميكية
                if offensive.get("evm_simulation"):
                    combined["evm_simulation"] = offensive["evm_simulation"]

                # دمج نتائج Quantum Deep Audit
                if offensive.get("quantum_findings"):
                    combined["quantum_findings"] = offensive["quantum_findings"]

                # دمج النتائج الهيوريستيكية مع التصنيف المنطقي الصارم
                offensive_findings = []
                for f_entry in offensive.get("findings", []):
                    for issue in f_entry.get("issues", []):
                        # استخراج رقم السطر من النص إن وُجد
                        _lm = _re_deep.search(r"at line (\d+)", issue.get("text", ""))
                        line_num = int(_lm.group(1)) if _lm else 0
                        offensive_findings.append(
                            {
                                "title": issue.get("text", "")[:200],
                                "severity": issue.get("severity", "low").lower(),
                                "category": "offensive_heuristic",
                                "description": issue.get("text", ""),
                                "line": line_num,
                                "confidence": (
                                    0.9 if issue.get("mathematically_proven") else 0.65
                                ),
                                "source": "offensive_security_engine",
                                "logic_trace": issue.get("logic_trace", []),
                                "mathematically_proven": issue.get(
                                    "mathematically_proven", False
                                ),
                                "formal_verification": issue.get(
                                    "formal_verification", {}
                                ),
                                "validation_status": issue.get("validation_status", ""),
                            }
                        )
                combined.setdefault("offensive_findings", []).extend(offensive_findings)

                # إعادة تشغيل الدمج وإزالة التكرارات مع النتائج الجديدة
                combined = self._deduplicate_and_cross_validate(combined)

                combined.setdefault("layers_used", []).append(
                    "offensive_security_engine"
                )
                combined["offensive_summary"] = offensive.get("severity_summary", {})
            except Exception as e:
                combined.setdefault("warnings", []).append(
                    f"OffensiveSecurityEngine: {e}"
                )

        combined["scan_mode"] = "deep"
        combined["time_seconds"] = round(time.time() - t0, 2)
        combined["total_findings"] = len(combined.get("all_findings_unified", []))
        return combined

    # ═══════════════════════════════════════════════════
    # State Extraction — استخراج الحالة المالية
    # ═══════════════════════════════════════════════════

    def extract_state(self, target: str) -> Dict[str, Any]:
        """
        استخراج الحالة المالية وبناء الرسم البياني الديناميكي.
        Layer 1: State Extraction Engine

        Args:
            target: مسار ملف .sol أو مجلد مشروع

        Returns:
            قاموس يحتوي على الرسم البياني المالي الكامل بصيغة JSON
        """
        if not self._state_engine:
            return {"error": "State Extraction Engine غير متاح", "status": "ERROR"}

        target = str(Path(target).resolve())
        if not os.path.exists(target):
            return {"error": f"المسار غير موجود: {target}", "status": "ERROR"}

        if os.path.isfile(target):
            result = self._state_engine.extract(target)
        else:
            result = self._state_engine.extract_project(target)

        return result.to_dict()

    def extract_state_json(self, target: str, indent: int = 2) -> str:
        """
        استخراج الحالة المالية كـ JSON نصي.

        Args:
            target: مسار ملف .sol أو مجلد مشروع
            indent: مسافة التنسيق

        Returns:
            JSON string بالرسم البياني المالي الكامل
        """
        result = self.extract_state(target)
        return json.dumps(result, indent=indent, ensure_ascii=False)

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
            "symbolic_findings": [],
            "severity_summary": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
        }

        # ═══ Layer 0: Import Flattening + Inheritance Resolution ═══
        source_code = ""
        flat_info = None
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                source_code = f.read()
        except Exception:
            pass

        if self._flattener:
            try:
                # اكتشاف مجلد المشروع تلقائياً
                project_root = self._detect_project_root(file_path)
                if project_root:
                    self._flattener.project_root = project_root
                    self._flattener._auto_detect_remappings()

                flat_result = self._flattener.flatten(file_path)
                if flat_result.files_included and len(flat_result.files_included) > 1:
                    # ملف متعدد الاستيرادات — نستخدم المصدر المدمج
                    source_code = flat_result.source
                    combined["layers_used"].append("import_flattener")
                    combined["flattened"] = {
                        "files_included": len(flat_result.files_included),
                        "contracts_found": flat_result.contracts_found,
                        "unresolved_imports": flat_result.unresolved_imports,
                        "total_lines": flat_result.total_lines,
                    }
                    flat_info = flat_result

                # Inheritance context for all contracts in the file
                inheritance_info = []
                for cname in flat_result.contracts_found:
                    ctx = self._flattener.get_full_context(cname)
                    if ctx.full_chain and len(ctx.full_chain) > 1:
                        inheritance_info.append(
                            {
                                "contract": cname,
                                "chain": ctx.full_chain,
                                "inherited_state_vars": len(ctx.all_state_vars),
                                "inherited_functions": len(ctx.all_functions),
                                "has_delegatecall": ctx.has_delegatecall,
                                "has_selfdestruct": ctx.has_selfdestruct,
                            }
                        )
                if inheritance_info:
                    combined["inheritance_context"] = inheritance_info
            except Exception as e:
                combined.setdefault("warnings", []).append(f"Flattener: {e}")

        # ═══ Layer 0.5: Z3 Symbolic Execution ═══
        if self._symbolic_engine and source_code:
            try:
                sym_findings = self._symbolic_engine.analyze(source_code, file_path)
                for sf in sym_findings:
                    combined["symbolic_findings"].append(
                        {
                            "title": sf.title,
                            "severity": sf.severity,
                            "category": sf.category,
                            "description": sf.description,
                            "line": sf.line,
                            "function": sf.function,
                            "confidence": sf.confidence,
                            "source": "z3_symbolic",
                            "is_proven": sf.is_proven,
                            "z3_model": sf.z3_model,
                            "counterexample": sf.counterexample,
                            "code_snippet": sf.code_snippet,
                            "detector_id": "z3_symbolic",
                        }
                    )
                if sym_findings:
                    combined["layers_used"].append("z3_symbolic_execution")
            except Exception as e:
                combined.setdefault("warnings", []).append(f"Symbolic engine: {e}")

        # Layer 1: Pattern Scan + CFG Analysis (with Cross-File context when available)
        if self._analyzer:
            try:
                # Try cross-file analysis if the file is part of a project
                r = None
                if file_path and os.path.isfile(file_path):
                    project_root = self._find_project_root(file_path)
                    if project_root:
                        try:
                            from agl.engines.smart_contract_analyzer import (
                                ProjectContext,
                            )

                            ctx = ProjectContext(project_root)
                            ctx.scan_project(project_root)
                            self._analyzer.set_project_context(ctx)
                            r = self._analyzer.analyze_file(file_path)
                            combined["layers_used"].append("smart_contract_analyzer")
                            combined["layers_used"].append("cross_file_context")
                            if r.get("unprotected_functions"):
                                combined.setdefault("cross_file", {})[
                                    "unprotected_functions"
                                ] = r["unprotected_functions"]
                        except Exception:
                            r = None  # Fall back to single-file
                if r is None:
                    r = self._analyzer.analyze(source_code or "")
                    combined["layers_used"].append("smart_contract_analyzer")
                combined["findings"].extend(r.get("findings", []))
                combined["contracts"] = r.get("contracts", [])
                combined["functions"] = r.get("functions", [])
                if r.get("advanced_analysis"):
                    combined["layers_used"].append("cfg_analysis")
                for w in r.get("warnings", []):
                    combined.setdefault("warnings", []).append(f"Layer 1: {w}")
            except Exception as e:
                combined.setdefault("warnings", []).append(f"Layer 1 error: {e}")

        # Layer 2: Security Orchestrator (Slither + Mythril + Semgrep + Z3 parallel)
        _orch_used = False
        if self._orchestrator:
            try:
                orch_findings = self._orchestrator.analyze_file(
                    file_path, skip_llm=True
                )
                for of in orch_findings:
                    combined["suite_findings"].append(
                        {
                            "id": getattr(of, "id", ""),
                            "title": getattr(of, "title", ""),
                            "severity": (
                                of.severity.value
                                if hasattr(of.severity, "value")
                                else str(getattr(of, "severity", "medium"))
                            ),
                            "category": (
                                of.category.value
                                if hasattr(of.category, "value")
                                else str(getattr(of, "category", "unknown"))
                            ),
                            "line": getattr(of, "line_start", 0),
                            "description": getattr(of, "description", ""),
                            "confidence": getattr(of, "confidence", 0.7),
                            "source": getattr(of, "source_tool", "orchestrator"),
                            "recommendation": getattr(of, "recommendation", ""),
                            "poc": getattr(of, "poc_code", ""),
                        }
                    )
                combined["layers_used"].append("security_orchestrator")
                _orch_used = True
            except Exception as e:
                combined.setdefault("warnings", []).append(f"Orchestrator error: {e}")

        # Layer 2 fallback: Security Suite (if orchestrator unavailable)
        if not _orch_used and self._suite:
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
                combined.setdefault("warnings", []).append(
                    f"Layer 4 (detectors) error: {e}"
                )

        # ═══ State Extraction (L1) → Action Space (L2) → Attack Engine (L3) → Search Engine (L4) ═══
        if self._state_engine:
            try:
                state_result = self._state_engine.extract(file_path)
                if state_result and state_result.graph:
                    graph = state_result.graph

                    # L1: Financial Graph
                    combined["state_extraction"] = {
                        "entities": len(graph.entities),
                        "relationships": len(graph.relationships),
                        "fund_flows": len(graph.fund_flows),
                        "balances": len(graph.balances),
                    }
                    combined["layers_used"].append("state_extraction")

                    # L1+: Dynamic State Transition Model (Temporal Analysis)
                    if graph.temporal_analysis:
                        ta = graph.temporal_analysis
                        combined["temporal_analysis"] = {
                            "cei_violations": (
                                len(ta.cei_violations)
                                if hasattr(ta, "cei_violations")
                                else 0
                            ),
                            "reentrancy_risks": (
                                len(ta.reentrancy_risks)
                                if hasattr(ta, "reentrancy_risks")
                                else 0
                            ),
                            "write_conflicts": (
                                len(ta.write_conflicts)
                                if hasattr(ta, "write_conflicts")
                                else 0
                            ),
                            "effects_count": (
                                len(ta.effects) if hasattr(ta, "effects") else 0
                            ),
                            "mutations_count": (
                                len(ta.mutations) if hasattr(ta, "mutations") else 0
                            ),
                        }
                        combined["layers_used"].append("temporal_analysis")

                        # Convert temporal reentrancy risks to findings
                        for risk in (
                            ta.reentrancy_risks
                            if hasattr(ta, "reentrancy_risks")
                            else []
                        ):
                            combined.setdefault("temporal_findings", []).append(
                                {
                                    "title": f"Temporal reentrancy risk: {getattr(risk, 'description', str(risk)[:150])}",
                                    "severity": "high",
                                    "category": "temporal_reentrancy",
                                    "confidence": 0.8,
                                    "source": "temporal_analysis",
                                    "line": getattr(risk, "line", 0),
                                }
                            )

                        # Convert CEI violations to findings
                        for viol in (
                            ta.cei_violations if hasattr(ta, "cei_violations") else []
                        ):
                            combined.setdefault("temporal_findings", []).append(
                                {
                                    "title": f"CEI violation: {getattr(viol, 'description', str(viol)[:150])}",
                                    "severity": "high",
                                    "category": "cei_violation",
                                    "confidence": 0.85,
                                    "source": "temporal_analysis",
                                    "line": getattr(viol, "line", 0),
                                    "function": getattr(viol, "function", ""),
                                }
                            )

                    # L2: Action Space
                    if graph.action_space:
                        as_data = graph.action_space
                        as_graph = getattr(as_data, "graph", None)
                        actions_count = (
                            len(as_graph.actions)
                            if as_graph and hasattr(as_graph, "actions")
                            else 0
                        )
                        sequences = getattr(as_data, "attack_sequences", [])
                        surfaces = getattr(as_data, "attack_surfaces", [])
                        targets = getattr(as_data, "high_value_targets", [])

                        combined["action_space"] = {
                            "total_actions": actions_count,
                            "attack_sequences": len(sequences),
                            "attack_surfaces": len(surfaces),
                            "high_value_targets": len(targets),
                        }
                        combined["layers_used"].append("action_space")

                        # High-value targets → findings
                        for tgt in targets[:10]:
                            combined.setdefault("action_space_findings", []).append(
                                {
                                    "title": f"High-value attack target: {tgt.get('function', tgt.get('action', str(tgt)[:120]))}",
                                    "severity": tgt.get("severity", "high"),
                                    "category": "attack_surface",
                                    "confidence": tgt.get("confidence", 0.7),
                                    "source": "action_space",
                                    "line": tgt.get("line", 0),
                                    "details": tgt,
                                }
                            )

                    # L3: Attack Simulation
                    if graph.attack_simulation:
                        sim = graph.attack_simulation
                        combined["attack_simulation"] = {
                            "total_sequences_tested": getattr(
                                sim, "total_sequences_tested", 0
                            ),
                            "profitable_attacks": getattr(sim, "profitable_attacks", 0),
                            "total_profit_usd": getattr(sim, "total_profit_usd", 0),
                            "attack_types_found": getattr(
                                sim, "attack_types_found", {}
                            ),
                            "severity_distribution": getattr(
                                sim, "severity_distribution", {}
                            ),
                            "execution_time_ms": getattr(sim, "execution_time_ms", 0),
                        }
                        combined["layers_used"].append("attack_simulation")

                        # Best attack → finding
                        best = getattr(sim, "best_attack", None)
                        if best and getattr(best, "is_profitable", False):
                            combined.setdefault("attack_findings", []).append(
                                {
                                    "title": f"Profitable attack: {getattr(best, 'attack_type', 'unknown')} — ${getattr(best, 'net_profit_usd', 0):.2f} profit",
                                    "severity": getattr(best, "severity", "critical"),
                                    "category": "profitable_exploit",
                                    "confidence": 0.9,
                                    "source": "attack_simulation",
                                    "details": {
                                        "attack_type": getattr(best, "attack_type", ""),
                                        "net_profit_usd": getattr(
                                            best, "net_profit_usd", 0
                                        ),
                                        "steps": len(getattr(best, "steps", [])),
                                    },
                                }
                            )

                        # Top profitable attacks → findings (capped)
                        _profitable = sorted(
                            [
                                a
                                for a in getattr(sim, "all_results", [])
                                if getattr(a, "is_profitable", False) and a is not best
                            ],
                            key=lambda a: getattr(a, "net_profit_usd", 0),
                            reverse=True,
                        )[
                            :19
                        ]  # top 19 + best = max 20
                        for atk in _profitable:
                            combined.setdefault("attack_findings", []).append(
                                {
                                    "title": f"Profitable attack: {getattr(atk, 'attack_type', 'unknown')} — ${getattr(atk, 'net_profit_usd', 0):.2f}",
                                    "severity": getattr(atk, "severity", "high"),
                                    "category": "profitable_exploit",
                                    "confidence": 0.85,
                                    "source": "attack_simulation",
                                }
                            )

                    # L4: Search Engine
                    if graph.search_results:
                        sr = graph.search_results
                        profitable_seqs = getattr(sr, "profitable_sequences", [])
                        combined["search_results"] = {
                            "profitable_sequences": len(profitable_seqs),
                            "total_evaluated": getattr(sr, "total_evaluated", 0),
                            "strategies_used": [
                                str(s) for s in getattr(sr, "strategies_used", [])
                            ],
                        }
                        combined["layers_used"].append("search_engine")

                        # Best profitable sequence → finding
                        for seq in profitable_seqs[:5]:
                            combined.setdefault("search_findings", []).append(
                                {
                                    "title": f"Search-found exploit: {getattr(seq, 'description', str(seq)[:120])}",
                                    "severity": getattr(seq, "severity", "high"),
                                    "category": "search_exploit",
                                    "confidence": getattr(seq, "confidence", 0.85),
                                    "source": "search_engine",
                                    "profit_usd": getattr(seq, "profit_usd", 0),
                                }
                            )

                    # Validation issues from graph → findings
                    if graph.validation and hasattr(graph.validation, "issues"):
                        for issue in graph.validation.issues:
                            combined.setdefault("validation_findings", []).append(
                                {
                                    "title": f"Consistency: {getattr(issue, 'description', str(issue)[:120])}",
                                    "severity": getattr(issue, "severity", "medium"),
                                    "category": "consistency_violation",
                                    "confidence": 0.75,
                                    "source": "state_validator",
                                }
                            )

            except Exception as e:
                combined.setdefault("warnings", []).append(
                    f"State Extraction pipeline (L1→L4): {e}"
                )

        # ═══ Layer 5: Exploit Reasoning — إثبات الاستغلال ═══
        try:
            combined = self._run_exploit_reasoning(combined, file_path)
        except Exception as e:
            combined.setdefault("warnings", []).append(f"Exploit reasoning: {e}")

        # ═══ Cross-layer deduplication + confidence boosting ═══
        combined = self._deduplicate_and_cross_validate(combined)

        # ═══ Layer 5: LLM Deep Analysis on CRITICAL/HIGH findings ═══
        if not self.config.get("skip_llm", False):
            try:
                combined = self._llm_enrich_findings(combined, file_path)
            except Exception as e:
                combined.setdefault("warnings", []).append(f"LLM enrichment: {e}")

        combined["total_findings"] = len(combined.get("all_findings_unified", []))
        combined["total_before_dedup"] = (
            len(combined["findings"])
            + len(combined["suite_findings"])
            + len(combined["detector_findings"])
            + len(combined.get("symbolic_findings", []))
        )
        # Deduplicate layers_used list
        seen_layers = []
        for l in combined.get("layers_used", []):
            if l not in seen_layers:
                seen_layers.append(l)
        combined["layers_used"] = seen_layers
        combined["time_seconds"] = round(time.time() - t0, 2)
        return combined

    # ═══════════════════════════════════════════════════
    # Cross-layer deduplication
    # ═══════════════════════════════════════════════════

    @staticmethod
    def _find_project_root(file_path: str) -> Optional[str]:
        """Find the Solidity project root by looking for common markers."""
        import os

        d = os.path.dirname(os.path.abspath(file_path))
        markers = (
            "foundry.toml",
            "hardhat.config.js",
            "hardhat.config.ts",
            "brownie-config.yaml",
            "truffle-config.js",
            "remappings.txt",
            "package.json",
        )
        for _ in range(8):  # max 8 levels up
            if any(os.path.exists(os.path.join(d, m)) for m in markers):
                return d
            # Also check if there's a contracts/ directory
            if os.path.isdir(os.path.join(d, "contracts")):
                return d
            parent = os.path.dirname(d)
            if parent == d:
                break
            d = parent
        return None

    def _deduplicate_and_cross_validate(
        self, combined: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        دمج النتائج من كل الطبقات مع إزالة التكرارات وتعزيز الثقة.
        Multi-source confirmed findings get boosted confidence.
        """
        seen: Dict[tuple, Dict] = {}  # (line, category_key) -> merged finding

        def _norm_cat(cat: str) -> str:
            cat = cat.lower().replace("-", "_").replace(" ", "_")
            for key in (
                "reentrancy",
                "access",
                "overflow",
                "underflow",
                "arithmetic",
                "delegatecall",
                "timestamp",
                "unchecked",
                "zero_address",
                "oracle",
                "flash_loan",
                "first_deposit",
                "price_stale",
                "divide_before",
                "logic",
                "token",
                "erc20",
            ):
                if key in cat:
                    return key
            return cat

        def _conf_float(val) -> float:
            """Normalize confidence to float (detectors use 'high'/'medium'/'low')."""
            if isinstance(val, (int, float)):
                return float(val)
            return {"high": 0.9, "medium": 0.7, "low": 0.5}.get(str(val).lower(), 0.5)

        def _process(findings_list: list, source_label: str):
            for f in findings_list:
                line = f.get("line", 0)
                cat = _norm_cat(
                    f.get("category", f.get("detector", f.get("detector_id", "")))
                )
                # Use line-bucket (within 20 lines = same finding) for cross-layer match
                line_bucket = line // 20
                key = (line_bucket, cat)

                if key in seen:
                    existing = seen[key]
                    sources = existing.setdefault("confirmed_by", [])
                    if source_label not in sources:
                        sources.append(source_label)
                    # Boost confidence for multi-source confirmation
                    existing["confidence"] = min(
                        1.0, _conf_float(existing.get("confidence", 0.7)) + 0.1
                    )
                    # Keep better description
                    if len(f.get("description", "")) > len(
                        existing.get("description", "")
                    ):
                        existing["description"] = f["description"]
                    # Keep higher severity
                    sev_rank = {
                        "critical": 0,
                        "high": 1,
                        "medium": 2,
                        "low": 3,
                        "info": 4,
                    }
                    if sev_rank.get(f.get("severity", "info"), 4) < sev_rank.get(
                        existing.get("severity", "info"), 4
                    ):
                        existing["severity"] = f["severity"]
                else:
                    merged = dict(f)
                    merged["confirmed_by"] = [source_label]
                    merged["confidence"] = _conf_float(merged.get("confidence", 0.7))
                    seen[key] = merged

        _process(combined.get("findings", []), "pattern_engine")
        _process(combined.get("suite_findings", []), "security_suite")
        _process(combined.get("detector_findings", []), "agl_22_detectors")
        _process(combined.get("symbolic_findings", []), "z3_symbolic")
        _process(combined.get("offensive_findings", []), "offensive_security")
        _process(combined.get("temporal_findings", []), "temporal_analysis")
        _process(combined.get("action_space_findings", []), "action_space")
        _process(combined.get("attack_findings", []), "attack_simulation")
        _process(combined.get("search_findings", []), "search_engine")
        _process(combined.get("validation_findings", []), "state_validator")

        # Sort: severity ▶ confidence descending
        sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        unified = sorted(
            seen.values(),
            key=lambda x: (
                sev_order.get(x.get("severity", "info"), 4),
                -x.get("confidence", 0),
            ),
        )

        # Recount severities from unified list
        combined["severity_summary"] = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for f in unified:
            sev = f.get("severity", "low").upper()
            if sev in combined["severity_summary"]:
                combined["severity_summary"][sev] += 1

        combined["all_findings_unified"] = unified
        combined["duplicates_removed"] = (
            len(combined.get("findings", []))
            + len(combined.get("suite_findings", []))
            + len(combined.get("detector_findings", []))
            + len(combined.get("symbolic_findings", []))
            + len(combined.get("temporal_findings", []))
            + len(combined.get("action_space_findings", []))
            + len(combined.get("attack_findings", []))
            + len(combined.get("search_findings", []))
            + len(combined.get("validation_findings", []))
            - len(unified)
        )
        return combined

    # ═══════════════════════════════════════════════════
    # Project Root Detection
    # ═══════════════════════════════════════════════════

    @staticmethod
    def _detect_project_root(file_path: str) -> Optional[str]:
        """اكتشاف جذر المشروع بالصعود من مسار الملف."""
        markers = [
            "foundry.toml",
            "hardhat.config.ts",
            "hardhat.config.js",
            "truffle-config.js",
            "brownie-config.yaml",
            "remappings.txt",
            "package.json",
        ]
        current = Path(file_path).parent
        for _ in range(10):
            for marker in markers:
                if (current / marker).exists():
                    return str(current)
            parent = current.parent
            if parent == current:
                break
            current = parent
        return None

    # ═══════════════════════════════════════════════════
    # Layer 5: Exploit Reasoning — طبقة إثبات الاستغلال
    # ═══════════════════════════════════════════════════

    def _run_exploit_reasoning(
        self, combined: Dict[str, Any], file_path: str
    ) -> Dict[str, Any]:
        """
        Run exploit reasoning on all findings to prove exploitability.
        Pipeline: findings → paths → Z3 → invariants → exploit assembly
        """
        from agl_security_tool.exploit_reasoning import ExploitReasoningEngine

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                source_code = f.read()
        except Exception:
            return combined

        engine = ExploitReasoningEngine()

        # Collect all findings into a flat list for analysis
        all_findings = []
        for f in combined.get("findings", []):
            all_findings.append(f)
        for f in combined.get("suite_findings", []):
            all_findings.append(f)
        for f in combined.get("detector_findings", []):
            all_findings.append(f)

        if not all_findings:
            return combined

        result = engine.analyze(all_findings, source_code, file_path)

        combined["exploit_reasoning"] = result
        combined["layers_used"].append("exploit_reasoning")

        # Inject exploit_proof into matching findings (boost confirmed exploits)
        proofs_by_func = {}
        for ep in result.get("exploit_proofs", []):
            proofs_by_func[ep.get("function", "").lower()] = ep

        for flist_key in ("findings", "suite_findings", "detector_findings"):
            for f in combined.get(flist_key, []):
                fn = f.get("function", "").lower()
                title = f.get("title", "").lower()
                for pf_name, proof_data in proofs_by_func.items():
                    if pf_name in fn or pf_name in title or fn in pf_name:
                        f["exploit_proof"] = proof_data
                        if proof_data.get("exploitable"):
                            # Boost severity and confidence for proven exploits
                            f["severity"] = "critical"
                            old_conf = f.get("confidence", 0.7)
                            if isinstance(old_conf, str):
                                old_conf = {"high": 0.9, "medium": 0.7, "low": 0.5}.get(
                                    old_conf, 0.7
                                )
                            f["confidence"] = min(1.0, float(old_conf) + 0.15)
                        break

        return combined

    # ═══════════════════════════════════════════════════
    # LLM enrichment
    # ═══════════════════════════════════════════════════

    def _llm_enrich_findings(
        self, combined: Dict[str, Any], file_path: str
    ) -> Dict[str, Any]:
        """
        تحليل عميق بالنموذج اللغوي — يضيف لكل ثغرة CRITICAL/HIGH:
        - llm_explanation: شرح مفصل للثغرة
        - fix: اقتراح إصلاح محدد
        - poc: كود PoC إن أمكن
        Uses a SINGLE batch LLM call (not per-finding) to avoid cold-start timeouts.
        """
        unified = combined.get("all_findings_unified", [])
        if not unified:
            return combined

        # Read code once
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                source_code = f.read()
            source_lines = source_code.split("\n")
        except Exception:
            return combined

        # Select CRITICAL/HIGH findings to enrich (max 5 to keep prompt reasonable)
        to_enrich = [
            f for f in unified if f.get("severity", "").lower() in ("critical", "high")
        ][:5]
        if not to_enrich:
            return combined

        # Build batch prompt with code context for each finding
        findings_desc = []
        for i, f in enumerate(to_enrich, 1):
            line = f.get("line", 0)
            ctx_start = max(0, line - 5)
            ctx_end = min(len(source_lines), line + 10)
            code_ctx = "\n".join(source_lines[ctx_start:ctx_end])
            findings_desc.append(
                f"### Code Issue {i}\n"
                f"- Priority: {f.get('severity','?').upper()}\n"
                f"- Line: {line}\n"
                f"- Title: {f.get('title','?')}\n"
                f"- Detail: {f.get('description','')[:200]}\n"
                f"```solidity\n{code_ctx}\n```"
            )

        system_msg = (
            "You are a senior Solidity code reviewer performing a quality and correctness audit. "
            "Your job is to help developers write safer, more robust smart contracts.\n"
            "For EACH code issue below, provide a thorough technical review.\n\n"
            "RESPOND with a JSON array where each element has:\n"
            '- "id": issue number (integer)\n'
            '- "explanation": detailed technical explanation of the code issue, '
            "why it matters, and what could go wrong in production\n"
            '- "fix": concrete Solidity code improvement (actual code, not description)\n'
            '- "poc": a test scenario demonstrating the issue '
            "(Foundry/Hardhat test code)\n\n"
            "IMPORTANT: Write real technical analysis. "
            "Focus on code correctness and edge cases."
        )
        user_msg = "\n\n".join(findings_desc)

        # ── Attempt 1: Direct Ollama /api/chat (single batch call) ──
        ollama_available = False
        if (
            self._orchestrator
            and hasattr(self._orchestrator, "llm")
            and self._orchestrator.llm
        ):
            if self._orchestrator.llm.available:
                ollama_available = True

        if ollama_available:
            try:
                import requests as _req

                resp = _req.post(
                    "http://localhost:11434/api/chat",
                    json={
                        "model": "qwen2.5:3b-instruct",
                        "messages": [
                            {"role": "system", "content": system_msg},
                            {"role": "user", "content": user_msg},
                        ],
                        "stream": False,
                    },
                    timeout=180,  # 3min for cold-start + generation
                )
                if resp.status_code == 200:
                    raw = resp.json().get("message", {}).get("content", "")
                    # Reject template-only responses (model echoed placeholders)
                    if raw and len(raw) > 100 and '"..."' not in raw:
                        combined["layers_used"].append("llm_analysis")
                        combined["llm_raw_response"] = raw[:3000]
                        combined["llm_source"] = "ollama_direct"
                        self._apply_llm_response(raw, to_enrich)
                        return combined
            except Exception as _e:
                combined.setdefault("warnings", []).append(
                    f"LLM Strategy 1 (Ollama direct): {_e}"
                )

        # ── Attempt 2: HolographicLLM batch (offensive engine) ──
        if (
            self._engine
            and hasattr(self._engine, "holo_brain")
            and self._engine.holo_brain
        ):
            try:
                messages = [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                ]
                raw = self._engine.holo_brain.chat_llm(
                    messages, max_new_tokens=2000, temperature=0.3
                )
                if raw and len(raw) > 100 and '"..."' not in raw:
                    combined["layers_used"].append("llm_analysis")
                    combined["llm_raw_response"] = raw[:3000]
                    combined["llm_source"] = "holographic_llm"
                    self._apply_llm_response(raw, to_enrich)
                    return combined
                elif raw:
                    # Template response — try direct Ollama /api/generate as last resort
                    import requests as _req2

                    resp2 = _req2.post(
                        "http://localhost:11434/api/generate",
                        json={
                            "model": "qwen2.5:3b-instruct",
                            "prompt": (
                                "You are a senior Solidity code reviewer.\n\n"
                                + user_msg
                                + "\n\n"
                                "Respond with detailed JSON analysis for each code issue. "
                                "Each entry: {id, explanation, fix, poc}. "
                                "Focus on correctness, edge cases, and code quality."
                            ),
                            "stream": False,
                        },
                        timeout=180,
                    )
                    if resp2.status_code == 200:
                        raw2 = resp2.json().get("response", "")
                        if raw2 and len(raw2) > 100:
                            combined["layers_used"].append("llm_analysis")
                            combined["llm_raw_response"] = raw2[:3000]
                            combined["llm_source"] = "ollama_generate_fallback"
                            self._apply_llm_response(raw2, to_enrich)
                            return combined
            except Exception as _e2:
                combined.setdefault("warnings", []).append(f"LLM Strategy 2: {_e2}")

        return combined

    def _apply_llm_response(self, raw: str, findings: list):
        """Parse LLM JSON response and enrich findings."""
        import re as _re

        # Clean control characters that break JSON parsing
        cleaned = raw.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
        cleaned = cleaned.replace("\t", " ")
        # Remove non-printable chars except spaces
        cleaned = "".join(c if c.isprintable() or c == " " else " " for c in cleaned)

        # Try to extract JSON array from response
        arr_match = _re.search(r"\[.*\]", cleaned, _re.DOTALL)
        if arr_match:
            try:
                parsed = json.loads(arr_match.group(), strict=False)
                # Handle nested arrays: [[{...}], [{...}]] → [{...}, {...}]
                items = []
                for item in parsed:
                    if isinstance(item, list):
                        items.extend(item)
                    elif isinstance(item, dict):
                        items.append(item)

                for item in items:
                    if not isinstance(item, dict):
                        continue
                    idx = item.get("id", 0)
                    if isinstance(idx, int) and 1 <= idx <= len(findings):
                        target_f = findings[idx - 1]
                        if item.get("fix"):
                            target_f["fix"] = str(item["fix"])
                        if item.get("poc"):
                            target_f["poc"] = str(item["poc"])
                        if item.get("explanation"):
                            target_f["llm_explanation"] = str(item["explanation"])
                return
            except (json.JSONDecodeError, ValueError):
                pass

        # Try single JSON object (model returned one object instead of array)
        obj_match = _re.search(
            r'\{[^{}]*"(?:fix|explanation|poc)"[^{}]*\}', cleaned, _re.DOTALL
        )
        if obj_match:
            try:
                data = json.loads(obj_match.group(), strict=False)
                if data.get("fix"):
                    findings[0]["fix"] = str(data["fix"])
                if data.get("poc"):
                    findings[0]["poc"] = str(data["poc"])
                if data.get("explanation"):
                    findings[0]["llm_explanation"] = str(data["explanation"])
                return
            except (json.JSONDecodeError, ValueError):
                pass

        # Raw text fallback — attach to first finding
        if len(raw.strip()) > 20 and findings:
            findings[0]["llm_explanation"] = raw[:2000]

        return

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
                results["severity_summary"][sev] += r.get("severity_summary", {}).get(
                    sev, 0
                )

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
                    lines.append(
                        f"           {desc[:120]}{'...' if len(desc) > 120 else ''}"
                    )

        # Offensive Security Findings (deep mode)
        offensive = result.get("offensive_findings", [])
        if offensive:
            lines.append(f"\n  ⚔️ Offensive Engine ({len(offensive)}):")
            for f in offensive:
                sev = f.get("severity", "?").upper()
                proven = " ✅PROVEN" if f.get("mathematically_proven") else ""
                title = f.get("title", "Unknown")[:100]
                lines.append(f"    [{sev}]{proven} {title}")

        # EVM Simulation (deep mode)
        evm = result.get("evm_simulation", {})
        if evm and evm.get("call_chains"):
            chains = evm["call_chains"]
            lines.append(f"\n  🔗 EVM Call Chain Simulation ({len(chains)} chains):")
            for chain in chains[:10]:
                danger = "🔴" if chain.get("danger_level") == "DANGEROUS" else "🟢"
                label = chain.get("chain_label", chain.get("label", "Unknown"))
                lines.append(f"    {danger} {label}")
                z3p = chain.get("z3_proof", {})
                if z3p:
                    lines.append(f"         Z3: {z3p.get('result', '')}")

        # Quantum Findings (deep mode)
        quantum = result.get("quantum_findings", [])
        if quantum:
            lines.append(f"\n  🧿 Quantum Deep Audit ({len(quantum)}):")
            for q in quantum[:5]:
                conf = q.get("confidence", "?")
                vector = q.get("vector", "Unknown")[:100]
                lines.append(f"    [{conf}] {vector}")

        # Unified Findings (post-deduplication cross-validated)
        unified = result.get("all_findings_unified", [])
        if unified:
            lines.append(f"\n  🎯 Unified Findings ({len(unified)}, deduplicated):")
            for f in unified:
                sev = f.get("severity", "?").upper()
                title = f.get("title", f.get("text", f.get("description", "Unknown")))[
                    :100
                ]
                conf = f.get("confidence", 0)
                sources = f.get("confirmed_by", [])
                src_str = "+".join(s[:10] for s in sources) if sources else "?"
                proven = " ✅" if f.get("mathematically_proven") else ""
                lines.append(f"    [{sev:>8}] ({conf:.0%}) [{src_str}]{proven} {title}")

        # Layers Used
        layers = result.get("layers_used", [])
        if layers:
            lines.append(f"\n  ⚙️ Layers Active ({len(layers)}): {', '.join(layers)}")

        # Summary
        summary = result.get("severity_summary", {})
        lines.append(f"\n  📊 Summary:")
        lines.append(f"    CRITICAL: {summary.get('CRITICAL', 0)}")
        lines.append(f"    HIGH:     {summary.get('HIGH', 0)}")
        lines.append(f"    MEDIUM:   {summary.get('MEDIUM', 0)}")
        lines.append(f"    LOW:      {summary.get('LOW', 0)}")
        if result.get("scan_mode") == "deep":
            lines.append(f"    ─────────")
            lines.append(f"    Total unified: {len(unified)}")
            proven_count = sum(1 for f in unified if f.get("mathematically_proven"))
            if proven_count:
                lines.append(f"    Mathematically proven: {proven_count}")
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
