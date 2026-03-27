"""
AGL State Extraction Engine — Layer 1 + Dynamic State Transition Model + Action Space
محرك استخراج الحالة المالية من العقود الذكية

يبني رسماً بيانياً مالياً ديناميكياً من كود Solidity يتضمن:
  1. Entity Extraction — استخراج الكيانات (Tokens, Pools, Balances, Debt, Governance)
  2. Relationship Mapping — رسم العلاقات (Access Control, Fund Flow, Oracle Links)
  3. Fund Mapping — خريطة الأموال والأرصدة لكل حساب/عقد
  4. Financial Graph — رسم بياني مالي ديناميكي قابل للتحديث أثناء المحاكاة
  5. Validation — التحقق من تناسق الأرصدة واكتشاف الدورات غير المنطقية
  6. Execution Semantics — ترتيب العمليات واكتشاف CEI violations
  7. State Mutations — State(t+1) = State(t) + Σ(deltas) per function
  8. Function Effects — ΔState = f(inputs) with cross-function dependencies
  9. Temporal Graph — رسم التبعيات الزمنية واكتشاف reentrancy/conflicts
 10. Action Space Builder — بناء فضاء الأفعال (Layer 2) لتصنيف الهجمات وتوليد مسارات الاستغلال
 11. Attack Simulation Engine — محرك الفيزياء الاقتصادية (Layer 3) لحساب ربح المهاجم
 12. Search Engine — البحث الاقتصادي الذكي (Layer 4) لإيجاد تسلسلات هجوم مربحة

Usage:
    from agl_security_tool.state_extraction import StateExtractionEngine
    engine = StateExtractionEngine()
    result = engine.extract("path/to/contract.sol")
    # الـ result يحتوي graph.temporal_analysis مع كل التحليل الزمني
"""

__version__ = "5.0.0"

from .models import (
    EntityType, RelationType, EdgeType, NodeType,
    Entity, Relationship, GraphNode, GraphEdge,
    FinancialGraph, BalanceEntry, FundFlow,
    ValidationResult, ValidationIssue,
    ExtractionResult,
    # === Dynamic State Transition Model ===
    ExecutionStep, CEIViolation, ExecutionTimeline,
    StateDelta, ExternalCallPoint, StateMutation,
    FunctionEffect,
    TemporalEdge, TemporalAnalysis,
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
from .engine import StateExtractionEngine

# === Layer 2: Action Space ===
try:
    from agl_security_tool.action_space import ActionSpaceBuilder
except ImportError:
    try:
        from action_space import ActionSpaceBuilder
    except ImportError:
        ActionSpaceBuilder = None

# === Layer 3: Attack Engine ===
try:
    from agl_security_tool.attack_engine import AttackSimulationEngine
except ImportError:
    try:
        from attack_engine import AttackSimulationEngine
    except ImportError:
        AttackSimulationEngine = None

# === Layer 4: Search Engine ===
try:
    from agl_security_tool.search_engine import SearchOrchestrator
except ImportError:
    try:
        from search_engine import SearchOrchestrator
    except ImportError:
        SearchOrchestrator = None

__all__ = [
    "StateExtractionEngine",
    "EntityExtractor",
    "RelationshipMapper",
    "FundMapper",
    "FinancialGraphBuilder",
    "ConsistencyValidator",
    "ExecutionSemanticsExtractor",
    "StateMutationTracker",
    "FunctionEffectModeler",
    "TemporalDependencyGraph",
    "FinancialGraph",
    "ExtractionResult",
    "TemporalAnalysis",
    "ActionSpaceBuilder",
    "AttackSimulationEngine",
    "SearchOrchestrator",
    "__version__",
]
