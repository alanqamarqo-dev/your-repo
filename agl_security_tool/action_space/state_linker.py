"""
AGL Action Space — State Linker
ربط الأفعال مع حالة النظام (State-Aware Actions)

لكل Action:
  1. احسب تأثيرها على ΔState
  2. ضع شروط صلاحية التنفيذ (preconditions must be met)
  3. ربط التأثيرات على Balance Ledger و Fund Flows
  4. اكتشف أي Action يفتح preconditions لـ Actions أخرى

هذه الخطوة تجعل الـ Action Space "واقعية" وقابلة للتنفيذ.
"""

from __future__ import annotations

import re
from typing import Dict, List, Any, Optional, Set, Tuple

from .models import Action, ActionCategory

import sys
from pathlib import Path

_TOOL_DIR = Path(__file__).parent.parent.resolve()
if str(_TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOL_DIR))

try:
    from state_extraction.models import (
        FinancialGraph, TemporalAnalysis, FundFlow, BalanceEntry,
        StateMutation, FunctionEffect, ExecutionTimeline,
    )
except ImportError:
    from agl_security_tool.state_extraction.models import (
        FinancialGraph, TemporalAnalysis, FundFlow, BalanceEntry,
        StateMutation, FunctionEffect, ExecutionTimeline,
    )


class StateLinker:
    """
    يربط كل Action بتأثيرها الحقيقي على حالة النظام.

    يستخدم بيانات Layer 1:
    - FinancialGraph: لمعرفة الكيانات والأرصدة
    - TemporalAnalysis: لمعرفة التبعيات الزمنية
    - FundFlows: لربط كل Action بتدفقات مالية

    المخرج: نفس قائمة Actions لكن مُخَصَّبة بـ:
    - balance_effects
    - tokens_involved
    - estimated_value_flow
    - temporal_constraints
    - must_execute_before / must_execute_after
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def link(
        self,
        actions: List[Action],
        graph: Optional[FinancialGraph] = None,
        temporal: Optional[TemporalAnalysis] = None,
    ) -> List[Action]:
        """
        إخصاب كل Action ببيانات الحالة والتبعيات الزمنية.

        Args:
            actions: كل الـ Actions من ParameterGenerator
            graph: الرسم البياني المالي (Layer 1)
            temporal: التحليل الزمني (Layer 1)

        Returns:
            نفس الـ Actions مع بيانات إضافية
        """
        # بناء lookup maps
        flow_map = self._build_flow_map(graph)
        balance_map = self._build_balance_map(graph)
        entity_map = self._build_entity_map(graph)
        action_by_func = self._build_action_func_map(actions)

        for action in actions:
            # 1. ربط التأثيرات المالية
            self._link_balance_effects(action, flow_map, balance_map, entity_map)

            # 2. ربط التبعيات الزمنية
            if temporal:
                self._link_temporal_constraints(action, temporal, action_by_func)

            # 3. حساب تقدير تدفق القيمة
            self._estimate_value_flow(action)

            # 4. التحقق من صلاحية الشروط المسبقة
            self._validate_preconditions(action, balance_map)

        return actions

    # ═══════════════════════════════════════════════════════════
    #  1. Balance Effects
    # ═══════════════════════════════════════════════════════════

    def _link_balance_effects(
        self,
        action: Action,
        flow_map: Dict[str, List[FundFlow]],
        balance_map: Dict[str, List[BalanceEntry]],
        entity_map: Dict[str, Dict[str, Any]],
    ) -> None:
        """ربط action بتأثيرها على الأرصدة"""
        key = f"{action.contract_name}.{action.function_name}"

        # من net_delta (Layer 1)
        for var, delta_expr in action.net_delta.items():
            var_lower = var.lower()
            if any(k in var_lower for k in ("balance", "deposit", "supply", "reserve")):
                action.balance_effects[var] = delta_expr

        # من fund flows
        flows = flow_map.get(action.function_name, [])
        for flow in flows:
            if flow.token_id:
                if flow.token_id not in action.tokens_involved:
                    action.tokens_involved.append(flow.token_id)

            # بناء balance effect
            effect_key = f"{flow.source_account}→{flow.target_account}"
            action.balance_effects[effect_key] = (
                f"{flow.flow_type}: {flow.amount_expr}"
            )

        # من state_writes — إذا كتبت balance vars
        for write_var in action.state_writes:
            for entity_id, entries in balance_map.items():
                for entry in entries:
                    if write_var in entry.balance_var:
                        if entry.token_id not in action.tokens_involved:
                            action.tokens_involved.append(entry.token_id)

    # ═══════════════════════════════════════════════════════════
    #  2. Temporal Constraints
    # ═══════════════════════════════════════════════════════════

    def _link_temporal_constraints(
        self,
        action: Action,
        temporal: TemporalAnalysis,
        action_by_func: Dict[str, List[str]],
    ) -> None:
        """ربط action بالقيود الزمنية من Temporal Graph"""
        func_key = f"{action.contract_name}.{action.function_name}"

        for edge in temporal.temporal_edges:
            # هل هذا الـ Action هو المصدر في ضلع زمني
            if edge.source_function == func_key:
                constraint = (
                    f"{edge.dependency_type}: {edge.description[:120]}"
                )
                if constraint not in action.temporal_constraints:
                    action.temporal_constraints.append(constraint)

                # إذا كان ضلع ثغرة، ضع reentrancy_window
                if edge.is_vulnerability and edge.vulnerability_type in (
                    "reentrancy", "cross_function_reentrancy",
                ):
                    action.reentrancy_window = True

                # ربط must_execute_before: هذا الـ Action يجب أن يُنفَّذ قبل target
                target_actions = action_by_func.get(edge.target_function, [])
                for ta_id in target_actions:
                    if ta_id != action.action_id and ta_id not in action.must_execute_before:
                        action.must_execute_before.append(ta_id)

            # هل هذا الـ Action هو الهدف في ضلع زمني
            if edge.target_function == func_key:
                # ربط must_execute_after
                source_actions = action_by_func.get(edge.source_function, [])
                for sa_id in source_actions:
                    if sa_id != action.action_id and sa_id not in action.must_execute_after:
                        action.must_execute_after.append(sa_id)

        # من CEI violations في timelines
        for tl in temporal.timelines:
            tl_key = f"{tl.contract_name}.{tl.function_name}"
            if tl_key == func_key and tl.cei_violations:
                for v in tl.cei_violations:
                    constraint = (
                        f"CEI-{v.violation_type}: call@step{v.call_step} "
                        f"→ write@step{v.write_step} ({v.write_target})"
                    )
                    if constraint not in action.temporal_constraints:
                        action.temporal_constraints.append(constraint)

    # ═══════════════════════════════════════════════════════════
    #  3. Value Flow Estimation
    # ═══════════════════════════════════════════════════════════

    def _estimate_value_flow(self, action: Action) -> None:
        """تقدير تدفق القيمة لهذا الـ Action"""
        flow_indicators = []

        # إذا يرسل ETH
        if action.sends_eth:
            flow_indicators.append("sends_eth")

        # إذا يكتب balance vars
        for var, delta in action.net_delta.items():
            if any(k in var.lower() for k in ("balance", "deposit", "reserve")):
                if "-" in delta:
                    flow_indicators.append(f"decreases_{var}")
                elif "+" in delta:
                    flow_indicators.append(f"increases_{var}")

        if flow_indicators:
            action.estimated_value_flow = "; ".join(flow_indicators)
        else:
            action.estimated_value_flow = "no_direct_value_flow"

    # ═══════════════════════════════════════════════════════════
    #  4. Precondition Validation
    # ═══════════════════════════════════════════════════════════

    def _validate_preconditions(
        self, action: Action, balance_map: Dict[str, List[BalanceEntry]]
    ) -> None:
        """تحقق هل الشروط المسبقة قابلة للتحقيق من منظور المهاجم"""

        # إذا الدالة تحتاج access ← تعطلها (إلا إذا سبق تعطيلها)
        if action.requires_access and action.caller_must_be not in ("anyone",):
            if action.is_valid:
                action.is_valid = False
                action.disabled_reason = (
                    f"requires {action.caller_must_be} access"
                )
            return

        # تحقق من preconditions: هل يوجد شروط "مستحيلة"
        for pre in action.preconditions:
            pre_lower = pre.lower()
            # شروط واضحة يمكن تحقيقها ← لا تعطل
            if any(k in pre_lower for k in (
                "msg.value", "amount", "balance", "> 0", ">= 0",
            )):
                continue
            # شروط تبدو تحتاج صلاحية ← تحقق عميق
            if any(k in pre_lower for k in (
                "msg.sender == owner", "hasrole", "onlyowner",
            )):
                action.is_valid = False
                action.disabled_reason = f"precondition requires privilege: {pre[:80]}"
                return

    # ═══════════════════════════════════════════════════════════
    #  State Dependency: ΔState enables other Actions
    # ═══════════════════════════════════════════════════════════

    def find_state_enables(self, actions: List[Action]) -> List[Dict[str, Any]]:
        """
        اكتشف أي Action يفتح preconditions لـ Actions أخرى.

        مثال:
          deposit() writes balances[user] += amount
          withdraw() requires balances[user] >= amount
          → deposit enables withdraw (deposit يفتح precondition لـ withdraw)

        Returns:
            قائمة {source_action, target_action, shared_variable, description}
        """
        enables = []

        # بناء: variable → [actions that write it]
        writers: Dict[str, List[str]] = {}
        for a in actions:
            if not a.is_valid:
                continue
            for var in a.state_writes:
                writers.setdefault(var, []).append(a.action_id)

        # بناء: variable → [actions that read it as precondition]
        readers: Dict[str, List[str]] = {}
        for a in actions:
            if not a.is_valid:
                continue
            for var in a.state_reads:
                readers.setdefault(var, []).append(a.action_id)

        # ربط: إذا A يكتب var و B يقرأه ← A enables B
        for var in writers:
            if var not in readers:
                continue
            for writer_id in writers[var]:
                for reader_id in readers[var]:
                    if writer_id == reader_id:
                        continue
                    enables.append({
                        "source_action": writer_id,
                        "target_action": reader_id,
                        "shared_variable": var,
                        "relationship": "state_enables",
                        "description": (
                            f"{writer_id} writes {var}, "
                            f"{reader_id} reads {var}"
                        ),
                    })
        return enables

    # ═══════════════════════════════════════════════════════════
    #  Lookup Map Builders
    # ═══════════════════════════════════════════════════════════

    def _build_flow_map(
        self, graph: Optional[FinancialGraph]
    ) -> Dict[str, List[FundFlow]]:
        """بناء map: function_name → [FundFlow]"""
        if not graph:
            return {}
        m: Dict[str, List[FundFlow]] = {}
        for flow in graph.fund_flows:
            m.setdefault(flow.function_name, []).append(flow)
        return m

    def _build_balance_map(
        self, graph: Optional[FinancialGraph]
    ) -> Dict[str, List[BalanceEntry]]:
        """بناء map: account_id → [BalanceEntry]"""
        if not graph:
            return {}
        m: Dict[str, List[BalanceEntry]] = {}
        for entry in graph.balances:
            m.setdefault(entry.account_id, []).append(entry)
        return m

    def _build_entity_map(
        self, graph: Optional[FinancialGraph]
    ) -> Dict[str, Dict[str, Any]]:
        """بناء map: entity_id → entity attributes"""
        if not graph:
            return {}
        m = {}
        for eid, entity in graph.entities.items():
            m[eid] = entity.to_dict()
        return m

    def _build_action_func_map(
        self, actions: List[Action]
    ) -> Dict[str, List[str]]:
        """بناء map: "Contract.function" → [action_ids]"""
        m: Dict[str, List[str]] = {}
        for a in actions:
            key = f"{a.contract_name}.{a.function_name}"
            m.setdefault(key, []).append(a.action_id)
        return m
