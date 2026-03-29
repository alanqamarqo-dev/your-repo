"""
AGL Input Validation Detectors — كاشفات التحقق من المدخلات
3 detectors for missing input validation:

1. UNSAFE-DOWNCAST — Integer downcast without bounds check
2. ZERO-ADDRESS — Missing zero-address validation on critical parameters
3. MISSING-INPUT-VALIDATION — Missing validation on function parameters
"""

from typing import List
import re
from . import (
    BaseDetector,
    Finding,
    Severity,
    Confidence,
    ParsedContract,
    ParsedFunction,
    OpType,
)


class UnsafeDowncast(BaseDetector):
    """
    تحويل عددي غير آمن — تقليص حجم integer بدون فحص.

    Pattern:
        uint128 value = uint128(largeValue);  // ✗ يقطع البتات العليا بصمت
        int8 small = int8(bigInt);            // ✗ قد يتحول لقيمة سالبة

    Safe:
        require(largeValue <= type(uint128).max);
        uint128 value = uint128(largeValue);  // ✓

    Detection: Type casts from larger to smaller integer types without
    bounds checking.

    Real-world: Compound governance (uint96), Solmate SafeCast
    """

    DETECTOR_ID = "UNSAFE-DOWNCAST"
    TITLE = "Integer downcast without overflow check"
    SEVERITY = Severity.HIGH
    CONFIDENCE = Confidence.MEDIUM

    # أنماط التحويل — من كبير لصغير
    _DOWNCAST_PATTERN = re.compile(
        r"(?:uint|int)(8|16|32|64|96|128|160|224)\s*\(\s*(\w+)\s*\)",
    )

    _SAFE_CAST_PATTERNS = [
        # SafeCast library
        re.compile(r"SafeCast|safe(?:Cast|To)(?:Uint|Int)", re.IGNORECASE),
        # require with type().max bounds
        re.compile(r"require\s*\(.*?<=\s*type\s*\(\s*(?:uint|int)\d+\s*\)\s*\.max", re.IGNORECASE),
        # Explicit bounds check
        re.compile(r"require\s*\(.*?<\s*(?:2\s*\*\*\s*\d+|0x[fF]+)", re.IGNORECASE),
        # unchecked block with SafeCast
        re.compile(r"using\s+SafeCast", re.IGNORECASE),
    ]

    def detect(
        self, contract: ParsedContract, all_contracts: List[ParsedContract]
    ) -> List[Finding]:
        findings = []

        if contract.contract_type in ("interface", "library"):
            return findings

        # هل يستخدم SafeCast على مستوى العقد؟
        full_source = ""
        for func in contract.functions.values():
            full_source += (func.raw_body or "") + "\n"

        uses_safe_cast = any(
            p.search(full_source) for p in self._SAFE_CAST_PATTERNS[:1]
        )
        if uses_safe_cast:
            return findings

        for fname, func in contract.functions.items():
            body = func.raw_body or ""
            if not body:
                continue

            # ابحث عن downcasts
            for match in self._DOWNCAST_PATTERN.finditer(body):
                target_bits = int(match.group(1))
                var_name = match.group(2)

                # هل يوجد فحص حدود قبل التحويل؟
                has_check = any(
                    p.search(body) for p in self._SAFE_CAST_PATTERNS
                )
                if has_check:
                    continue

                # هل المتغير هو parameter (أكثر خطورة) أو local؟
                param_names = []
                for p in (func.parameters or []):
                    if isinstance(p, dict):
                        param_names.append(p.get("name", ""))
                    else:
                        parts = str(p).strip().split()
                        param_names.append(parts[-1] if parts else str(p))
                is_param = var_name in param_names

                findings.append(
                    self._make_finding(
                        contract,
                        func,
                        f"Function `{fname}` downcasts `{var_name}` to `uint{target_bits}` "
                        f"without bounds checking. If the value exceeds "
                        f"`type(uint{target_bits}).max`, the upper bits are silently "
                        f"truncated, causing incorrect values. Use OpenZeppelin's "
                        f"`SafeCast` library or add an explicit bounds check: "
                        f"`require({var_name} <= type(uint{target_bits}).max)`.",
                        line=func.line_start,
                        confidence=Confidence.HIGH if is_param else Confidence.MEDIUM,
                        extra={
                            "variable": var_name,
                            "target_type": f"uint{target_bits}",
                        },
                    )
                )

        return findings


class ZeroAddressCheck(BaseDetector):
    """
    فحص العنوان الصفري مفقود — بارامترات عناوين حرجة بلا تحقق.

    Pattern:
        function setOwner(address _owner) external onlyOwner {
            owner = _owner;  // ✗ إذا _owner == address(0) يُقفل العقد للأبد
        }

    Safe:
        require(_owner != address(0), "zero address");
        owner = _owner;  // ✓

    Detection: Functions that write address parameters to state without
    checking for address(0).

    Real-world: Permanent lockout of admin functions, lost funds
    """

    DETECTOR_ID = "ZERO-ADDRESS"
    TITLE = "Missing zero-address validation"
    SEVERITY = Severity.MEDIUM
    CONFIDENCE = Confidence.MEDIUM

    _CRITICAL_STATE = re.compile(
        r"(?:owner|admin|governance|operator|treasury|fee\s*Recipient|vault|controller|manager|authority)",
        re.IGNORECASE,
    )

    _ZERO_CHECK_PATTERNS = [
        re.compile(r"require\s*\([^)]*!=\s*address\s*\(\s*0\s*\)", re.IGNORECASE),
        re.compile(r"if\s*\([^)]*==\s*address\s*\(\s*0\s*\)\s*\)\s*revert", re.IGNORECASE),
        re.compile(r"_checkNonZero|_requireNonZero|_notZero", re.IGNORECASE),
        # Custom error pattern
        re.compile(r"revert\s+Zero\s*Address", re.IGNORECASE),
    ]

    def detect(
        self, contract: ParsedContract, all_contracts: List[ParsedContract]
    ) -> List[Finding]:
        findings = []

        if contract.contract_type in ("interface", "library"):
            return findings

        for fname, func in contract.functions.items():
            if func.mutability in ("view", "pure"):
                continue
            # تخطي constructors — عادةً تأخذ عناوين موثوقة من deployer
            if func.is_constructor:
                continue
            body = func.raw_body or ""
            if not body:
                continue

            # استخرج بارامترات العناوين
            address_params = []
            for param in (func.parameters or []):
                if isinstance(param, dict):
                    if "address" in (param.get("type", "") or ""):
                        address_params.append(param.get("name", ""))
                else:
                    # Fallback for string format
                    param_str = str(param)
                    if "address" in param_str.lower():
                        parts = param_str.strip().split()
                        param_name = parts[-1] if parts else param_str
                        address_params.append(param_name)

            if not address_params:
                continue

            # هل يوجد فحص للعنوان الصفري؟
            has_zero_check = any(p.search(body) for p in self._ZERO_CHECK_PATTERNS)
            if has_zero_check:
                continue

            # هل الدالة تكتب في state var حرج فعلاً؟ (ليس فقط أي state write)
            critical_writes = [w for w in func.state_writes if self._CRITICAL_STATE.search(w)]
            if not critical_writes:
                continue

            # هل البارامتر يُكتب في state variable حرج؟
            for param_name in address_params:
                for write_var in critical_writes:
                    if self._CRITICAL_STATE.search(write_var):
                        findings.append(
                            self._make_finding(
                                contract,
                                func,
                                f"Function `{fname}` sets critical state variable "
                                f"`{write_var}` from parameter `{param_name}` without "
                                f"checking for `address(0)`. If called with the zero "
                                f"address, this may permanently lock the contract's "
                                f"admin functionality or redirect funds to a burn address. "
                                f"Add: `require({param_name} != address(0))`.",
                                line=func.line_start,
                                extra={
                                    "parameter": param_name,
                                    "state_var": write_var,
                                },
                            )
                        )
                        break  # واحد لكل دالة

        return findings


class MissingInputValidation(BaseDetector):
    """
    تحقق من المدخلات مفقود — بارامترات حرجة بلا bounds check.

    Pattern:
        function setFee(uint256 _fee) external onlyOwner {
            fee = _fee;  // ✗ يمكن جعل الـ fee = 100% → سرقة كل الأموال
        }

    Safe:
        require(_fee <= MAX_FEE, "fee too high");
        fee = _fee;  // ✓

    Detection: Functions that write numeric parameters to state without
    upper/lower bounds validation, specifically for fee/rate/limit patterns.
    """

    DETECTOR_ID = "MISSING-INPUT-VALIDATION"
    TITLE = "Missing bounds validation on critical parameter"
    SEVERITY = Severity.MEDIUM
    CONFIDENCE = Confidence.LOW

    _CRITICAL_PARAMS = re.compile(
        r"(?:^|_)(?:fee|rate|ratio|percent|bps|threshold|limit|leverage|cap|floor|ceiling|duration|delay|period|multiplier)(?:$|_|\b)",
        re.IGNORECASE,
    )

    _BOUNDS_CHECK = [
        re.compile(r"require\s*\([^)]*(?:<=|>=|<|>)\s*(?:\d+|MAX_|MIN_|_MAX|_MIN)", re.IGNORECASE),
        re.compile(r"if\s*\([^)]*(?:<=|>=|<|>)\s*(?:\d+|MAX_|MIN_).*?\)\s*revert", re.IGNORECASE),
        re.compile(r"require\s*\([^)]*(?:<=|>=)\s*\d+", re.IGNORECASE),
    ]

    def detect(
        self, contract: ParsedContract, all_contracts: List[ParsedContract]
    ) -> List[Finding]:
        findings = []

        if contract.contract_type in ("interface", "library"):
            return findings

        for fname, func in contract.functions.items():
            if func.mutability in ("view", "pure"):
                continue
            if func.visibility not in ("public", "external"):
                continue
            body = func.raw_body or ""
            if not body:
                continue

            # هل البارامترات تحتوي على أسماء حرجة؟
            critical_params = []
            for param in (func.parameters or []):
                if isinstance(param, dict):
                    param_str = param.get("name", "") or ""
                else:
                    param_str = str(param)
                    parts = param_str.strip().split()
                    param_str = parts[-1] if parts else param_str
                if self._CRITICAL_PARAMS.search(param_str):
                    critical_params.append(param_str)

            if not critical_params:
                continue

            # هل يوجد فحص حدود؟
            has_bounds = any(p.search(body) for p in self._BOUNDS_CHECK)
            if has_bounds:
                continue

            # هل الدالة تكتب في state؟
            if not func.state_writes:
                continue

            findings.append(
                self._make_finding(
                    contract,
                    func,
                    f"Function `{fname}` accepts critical parameter(s) "
                    f"({', '.join(critical_params)}) and writes to state without "
                    f"bounds validation. A privileged caller (or attacker if unprotected) "
                    f"could set extreme values. Add upper/lower bound checks.",
                    line=func.line_start,
                    extra={"critical_params": critical_params},
                )
            )

        return findings
