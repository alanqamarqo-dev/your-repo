"""
AGL DeFi Business Logic Detectors — كاشفات منطق الأعمال في DeFi
5 detectors for DeFi-specific vulnerabilities:

1. FIRST-DEPOSITOR — Vault share inflation attack (ERC4626)
2. ORACLE-MANIPULATION — Single-block price oracle without TWAP
3. PRICE-STALE-CHECK — Oracle data without freshness validation
4. DIVIDE-BEFORE-MULTIPLY — Precision loss from wrong math order
5. FLASH-LOAN-CALLBACK — Missing validation in flash loan callbacks
"""

from typing import List, Set
import re
from . import (
    BaseDetector, Finding, Severity, Confidence,
    ParsedContract, ParsedFunction, OpType
)


class FirstDepositorAttack(BaseDetector):
    """
    هجوم المودع الأول — تضخم أسهم الـ Vault.

    Pattern (ERC4626 or similar):
        shares = (amount * totalSupply) / totalAssets
        When totalSupply == 0, attacker can:
        1. Deposit 1 wei → get 1 share
        2. "Donate" large amount directly → inflate totalAssets
        3. Next depositor gets 0 shares due to rounding

    Detection: Find deposit/mint functions that calculate shares from
    totalSupply/totalAssets ratio without minimum deposit protection.

    Real-world: Multiple ERC4626 vaults, Yearn, many protocols
    """

    DETECTOR_ID = "FIRST-DEPOSITOR"
    TITLE = "First depositor / share inflation attack in vault"
    SEVERITY = Severity.HIGH
    CONFIDENCE = Confidence.MEDIUM

    _DEPOSIT_NAMES = {
        'deposit', 'mint', 'stake', 'supply', 'addLiquidity',
        'provide', 'join', 'enter', 'invest',
    }

    _SHARE_PATTERNS = [
        # shares = amount * totalSupply / totalAssets
        re.compile(r'totalSupply.*?/.*?total(?:Assets|Balance)', re.IGNORECASE),
        re.compile(r'total(?:Assets|Balance).*?/.*?totalSupply', re.IGNORECASE),
        # mulDiv / mulDown / mulUp patterns
        re.compile(r'mul(?:Div|Down|Up)\s*\(.*?totalSupply', re.IGNORECASE),
        # Direct totalSupply == 0 check (vault pattern)
        re.compile(r'totalSupply\s*\(\s*\)\s*==\s*0', re.IGNORECASE),
    ]

    _PROTECTION_PATTERNS = [
        # Minimum deposit requirement
        re.compile(r'require.*?>=\s*\d{2,}|MIN_DEPOSIT|MINIMUM', re.IGNORECASE),
        # Dead shares / virtual offset (OpenZeppelin mitigation)
        re.compile(r'_decimalsOffset|virtualAssets|virtualShares|DEAD_SHARES', re.IGNORECASE),
        # Internal balance check
        re.compile(r'_initialDeposit|_mintDeadShares|_bootstrap', re.IGNORECASE),
    ]

    def detect(self, contract: ParsedContract, all_contracts: List[ParsedContract]) -> List[Finding]:
        findings = []

        for fname, func in contract.functions.items():
            # هل هذه دالة إيداع؟
            is_deposit = fname.lower() in {n.lower() for n in self._DEPOSIT_NAMES}
            if not is_deposit:
                continue

            body = func.raw_body or ""

            # هل تحسب الأسهم من النسبة؟
            has_share_calc = any(p.search(body) for p in self._SHARE_PATTERNS)
            if not has_share_calc:
                continue

            # هل هناك حماية؟
            has_protection = any(p.search(body) for p in self._PROTECTION_PATTERNS)
            if has_protection:
                continue

            # أيضاً تحقق من العقد بأكمله
            all_source = "".join(f.raw_body or "" for f in contract.functions.values())
            has_global_protection = any(p.search(all_source) for p in self._PROTECTION_PATTERNS)
            if has_global_protection:
                continue

            findings.append(self._make_finding(
                contract, func,
                f"Vault function `{fname}` calculates shares from totalSupply/totalAssets "
                f"ratio without first-depositor protection. An attacker can: "
                f"(1) deposit 1 wei to become first depositor, "
                f"(2) directly transfer tokens to inflate totalAssets, "
                f"(3) subsequent depositors get 0 shares due to rounding. "
                f"Mitigate with: minimum deposit amount, virtual offset "
                f"(OpenZeppelin ERC4626 with _decimalsOffset), or dead shares.",
                line=func.line_start,
                extra={
                    "function": fname,
                    "pattern": "share inflation / first depositor",
                    "mitigation": "virtual_offset or minimum_deposit",
                }
            ))

        return findings


class OracleManipulation(BaseDetector):
    """
    تلاعب بالأوراكل — استخدام سعر فوري بدون TWAP.

    Pattern:
        price = pool.slot0()           // سعر فوري — قابل للتلاعب في نفس البلوك
        // بدل:
        price = pool.observe(...)      // TWAP — مقاوم للتلاعب

    Detection: Find calls to getReserves/slot0/latestAnswer without
    TWAP or time-weighted averaging.

    Real-world: Most flash loan attacks, Harvest Finance, many AMMs
    """

    DETECTOR_ID = "ORACLE-MANIPULATION"
    TITLE = "Potential oracle price manipulation"
    SEVERITY = Severity.HIGH
    CONFIDENCE = Confidence.MEDIUM

    _SPOT_PRICE_PATTERNS = [
        # Uniswap V2 reserves
        re.compile(r'getReserves\s*\('),
        # Uniswap V3 slot0 (instantaneous price)
        re.compile(r'\.slot0\s*\('),
        # Direct balance oracle
        re.compile(r'balanceOf\s*\([^)]*\)\s*/\s*(?:balanceOf|totalSupply)'),
        # token0.balanceOf(pool) / token1.balanceOf(pool)
        re.compile(r'balance(?:Of)?\s*\(.*?(?:pair|pool|reserve)', re.IGNORECASE),
    ]

    _TWAP_PROTECTION = [
        re.compile(r'observe\s*\('),      # Uniswap V3 TWAP
        re.compile(r'consult\s*\('),      # TWAP oracle
        re.compile(r'twap|TWAP', re.IGNORECASE),
        re.compile(r'time[_-]?weighted', re.IGNORECASE),
        re.compile(r'getPrice.*?period', re.IGNORECASE),
        re.compile(r'cumulativePrice'),
    ]

    def detect(self, contract: ParsedContract, all_contracts: List[ParsedContract]) -> List[Finding]:
        findings = []

        all_source = "".join(
            (f.raw_body or "") for f in contract.functions.values()
        )

        # هل يستخدم العقد TWAP؟
        uses_twap = any(p.search(all_source) for p in self._TWAP_PROTECTION)

        for fname, func in contract.functions.items():
            body = func.raw_body or ""

            for pattern in self._SPOT_PRICE_PATTERNS:
                match = pattern.search(body)
                if match:
                    if uses_twap:
                        continue  # العقد يستخدم TWAP بالفعل

                    spot_call = match.group(0)
                    findings.append(self._make_finding(
                        contract, func,
                        f"Function `{fname}` uses spot price data (`{spot_call}`) "
                        f"which can be manipulated within a single transaction via "
                        f"flash loans. An attacker can: "
                        f"(1) borrow large amount via flash loan, "
                        f"(2) manipulate pool price, "
                        f"(3) interact with your contract at the manipulated price, "
                        f"(4) restore price and profit. "
                        f"Use TWAP (time-weighted average) or Chainlink oracles.",
                        line=func.line_start,
                        extra={
                            "spot_call": spot_call,
                            "mitigation": "TWAP or Chainlink",
                        }
                    ))
                    break  # واحد لكل دالة

        return findings


class PriceStaleCheck(BaseDetector):
    """
    فحص انتهاء صلاحية السعر — بيانات أوراكل بدون فحص الحداثة.

    Pattern (Chainlink):
        (, int256 price, , ,) = priceFeed.latestRoundData();
        // لا يوجد فحص updatedAt أو answeredInRound!

    Detection: latestRoundData() call without checking updatedAt/answeredInRound.

    Real-world: Many protocols lost funds using stale prices
    """

    DETECTOR_ID = "PRICE-STALE-CHECK"
    TITLE = "Missing price freshness check (stale oracle data)"
    SEVERITY = Severity.MEDIUM
    CONFIDENCE = Confidence.HIGH

    def detect(self, contract: ParsedContract, all_contracts: List[ParsedContract]) -> List[Finding]:
        findings = []

        for fname, func in contract.functions.items():
            body = func.raw_body or ""

            # هل يستدعي latestRoundData?
            if 'latestRoundData' not in body:
                continue

            # هل يفحص حداثة البيانات؟
            has_staleness_check = bool(
                re.search(r'updatedAt.*?block\.timestamp|block\.timestamp.*?updatedAt', body) or
                re.search(r'answeredInRound.*?roundId|roundId.*?answeredInRound', body) or
                re.search(r'stalePeriod|MAX_DELAY|HEARTBEAT|priceTimeout', body, re.IGNORECASE) or
                re.search(r'require.*?updatedAt|require.*?answeredIn', body)
            )

            # هل يفحص أن السعر > 0?
            has_price_check = bool(
                re.search(r'require.*?price\s*>|price\s*>\s*0|answer\s*>', body)
            )

            issues = []
            if not has_staleness_check:
                issues.append("no staleness check (updatedAt not verified)")
            if not has_price_check:
                issues.append("price not validated > 0")

            if issues:
                findings.append(self._make_finding(
                    contract, func,
                    f"Function `{fname}` uses Chainlink `latestRoundData()` but: "
                    f"{'; '.join(issues)}. "
                    f"Stale or zero prices can cause incorrect valuations, "
                    f"leading to under-collateralized loans or incorrect swaps. "
                    f"Add: `require(updatedAt > block.timestamp - MAX_DELAY)` and "
                    f"`require(price > 0)`.",
                    line=func.line_start,
                    extra={
                        "issues": issues,
                        "has_staleness_check": has_staleness_check,
                        "has_price_check": has_price_check,
                    }
                ))

        return findings


class DivideBeforeMultiply(BaseDetector):
    """
    القسمة قبل الضرب — فقدان الدقة في الحسابات.

    Pattern:
        result = a / b * c    // ✗ فقدان الدقة — a/b يُقرّب أولاً
        result = a * c / b    // ✓ دقة أفضل

    Example: 
        a=7, b=3, c=10
        7/3*10 = 2*10 = 20  (wrong — truncation at 7/3)
        7*10/3 = 70/3 = 23  (correct)

    Detection: Find expression patterns like var/X * Y or (expr/X) * Y

    Real-world: Common in yield calculations, fee computations
    """

    DETECTOR_ID = "DIVIDE-BEFORE-MULTIPLY"
    TITLE = "Precision loss: divide before multiply"
    SEVERITY = Severity.MEDIUM
    CONFIDENCE = Confidence.MEDIUM

    _PATTERNS = [
        # Direct: a / b * c
        re.compile(r'(\w+)\s*/\s*(\w+)\s*\*\s*(\w+)'),
        # Parenthesized: (a / b) * c
        re.compile(r'\([^)]*?/[^)]*?\)\s*\*'),
        # Assignment: result = expr / X; ... result * Y
    ]

    _SAFE_PATTERNS = [
        # mulDiv is intentional
        re.compile(r'mulDiv|FullMath|PRBMath', re.IGNORECASE),
        # Constant denominators that are powers of 2 or known precision
        re.compile(r'/\s*(?:1e\d+|10\*\*\d+|WAD|RAY|PRECISION|SCALE|BPS|1000+)'),
    ]

    def detect(self, contract: ParsedContract, all_contracts: List[ParsedContract]) -> List[Finding]:
        findings = []

        for fname, func in contract.functions.items():
            body = func.raw_body or ""
            lines = body.splitlines()

            for i, line in enumerate(lines):
                stripped = line.strip()

                # تخطي التعليقات
                if stripped.startswith('//') or stripped.startswith('*'):
                    continue

                for pattern in self._PATTERNS:
                    match = pattern.search(stripped)
                    if match:
                        # هل هذا آمن (mulDiv, ثابت معروف)؟
                        if any(sp.search(stripped) for sp in self._SAFE_PATTERNS):
                            continue

                        # هل في سياق require/assert (وليس حساب)؟
                        if stripped.strip().startswith(('require', 'assert')):
                            continue

                        findings.append(self._make_finding(
                            contract, func,
                            f"Function `{fname}` has division before multiplication: "
                            f"`{match.group(0).strip()}`. In Solidity, integer division "
                            f"truncates, so `a/b*c` loses precision. Reorder to `a*c/b` "
                            f"or use `mulDiv()` for safe fixed-point arithmetic.",
                            line=func.line_start + i,
                            extra={
                                "expression": match.group(0).strip(),
                                "fix": "Reorder to multiply before divide, or use mulDiv()",
                            }
                        ))
                        break  # واحد لكل سطر

        return findings


class FlashLoanCallbackValidation(BaseDetector):
    """
    استدعاء flash loan بدون التحقق من المُرسل.

    Pattern:
        function executeOperation(
            address[] assets, uint256[] amounts, uint256[] premiums, address initiator, bytes params
        ) external returns (bool) {
            // ✗ لا يوجد: require(msg.sender == POOL)
            // ✗ لا يوجد: require(initiator == address(this))
        }

    Detection: Flash loan callback without msg.sender or initiator validation.

    Real-world: Callbacks exploited to drain protocols
    """

    DETECTOR_ID = "FLASH-LOAN-CALLBACK"
    TITLE = "Flash loan callback without sender validation"
    SEVERITY = Severity.HIGH
    CONFIDENCE = Confidence.MEDIUM

    _CALLBACK_NAMES = {
        'executeOperation',     # Aave V2/V3
        'onFlashLoan',          # ERC3156
        'flashLoanCallback',    # Custom
        'uniswapV2Call',        # Uniswap V2
        'uniswapV3FlashCallback',  # Uniswap V3
        'pancakeCall',          # PancakeSwap
        'callFunction',         # dYdX
        'onDydxFlashLoan',      # dYdX
        'receiveFlashLoan',     # Balancer
    }

    def detect(self, contract: ParsedContract, all_contracts: List[ParsedContract]) -> List[Finding]:
        findings = []

        for fname, func in contract.functions.items():
            if fname not in self._CALLBACK_NAMES:
                continue
            if func.visibility not in ('public', 'external'):
                continue

            body = func.raw_body or ""
            checks = func.require_checks

            # هل يتحقق من msg.sender؟
            checks_sender = any(
                'msg.sender' in check for check in checks
            ) or bool(re.search(r'require\s*\(.*?msg\.sender', body))

            # هل يتحقق من initiator/sender parameter؟
            checks_initiator = any(
                'initiator' in check or 'sender' in check
                for check in checks
            ) or bool(re.search(r'require\s*\(.*?initiator', body))

            if not checks_sender and not checks_initiator:
                findings.append(self._make_finding(
                    contract, func,
                    f"Flash loan callback `{fname}` does not validate `msg.sender` "
                    f"(should be the lending pool) or `initiator` (should be this contract). "
                    f"An attacker can call this function directly, bypassing the flash loan "
                    f"mechanism to execute arbitrary operations. Add: "
                    f"`require(msg.sender == address(POOL))` and "
                    f"`require(initiator == address(this))`.",
                    line=func.line_start,
                    extra={
                        "callback": fname,
                        "checks_sender": checks_sender,
                        "checks_initiator": checks_initiator,
                    }
                ))

        return findings
