"""
AGL Action Space Builder — Layer 2
بناء مساحة الهجوم من مخرجات Layer 1

يحوّل الرسم البياني المالي والتحليل الزمني إلى مساحة بحث فعلية للهجمات:
  1. Action Enumeration — استخراج كل الأفعال الممكنة من العقود
  2. Parameter Generation — توليد variants بمعاملات استراتيجية
  3. State Linking — ربط كل فعل بتأثيره على ΔState والأرصدة
  4. Attack Classification — تصنيف حسب نوع الهجوم والخطورة
  5. Action Graph — بناء رسم اعتماديات: Nodes=Actions, Edges=Dependencies
  6. Attack Summary — ملخص أسطح الهجوم ومسارات الهجوم المرتبة

Usage:
    from agl_security_tool.action_space import ActionSpaceBuilder
    builder = ActionSpaceBuilder()
    space = builder.build(contracts, graph, temporal)
    print(space.to_json())
"""

__version__ = "1.0.0"

from .models import (
    AttackType, ActionCategory, ParamDomain,
    ActionParameter, Action, ActionEdge,
    ActionGraph, ActionSpace,
)
from .action_enumerator import ActionEnumerator
from .parameter_generator import ParameterGenerator
from .state_linker import StateLinker
from .action_classifier import ActionClassifier
from .action_graph import ActionGraphBuilder
from .builder import ActionSpaceBuilder

__all__ = [
    "ActionSpaceBuilder",
    "ActionEnumerator",
    "ParameterGenerator",
    "StateLinker",
    "ActionClassifier",
    "ActionGraphBuilder",
    "Action",
    "ActionParameter",
    "ActionEdge",
    "ActionGraph",
    "ActionSpace",
    "AttackType",
    "ActionCategory",
    "ParamDomain",
    "__version__",
]
