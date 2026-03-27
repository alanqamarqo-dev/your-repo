"""
AGL State Extraction — State Mutation Tracker
متتبع تحولات الحالة — يبني نموذج State(t+1) = State(t) + Σ(deltas)

لكل دالة يبني:
  - الشروط المسبقة (preconditions) — كل require/assert قبل أي تغيير
  - القراءات (state reads) — ماذا تقرأ الدالة من الحالة
  - التغييرات المرتبة (deltas) — كل كتابة حالة بالترتيب الدقيق
  - نقاط الاستدعاء الخارجي (call points) — أين بالضبط تحدث الاستدعاءات بين التغييرات
  - التأثير الصافي (net effect) — {variable: "+amount" / "-amount" / "=expr"}

المفتاح هنا: الترتيب النسبي بين deltas و external calls.
إذا كان call point يقع بين delta[i] و delta[i+1] → reentrancy window.
"""

import re
from typing import List, Dict, Set, Optional, Any, Tuple

from .models import (
    StateDelta, ExternalCallPoint, StateMutation,
)

# Import parser types
import sys
from pathlib import Path
_TOOL_DIR = Path(__file__).parent.parent.resolve()
if str(_TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOL_DIR))

try:
    from detectors import ParsedContract, ParsedFunction, Operation, OpType
except ImportError:
    from agl_security_tool.detectors import ParsedContract, ParsedFunction, Operation, OpType


# ═══════════════════════════════════════════════════════════
#  Regex patterns for extracting delta operations
# ═══════════════════════════════════════════════════════════

_RE_ASSIGN = re.compile(r'(\w[\w\[\]\.\(\)]*)\s*=\s*(.+)')
_RE_ADD_ASSIGN = re.compile(r'(\w[\w\[\]\.\(\)]*)\s*\+=\s*(.+)')
_RE_SUB_ASSIGN = re.compile(r'(\w[\w\[\]\.\(\)]*)\s*-=\s*(.+)')
_RE_MUL_ASSIGN = re.compile(r'(\w[\w\[\]\.\(\)]*)\s*\*=\s*(.+)')
_RE_DIV_ASSIGN = re.compile(r'(\w[\w\[\]\.\(\)]*)\s*\/=\s*(.+)')
_RE_DELETE = re.compile(r'delete\s+(\w[\w\[\]\.\(\)]*)')
_RE_PUSH = re.compile(r'(\w[\w\[\]\.]*)\s*\.\s*push\s*\(')
_RE_POP = re.compile(r'(\w[\w\[\]\.]*)\s*\.\s*pop\s*\(')
_RE_INCREMENT = re.compile(r'(\w[\w\[\]\.\(\)]*)\s*\+\+|(\+\+)\s*(\w[\w\[\]\.\(\)]*)')
_RE_DECREMENT = re.compile(r'(\w[\w\[\]\.\(\)]*)\s*--|(--)(\w[\w\[\]\.\(\)]*)')


class StateMutationTracker:
    """
    يبني نموذج State(t+1) = State(t) + Σ(deltas) لكل دالة.

    يتتبع بالضبط:
    1. ما هي الشروط المسبقة (require/if) قبل التغييرات
    2. ما هي متغيرات الحالة المقروءة (inputs to delta calculation)
    3. ما هي التغييرات بالترتيب الدقيق (ordered deltas)
    4. أين تحدث الاستدعاءات الخارجية بالنسبة للتغييرات (reentrancy window)

    Usage:
        tracker = StateMutationTracker()
        mutations = tracker.track(contracts)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    # ═══════════════════════════════════════════════════════════
    #  Main API
    # ═══════════════════════════════════════════════════════════

    def track(
        self, contracts: List[ParsedContract]
    ) -> List[StateMutation]:
        """
        بناء نماذج التحول لكل دالة غير view/pure.

        Args:
            contracts: العقود المحللة

        Returns:
            قائمة StateMutation واحدة لكل دالة تكتب حالة
        """
        mutations = []
        for contract in contracts:
            if contract.contract_type in ("interface", "library"):
                continue
            for fname, func in contract.functions.items():
                if func.mutability in ('view', 'pure'):
                    continue
                if not func.operations:
                    continue
                mutation = self._build_mutation(contract, func)
                if mutation and (mutation.deltas or mutation.call_points):
                    mutations.append(mutation)
        return mutations

    def track_function(
        self, contract: ParsedContract, func: ParsedFunction
    ) -> StateMutation:
        """
        بناء نموذج تحول لدالة واحدة.
        """
        return self._build_mutation(contract, func)

    # ═══════════════════════════════════════════════════════════
    #  Mutation Construction
    # ═══════════════════════════════════════════════════════════

    def _build_mutation(
        self, contract: ParsedContract, func: ParsedFunction
    ) -> StateMutation:
        """
        بناء StateMutation كاملة من عمليات الدالة.

        المنهج:
        1. نمر على operations بالترتيب
        2. require → precondition
        3. state_read → state_reads
        4. state_write → delta (مع تحليل نوع العملية)
        5. external_call → call_point (مع حساب deltas_before/after)
        """
        mutation = StateMutation(
            function_name=func.name,
            contract_name=contract.name,
        )

        state_var_names = set(contract.state_vars.keys())
        accumulated_preconditions: List[str] = []
        accumulated_reads: Set[str] = set()
        delta_index = 0
        call_index = 0

        for op_idx, op in enumerate(func.operations):
            # ─── Preconditions ───
            if op.op_type in (OpType.REQUIRE, OpType.ASSERT):
                cond = op.target or op.raw_text
                accumulated_preconditions.append(cond)
                mutation.preconditions.append(cond)
                continue

            if op.op_type == OpType.REVERT:
                # revert يعني شرط فشل — نسجله كـ precondition سلبي
                mutation.preconditions.append(f"!({op.raw_text})")
                continue

            # ─── State Reads ───
            if op.op_type in (OpType.STATE_READ, OpType.MAPPING_ACCESS):
                var_name = op.target
                if var_name:
                    accumulated_reads.add(var_name)
                    if var_name not in mutation.state_reads:
                        mutation.state_reads.append(var_name)
                continue

            # ─── State Writes → Delta ───
            if op.op_type == OpType.STATE_WRITE:
                delta = self._build_delta(
                    delta_index, op, op_idx,
                    accumulated_preconditions.copy(),
                    list(accumulated_reads),
                    state_var_names,
                )
                if delta:
                    mutation.deltas.append(delta)
                    if delta.variable not in mutation.state_writes:
                        mutation.state_writes.append(delta.variable)
                    delta_index += 1
                continue

            # ─── External Calls → Call Points ───
            if op.op_type in (OpType.EXTERNAL_CALL, OpType.EXTERNAL_CALL_ETH,
                              OpType.DELEGATECALL):
                cp = self._build_call_point(
                    call_index, op, op_idx,
                    delta_index,  # deltas_before = current delta count
                    list(accumulated_reads),
                )
                mutation.call_points.append(cp)
                call_index += 1
                continue

            # ─── Array operations → Delta ───
            if op.op_type in (OpType.ARRAY_PUSH,):
                delta = StateDelta(
                    delta_index=delta_index,
                    variable=op.target,
                    operation="push",
                    expression=op.raw_text,
                    preconditions=accumulated_preconditions.copy(),
                    depends_on_reads=list(accumulated_reads),
                    line=op.line,
                    step_index=op_idx,
                    in_loop=op.in_loop,
                )
                mutation.deltas.append(delta)
                delta_index += 1
                continue

        # ─── Post-processing: حساب deltas_after لكل call point ───
        total_deltas = len(mutation.deltas)
        for cp in mutation.call_points:
            cp.deltas_after = total_deltas - cp.deltas_before

        # ─── Net Effect: حساب التأثير الصافي ───
        mutation.net_effect = self._compute_net_effect(mutation.deltas)

        # ─── Risk indicators ───
        self._assess_risks(mutation)

        return mutation

    def _build_delta(
        self, idx: int, op: Operation, op_idx: int,
        preconditions: List[str], reads: List[str],
        state_var_names: Set[str],
    ) -> Optional[StateDelta]:
        """
        بناء StateDelta من عملية كتابة حالة.
        يحلل النص الخام لتحديد نوع العملية (= / += / -= / delete).
        """
        raw = op.raw_text.strip().rstrip(';').strip()
        var_name = op.target

        # ─── تحديد نوع العملية ───
        operation = "="
        expression = raw

        # += assignment
        m = _RE_ADD_ASSIGN.search(raw)
        if m:
            var_name = var_name or m.group(1).strip()
            operation = "+="
            expression = m.group(2).strip().rstrip(';')
            return StateDelta(
                delta_index=idx, variable=var_name, operation=operation,
                expression=expression, preconditions=preconditions,
                depends_on_reads=reads, line=op.line, step_index=op_idx,
                in_loop=op.in_loop, conditional=op.in_condition,
            )

        # -= assignment
        m = _RE_SUB_ASSIGN.search(raw)
        if m:
            var_name = var_name or m.group(1).strip()
            operation = "-="
            expression = m.group(2).strip().rstrip(';')
            return StateDelta(
                delta_index=idx, variable=var_name, operation=operation,
                expression=expression, preconditions=preconditions,
                depends_on_reads=reads, line=op.line, step_index=op_idx,
                in_loop=op.in_loop, conditional=op.in_condition,
            )

        # *= assignment
        m = _RE_MUL_ASSIGN.search(raw)
        if m:
            var_name = var_name or m.group(1).strip()
            operation = "*="
            expression = m.group(2).strip().rstrip(';')
            return StateDelta(
                delta_index=idx, variable=var_name, operation=operation,
                expression=expression, preconditions=preconditions,
                depends_on_reads=reads, line=op.line, step_index=op_idx,
                in_loop=op.in_loop, conditional=op.in_condition,
            )

        # /= assignment
        m = _RE_DIV_ASSIGN.search(raw)
        if m:
            var_name = var_name or m.group(1).strip()
            operation = "/="
            expression = m.group(2).strip().rstrip(';')
            return StateDelta(
                delta_index=idx, variable=var_name, operation=operation,
                expression=expression, preconditions=preconditions,
                depends_on_reads=reads, line=op.line, step_index=op_idx,
                in_loop=op.in_loop, conditional=op.in_condition,
            )

        # delete
        m = _RE_DELETE.search(raw)
        if m:
            var_name = m.group(1).strip()
            return StateDelta(
                delta_index=idx, variable=var_name, operation="delete",
                expression="0", preconditions=preconditions,
                depends_on_reads=reads, line=op.line, step_index=op_idx,
                in_loop=op.in_loop, conditional=op.in_condition,
            )

        # push
        m = _RE_PUSH.search(raw)
        if m:
            var_name = m.group(1).strip()
            return StateDelta(
                delta_index=idx, variable=var_name, operation="push",
                expression=raw, preconditions=preconditions,
                depends_on_reads=reads, line=op.line, step_index=op_idx,
                in_loop=op.in_loop, conditional=op.in_condition,
            )

        # pop
        m = _RE_POP.search(raw)
        if m:
            var_name = m.group(1).strip()
            return StateDelta(
                delta_index=idx, variable=var_name, operation="pop",
                expression=raw, preconditions=preconditions,
                depends_on_reads=reads, line=op.line, step_index=op_idx,
                in_loop=op.in_loop, conditional=op.in_condition,
            )

        # ++ increment
        m = _RE_INCREMENT.search(raw)
        if m:
            var_name = (m.group(1) or m.group(3) or "").strip()
            return StateDelta(
                delta_index=idx, variable=var_name, operation="+=",
                expression="1", preconditions=preconditions,
                depends_on_reads=reads, line=op.line, step_index=op_idx,
                in_loop=op.in_loop, conditional=op.in_condition,
            )

        # -- decrement
        m = _RE_DECREMENT.search(raw)
        if m:
            var_name = (m.group(1) or m.group(3) or "").strip()
            return StateDelta(
                delta_index=idx, variable=var_name, operation="-=",
                expression="1", preconditions=preconditions,
                depends_on_reads=reads, line=op.line, step_index=op_idx,
                in_loop=op.in_loop, conditional=op.in_condition,
            )

        # = simple assignment (fallback)
        m = _RE_ASSIGN.search(raw)
        if m:
            var_name = var_name or m.group(1).strip()
            expression = m.group(2).strip().rstrip(';')
            return StateDelta(
                delta_index=idx, variable=var_name, operation="=",
                expression=expression, preconditions=preconditions,
                depends_on_reads=reads, line=op.line, step_index=op_idx,
                in_loop=op.in_loop, conditional=op.in_condition,
            )

        # Fallback: إذا لم نتمكن من تحليل العملية
        if var_name:
            return StateDelta(
                delta_index=idx, variable=var_name, operation="custom",
                expression=raw, preconditions=preconditions,
                depends_on_reads=reads, line=op.line, step_index=op_idx,
                in_loop=op.in_loop, conditional=op.in_condition,
            )

        return None

    def _build_call_point(
        self, idx: int, op: Operation, op_idx: int,
        deltas_before: int, reads: List[str],
    ) -> ExternalCallPoint:
        """
        بناء ExternalCallPoint من عملية استدعاء خارجي.
        """
        # تحديد نوع الاستدعاء
        call_type = "call"
        if op.op_type == OpType.EXTERNAL_CALL_ETH:
            call_type = "call_eth"
        elif op.op_type == OpType.DELEGATECALL:
            call_type = "delegatecall"

        # محاولة استخراج قيمة الـ value
        value_expr = ""
        if op.sends_eth and op.raw_text:
            import re
            val_m = re.search(r'value:\s*([^}]+)', op.raw_text)
            if val_m:
                value_expr = val_m.group(1).strip().rstrip(',')

        return ExternalCallPoint(
            call_index=idx,
            target=op.target,
            call_type=call_type,
            sends_eth=op.sends_eth,
            value_expression=value_expr,
            line=op.line,
            step_index=op_idx,
            deltas_before=deltas_before,
            deltas_after=0,  # يُحسب لاحقاً
            reads_consumed=reads,
        )

    # ═══════════════════════════════════════════════════════════
    #  Net Effect Computation
    # ═══════════════════════════════════════════════════════════

    def _compute_net_effect(
        self, deltas: List[StateDelta]
    ) -> Dict[str, str]:
        """
        حساب التأثير الصافي لكل متغير.

        مثال:
            balance[msg.sender] -= amount    → "-amount"
            balance[to] += amount            → "+amount"
            totalSupply = totalSupply        → "=totalSupply"
        """
        net = {}
        for delta in deltas:
            var = delta.variable
            if delta.operation == "+=":
                prev = net.get(var, "0")
                if prev == "0":
                    net[var] = f"+{delta.expression}"
                else:
                    net[var] = f"{prev} + {delta.expression}"
            elif delta.operation == "-=":
                prev = net.get(var, "0")
                if prev == "0":
                    net[var] = f"-{delta.expression}"
                else:
                    net[var] = f"{prev} - {delta.expression}"
            elif delta.operation == "=":
                net[var] = f"= {delta.expression}"
            elif delta.operation == "delete":
                net[var] = "= 0 (deleted)"
            elif delta.operation in ("push", "pop"):
                net[var] = f"{delta.operation}(...)"
            else:
                net[var] = f"custom: {delta.expression}"
        return net

    # ═══════════════════════════════════════════════════════════
    #  Risk Assessment
    # ═══════════════════════════════════════════════════════════

    def _assess_risks(self, mutation: StateMutation) -> None:
        """
        تقييم مخاطر التحول.
        """
        if not mutation.call_points:
            return

        # هل يوجد call بين deltas
        for cp in mutation.call_points:
            if cp.deltas_before > 0 and cp.deltas_after > 0:
                mutation.calls_between_deltas = True
                break

        # هل يوجد delta بعد call
        if mutation.call_points and mutation.deltas:
            last_call_step = max(cp.step_index for cp in mutation.call_points)
            if any(d.step_index > last_call_step for d in mutation.deltas):
                mutation.writes_after_calls = True

            # هل يوجد reads قبل call
            first_call_step = min(cp.step_index for cp in mutation.call_points)
            if mutation.state_reads:
                mutation.reads_before_calls = True
