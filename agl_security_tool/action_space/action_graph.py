"""
AGL Action Space — Action Graph Builder
بناء رسم الأفعال الكامل: Nodes=Actions, Edges=Dependencies

أنواع الأضلاع:
1. state_enables: A يكتب var → B يحتاج var كـ precondition
2. temporal: A يجب أن يُنفَّذ قبل/بعد B (من Temporal Graph)
3. reentrancy: A يفتح نافذة reentry → B يمكن استغلالها
4. conflict: A و B يكتبان نفس المتغير (write-write)
5. profit_chain: A يُمهد (state manipulation) → B يحقق ربح

هذا الرسم هو مساحة البحث لـ Layer 3 (Attack Simulator).
"""

from __future__ import annotations

from typing import Dict, List, Any, Optional, Set, Tuple

from .models import (
    Action, ActionEdge, ActionGraph, AttackType, ActionCategory,
)

import sys
from pathlib import Path

_TOOL_DIR = Path(__file__).parent.parent.resolve()
if str(_TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOL_DIR))

try:
    from state_extraction.models import TemporalAnalysis
except ImportError:
    from agl_security_tool.state_extraction.models import TemporalAnalysis


class ActionGraphBuilder:
    """
    يبني ActionGraph من قائمة Actions مصنفة ومُخَصَّبة.

    Pipeline:
    1. إضافة كل Actions كعقد
    2. بناء state_enables edges
    3. بناء temporal edges
    4. بناء reentrancy edges
    5. بناء conflict edges
    6. بناء profit_chain edges
    7. ترتيب أوزان الأضلاع للبحث
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._edge_counter = 0

    def build(
        self,
        actions: List[Action],
        state_enables: Optional[List[Dict[str, Any]]] = None,
        temporal: Optional[TemporalAnalysis] = None,
    ) -> ActionGraph:
        """
        بناء الرسم الكامل.

        Args:
            actions: كل الأفعال المصنفة والمُخَصَّبة
            state_enables: نتائج StateLinker.find_state_enables()
            temporal: TemporalAnalysis من Layer 1

        Returns:
            ActionGraph جاهز للبحث
        """
        self._edge_counter = 0
        graph = ActionGraph()

        # === Step 1: إضافة العقد ===
        valid_actions = [a for a in actions if a.is_valid]
        for action in valid_actions:
            graph.add_action(action)

        if not valid_actions:
            return graph

        # بناء lookup maps
        func_to_actions = self._build_func_map(valid_actions)
        writes_to_actions = self._build_writes_map(valid_actions)
        reads_to_actions = self._build_reads_map(valid_actions)

        # === Step 2: State Enables Edges ===
        if state_enables:
            self._add_state_enables_edges(graph, state_enables)

        # === Step 3: Temporal Edges ===
        if temporal:
            self._add_temporal_edges(graph, temporal, func_to_actions)

        # === Step 4: Reentrancy Edges ===
        self._add_reentrancy_edges(graph, valid_actions, func_to_actions)

        # === Step 5: Write-Write Conflict Edges ===
        self._add_conflict_edges(graph, valid_actions, writes_to_actions)

        # === Step 6: Profit Chain Edges ===
        self._add_profit_chain_edges(graph, valid_actions)

        # === Step 7: ترتيب الأوزان ===
        self._compute_weights(graph)

        return graph

    # ═══════════════════════════════════════════════════════════
    #  Step 2: State Enables
    # ═══════════════════════════════════════════════════════════

    def _add_state_enables_edges(
        self, graph: ActionGraph, enables: List[Dict[str, Any]]
    ) -> None:
        """أضلاع state_enables: A يفتح precondition لـ B"""
        seen = set()
        for en in enables:
            src = en.get("source_action", "")
            tgt = en.get("target_action", "")
            if not src or not tgt or src == tgt:
                continue
            if src not in graph.actions or tgt not in graph.actions:
                continue
            pair_key = f"{src}→{tgt}"
            if pair_key in seen:
                continue
            seen.add(pair_key)

            self._edge_counter += 1
            edge = ActionEdge(
                edge_id=f"ae_{self._edge_counter}",
                source_action=src,
                target_action=tgt,
                edge_type="state_enables",
                shared_variable=en.get("shared_variable", ""),
                description=en.get("description", ""),
                weight=0.5,
            )
            graph.add_edge(edge)

    # ═══════════════════════════════════════════════════════════
    #  Step 3: Temporal Edges
    # ═══════════════════════════════════════════════════════════

    def _add_temporal_edges(
        self,
        graph: ActionGraph,
        temporal: TemporalAnalysis,
        func_to_actions: Dict[str, List[str]],
    ) -> None:
        """أضلاع من Temporal Graph: ترتيب زمني واعتماديات"""
        for te in temporal.temporal_edges:
            src_key = te.source_function
            tgt_key = te.target_function

            src_actions = func_to_actions.get(src_key, [])
            tgt_actions = func_to_actions.get(tgt_key, [])

            if not src_actions or not tgt_actions:
                continue

            for sa_id in src_actions:
                for ta_id in tgt_actions:
                    if sa_id == ta_id:
                        continue
                    if sa_id not in graph.actions or ta_id not in graph.actions:
                        continue

                    self._edge_counter += 1
                    is_attack = te.is_vulnerability
                    edge = ActionEdge(
                        edge_id=f"ae_{self._edge_counter}",
                        source_action=sa_id,
                        target_action=ta_id,
                        edge_type="temporal",
                        shared_variable=te.shared_variable,
                        description=(
                            f"[{te.dependency_type}] {te.description[:150]}"
                        ),
                        weight=2.0 if is_attack else 0.3,
                        is_attack_path=is_attack,
                    )
                    graph.add_edge(edge)

    # ═══════════════════════════════════════════════════════════
    #  Step 4: Reentrancy Edges
    # ═══════════════════════════════════════════════════════════

    def _add_reentrancy_edges(
        self,
        graph: ActionGraph,
        actions: List[Action],
        func_to_actions: Dict[str, List[str]],
    ) -> None:
        """
        أضلاع reentrancy: A يفتح نافذة → B يمكن استغلالها.

        القاعدة: إذا A لها reentrancy_window + CEI violation
        + B تقرأ نفس المتغير الذي لم يُحدَّث بعد → reentrancy edge
        """
        # اكتشف الـ actions التي تفتح نوافذ reentrancy
        reentrant_actions = [
            a for a in actions
            if a.reentrancy_window and a.has_cei_violation
        ]

        for ra in reentrant_actions:
            # المتغيرات التي ستكون stale أثناء الـ external call
            stale_vars = set(ra.state_writes)

            # ابحث عن actions أخرى تقرأ هذه المتغيرات
            for other in actions:
                if other.action_id == ra.action_id:
                    continue
                if other.action_id not in graph.actions:
                    continue

                shared = stale_vars & set(other.state_reads)
                if not shared:
                    continue

                for var in shared:
                    self._edge_counter += 1
                    edge = ActionEdge(
                        edge_id=f"ae_{self._edge_counter}",
                        source_action=ra.action_id,
                        target_action=other.action_id,
                        edge_type="reentrancy",
                        shared_variable=var,
                        description=(
                            f"{ra.function_name} has CEI violation on {var}. "
                            f"During external call, {other.function_name} "
                            f"can read stale {var} value."
                        ),
                        weight=3.0,  # وزن عالي — reentrancy Attack
                        is_attack_path=True,
                    )
                    graph.add_edge(edge)

            # Self-reentrancy: نفس الدالة تُستدعى مرة أخرى
            if ra.action_id in graph.actions:
                self._edge_counter += 1
                edge = ActionEdge(
                    edge_id=f"ae_{self._edge_counter}",
                    source_action=ra.action_id,
                    target_action=ra.action_id,
                    edge_type="reentrancy",
                    shared_variable=",".join(stale_vars),
                    description=(
                        f"Self-reentrancy: {ra.function_name} can re-enter itself "
                        f"during external call. Stale vars: {', '.join(stale_vars)}"
                    ),
                    weight=4.0,  # أعلى وزن — self-reentrancy
                    is_attack_path=True,
                )
                graph.add_edge(edge)

    # ═══════════════════════════════════════════════════════════
    #  Step 5: Write-Write Conflict Edges
    # ═══════════════════════════════════════════════════════════

    def _add_conflict_edges(
        self,
        graph: ActionGraph,
        actions: List[Action],
        writes_to_actions: Dict[str, List[str]],
    ) -> None:
        """أضلاع write-write conflict: دالتان تكتبان نفس المتغير"""
        seen_conflicts: Set[str] = set()

        for var, writer_ids in writes_to_actions.items():
            if len(writer_ids) < 2:
                continue

            for i, w1 in enumerate(writer_ids):
                for w2 in writer_ids[i + 1:]:
                    if w1 == w2:
                        continue
                    if w1 not in graph.actions or w2 not in graph.actions:
                        continue

                    conflict_key = f"{min(w1,w2)}↔{max(w1,w2)}:{var}"
                    if conflict_key in seen_conflicts:
                        continue
                    seen_conflicts.add(conflict_key)

                    a1 = graph.actions[w1]
                    a2 = graph.actions[w2]

                    self._edge_counter += 1
                    edge = ActionEdge(
                        edge_id=f"ae_{self._edge_counter}",
                        source_action=w1,
                        target_action=w2,
                        edge_type="conflict",
                        shared_variable=var,
                        description=(
                            f"Both {a1.function_name} and {a2.function_name} "
                            f"write to {var}. Concurrent or reentrant calls "
                            f"may cause inconsistent state."
                        ),
                        weight=0.8,
                        is_attack_path=(
                            any(not a.requires_access for a in (a1, a2)) and
                            any(a.reentrancy_window for a in (a1, a2))
                        ),
                    )
                    graph.add_edge(edge)

    # ═══════════════════════════════════════════════════════════
    #  Step 6: Profit Chain Edges
    # ═══════════════════════════════════════════════════════════

    def _add_profit_chain_edges(
        self, graph: ActionGraph, actions: List[Action]
    ) -> None:
        """
        أضلاع profit_chain: A يُمهِّد (state_manipulation) → B يحقق الربح.

        مثال: A = deposit (يزيد balance)
               B = withdraw (يسحب balance)
               A → B = profit chain إذا B تحقق أكثر مما أدخلت A
        """
        manipulators = [
            a for a in actions
            if AttackType.STATE_MANIPULATION in a.attack_types
            and a.state_writes
        ]
        profiteers = [
            a for a in actions
            if a.is_profitable and a.state_reads
        ]

        for manip in manipulators:
            if manip.action_id not in graph.actions:
                continue
            for profit in profiteers:
                if profit.action_id not in graph.actions:
                    continue
                if manip.action_id == profit.action_id:
                    continue

                # هل manipulator يكتب ما profiteer يقرأ
                shared = set(manip.state_writes) & set(profit.state_reads)
                if not shared:
                    continue

                self._edge_counter += 1
                edge = ActionEdge(
                    edge_id=f"ae_{self._edge_counter}",
                    source_action=manip.action_id,
                    target_action=profit.action_id,
                    edge_type="profit_chain",
                    shared_variable=",".join(shared),
                    description=(
                        f"[Profit chain] {manip.function_name} manipulates "
                        f"{', '.join(shared)}, then {profit.function_name} "
                        f"profits from changed state."
                    ),
                    weight=2.5,
                    is_attack_path=True,
                )
                graph.add_edge(edge)

    # ═══════════════════════════════════════════════════════════
    #  Step 7: Weight Computation
    # ═══════════════════════════════════════════════════════════

    def _compute_weights(self, graph: ActionGraph) -> None:
        """حساب الأوزان النهائية للأضلاع لتوجيه محرك البحث"""
        for edge in graph.edges.values():
            base_weight = edge.weight

            # ضاعف الوزن إذا المصدر أو الهدف critical
            src = graph.actions.get(edge.source_action)
            tgt = graph.actions.get(edge.target_action)
            if src and src.severity == "CRITICAL":
                base_weight *= 1.5
            if tgt and tgt.severity == "CRITICAL":
                base_weight *= 1.5

            # ضاعف إذا يتضمن ربح مباشر
            if src and src.is_profitable:
                base_weight *= 1.2
            if tgt and tgt.is_profitable:
                base_weight *= 1.3

            # ضاعف إذا reentrancy
            if edge.edge_type == "reentrancy":
                base_weight *= 1.5

            edge.weight = round(base_weight, 2)

    # ═══════════════════════════════════════════════════════════
    #  Lookup Maps
    # ═══════════════════════════════════════════════════════════

    def _build_func_map(self, actions: List[Action]) -> Dict[str, List[str]]:
        """map: "Contract.function" → [action_ids]"""
        m: Dict[str, List[str]] = {}
        for a in actions:
            key = f"{a.contract_name}.{a.function_name}"
            m.setdefault(key, []).append(a.action_id)
        return m

    def _build_writes_map(self, actions: List[Action]) -> Dict[str, List[str]]:
        """map: variable → [action_ids that write it]"""
        m: Dict[str, List[str]] = {}
        for a in actions:
            for var in a.state_writes:
                m.setdefault(var, []).append(a.action_id)
        return m

    def _build_reads_map(self, actions: List[Action]) -> Dict[str, List[str]]:
        """map: variable → [action_ids that read it]"""
        m: Dict[str, List[str]] = {}
        for a in actions:
            for var in a.state_reads:
                m.setdefault(var, []).append(a.action_id)
        return m
