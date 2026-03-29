"""
AGL Action Space — Builder (Main Orchestrator)
المنسّق الرئيسي لـ Layer 2: يربط كل المكونات

Pipeline:
  1. ActionEnumerator   → استخراج Actions أساسية من كل دالة
  2. ParameterGenerator → توليد variants بمعاملات استراتيجية
  3. StateLinker        → ربط كل Action بـ ΔState + balance effects + temporal
  4. ActionClassifier   → تصنيف كل Action بنوع الهجوم والخطورة
  5. ActionGraphBuilder → بناء الرسم: Nodes=Actions, Edges=Dependencies
  6. Summary           → ملخص سطح الهجوم + مسارات + أهداف

Usage:
    builder = ActionSpaceBuilder()
    space = builder.build(contracts, graph, temporal)
    json_str = space.to_json()
"""

from __future__ import annotations

import time
from typing import Dict, List, Any, Optional

from .models import Action, ActionGraph, ActionSpace, AttackType
from .action_enumerator import ActionEnumerator
from .parameter_generator import ParameterGenerator
from .state_linker import StateLinker
from .action_classifier import ActionClassifier
from .action_graph import ActionGraphBuilder

import sys
from pathlib import Path

_TOOL_DIR = Path(__file__).parent.parent.resolve()
if str(_TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOL_DIR))

try:
    from state_extraction.models import (
        FinancialGraph, TemporalAnalysis,
        FunctionEffect, StateMutation, ExecutionTimeline,
    )
except ImportError:
    from agl_security_tool.state_extraction.models import (
        FinancialGraph, TemporalAnalysis,
        FunctionEffect, StateMutation, ExecutionTimeline,
    )

try:
    from detectors import ParsedContract
except ImportError:
    from agl_security_tool.detectors import ParsedContract


class ActionSpaceBuilder:
    """
    المنسّق الرئيسي لبناء مساحة الهجوم.

    يأخذ مخرجات Layer 1 ويحولها إلى ActionSpace جاهز لـ Layer 3.
    """

    VERSION = "1.0.0"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Args:
            config: إعدادات اختيارية:
                - max_variants: int — حد أقصى لـ variants لكل دالة (default: 8)
                - include_invalid: bool — هل تُضمّن Actions المعطلة (default: False)
                - skip_view: bool — هل تتجاهل دوال view/pure (default: True)
        """
        self.config = config or {}
        self._enumerator = ActionEnumerator(config)
        self._param_gen = ParameterGenerator(config)
        self._state_linker = StateLinker(config)
        self._classifier = ActionClassifier(config)
        self._graph_builder = ActionGraphBuilder(config)

    def build(
        self,
        contracts: List[ParsedContract],
        graph: Optional[FinancialGraph] = None,
        temporal: Optional[TemporalAnalysis] = None,
    ) -> ActionSpace:
        """
        بناء مساحة الهجوم الكاملة.

        Args:
            contracts: العقود المحللة (من SoliditySemanticParser)
            graph: الرسم البياني المالي (Layer 1)
            temporal: التحليل الزمني (Layer 1)

        Returns:
            ActionSpace جاهز لـ Layer 3
        """
        start_time = time.time()
        space = ActionSpace(version=self.VERSION)

        try:
            # استخراج بيانات من temporal إذا متاحة
            effects = temporal.effects if temporal else None
            mutations = temporal.mutations if temporal else None
            timelines = temporal.timelines if temporal else None

            # ─── Step 1: Enumerate base Actions ───
            base_actions = self._enumerator.enumerate(
                contracts, effects, mutations, timelines
            )

            # ─── Step 2: Generate parameter variants ───
            if self.config.get("skip_view", True):
                # لا تولَّد variants لدوال view/pure
                expandable = [a for a in base_actions if a.mutability not in ("view", "pure")]
                view_actions = [a for a in base_actions if a.mutability in ("view", "pure")]
                expanded = self._param_gen.generate(expandable)
                all_actions = expanded + view_actions
            else:
                all_actions = self._param_gen.generate(base_actions)

            # ─── Step 3: Link with state ───
            all_actions = self._state_linker.link(all_actions, graph, temporal)
            state_enables = self._state_linker.find_state_enables(all_actions)

            # ─── Step 4: Classify ───
            all_actions = self._classifier.classify(all_actions)

            # ─── Step 5: Build Action Graph ───
            action_graph = self._graph_builder.build(
                all_actions, state_enables, temporal
            )

            space.graph = action_graph

            # ─── Step 6: Build Summary ───
            space.attack_surfaces = self._summarize_attack_surface(all_actions)
            space.high_value_targets = self._find_high_value_targets(all_actions)
            space.attack_sequences = self._extract_attack_sequences(action_graph)

        except Exception as e:
            space.errors.append(f"خطأ في بناء مساحة الهجوم: {str(e)[:300]}")

        space.build_time = time.time() - start_time
        return space

    # ═══════════════════════════════════════════════════════════
    #  Summary: Attack Surface
    # ═══════════════════════════════════════════════════════════

    def _summarize_attack_surface(self, actions: List[Action]) -> List[Dict[str, Any]]:
        """ملخص سطح الهجوم"""
        surfaces = []

        # تجميع حسب العقد
        by_contract: Dict[str, List[Action]] = {}
        for a in actions:
            by_contract.setdefault(a.contract_name, []).append(a)

        for contract_name, contract_actions in by_contract.items():
            valid = [a for a in contract_actions if a.is_valid]
            profitable = [a for a in valid if a.is_profitable]
            risky = [a for a in valid if a.severity in ("CRITICAL", "HIGH")]

            # جمع أنماط الهجوم
            all_attack_types = set()
            for a in valid:
                for at in a.attack_types:
                    all_attack_types.add(at.value)

            surface = {
                "contract": contract_name,
                "total_actions": len(contract_actions),
                "valid_actions": len(valid),
                "profitable_actions": len(profitable),
                "critical_or_high": len(risky),
                "attack_types": sorted(all_attack_types),
                "has_reentrancy": any(a.has_cei_violation for a in valid),
                "has_unguarded_reentrancy": any(
                    a.has_cei_violation and not a.reentrancy_guarded
                    for a in valid
                ),
                "sends_eth": any(a.sends_eth for a in valid),
                "has_delegatecall": any(a.has_delegatecall for a in valid),
                "exposed_functions": list({
                    a.function_name: {
                        "function": a.function_name,
                        "severity": a.severity,
                        "attacks": [at.value for at in a.attack_types],
                        "profit": a.profit_potential,
                    }
                    for a in risky
                }.values()),
            }
            surfaces.append(surface)

        return surfaces

    # ═══════════════════════════════════════════════════════════
    #  Summary: High-Value Targets
    # ═══════════════════════════════════════════════════════════

    def _find_high_value_targets(self, actions: List[Action]) -> List[Dict[str, Any]]:
        """الأهداف عالية القيمة — أخطر الأفعال"""
        targets = []

        for a in actions:
            if not a.is_valid:
                continue
            if a.severity not in ("CRITICAL", "HIGH"):
                continue

            target = {
                "action_id": a.action_id,
                "contract": a.contract_name,
                "function": a.function_name,
                "severity": a.severity,
                "attack_types": [at.value for at in a.attack_types],
                "profit_potential": a.profit_potential,
                "sends_eth": a.sends_eth,
                "has_cei_violation": a.has_cei_violation,
                "reentrancy_guarded": a.reentrancy_guarded,
                "cross_function_risk": a.cross_function_risk,
                "state_writes": a.state_writes[:5],
                "tokens_involved": a.tokens_involved,
                "description": self._describe_target(a),
            }
            targets.append(target)

        # ترتيب: critical أولاً، ثم high, ثم بالربحية
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        profit_order = {"high": 0, "medium": 1, "low": 2, "none": 3}
        targets.sort(key=lambda t: (
            severity_order.get(t["severity"], 4),
            profit_order.get(t["profit_potential"], 4),
        ))

        return targets

    def _describe_target(self, action: Action) -> str:
        """وصف نصي للهدف"""
        parts = []
        if action.has_cei_violation and not action.reentrancy_guarded:
            parts.append(f"UNGUARDED reentrancy ({action.cei_violation_count} CEI violations)")
        if action.sends_eth:
            parts.append("sends ETH")
        if action.has_delegatecall:
            parts.append("uses delegatecall")
        if action.cross_function_risk:
            parts.append("cross-function risk")

        for at in action.attack_types:
            if at == AttackType.FLASH_LOAN:
                parts.append("flash loan amplifiable")
            elif at == AttackType.PRICE_MANIPULATION:
                parts.append("price manipulation possible")
            elif at == AttackType.DONATION:
                parts.append("donation/inflation attack")

        return "; ".join(parts) if parts else "potential vulnerability"

    # ═══════════════════════════════════════════════════════════
    #  Summary: Attack Sequences
    # ═══════════════════════════════════════════════════════════

    def _extract_attack_sequences(
        self, graph: ActionGraph
    ) -> List[Dict[str, Any]]:
        """استخراج تسلسلات الهجوم المرتبة"""
        paths = graph.get_attack_paths()
        sequences = []

        for idx, path in enumerate(paths):
            if idx >= 20:  # حد أقصى 20 مسار
                break

            steps = []
            total_weight = 0.0
            severity = "LOW"
            attack_types = set()

            for i, action_id in enumerate(path):
                action = graph.actions.get(action_id)
                if not action:
                    continue
                steps.append({
                    "step": i + 1,
                    "action": action_id,
                    "function": f"{action.contract_name}.{action.function_name}",
                    "category": action.category.value,
                    "sends_eth": action.sends_eth,
                })
                for at in action.attack_types:
                    attack_types.add(at.value)

                # أعلى severity
                sev_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}
                if sev_order.get(action.severity, 0) > sev_order.get(severity, 0):
                    severity = action.severity

            # حساب الوزن الإجمالي من الأضلاع
            for i in range(len(path) - 1):
                for eid, edge in graph.edges.items():
                    if edge.source_action == path[i] and edge.target_action == path[i + 1]:
                        total_weight += edge.weight
                        break

            sequence = {
                "sequence_id": f"seq_{idx + 1}",
                "steps": steps,
                "total_steps": len(steps),
                "severity": severity,
                "attack_types": sorted(attack_types),
                "total_weight": round(total_weight, 2),
            }
            sequences.append(sequence)

        # ترتيب حسب الوزن (الأخطر أولاً)
        sequences.sort(key=lambda s: -s["total_weight"])

        return sequences

    # ═══════════════════════════════════════════════════════════
    #  Info
    # ═══════════════════════════════════════════════════════════

    def get_info(self) -> Dict[str, Any]:
        return {
            "name": "AGL Action Space Builder",
            "layer": 2,
            "version": self.VERSION,
            "components": {
                "action_enumerator": "ActionEnumerator",
                "parameter_generator": "ParameterGenerator",
                "state_linker": "StateLinker",
                "action_classifier": "ActionClassifier",
                "action_graph_builder": "ActionGraphBuilder",
            },
            "capabilities": [
                "Extract callable actions from parsed contracts",
                "Generate strategic parameter variants",
                "Link actions to ΔState and balance effects",
                "Classify actions by attack type and severity",
                "Build action dependency graph",
                "Detect reentrancy attack paths",
                "Detect cross-function attack paths",
                "Detect profit chain opportunities",
                "Generate ranked attack sequences",
                "Provide attack surface summary",
            ],
        }
