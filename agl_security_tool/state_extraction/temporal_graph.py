"""
AGL State Extraction — Temporal Dependency Graph
الرسم البياني للتبعيات الزمنية

يبني أضلاع زمنية (TemporalEdge) تربط بين العمليات عبر الدوال والعقود.

أنواع التبعيات الزمنية:
  1. happens_before — A يجب أن ينفذ قبل B (ترتيب داخل الدالة)
  2. call_then_update — استدعاء خارجي ثم تحديث حالة (reentrancy window)
  3. reads_then_writes — قراءة حالة ثم كتابة (stale read risk)
  4. write_write — دالتان تكتبان نفس المتغير (race condition)
  5. cross_function — تبعية بين دوال مختلفة عبر متغير مشترك

يكشف:
  - Reentrancy الكلاسيكي (call{value:} قبل state update)
  - Read-only reentrancy (view يقرأ حالة stale)
  - Cross-function reentrancy (A يستدعي خارجياً، B يقرأ حالة لم تُحدَّث)
  - Write conflicts (متغير يُكتب من دالتين بدون حماية)
  - Temporal ordering anomalies

هذا هو المكون الذي تحدث عنه الناقد: "متى تحدث التغييرات بالنسبة لأحداث أخرى"
"""

from typing import List, Dict, Set, Optional, Any

from .models import (
    ExecutionTimeline, StateMutation, FunctionEffect,
    TemporalEdge, TemporalAnalysis,
)

# Import parser types
import sys
from pathlib import Path
_TOOL_DIR = Path(__file__).parent.parent.resolve()
if str(_TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOL_DIR))

try:
    from detectors import ParsedContract, ParsedFunction, OpType
except ImportError:
    from agl_security_tool.detectors import ParsedContract, ParsedFunction, OpType


class TemporalDependencyGraph:
    """
    يبني رسم بياني للتبعيات الزمنية بين كل العمليات عبر كل الدوال.

    المدخلات:
    - ExecutionTimelines (من ExecutionSemanticsExtractor)
    - StateMutations (من StateMutationTracker)
    - FunctionEffects (من FunctionEffectModeler)
    - ParsedContracts (من SoliditySemanticParser)

    المخرجات:
    - TemporalAnalysis يحتوي:
      - temporal_edges: أضلاع زمنية مع vulnerability detection
      - vulnerability_candidates: قائمة ثغرات مكتشفة من التحليل الزمني
      - ملخص إحصائي

    Usage:
        tdg = TemporalDependencyGraph()
        analysis = tdg.build(timelines, mutations, effects, contracts)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._edge_counter = 0

    # ═══════════════════════════════════════════════════════════
    #  Main API
    # ═══════════════════════════════════════════════════════════

    def build(
        self,
        timelines: List[ExecutionTimeline],
        mutations: List[StateMutation],
        effects: List[FunctionEffect],
        contracts: List[ParsedContract],
    ) -> TemporalAnalysis:
        """
        بناء التحليل الزمني الكامل.
        """
        self._edge_counter = 0

        analysis = TemporalAnalysis(
            timelines=timelines,
            mutations=mutations,
            effects=effects,
        )

        # ─── Step 1: Intra-function temporal edges ───
        # ترتيب العمليات داخل كل دالة (call → write)
        intra_edges = self._build_intra_function_edges(timelines)
        analysis.temporal_edges.extend(intra_edges)

        # ─── Step 2: State mutation ordering edges ───
        # نقاط الاستدعاء بين التغييرات (حيث يحدث reentrancy)
        mutation_edges = self._build_mutation_ordering_edges(mutations)
        analysis.temporal_edges.extend(mutation_edges)

        # ─── Step 3: Cross-function dependency edges ───
        # تبعيات بين دوال مختلفة عبر متغيرات مشتركة
        cross_edges = self._build_cross_function_edges(effects, contracts)
        analysis.temporal_edges.extend(cross_edges)

        # ─── Step 4: Write-write conflict edges ───
        conflict_edges = self._build_write_conflict_edges(effects)
        analysis.temporal_edges.extend(conflict_edges)

        # ─── Step 5: Aggregate vulnerability candidates ───
        self._aggregate_vulnerabilities(analysis)

        return analysis

    # ═══════════════════════════════════════════════════════════
    #  Step 1: Intra-Function Temporal Edges
    # ═══════════════════════════════════════════════════════════

    def _build_intra_function_edges(
        self, timelines: List[ExecutionTimeline]
    ) -> List[TemporalEdge]:
        """
        بناء أضلاع زمنية داخل كل دالة.

        الأنماط المكتشفة:
        1. call_then_update: external call (step i) → state write (step j where j > i)
           → هذا هو reentrancy window الكلاسيكي
        2. read_then_call: state read (step i) → external call (step j)
           → القراءة قد تكون stale عند إعادة الدخول
        """
        edges = []

        for tl in timelines:
            func_ref = f"{tl.contract_name}.{tl.function_name}"

            if tl.has_reentrancy_guard:
                continue

            # نجمع كل الـ calls و writes
            ext_calls = [s for s in tl.steps if s.is_external_call]
            state_writes = [s for s in tl.steps if s.is_state_write]
            state_reads = [s for s in tl.steps if s.is_state_read]

            # ─── call_then_update edges ───
            for call in ext_calls:
                for write in state_writes:
                    if write.step_index > call.step_index:
                        is_vuln = True  # CEI violation
                        edge = self._make_edge(
                            source_function=func_ref,
                            target_function=func_ref,
                            source_step=call.step_index,
                            target_step=write.step_index,
                            dep_type="call_then_update",
                            shared_var=write.target,
                            description=(
                                f"External call to `{call.target}` (step {call.step_index}, "
                                f"line {call.line}) happens BEFORE state update "
                                f"`{write.target}` (step {write.step_index}, line {write.line}). "
                                f"Reentrancy window: attacker can re-enter while "
                                f"`{write.target}` still has old value."
                            ),
                            is_vuln=is_vuln,
                            vuln_type="reentrancy" if call.sends_eth else "non_eth_reentrancy",
                            vuln_severity="critical" if call.sends_eth else "high",
                        )
                        edges.append(edge)

            # ─── read_then_call edges ───
            for read in state_reads:
                for call in ext_calls:
                    if call.step_index > read.step_index:
                        # قراءة ثم استدعاء — القيمة المقروءة قد تكون stale
                        edge = self._make_edge(
                            source_function=func_ref,
                            target_function=func_ref,
                            source_step=read.step_index,
                            target_step=call.step_index,
                            dep_type="reads_then_calls",
                            shared_var=read.target,
                            description=(
                                f"State `{read.target}` read (step {read.step_index}) "
                                f"before external call (step {call.step_index}). "
                                f"Value may be stale if re-entered."
                            ),
                            is_vuln=False,  # not automatically a vuln
                        )
                        edges.append(edge)

        return edges

    # ═══════════════════════════════════════════════════════════
    #  Step 2: Mutation Ordering Edges
    # ═══════════════════════════════════════════════════════════

    def _build_mutation_ordering_edges(
        self, mutations: List[StateMutation]
    ) -> List[TemporalEdge]:
        """
        بناء أضلاع من نقاط الاستدعاء بين التغييرات.

        إذا كان هناك:
          delta[0]: balance -= amount    (step 5)
          call_point: msg.sender.call()  (step 7) ← بين التغييرين!
          delta[1]: totalSupply -= amount (step 9)

        هذا يعني أن المهاجم يمكنه إعادة الدخول بعد تعديل balance
        لكن قبل تعديل totalSupply.
        """
        edges = []

        for mutation in mutations:
            func_ref = f"{mutation.contract_name}.{mutation.function_name}"

            for cp in mutation.call_points:
                # Call between deltas
                if cp.deltas_before > 0 and cp.deltas_after > 0:
                    # نجد الـ delta قبل وبعد
                    deltas_before = [
                        d for d in mutation.deltas
                        if d.step_index < cp.step_index
                    ]
                    deltas_after = [
                        d for d in mutation.deltas
                        if d.step_index > cp.step_index
                    ]

                    for db in deltas_before:
                        for da in deltas_after:
                            edge = self._make_edge(
                                source_function=func_ref,
                                target_function=func_ref,
                                source_step=db.step_index,
                                target_step=da.step_index,
                                dep_type="call_between_deltas",
                                shared_var=f"{db.variable} → {da.variable}",
                                description=(
                                    f"External call at step {cp.step_index} "
                                    f"(line {cp.line}) splits state updates: "
                                    f"`{db.variable}` updated before call, "
                                    f"`{da.variable}` updated after. "
                                    f"State is partially updated during call."
                                ),
                                is_vuln=True,
                                vuln_type="partial_state_reentrancy",
                                vuln_severity="high",
                            )
                            edges.append(edge)

                # Call after all deltas — relatively safer but still risky if
                # reads before call used stale values
                if cp.deltas_before == 0 and cp.deltas_after > 0:
                    for da in mutation.deltas:
                        if da.step_index > cp.step_index:
                            edge = self._make_edge(
                                source_function=func_ref,
                                target_function=func_ref,
                                source_step=cp.step_index,
                                target_step=da.step_index,
                                dep_type="call_then_update",
                                shared_var=da.variable,
                                description=(
                                    f"All state writes happen AFTER external call "
                                    f"at step {cp.step_index}. Classic CEI violation."
                                ),
                                is_vuln=True,
                                vuln_type="classic_cei_violation",
                                vuln_severity="critical" if cp.sends_eth else "high",
                            )
                            edges.append(edge)

        return edges

    # ═══════════════════════════════════════════════════════════
    #  Step 3: Cross-Function Dependency Edges
    # ═══════════════════════════════════════════════════════════

    def _build_cross_function_edges(
        self, effects: List[FunctionEffect],
        contracts: List[ParsedContract],
    ) -> List[TemporalEdge]:
        """
        بناء أضلاع تبعية بين دوال مختلفة.

        النمط:
          - دالة A public تستدعي خارجياً وتكتب var X بعد الاستدعاء
          - دالة B public تقرأ var X
          → أثناء الاستدعاء الخارجي في A، المهاجم يستدعي B ويحصل على قيمة قديمة لـ X

        هذا هو cross-function reentrancy.
        """
        edges = []

        # بناء خريطة: (contract, var) → functions that write / read
        write_map: Dict[str, List[FunctionEffect]] = {}  # "Contract.var" → [effects]
        read_map: Dict[str, List[FunctionEffect]] = {}

        for effect in effects:
            for var in effect.writes:
                key = f"{effect.contract_name}.{var}"
                write_map.setdefault(key, []).append(effect)
            for var in effect.reads:
                key = f"{effect.contract_name}.{var}"
                read_map.setdefault(key, []).append(effect)

        # لكل دالة تكتب وتستدعي خارجياً
        for effect in effects:
            if not effect.external_calls:
                continue
            if effect.reentrancy_guarded:
                continue

            writer_ref = f"{effect.contract_name}.{effect.function_name}"

            for var in effect.writes:
                key = f"{effect.contract_name}.{var}"
                readers = read_map.get(key, [])

                for reader in readers:
                    if reader.function_name == effect.function_name:
                        continue

                    # Check if reader is public/external (callable by attacker)
                    is_exposed = False
                    for contract in contracts:
                        if contract.name == reader.contract_name:
                            func = contract.functions.get(reader.function_name)
                            if func and func.visibility in ('public', 'external'):
                                is_exposed = True
                            break

                    if not is_exposed:
                        continue

                    reader_ref = f"{reader.contract_name}.{reader.function_name}"

                    # هذه تبعية cross-function — خطيرة إذا كانت الكتابة بعد الاستدعاء
                    edge = self._make_edge(
                        source_function=writer_ref,
                        target_function=reader_ref,
                        dep_type="cross_function",
                        shared_var=var,
                        description=(
                            f"`{writer_ref}` writes `{var}` and makes external call. "
                            f"`{reader_ref}` reads `{var}`. If write happens after call, "
                            f"attacker can re-enter via `{reader_ref}` to read stale `{var}`."
                        ),
                        is_vuln=True,
                        vuln_type="cross_function_reentrancy",
                        vuln_severity="high",
                    )
                    edges.append(edge)

        return edges

    # ═══════════════════════════════════════════════════════════
    #  Step 4: Write-Write Conflict Edges
    # ═══════════════════════════════════════════════════════════

    def _build_write_conflict_edges(
        self, effects: List[FunctionEffect],
    ) -> List[TemporalEdge]:
        """
        بناء أضلاع تعارض كتابة-كتابة.

        إذا كانت دالتان public تكتبان نفس المتغير بدون حماية:
        → race condition محتمل
        """
        edges = []
        seen = set()

        for i, effect_a in enumerate(effects):
            if not effect_a.writes:
                continue
            for j, effect_b in enumerate(effects):
                if j <= i:
                    continue
                if effect_a.contract_name != effect_b.contract_name:
                    continue
                if not effect_b.writes:
                    continue

                shared_writes = set(effect_a.writes) & set(effect_b.writes)
                if not shared_writes:
                    continue

                pair_key = frozenset([
                    f"{effect_a.contract_name}.{effect_a.function_name}",
                    f"{effect_b.contract_name}.{effect_b.function_name}",
                ])
                if pair_key in seen:
                    continue
                seen.add(pair_key)

                for var in shared_writes:
                    ref_a = f"{effect_a.contract_name}.{effect_a.function_name}"
                    ref_b = f"{effect_b.contract_name}.{effect_b.function_name}"

                    # Check if both are unguarded
                    both_unguarded = (
                        not effect_a.requires_access and not effect_b.requires_access
                    )

                    edge = self._make_edge(
                        source_function=ref_a,
                        target_function=ref_b,
                        dep_type="write_write",
                        shared_var=var,
                        description=(
                            f"Both `{ref_a}` and `{ref_b}` write to `{var}`. "
                            + ("Neither has access control. " if both_unguarded else "")
                            + "Concurrent or reentrant calls may cause inconsistent state."
                        ),
                        is_vuln=both_unguarded,
                        vuln_type="write_conflict" if both_unguarded else "",
                        vuln_severity="medium" if both_unguarded else "",
                    )
                    edges.append(edge)

        return edges

    # ═══════════════════════════════════════════════════════════
    #  Vulnerability Aggregation
    # ═══════════════════════════════════════════════════════════

    def _aggregate_vulnerabilities(self, analysis: TemporalAnalysis) -> None:
        """
        تجميع كل الثغرات المكتشفة من التحليل الزمني.
        """
        vuln_edges = [
            e for e in analysis.temporal_edges
            if e.is_vulnerability
        ]

        # إحصائيات
        for edge in vuln_edges:
            if "reentrancy" in edge.vulnerability_type:
                analysis.total_reentrancy_risks += 1
            if "cross_function" in edge.dependency_type:
                analysis.total_cross_function_deps += 1
            if "write_conflict" in edge.vulnerability_type:
                analysis.total_write_conflicts += 1

        # CEI violations from timelines
        for tl in analysis.timelines:
            analysis.total_cei_violations += len([
                v for v in tl.cei_violations
                if v.violation_type not in ("read_only_reentrancy_surface",)
            ])

        # Build vulnerability candidates list
        seen_vulns = set()
        for edge in vuln_edges:
            # Deduplicate
            vuln_key = (
                edge.source_function, edge.target_function,
                edge.vulnerability_type, edge.shared_variable,
            )
            if vuln_key in seen_vulns:
                continue
            seen_vulns.add(vuln_key)

            analysis.vulnerability_candidates.append({
                "type": edge.vulnerability_type,
                "severity": edge.vulnerability_severity,
                "source": edge.source_function,
                "target": edge.target_function,
                "variable": edge.shared_variable,
                "dependency": edge.dependency_type,
                "description": edge.description,
            })

        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        analysis.vulnerability_candidates.sort(
            key=lambda v: severity_order.get(v.get("severity", "low"), 4)
        )

    # ═══════════════════════════════════════════════════════════
    #  Helpers
    # ═══════════════════════════════════════════════════════════

    def _make_edge(
        self,
        source_function: str,
        target_function: str,
        dep_type: str,
        shared_var: str = "",
        description: str = "",
        source_step: int = 0,
        target_step: int = 0,
        is_vuln: bool = False,
        vuln_type: str = "",
        vuln_severity: str = "",
    ) -> TemporalEdge:
        """
        إنشاء TemporalEdge جديد مع edge_id فريد.
        """
        self._edge_counter += 1
        return TemporalEdge(
            edge_id=f"temporal_{self._edge_counter}",
            source_function=source_function,
            target_function=target_function,
            source_step=source_step,
            target_step=target_step,
            dependency_type=dep_type,
            shared_variable=shared_var,
            description=description,
            is_vulnerability=is_vuln,
            vulnerability_type=vuln_type,
            vulnerability_severity=vuln_severity,
        )
