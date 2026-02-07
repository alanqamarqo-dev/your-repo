"""
AGL Reentrancy Detectors — كاشفات إعادة الدخول
4 detectors covering all reentrancy variants:

1. REENTRANCY-ETH — External call sending ETH before state update (classic)
2. REENTRANCY-NO-ETH — External call (no ETH) before state update  
3. REENTRANCY-READ-ONLY — View function reads state during external call
4. REENTRANCY-CROSS-FUNCTION — State shared across public functions, call then write

These check the ORDER of operations, not regex patterns.
"""

from typing import List, Dict, Set
from . import (
    BaseDetector, Finding, Severity, Confidence,
    ParsedContract, ParsedFunction, Operation, OpType
)


class ReentrancyETH(BaseDetector):
    """
    كاشف إعادة الدخول الكلاسيكي — استدعاء خارجي يرسل ETH قبل تحديث الحالة.

    Pattern:
        external_call{value: x}(...)   // sends ETH → attacker callback
        state_var = ...                 // state update AFTER call
    
    Real-world: The DAO hack, many DeFi vaults
    Excludes: Functions with nonReentrant modifier
    """

    DETECTOR_ID = "REENTRANCY-ETH"
    TITLE = "Reentrancy vulnerability (ETH transfer before state update)"
    SEVERITY = Severity.CRITICAL
    CONFIDENCE = Confidence.HIGH

    def detect(self, contract: ParsedContract, all_contracts: List[ParsedContract]) -> List[Finding]:
        findings = []

        for fname, func in contract.functions.items():
            # تخطي الدوال المحمية
            if func.has_reentrancy_guard:
                continue
            if func.mutability in ('view', 'pure'):
                continue

            # البحث عن: EXTERNAL_CALL_ETH يتبعه STATE_WRITE
            eth_calls = []
            state_writes_after_call = []

            found_eth_call = False
            for op in func.operations:
                if op.op_type == OpType.EXTERNAL_CALL_ETH:
                    found_eth_call = True
                    eth_calls.append(op)
                elif op.op_type == OpType.STATE_WRITE and found_eth_call:
                    state_writes_after_call.append(op)

            if eth_calls and state_writes_after_call:
                call = eth_calls[0]
                write = state_writes_after_call[0]
                findings.append(self._make_finding(
                    contract, func,
                    f"Function `{fname}` sends ETH via `{call.target}` (line {call.line}) "
                    f"before updating state variable `{write.target}` (line {write.line}). "
                    f"An attacker can re-enter during the ETH transfer to exploit the "
                    f"stale state. Apply checks-effects-interactions (CEI) pattern: "
                    f"update state BEFORE the external call, or use a reentrancy guard.",
                    line=call.line,
                    extra={
                        "call_target": call.target,
                        "call_line": call.line,
                        "state_var": write.target,
                        "write_line": write.line,
                        "pattern": "checks-effects-interactions violation",
                    }
                ))

        return findings


class ReentrancyNoETH(BaseDetector):
    """
    إعادة دخول بدون ETH — استدعاء خارجي (ERC20/عقد) قبل تحديث الحالة.

    Pattern:
        token.transfer(to, amount)     // external call (ERC777 hooks!)
        balances[msg.sender] -= amount // state update AFTER
    
    Real-world: imBTC/Uniswap v1 (ERC777), many token interactions
    """

    DETECTOR_ID = "REENTRANCY-NO-ETH"
    TITLE = "Reentrancy vulnerability (external call before state update)"
    SEVERITY = Severity.HIGH
    CONFIDENCE = Confidence.MEDIUM

    def detect(self, contract: ParsedContract, all_contracts: List[ParsedContract]) -> List[Finding]:
        findings = []

        for fname, func in contract.functions.items():
            if func.has_reentrancy_guard:
                continue
            if func.mutability in ('view', 'pure'):
                continue

            # External call (non-ETH) followed by state write
            ext_calls = []
            state_writes_after = []
            found_ext_call = False

            for op in func.operations:
                if op.op_type == OpType.EXTERNAL_CALL and not op.sends_eth:
                    found_ext_call = True
                    ext_calls.append(op)
                elif op.op_type == OpType.STATE_WRITE and found_ext_call:
                    state_writes_after.append(op)

            if ext_calls and state_writes_after:
                call = ext_calls[0]
                write = state_writes_after[0]
                # Skip if the call target is the same as the write target
                # (e.g., token.transfer then token = ...)
                findings.append(self._make_finding(
                    contract, func,
                    f"Function `{fname}` makes external call via `{call.target}.{call.details or 'call'}` "
                    f"(line {call.line}) before updating `{write.target}` (line {write.line}). "
                    f"If the called contract has hooks (ERC777, ERC721 onReceived, etc.), "
                    f"an attacker can re-enter. Update state before external interactions.",
                    line=call.line,
                    extra={
                        "call_target": call.target,
                        "call_method": call.details,
                        "state_var": write.target,
                        "write_line": write.line,
                    }
                ))

        return findings


class ReentrancyReadOnly(BaseDetector):
    """
    إعادة دخول القراءة فقط — دالة view تقرأ حالة غير متسقة أثناء استدعاء خارجي.

    Pattern:
        funcA(): external_call → state is inconsistent during callback
        funcB() view: reads same state → returns wrong value
    
    Real-world: Curve/Vyper read-only reentrancy ($60M+), Balancer
    
    Detection: Find functions that make external calls AND share state
    with view functions that DON'T have reentrancy guards.
    """

    DETECTOR_ID = "REENTRANCY-READ-ONLY"
    TITLE = "Read-only reentrancy (view function reads inconsistent state)"
    SEVERITY = Severity.HIGH
    CONFIDENCE = Confidence.MEDIUM

    def detect(self, contract: ParsedContract, all_contracts: List[ParsedContract]) -> List[Finding]:
        findings = []

        # الخطوة 1: جمع الدوال التي تجري مكالمات خارجية وتعدّل الحالة
        callers_with_state = {}  # fname -> (call_ops, written_vars)
        for fname, func in contract.functions.items():
            if not func.external_calls:
                continue
            if not func.state_writes:
                continue

            # هل الاستدعاء الخارجي يأتي قبل كتابة الحالة؟
            first_call_idx = None
            first_write_idx = None
            for i, op in enumerate(func.operations):
                if first_call_idx is None and op.op_type in (OpType.EXTERNAL_CALL, OpType.EXTERNAL_CALL_ETH):
                    first_call_idx = i
                if first_write_idx is None and op.op_type == OpType.STATE_WRITE:
                    first_write_idx = i

            # Call happens, state is written (in any order — state could be inconsistent during call)
            if first_call_idx is not None:
                callers_with_state[fname] = (func.external_calls, set(func.state_writes))

        if not callers_with_state:
            return findings

        # الخطوة 2: البحث عن دوال view تقرأ نفس المتغيرات
        for fname, func in contract.functions.items():
            if func.mutability != 'view':
                continue
            if func.has_reentrancy_guard:
                continue

            read_vars = set(func.state_reads)
            if not read_vars:
                continue

            # هل تقرأ متغيرات يعدّلها caller مع مكالمة خارجية؟
            for caller_name, (calls, written_vars) in callers_with_state.items():
                overlap = read_vars & written_vars
                if overlap:
                    findings.append(self._make_finding(
                        contract, func,
                        f"View function `{fname}` reads state variables "
                        f"`{', '.join(overlap)}` that are modified by `{caller_name}`, "
                        f"which also makes external calls. During the external call in "
                        f"`{caller_name}`, an attacker can call `{fname}` and observe "
                        f"inconsistent state (read-only reentrancy). "
                        f"Use a reentrancy guard on view functions that read sensitive state, "
                        f"or ensure state is updated before external calls.",
                        line=func.line_start,
                        extra={
                            "view_function": fname,
                            "caller_function": caller_name,
                            "shared_vars": list(overlap),
                            "pattern": "read-only reentrancy",
                        }
                    ))

        return findings


class ReentrancyCrossFunction(BaseDetector):
    """
    إعادة الدخول عبر الدوال — المهاجم يعيد الدخول عبر دالة مختلفة.

    Pattern:
        withdraw(): call{value}(msg.sender) → state not yet updated
        attacker re-enters via deposit() or another function that reads stale state
    
    Detection: Function A has external call, Function B reads/writes same state
    variables, and B is public/external without reentrancy guard.
    """

    DETECTOR_ID = "REENTRANCY-CROSS-FUNCTION"
    TITLE = "Cross-function reentrancy"
    SEVERITY = Severity.HIGH
    CONFIDENCE = Confidence.MEDIUM

    def detect(self, contract: ParsedContract, all_contracts: List[ParsedContract]) -> List[Finding]:
        findings = []

        # جمع الدوال التي تجري مكالمات خارجية
        callers = {}  # fname -> (call_ops, set of state vars written AFTER call)
        for fname, func in contract.functions.items():
            if not func.external_calls:
                continue
            if func.has_reentrancy_guard:
                continue

            # متغيرات الحالة المكتوبة بعد المكالمة الخارجية
            found_call = False
            vars_after_call = set()
            # Also collect vars that could be read in stale state
            vars_in_scope = set(func.state_writes) | set(func.state_reads)

            for op in func.operations:
                if op.op_type in (OpType.EXTERNAL_CALL, OpType.EXTERNAL_CALL_ETH):
                    found_call = True
                elif found_call and op.op_type == OpType.STATE_WRITE:
                    vars_after_call.add(op.target)

            if found_call:
                callers[fname] = (func.external_calls, vars_after_call, vars_in_scope)

        if not callers:
            return findings

        # البحث عن دوال أخرى عامة تتعامل مع نفس المتغيرات
        for fname, func in contract.functions.items():
            if fname in callers:
                continue  # لا نقارن الدالة بنفسها
            if func.visibility not in ('public', 'external'):
                continue
            if func.has_reentrancy_guard:
                continue

            func_vars = set(func.state_reads) | set(func.state_writes)
            if not func_vars:
                continue

            for caller_name, (calls, vars_after_call, vars_in_scope) in callers.items():
                # Check for shared state variables
                shared = func_vars & vars_in_scope
                critical_shared = func_vars & vars_after_call  # vars written AFTER call

                if shared and (critical_shared or func.modifies_state):
                    findings.append(self._make_finding(
                        contract, func,
                        f"Function `{caller_name}` makes external calls without "
                        f"reentrancy protection and shares state variables "
                        f"`{', '.join(shared)}` with public function `{fname}`. "
                        f"An attacker can re-enter via `{fname}` during the external "
                        f"call and manipulate shared state. "
                        f"Apply nonReentrant modifier to both functions.",
                        line=func.line_start,
                        extra={
                            "caller_function": caller_name,
                            "target_function": fname,
                            "shared_vars": list(shared),
                            "vars_stale_during_call": list(critical_shared),
                        }
                    ))

        return findings
