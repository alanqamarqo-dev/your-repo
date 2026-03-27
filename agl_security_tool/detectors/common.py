"""
AGL Common Vulnerability Detectors — كاشفات الثغرات الشائعة
6 detectors for common Solidity pitfalls:

1. UNCHECKED-CALL — Low-level call without return value check
2. UNBOUNDED-LOOP — Loop over dynamic array (DoS risk)
3. DUPLICATE-CONDITION — Same condition checked twice (logic error)
4. SHADOWED-STATE — Local variable shadows state variable
5. ENCODE-PACKED — abi.encodePacked with multiple dynamic types (hash collision)
6. MISSING-EVENT — State-changing function without event emission
"""

from typing import List, Set, Dict
import re
from . import (
    BaseDetector, Finding, Severity, Confidence,
    ParsedContract, ParsedFunction, OpType
)


class UncheckedLowLevelCall(BaseDetector):
    """
    استدعاء منخفض المستوى بدون فحص القيمة المرجعة.

    Pattern:
        target.call{value: x}("");  // ✗ القيمة المرجعة مُتجاهلة
        (bool ok,) = target.call{value: x}(""); require(ok);  // ✓

    Solidity .call returns (bool success, bytes memory data).
    Ignoring success means failed transfers go unnoticed.
    """

    DETECTOR_ID = "UNCHECKED-CALL"
    TITLE = "Unchecked low-level call return value"
    SEVERITY = Severity.HIGH
    CONFIDENCE = Confidence.HIGH

    def detect(self, contract: ParsedContract, all_contracts: List[ParsedContract]) -> List[Finding]:
        findings = []

        for fname, func in contract.functions.items():
            for op in func.operations:
                if op.op_type not in (OpType.EXTERNAL_CALL, OpType.EXTERNAL_CALL_ETH):
                    continue
                if not op.raw_text:
                    continue

                raw = op.raw_text.strip()

                # هل يستخدم .call أو .send؟
                if '.call' not in raw and '.send' not in raw:
                    continue

                # هل القيمة المرجعة مُلتقطة ومفحوصة؟
                # Patterns for checked:
                #   (bool success, ) = ... ; require(success)
                #   if (!target.send(...)) revert
                #   bool ok = target.send(...); require(ok)

                is_checked = False

                # Pattern 1: (bool ...) = ...
                if re.match(r'\(bool\s+\w+', raw):
                    is_checked = True
                # Pattern 2: bool x = ...
                elif re.match(r'bool\s+\w+\s*=', raw):
                    is_checked = True
                # Pattern 3: If statement wrapping
                elif raw.startswith('if'):
                    is_checked = True
                # Pattern 4: require wrapping
                elif 'require' in raw:
                    is_checked = True

                # Even if captured, check if it's actually used in require
                if is_checked:
                    # Extract the bool variable name
                    m = re.search(r'bool\s+(\w+)', raw)
                    if m:
                        bool_var = m.group(1)
                        # Check subsequent operations for require(bool_var)
                        found_in_ops = False
                        for subsequent_op in func.operations:
                            if subsequent_op.line <= op.line:
                                continue
                            if subsequent_op.op_type == OpType.REQUIRE and subsequent_op.target:
                                if bool_var in subsequent_op.target:
                                    found_in_ops = True
                                    break
                        if not found_in_ops:
                            # Bool captured but never checked
                            is_checked = False

                if not is_checked:
                    findings.append(self._make_finding(
                        contract, func,
                        f"Function `{fname}` has unchecked low-level call (line {op.line}). "
                        f"The return value of `.call` / `.send` is not verified. "
                        f"If the call fails, execution continues silently. "
                        f"Capture and check: `(bool success,) = addr.call{{...}}(...); "
                        f"require(success);`",
                        line=op.line,
                        extra={"call_text": raw[:100]}
                    ))

        return findings


class UnboundedLoop(BaseDetector):
    """
    حلقة غير محدودة — تكرار على مصفوفة ديناميكية (خطر DoS).

    Pattern:
        for (uint i = 0; i < users.length; i++) {
            users[i].transfer(rewards[i]);  // إذا قائمة users كبيرة → out of gas
        }

    Detection: Loop where the bound is a storage array .length or
    a variable that can grow unbounded.

    Real-world: GovernMental Ponzi (1100 ETH stuck), many airdrop contracts
    """

    DETECTOR_ID = "UNBOUNDED-LOOP"
    TITLE = "Unbounded loop over storage array (DoS risk)"
    SEVERITY = Severity.MEDIUM
    CONFIDENCE = Confidence.MEDIUM

    def detect(self, contract: ParsedContract, all_contracts: List[ParsedContract]) -> List[Finding]:
        findings = []

        state_arrays = {
            name for name, var in contract.state_vars.items()
            if var.is_array or var.is_mapping
        }

        for fname, func in contract.functions.items():
            body = func.raw_body or ""

            # البحث عن أنماط الحلقات
            for_matches = re.finditer(
                r'for\s*\([^;]*;\s*\w+\s*<\s*(\w[\w.\[\]()]*)\s*;',
                body
            )

            for match in for_matches:
                bound = match.group(1).strip()
                base_var = bound.split('.')[0].split('[')[0]

                # هل الحد هو .length لمصفوفة حالة؟
                is_storage_bound = (
                    ('.length' in bound and base_var in state_arrays) or
                    base_var in state_arrays
                )

                # هل يوجد فحص حد أقصى؟
                has_max_check = bool(
                    re.search(r'require.*?<\s*MAX|maxIterations|MAX_LENGTH|BATCH_SIZE',
                              body, re.IGNORECASE)
                )

                if is_storage_bound and not has_max_check:
                    # هل الحلقة تتضمن عمليات مكلفة (رسائل خارجية)؟
                    has_costly_ops = any(
                        op.op_type in (OpType.EXTERNAL_CALL, OpType.EXTERNAL_CALL_ETH) and op.in_loop
                        for op in func.operations
                    )

                    severity = Severity.HIGH if has_costly_ops else Severity.MEDIUM

                    findings.append(self._make_finding(
                        contract, func,
                        f"Function `{fname}` loops over storage array `{base_var}` "
                        f"without a maximum iteration limit. As the array grows, "
                        f"the function may exceed the block gas limit, making it "
                        f"permanently uncallable (DoS). "
                        f"{'Loop also contains external calls, amplifying gas cost. ' if has_costly_ops else ''}"
                        f"Add a maximum iteration limit or use pagination.",
                        line=func.line_start,
                        severity=severity,
                        extra={
                            "array": base_var,
                            "bound": bound,
                            "has_external_calls": has_costly_ops,
                        }
                    ))

        return findings


class DuplicateCondition(BaseDetector):
    """
    شرط مكرر — نفس الشرط يُفحص مرتين (خطأ منطقي أو نسخ).

    Pattern:
        require(x > 0 && x > 0);     // شرط مكرر
        if (a == b || a == b) { ... } // نفس الشيء

    ALSO catches: require(A); ... require(A); (same condition in different requires)

    Real-world: Salty.IO contest M-09 — duplicate condition masked a bug
    """

    DETECTOR_ID = "DUPLICATE-CONDITION"
    TITLE = "Duplicate condition in expression"
    SEVERITY = Severity.MEDIUM
    CONFIDENCE = Confidence.HIGH

    def detect(self, contract: ParsedContract, all_contracts: List[ParsedContract]) -> List[Finding]:
        findings = []

        for fname, func in contract.functions.items():
            # ═══ Check 1: Same sub-condition within && or || ═══
            body = func.raw_body or ""

            # Find all conditions in require/if
            conditions = []
            for m in re.finditer(r'(?:require|if|assert)\s*\((.+?)\)(?:\s*;|\s*\{)', body, re.DOTALL):
                conditions.append((m.start(), m.group(1).strip()))

            for _, cond in conditions:
                # Split by && and ||
                parts_and = [p.strip() for p in re.split(r'&&', cond)]
                parts_or = [p.strip() for p in re.split(r'\|\|', cond)]

                for parts, op in [(parts_and, '&&'), (parts_or, '||')]:
                    seen = set()
                    for part in parts:
                        normalized = re.sub(r'\s+', '', part)
                        if normalized in seen and normalized:
                            findings.append(self._make_finding(
                                contract, func,
                                f"Function `{fname}` has duplicate condition `{part}` "
                                f"within `{op}` expression. This is either: "
                                f"(1) a copy-paste bug where a different condition was intended, or "
                                f"(2) redundant code. Check if a different condition should be used.",
                                line=func.line_start,
                                extra={
                                    "duplicate": part,
                                    "operator": op,
                                    "full_condition": cond[:200],
                                }
                            ))
                        seen.add(normalized)

            # ═══ Check 2: Same require condition repeated in function ═══
            require_conditions = []
            for op in func.operations:
                if op.op_type == OpType.REQUIRE and op.target:
                    normalized = re.sub(r'\s+', '', op.target)
                    require_conditions.append((op.line, normalized, op.target))

            seen_reqs: Dict[str, int] = {}
            for line, normalized, original in require_conditions:
                if normalized in seen_reqs:
                    findings.append(self._make_finding(
                        contract, func,
                        f"Function `{fname}` has the same require condition "
                        f"`{original}` at lines {seen_reqs[normalized]} and {line}. "
                        f"This is likely a copy-paste error — the second condition may "
                        f"need to check something different.",
                        line=line,
                        confidence=Confidence.MEDIUM,
                        extra={
                            "condition": original,
                            "first_line": seen_reqs[normalized],
                            "second_line": line,
                        }
                    ))
                else:
                    seen_reqs[normalized] = line

        return findings


class ShadowedStateVariable(BaseDetector):
    """
    تظليل متغير الحالة — متغير محلي بنفس اسم متغير الحالة.

    Pattern:
        uint256 balance;  // state variable
        function foo() {
            uint256 balance = 0;  // ✗ يظلل المتغير ↑ — أي balance؟
        }

    Detection: Local variable declaration with same name as state var.
    """

    DETECTOR_ID = "SHADOWED-STATE"
    TITLE = "Local variable shadows state variable"
    SEVERITY = Severity.LOW
    CONFIDENCE = Confidence.HIGH

    def detect(self, contract: ParsedContract, all_contracts: List[ParsedContract]) -> List[Finding]:
        findings = []
        state_names = set(contract.state_vars.keys())

        for fname, func in contract.functions.items():
            if func.is_constructor:
                continue  # constructor parameters commonly shadow

            body = func.raw_body or ""

            # البحث عن تعريفات المتغيرات المحلية
            local_decls = re.finditer(
                r'(?:uint\d*|int\d*|address|bool|bytes\d*|string|mapping)\s+(?:memory\s+|storage\s+|calldata\s+)?(\w+)',
                body
            )

            for m in local_decls:
                var_name = m.group(1)
                if var_name in state_names:
                    findings.append(self._make_finding(
                        contract, func,
                        f"Local variable `{var_name}` in `{fname}` shadows "
                        f"state variable `{var_name}` (declared at line "
                        f"{contract.state_vars[var_name].line}). This can cause "
                        f"confusion: modifications to the local variable don't affect "
                        f"the state. Rename the local variable to avoid ambiguity.",
                        line=func.line_start,
                        extra={
                            "variable": var_name,
                            "state_line": contract.state_vars[var_name].line,
                        }
                    ))

            # أيضاً فحص معاملات الدالة
            for param in func.parameters:
                p_name = param.get("name", "")
                if p_name in state_names:
                    findings.append(self._make_finding(
                        contract, func,
                        f"Parameter `{p_name}` in `{fname}` shadows state variable "
                        f"`{p_name}`. Inside the function, `{p_name}` refers to the "
                        f"parameter, not the state variable.",
                        line=func.line_start,
                        confidence=Confidence.MEDIUM,
                        extra={"variable": p_name, "source": "parameter"}
                    ))

        return findings


class EncodePacked(BaseDetector):
    """
    abi.encodePacked مع أنواع ديناميكية متعددة — خطر تصادم التجزئة.

    Pattern:
        keccak256(abi.encodePacked(name, data))
        // name="ab", data="cd" → "abcd"
        // name="abc", data="d" → "abcd" ← تصادم!

    abi.encodePacked لا يضيف padding — أنواع ديناميكية متجاورة تتصادم.
    استخدم abi.encode بدلاً منه.
    """

    DETECTOR_ID = "ENCODE-PACKED-COLLISION"
    TITLE = "Hash collision risk with abi.encodePacked"
    SEVERITY = Severity.MEDIUM
    CONFIDENCE = Confidence.MEDIUM

    _DYNAMIC_TYPES = {'string', 'bytes', 'uint[]', 'int[]', 'address[]',
                       'bool[]', 'bytes32[]'}

    def detect(self, contract: ParsedContract, all_contracts: List[ParsedContract]) -> List[Finding]:
        findings = []

        for fname, func in contract.functions.items():
            body = func.raw_body or ""

            # البحث عن abi.encodePacked(...)
            for m in re.finditer(r'abi\.encodePacked\s*\(([^)]+)\)', body):
                args = m.group(1)
                arg_list = [a.strip() for a in args.split(',')]

                if len(arg_list) < 2:
                    continue

                # عدّ الأنواع الديناميكية
                dynamic_count = 0
                for arg in arg_list:
                    # Check if argument is a known dynamic type variable
                    arg_base = arg.split('[')[0].strip()
                    # Check function parameters
                    for param in func.parameters:
                        if param.get("name") == arg_base and param.get("type") in self._DYNAMIC_TYPES:
                            dynamic_count += 1
                            break
                    # Check if it looks like a string or bytes
                    if 'string' in arg.lower() or arg_base in ('name', 'symbol', 'data', 'message'):
                        dynamic_count += 1

                # Even without type info, flag if used with keccak256
                is_hashed = bool(re.search(
                    r'keccak256\s*\(\s*abi\.encodePacked',
                    body[max(0, m.start() - 30):m.end()]
                ))

                if dynamic_count >= 2 or (is_hashed and len(arg_list) >= 2):
                    findings.append(self._make_finding(
                        contract, func,
                        f"Function `{fname}` uses `abi.encodePacked` with multiple "
                        f"arguments ({len(arg_list)} args). encodePacked doesn't pad "
                        f"dynamic types, causing potential hash collisions: "
                        f'`encodePacked("ab","cd") == encodePacked("abc","d")`. '
                        f"Use `abi.encode` instead of `abi.encodePacked`.",
                        line=func.line_start,
                        extra={
                            "args": args,
                            "dynamic_count": dynamic_count,
                            "is_hashed": is_hashed,
                        }
                    ))

        return findings


class MissingEventEmission(BaseDetector):
    """
    دالة تغيّر الحالة بدون إصدار حدث (event).

    Pattern:
        function setOwner(address _owner) onlyOwner {
            owner = _owner;  // ✗ لا يوجد emit
        }

    Events are critical for:
    - Off-chain monitoring and indexing
    - UI updates
    - Audit trails
    - Detecting suspicious changes

    Detection: Public/external function that modifies state without emit.
    """

    DETECTOR_ID = "MISSING-EVENT"
    TITLE = "State change without event emission"
    SEVERITY = Severity.LOW
    CONFIDENCE = Confidence.MEDIUM

    # أسماء تدل على تعديل — لا تحتاج event لا محالة
    _SKIP_NAMES = {'constructor', 'receive', 'fallback', '_'}

    def detect(self, contract: ParsedContract, all_contracts: List[ParsedContract]) -> List[Finding]:
        findings = []

        for fname, func in contract.functions.items():
            if fname in self._SKIP_NAMES or fname.startswith('_'):
                continue
            if func.visibility not in ('public', 'external'):
                continue
            if func.mutability in ('view', 'pure'):
                continue
            if not func.modifies_state:
                continue

            # هل أصدرت حدثاً؟
            has_emit = any(op.op_type == OpType.EMIT for op in func.operations)
            if has_emit:
                continue

            # هل الدالة "setter" أو "admin" (أهم)
            is_setter = bool(re.match(r'^set[A-Z]|^update[A-Z]|^change[A-Z]', fname))
            is_admin = func.has_access_control

            # فقط الـ setters والـ admin functions
            if is_setter or is_admin:
                findings.append(self._make_finding(
                    contract, func,
                    f"{'Admin' if is_admin else 'Setter'} function `{fname}` modifies "
                    f"state variables `{', '.join(func.state_writes)}` without emitting "
                    f"an event. Events are essential for off-chain monitoring, UI updates, "
                    f"and detecting suspicious admin actions. Add an event emission.",
                    line=func.line_start,
                    extra={
                        "state_writes": func.state_writes,
                        "is_admin": is_admin,
                        "is_setter": is_setter,
                    }
                ))

        return findings
