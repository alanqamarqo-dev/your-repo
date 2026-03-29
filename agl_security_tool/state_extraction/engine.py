"""
AGL State Extraction — Main Engine
المحرك الرئيسي لاستخراج الحالة المالية

يربط كل المكونات في واجهة موحدة:
  1. يحلل Solidity (parser + flattener)
  2. يستخرج الكيانات (EntityExtractor)
  3. يرسم العلاقات (RelationshipMapper)
  4. يبني خريطة الأموال (FundMapper)
  5. يبني الرسم البياني (FinancialGraphBuilder)
  6. يتحقق من التناسق (ConsistencyValidator)
  7. يصدّر JSON ديناميكي

Usage:
    engine = StateExtractionEngine()

    # من ملف واحد
    result = engine.extract("path/to/contract.sol")

    # من مجلد مشروع كامل
    result = engine.extract_project("path/to/project/")

    # من كود مباشر
    result = engine.extract_source(solidity_code)

    # تصدير JSON
    json_str = result.to_json()
"""

import os
import time
import json
from typing import Dict, List, Optional, Any
from pathlib import Path

from .models import (
    FinancialGraph,
    ExtractionResult,
    TemporalAnalysis,
)
from .entity_extractor import EntityExtractor
from .relationship_mapper import RelationshipMapper
from .fund_mapper import FundMapper
from .financial_graph import FinancialGraphBuilder
from .validator import ConsistencyValidator
from .execution_semantics import ExecutionSemanticsExtractor
from .state_mutation import StateMutationTracker
from .function_effects import FunctionEffectModeler
from .temporal_graph import TemporalDependencyGraph

# Layer 2: Action Space Builder
try:
    from agl_security_tool.action_space import ActionSpaceBuilder
except ImportError:
    try:
        from action_space import ActionSpaceBuilder
    except ImportError:
        ActionSpaceBuilder = None

# Layer 3: Attack Simulation Engine
try:
    from agl_security_tool.attack_engine import AttackSimulationEngine
except ImportError:
    try:
        from attack_engine import AttackSimulationEngine
    except ImportError:
        AttackSimulationEngine = None

# Layer 4: Search Engine (Intelligent Economic Search)
try:
    from agl_security_tool.search_engine import SearchOrchestrator
except ImportError:
    try:
        from search_engine import SearchOrchestrator
    except ImportError:
        SearchOrchestrator = None

# Import existing parsers — use package-qualified imports with fallback;
# avoid sys.path manipulation which can cause import shadowing.
try:
    from agl_security_tool.detectors.solidity_parser import SoliditySemanticParser
    from agl_security_tool.detectors import ParsedContract
except ImportError:
    try:
        from detectors.solidity_parser import SoliditySemanticParser
        from detectors import ParsedContract
    except ImportError:
        # Last resort: add parent to path (legacy compat)
        import sys as _sys

        _TOOL_DIR = Path(__file__).parent.parent.resolve()
        if str(_TOOL_DIR) not in _sys.path:
            _sys.path.insert(0, str(_TOOL_DIR))
        from detectors.solidity_parser import SoliditySemanticParser
        from detectors import ParsedContract

try:
    from solidity_flattener import SolidityFlattener
except ImportError:
    try:
        from agl_security_tool.solidity_flattener import SolidityFlattener
    except ImportError:
        SolidityFlattener = None


class StateExtractionEngine:
    """
    Main engine for extracting financial state from smart contracts.
    المحرك الرئيسي لاستخراج الحالة المالية من العقود الذكية.

    Builds a dynamic financial graph containing:
    يبني رسماً بيانياً مالياً ديناميكياً يحتوي على:
    - All financial entities (Tokens, Pools, Vaults, Oracles, Governance...)
    - All relationships (Access Control, Fund Flow, Price Dependencies, Structural)
    - Balance ledger (خريطة الأرصدة)
    - Capital flows (تدفقات رأس المال)
    - Validation results (نتائج التحقق من التناسق)

    Usage:
        engine = StateExtractionEngine()
        result = engine.extract("contract.sol")
        print(result.to_json())
    """

    VERSION = "5.0.0"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        تهيئة المحرك.

        Args:
            config: إعدادات اختيارية
                - flatten: bool — هل يتم دمج الاستيرادات (default: True)
                - validate: bool — هل يتم التحقق من التناسق (default: True)
                - temporal: bool — هل يتم بناء التحليل الزمني (default: True)
                - project_root: str — جذر المشروع (لحل الاستيرادات)
        """
        self.config = config or {}
        self._parser = SoliditySemanticParser()
        self._entity_extractor = EntityExtractor()
        self._relationship_mapper = RelationshipMapper()
        self._fund_mapper = FundMapper()
        self._graph_builder = FinancialGraphBuilder()
        self._validator = ConsistencyValidator()

        # === Dynamic State Transition Model (الناقد طلب هذا) ===
        self._exec_semantics = ExecutionSemanticsExtractor()
        self._mutation_tracker = StateMutationTracker()
        self._effect_modeler = FunctionEffectModeler()
        self._temporal_graph = TemporalDependencyGraph()

        # === Layer 2: Action Space Builder ===
        self._action_builder = None
        if ActionSpaceBuilder and self.config.get("action_space", True):
            self._action_builder = ActionSpaceBuilder(config)

        # === Layer 3: Attack Simulation Engine ===
        self._attack_engine = None
        if AttackSimulationEngine and self.config.get("attack_simulation", True):
            self._attack_engine = AttackSimulationEngine(config)

        # === Layer 4: Search Engine ===
        self._search_engine = None
        if SearchOrchestrator and self.config.get("search_engine", True):
            self._search_engine = SearchOrchestrator(config)

        # Flattener (إذا كان متاحاً)
        self._flattener = None
        project_root = self.config.get("project_root", "")
        if SolidityFlattener and project_root:
            try:
                self._flattener = SolidityFlattener(project_root)
            except Exception:
                pass

    # ═══════════════════════════════════════════════════════════
    #  Main Extraction APIs
    # ═══════════════════════════════════════════════════════════

    def extract(self, file_path: str, pre_parsed=None) -> ExtractionResult:
        """
        استخراج الحالة المالية من ملف Solidity واحد.

        Args:
            file_path: مسار ملف .sol
            pre_parsed: قائمة ParsedContract اختيارية من shared_parse

        Returns:
            ExtractionResult مع الرسم البياني المالي
        """
        start_time = time.time()
        result = ExtractionResult()

        try:
            # قراءة الملف
            source = self._read_file(file_path)
            if not source:
                result.success = False
                result.errors.append(f"لا يمكن قراءة الملف: {file_path}")
                return result

            # محاولة دمج الاستيرادات
            if self._flattener and self.config.get("flatten", True):
                try:
                    flat_result = self._flattener.flatten(file_path)
                    if flat_result and flat_result.source:
                        source = flat_result.source
                        result.warnings.append(
                            f"تم دمج {len(flat_result.files_included)} ملف"
                        )
                except Exception as e:
                    result.warnings.append(f"تنبيه: فشل الدمج — {str(e)[:100]}")

            # تنفيذ الاستخراج
            graph = self._extract_from_source(source, file_path, result, pre_parsed=pre_parsed)

            # تعيين النتائج
            if graph:
                graph.extraction_time = time.time() - start_time
                graph.source_files = [file_path]
                graph.engine_version = self.VERSION
                result.graph = graph

        except Exception as e:
            result.success = False
            result.errors.append(f"خطأ في الاستخراج: {str(e)[:200]}")

        return result

    def extract_source(
        self, source: str, file_path: str = "<source>"
    ) -> ExtractionResult:
        """
        استخراج الحالة المالية من كود Solidity مباشرةً.

        Args:
            source: كود Solidity
            file_path: مسار افتراضي للتقارير

        Returns:
            ExtractionResult
        """
        start_time = time.time()
        result = ExtractionResult()

        try:
            graph = self._extract_from_source(source, file_path, result)
            if graph:
                graph.extraction_time = time.time() - start_time
                graph.source_files = [file_path]
                graph.engine_version = self.VERSION
                result.graph = graph
        except Exception as e:
            result.success = False
            result.errors.append(f"خطأ في الاستخراج: {str(e)[:200]}")

        return result

    def extract_project(self, project_dir: str) -> ExtractionResult:
        """
        استخراج الحالة المالية من مشروع كامل.
        يفحص كل ملفات .sol في المشروع ويدمجها في رسم بياني واحد.

        Args:
            project_dir: مسار مجلد المشروع

        Returns:
            ExtractionResult — رسم بياني موحد
        """
        start_time = time.time()
        result = ExtractionResult()

        try:
            # جمع كل ملفات Solidity
            sol_files = self._find_sol_files(project_dir)
            if not sol_files:
                result.success = False
                result.errors.append(f"لا توجد ملفات .sol في: {project_dir}")
                return result

            # Initialize flattener for project
            if SolidityFlattener and not self._flattener:
                try:
                    self._flattener = SolidityFlattener(project_dir)
                except Exception:
                    pass

            # استخراج من كل ملف
            all_graphs: List[FinancialGraph] = []
            for sol_file in sol_files:
                try:
                    file_result = self.extract(sol_file)
                    if file_result.graph:
                        all_graphs.append(file_result.graph)
                    result.errors.extend(file_result.errors)
                    result.warnings.extend(file_result.warnings)
                except Exception as e:
                    result.warnings.append(
                        f"تنبيه: فشل تحليل {os.path.basename(sol_file)}: {str(e)[:100]}"
                    )

            # دمج كل الرسومات
            if all_graphs:
                merged = self._graph_builder.merge_graphs(*all_graphs)
                merged.extraction_time = time.time() - start_time
                merged.source_files = sol_files
                merged.engine_version = self.VERSION

                # تحقق من التناسق
                if self.config.get("validate", True):
                    merged.validation = self._validator.validate(merged)
                    result.validation_issues = len(merged.validation.issues)

                result.graph = merged
                result.contracts_parsed = len(merged.entities)
                result.entities_found = len(merged.entities)
                result.relationships_found = len(merged.relationships)
                result.fund_flows_found = len(merged.fund_flows)
            else:
                result.success = False
                result.errors.append("فشل تحليل كل الملفات")

        except Exception as e:
            result.success = False
            result.errors.append(f"خطأ في تحليل المشروع: {str(e)[:200]}")

        return result

    # ═══════════════════════════════════════════════════════════
    #  Core Extraction Pipeline
    # ═══════════════════════════════════════════════════════════

    def _extract_from_source(
        self,
        source: str,
        file_path: str,
        result: ExtractionResult,
        pre_parsed=None,
    ) -> Optional[FinancialGraph]:
        """
        Pipeline الاستخراج الأساسي:
          parse → extract entities → map relationships → map funds →
          build graph → execution semantics → state mutations →
          function effects → temporal graph → validate → JSON

        v2.0: يشمل الآن Dynamic State Transition Model
        """
        # ─── Step 1: Parse Solidity (reuse shared_parse if available) ───
        contracts = pre_parsed if pre_parsed else self._parser.parse(source, file_path)
        if not contracts:
            result.warnings.append(f"لم يُعثر على عقود في: {file_path}")
            return None

        result.contracts_parsed = len(contracts)

        # ─── Step 2: Extract Entities ───
        entities = self._entity_extractor.extract_from_contracts(contracts, file_path)
        result.entities_found = len(entities)

        # ─── Step 3: Map Relationships ───
        relationships = self._relationship_mapper.map_relationships(entities, contracts)
        result.relationships_found = len(relationships)

        # ─── Step 4: Map Funds ───
        balances, fund_flows = self._fund_mapper.map_funds(
            entities, contracts, relationships
        )
        result.fund_flows_found = len(fund_flows)

        # ─── Step 5: Build Financial Graph ───
        graph = self._graph_builder.build(
            entities=entities,
            relationships=relationships,
            balances=balances,
            fund_flows=fund_flows,
            source_files=[file_path],
        )

        # ─── Step 6: Validate ───
        if self.config.get("validate", True):
            graph.validation = self._validator.validate(graph)
            result.validation_issues = len(graph.validation.issues)

        # ─── Step 7: Dynamic State Transition Model ───
        temporal = None
        if self.config.get("temporal", True):
            try:
                temporal = self._build_temporal_analysis(contracts)
                graph.temporal_analysis = temporal
            except Exception as e:
                result.warnings.append(f"تنبيه: فشل التحليل الزمني — {str(e)[:150]}")

        # ─── Step 8: Action Space (Layer 2) ───
        if self._action_builder and self.config.get("action_space", True):
            try:
                action_space = self._action_builder.build(contracts, graph, temporal)
                graph.action_space = action_space
            except Exception as e:
                result.warnings.append(f"تنبيه: فشل بناء مساحة الهجوم — {str(e)[:150]}")

        # ─── Step 9: Attack Simulation (Layer 3) ───
        if (
            self._attack_engine
            and graph.action_space
            and self.config.get("attack_simulation", True)
        ):
            try:
                simulation = self._attack_engine.simulate_all(graph, graph.action_space)
                graph.attack_simulation = simulation
            except Exception as e:
                result.warnings.append(f"تنبيه: فشل محاكاة الهجوم — {str(e)[:150]}")

        # ─── Step 10: Intelligent Search (Layer 4) ───
        if (
            self._search_engine
            and self._attack_engine
            and graph.action_space
            and self.config.get("search_engine", True)
        ):
            try:
                search_result = self._search_engine.search(
                    graph, graph.action_space, self._attack_engine
                )
                graph.search_results = search_result
            except Exception as e:
                result.warnings.append(f"تنبيه: فشل البحث الذكي — {str(e)[:150]}")

        return graph

    # ═══════════════════════════════════════════════════════════
    #  Dynamic State Transition Model Pipeline
    # ═══════════════════════════════════════════════════════════

    def _build_temporal_analysis(
        self, contracts: List[ParsedContract]
    ) -> TemporalAnalysis:
        """
        بناء التحليل الزمني الكامل — يجيب على النقد:

        1. Execution Semantics — ترتيب العمليات داخل كل دالة
        2. State Mutations — State(t+1) = State(t) + Σ(deltas)
        3. Function Effects — ΔState = f(inputs)
        4. Temporal Dependencies — متى تحدث التغييرات بالنسبة لأحداث أخرى
        """
        # Step 7a: Execution Semantics
        timelines = self._exec_semantics.extract(contracts)

        # Step 7b: State Mutations
        mutations = self._mutation_tracker.track(contracts)

        # Step 7c: Function Effects
        effects = self._effect_modeler.model(contracts, mutations)

        # Step 7d: Temporal Dependency Graph
        analysis = self._temporal_graph.build(timelines, mutations, effects, contracts)

        return analysis

    # ═══════════════════════════════════════════════════════════
    #  JSON Export
    # ═══════════════════════════════════════════════════════════

    def to_json(self, result: ExtractionResult, indent: int = 2) -> str:
        """تصدير النتيجة الكاملة كـ JSON"""
        return result.to_json(indent=indent)

    def export_graph_json(self, graph: FinancialGraph, indent: int = 2) -> str:
        """تصدير الرسم البياني فقط كـ JSON"""
        return graph.to_json(indent=indent)

    def save_json(self, result: ExtractionResult, output_path: str) -> str:
        """حفظ النتيجة في ملف JSON"""
        json_str = result.to_json(indent=2)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(json_str)
        return output_path

    # ═══════════════════════════════════════════════════════════
    #  Utilities
    # ═══════════════════════════════════════════════════════════

    def _read_file(self, file_path: str) -> Optional[str]:
        """قراءة ملف Solidity"""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception:
            return None

    def _find_sol_files(self, project_dir: str) -> List[str]:
        """
        جمع كل ملفات .sol من المشروع.
        يستثني: test, mock, node_modules, lib, out, cache
        """
        sol_files = []
        exclude_dirs = {
            "node_modules",
            "lib",
            "out",
            "cache",
            "artifacts",
            ".git",
            "__pycache__",
            "forge-cache",
        }
        exclude_patterns = {"test", "mock", "script", "Test", "Mock"}

        for root, dirs, files in os.walk(project_dir):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            # Check if path contains test/mock
            rel_path = os.path.relpath(root, project_dir)
            if any(p in rel_path for p in exclude_patterns):
                continue

            for fname in files:
                if fname.endswith(".sol") and not any(
                    p in fname for p in ["Test", "test", "Mock", "mock"]
                ):
                    sol_files.append(os.path.join(root, fname))

        return sol_files

    # ═══════════════════════════════════════════════════════════
    #  Summary & Info
    # ═══════════════════════════════════════════════════════════

    def get_info(self) -> Dict[str, Any]:
        """معلومات عن المحرك"""
        return {
            "name": "AGL State Extraction Engine",
            "version": self.VERSION,
            "components": {
                "parser": "SoliditySemanticParser",
                "entity_extractor": "EntityExtractor",
                "relationship_mapper": "RelationshipMapper",
                "fund_mapper": "FundMapper",
                "graph_builder": "FinancialGraphBuilder",
                "validator": "ConsistencyValidator",
                "flattener": "SolidityFlattener" if self._flattener else "N/A",
                "execution_semantics": "ExecutionSemanticsExtractor",
                "state_mutation": "StateMutationTracker",
                "function_effects": "FunctionEffectModeler",
                "temporal_graph": "TemporalDependencyGraph",
            },
            "capabilities": [
                "Solidity parsing & entity extraction",
                "Token/Pool/Vault/Oracle/Governance detection",
                "Access control relationship mapping",
                "Fund flow analysis",
                "Balance ledger construction",
                "Dynamic financial graph",
                "Consistency validation",
                "Cycle detection",
                "JSON export/import",
                "Project-wide analysis",
                "Import flattening",
                # === Dynamic State Transition Model ===
                "Execution semantics extraction (operation ordering)",
                "CEI violation detection (reentrancy patterns)",
                "State mutation tracking: State(t+1) = State(t) + Σ(deltas)",
                "Function effect modeling: ΔState = f(inputs)",
                "Temporal dependency graph",
                "Cross-function reentrancy detection",
                "Write-write conflict detection",
                "Attack surface analysis",
                # === Layer 2: Action Space ===
                "Action enumeration from callable functions",
                "Strategic parameter variant generation",
                "State-aware action linking",
                "Attack type classification",
                "Action dependency graph construction",
                "Attack sequence extraction",
            ],
        }
