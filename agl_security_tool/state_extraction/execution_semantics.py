"""
AGL State Extraction — Execution Semantics Layer
طبقة دلالات التنفيذ — تحلل ترتيب العمليات داخل كل دالة

تحول العمليات المرتبة من SoliditySemanticParser إلى:
  1. ExecutionTimeline — خط زمني مرقم لكل دالة
  2. CEI Violations — كشف انتهاكات Checks-Effects-Interactions
  3. Operation ordering analysis — تحليل ترتيب العمليات

هنا يتم اكتشاف ثغرات إعادة الدخول (reentrancy) على مستوى الترتيب:
  - استدعاء خارجي يرسل ETH قبل تحديث الحالة → reentrancy كلاسيكي
  - قراءة حالة ثم استدعاء خارجي → read-only reentrancy
  - delegatecall يمكنه تعديل الحالة → storage collision

يستخدم البيانات الموجودة مسبقاً في ParsedFunction.operations
(التي يستخرجها SoliditySemanticParser بترتيب التنفيذ).
"""

from typing import List, Dict, Set, Optional, Any

from .models import (
    ExecutionStep, ExecutionTimeline, CEIViolation,
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
#  OpTypes that represent external calls / state writes / reads
# ═══════════════════════════════════════════════════════════

_EXTERNAL_CALL_OPS = {
    OpType.EXTERNAL_CALL,
    OpType.EXTERNAL_CALL_ETH,
    OpType.DELEGATECALL,
}

_ETH_SENDING_OPS = {
    OpType.EXTERNAL_CALL_ETH,
}

_STATE_WRITE_OPS = {
    OpType.STATE_WRITE,
}

_STATE_READ_OPS = {
    OpType.STATE_READ,
    OpType.MAPPING_ACCESS,
}

_CHECK_OPS = {
    OpType.REQUIRE,
    OpType.ASSERT,
    OpType.REVERT,
}


class ExecutionSemanticsExtractor:
    """
    يستخرج دلالات التنفيذ من العقود المحللة.

    يأخذ ParsedContract (الذي يحتوي على ParsedFunction مع operations مرتبة)
    ويحولها إلى ExecutionTimeline لكل دالة.

    Usage:
        extractor = ExecutionSemanticsExtractor()
        timelines = extractor.extract(contracts)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        # تعطيل تحليل view/pure (لا يكتبون حالة)
        self._analyze_view_pure = self.config.get("analyze_view_pure", True)

    # ═══════════════════════════════════════════════════════════
    #  Main API
    # ═══════════════════════════════════════════════════════════

    def extract(
        self, contracts: List[ParsedContract]
    ) -> List[ExecutionTimeline]:
        """
        استخراج timelines لكل الدوال في كل العقود.

        Args:
            contracts: العقود المحللة من SoliditySemanticParser

        Returns:
            قائمة ExecutionTimeline واحد لكل دالة
        """
        timelines = []
        for contract in contracts:
            if contract.contract_type in ("interface", "library"):
                continue
            for fname, func in contract.functions.items():
                tl = self._build_timeline(contract.name, func)
                if tl and tl.steps:
                    timelines.append(tl)
        return timelines

    def extract_for_function(
        self, contract_name: str, func: ParsedFunction
    ) -> ExecutionTimeline:
        """
        استخراج timeline لدالة واحدة.
        """
        return self._build_timeline(contract_name, func)

    # ═══════════════════════════════════════════════════════════
    #  Timeline Construction
    # ═══════════════════════════════════════════════════════════

    def _build_timeline(
        self, contract_name: str, func: ParsedFunction
    ) -> ExecutionTimeline:
        """
        بناء ExecutionTimeline من ParsedFunction.operations.

        يقوم ب:
        1. تحويل كل Operation إلى ExecutionStep مرقم
        2. كشف CEI violations (استدعاء قبل كتابة)
        3. حساب إحصائيات الترتيب
        """
        tl = ExecutionTimeline(
            function_name=func.name,
            contract_name=contract_name,
            visibility=func.visibility,
            mutability=func.mutability,
            has_reentrancy_guard=func.has_reentrancy_guard,
        )

        if not func.operations:
            return tl

        # ─── Step 1: تحويل Operations إلى ExecutionSteps ───
        for idx, op in enumerate(func.operations):
            step = self._operation_to_step(idx, op, func.name, contract_name)
            tl.steps.append(step)

        # ─── Step 2: كشف CEI violations ───
        if not func.has_reentrancy_guard:
            tl.cei_violations = self._detect_cei_violations(tl.steps, func)

        # ─── Step 3: حساب الإحصائيات ───
        self._compute_stats(tl, func)

        return tl

    def _operation_to_step(
        self, idx: int, op: Operation, func_name: str, contract_name: str
    ) -> ExecutionStep:
        """
        تحويل Operation واحد من الـ parser إلى ExecutionStep.
        """
        is_ext_call = op.op_type in _EXTERNAL_CALL_OPS
        is_write = op.op_type in _STATE_WRITE_OPS
        is_read = op.op_type in _STATE_READ_OPS

        return ExecutionStep(
            step_index=idx,
            op_type=op.op_type.value,
            target=op.target,
            details=op.details,
            line=op.line,
            function_name=func_name,
            contract_name=contract_name,
            is_external_call=is_ext_call,
            is_state_write=is_write,
            is_state_read=is_read,
            sends_eth=op.sends_eth,
            in_loop=op.in_loop,
            in_condition=op.in_condition,
            raw_text=op.raw_text,
        )

    # ═══════════════════════════════════════════════════════════
    #  CEI Violation Detection
    # ═══════════════════════════════════════════════════════════

    def _detect_cei_violations(
        self, steps: List[ExecutionStep], func: ParsedFunction
    ) -> List[CEIViolation]:
        """
        كشف انتهاكات Checks-Effects-Interactions.

        النمط الخطير:
            1. require(...) ← CHECK
            2. call{value: x}(...)  ← INTERACTION (خارجي) ← ⚠️ هنا يمكن إعادة الدخول
            3. balance -= amount    ← EFFECT (كتابة حالة) ← الرصيد لم يتحدث بعد!

        النمط الآمن (CEI):
            1. require(...)         ← CHECK
            2. balance -= amount    ← EFFECT ← يتحدث الرصيد أولاً
            3. call{value: x}(...)  ← INTERACTION ← الآن حتى لو أعاد الدخول، الرصيد محدَّث
        """
        violations = []

        # جمع كل الاستدعاءات الخارجية وكل كتابات الحالة
        external_calls = [
            s for s in steps if s.is_external_call
        ]
        state_writes = [
            s for s in steps if s.is_state_write
        ]

        if not external_calls or not state_writes:
            return violations

        for call in external_calls:
            # نبحث عن كتابات حالة تأتي بعد هذا الاستدعاء
            writes_after = [
                w for w in state_writes
                if w.step_index > call.step_index
            ]

            for write in writes_after:
                # ─── Classic reentrancy: ETH call before write ───
                if call.sends_eth:
                    vtype = "classic_reentrancy"
                    sev = "critical"
                # ─── Non-ETH call before write (ERC777, hooks) ───
                else:
                    vtype = "non_eth_reentrancy"
                    sev = "high"

                violations.append(CEIViolation(
                    call_step=call.step_index,
                    write_step=write.step_index,
                    call_target=call.target,
                    call_line=call.line,
                    write_target=write.target,
                    write_line=write.line,
                    sends_eth=call.sends_eth,
                    violation_type=vtype,
                    severity=sev,
                ))

        # ─── Read-only reentrancy pattern ───
        # view function يقرأ حالة يمكن أن تكون stale أثناء reentrancy
        if self._analyze_view_pure and func.mutability in ('view', 'pure'):
            # view functions can be re-entered during an external call
            # if they read state that hasn't been updated yet
            state_reads = [s for s in steps if s.is_state_read]
            if state_reads:
                # هذه ليست CEI violation مباشرة لكنها مؤشر read-only reentrancy
                # نسجلها كـ read_only violation مع severity مختلف
                for read in state_reads:
                    violations.append(CEIViolation(
                        call_step=-1,  # لا يوجد call في هذه الدالة
                        write_step=-1,
                        call_target="",
                        call_line=0,
                        write_target=read.target,
                        write_line=read.line,
                        sends_eth=False,
                        violation_type="read_only_reentrancy_surface",
                        severity="medium",
                    ))

        return violations

    # ═══════════════════════════════════════════════════════════
    #  Statistics
    # ═══════════════════════════════════════════════════════════

    def _compute_stats(self, tl: ExecutionTimeline, func: ParsedFunction) -> None:
        """
        حساب إحصائيات الترتيب.
        """
        first_call_index = -1
        first_write_index = -1

        for step in tl.steps:
            if step.is_external_call and first_call_index == -1:
                first_call_index = step.step_index
            if step.is_state_write and first_write_index == -1:
                first_write_index = step.step_index

        # عدد الاستدعاءات الخارجية قبل أول كتابة
        if first_call_index != -1 and first_write_index != -1:
            if first_call_index < first_write_index:
                tl.external_calls_before_writes = sum(
                    1 for s in tl.steps
                    if s.is_external_call and s.step_index < first_write_index
                )

        # عدد القراءات قبل أول استدعاء خارجي
        if first_call_index != -1:
            tl.state_reads_before_calls = sum(
                1 for s in tl.steps
                if s.is_state_read and s.step_index < first_call_index
            )

        # كتابات حالة داخل حلقات
        tl.writes_in_loops = sum(
            1 for s in tl.steps
            if s.is_state_write and s.in_loop
        )

        # عدد delegatecall
        tl.delegatecalls_count = sum(
            1 for s in tl.steps
            if s.op_type == OpType.DELEGATECALL.value
        )

    # ═══════════════════════════════════════════════════════════
    #  Cross-Function Analysis (for reentrancy-cross-function)
    # ═══════════════════════════════════════════════════════════

    def find_cross_function_risks(
        self,
        timelines: List[ExecutionTimeline],
        contracts: List[ParsedContract],
    ) -> List[Dict[str, Any]]:
        """
        كشف مخاطر إعادة الدخول عبر الدوال.

        النمط: دالة A تستدعي خارجياً ← أثناء الاستدعاء، المهاجم يستدعي دالة B
        التي تقرأ متغير حالة لم يُحدَّث بعد في دالة A.

        مثال:
            withdraw():
                call{value: balance[msg.sender]}(...)  ← هنا المهاجم يعود
                balance[msg.sender] = 0                ← لم تُنفذ بعد

            getBalance() view:
                return balance[msg.sender]             ← يقرأ الرصيد القديم!
        """
        risks = []

        # لكل عقد: نبني خريطة vars → functions
        for contract in contracts:
            if contract.contract_type in ("interface", "library"):
                continue

            # خريطة: متغير → دوال تكتبه
            var_writers: Dict[str, List[str]] = {}
            # خريطة: متغير → دوال تقرأه
            var_readers: Dict[str, List[str]] = {}

            for fname, func in contract.functions.items():
                for var in func.state_writes:
                    var_writers.setdefault(var, []).append(fname)
                for var in func.state_reads:
                    var_readers.setdefault(var, []).append(fname)

            # لكل timeline فيها CEI violation
            for tl in timelines:
                if tl.contract_name != contract.name:
                    continue
                if not tl.cei_violations:
                    continue

                for violation in tl.cei_violations:
                    if violation.violation_type in ("read_only_reentrancy_surface",):
                        continue

                    write_var = violation.write_target
                    if not write_var:
                        continue

                    # أي دالة أخرى public/external تقرأ نفس المتغير
                    readers = var_readers.get(write_var, [])
                    for reader_fn in readers:
                        if reader_fn == tl.function_name:
                            continue
                        func = contract.functions.get(reader_fn)
                        if not func:
                            continue
                        if func.visibility not in ('public', 'external'):
                            continue

                        risks.append({
                            "risk_type": "cross_function_reentrancy",
                            "contract": contract.name,
                            "writer_function": tl.function_name,
                            "reader_function": reader_fn,
                            "shared_variable": write_var,
                            "call_target": violation.call_target,
                            "call_line": violation.call_line,
                            "write_line": violation.write_line,
                            "severity": "high",
                            "description": (
                                f"During external call in `{tl.function_name}` "
                                f"(line {violation.call_line}), attacker can re-enter "
                                f"via `{reader_fn}` which reads `{write_var}` that "
                                f"hasn't been updated yet (line {violation.write_line})"
                            ),
                        })

        return risks
