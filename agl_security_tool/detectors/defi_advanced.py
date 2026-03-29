"""
AGL DeFi Advanced Detectors — كاشفات DeFi المتقدمة
3 detectors for advanced DeFi vulnerabilities:

1. MISSING-SLIPPAGE — Swap/AMM without minimum output protection
2. MISSING-DEADLINE — Swap/AMM without deadline parameter
3. SANDWICH-VULNERABLE — Transaction ordering dependency in DeFi operations
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


class MissingSlippageProtection(BaseDetector):
    """
    حماية الانزلاق السعري مفقودة — عمليات التبادل بدون حد أدنى للمخرجات.

    Pattern:
        router.swapExactTokensForTokens(amountIn, 0, path, to, deadline);
        // ✗ amountOutMin = 0 → sandwich attack ممكن

    Safe:
        router.swapExactTokensForTokens(amountIn, minOut, path, to, deadline);
        // ✓ minOut > 0

    Detection: Find swap/exchange calls where amountOutMin is literal 0 or
    where no minimum output parameter is validated.

    Real-world: Uniswap, SushiSwap, PancakeSwap integrations
    """

    DETECTOR_ID = "MISSING-SLIPPAGE"
    TITLE = "Missing slippage protection in swap"
    SEVERITY = Severity.HIGH
    CONFIDENCE = Confidence.HIGH

    # اسماء دوال التبادل المعروفة
    _SWAP_PATTERNS = [
        re.compile(r"swap(?:Exact)?(?:Tokens|ETH|Ether)(?:For)?(?:Tokens|ETH|Ether)?", re.IGNORECASE),
        re.compile(r"exchange|removeLiquidity|addLiquidity", re.IGNORECASE),
    ]

    # نمط amountOutMin = 0 أو الحد الأدنى = 0
    _ZERO_MIN_PATTERNS = [
        # swapExact...(amount, 0, ...)
        re.compile(r"swap\w*\([^)]*,\s*0\s*,", re.IGNORECASE),
        # removeLiquidity...(... , 0, 0, ...)
        re.compile(r"removeLiquidity\w*\([^)]*,\s*0\s*,\s*0\s*,", re.IGNORECASE),
        # amountOutMin = 0 or minAmountOut = 0
        re.compile(r"(?:amount\s*Out\s*Min|min\s*(?:Amount\s*)?Out|minOutput)\s*(?:=|:)\s*0\b", re.IGNORECASE),
    ]

    # أنماط الحماية — تُسقط الكشف
    _PROTECTION_PATTERNS = [
        # require(amountOut >= minOut)
        re.compile(r"require\s*\(.*?(?:amount|output|received).*?>=.*?(?:min|slippage)", re.IGNORECASE),
        # slippage tolerance calculation
        re.compile(r"slippage(?:Tolerance|Protection|Check|Guard)", re.IGNORECASE),
        # OracleSlippageGuard pattern
        re.compile(r"(?:oracle|twap|chainlink).*?(?:min|floor|bound)", re.IGNORECASE),
        # require minAmountOut > 0
        re.compile(r"require\s*\(.*?min\w*\s*>\s*0", re.IGNORECASE),
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
            body = func.raw_body or ""
            if not body:
                continue

            # هل الدالة تحتوي على عملية تبادل؟
            has_swap = any(p.search(body) for p in self._SWAP_PATTERNS)
            if not has_swap:
                continue

            # هل يوجد حماية من الانزلاق؟
            has_protection = any(p.search(body) for p in self._PROTECTION_PATTERNS)
            if has_protection:
                continue

            # هل الحد الأدنى = 0 صراحة؟
            has_zero_min = any(p.search(body) for p in self._ZERO_MIN_PATTERNS)

            # أو لا يوجد أي ذكر لـ min/slippage في البارامترات
            has_min_param = re.search(
                r"(?:min|slippage|deadline)", body, re.IGNORECASE
            )

            if has_zero_min:
                # تأكيد عالي — 0 صريح
                findings.append(
                    self._make_finding(
                        contract,
                        func,
                        f"Function `{fname}` performs a swap with `amountOutMin = 0`. "
                        f"This allows sandwich attacks where a frontrunner can manipulate "
                        f"the price before the transaction executes. "
                        f"Always calculate a reasonable minimum output based on oracle "
                        f"price or allow the user to specify slippage tolerance.",
                        line=func.line_start,
                        extra={"pattern": "zero_min_output"},
                    )
                )
            elif not has_min_param:
                # الدالة تبادل بدون أي ذكر للحد الأدنى
                findings.append(
                    self._make_finding(
                        contract,
                        func,
                        f"Function `{fname}` performs a swap without any slippage "
                        f"protection parameter. There is no `amountOutMin`, "
                        f"`minOutput`, or slippage check. Swaps without minimum "
                        f"output protection are vulnerable to sandwich attacks.",
                        line=func.line_start,
                        confidence=Confidence.MEDIUM,
                        extra={"pattern": "no_min_parameter"},
                    )
                )

        return findings


class MissingDeadline(BaseDetector):
    """
    مهلة زمنية مفقودة — عمليات AMM/DEX بدون deadline.

    Pattern:
        router.swapExactTokensForTokens(amountIn, minOut, path, to, block.timestamp);
        // ✗ block.timestamp كـ deadline يعني لا حماية — المعاملة تنفذ دائماً

    Safe:
        router.swapExactTokensForTokens(amountIn, minOut, path, to, deadline);
        // ✓ deadline من المستخدم

    Real-world: Uniswap V2 router, أي مشروع يتكامل مع AMM
    """

    DETECTOR_ID = "MISSING-DEADLINE"
    TITLE = "Missing or ineffective deadline in DEX interaction"
    SEVERITY = Severity.MEDIUM
    CONFIDENCE = Confidence.MEDIUM

    _SWAP_CALL_PATTERN = re.compile(
        r"(?:swap|addLiquidity|removeLiquidity)\w*\s*\(", re.IGNORECASE
    )

    # deadline = block.timestamp يعني عدم الحماية
    _INEFFECTIVE_DEADLINE = [
        re.compile(r"block\.timestamp\s*\)", re.IGNORECASE),
        re.compile(r"deadline\s*(?:=|:)\s*block\.timestamp", re.IGNORECASE),
        re.compile(r"type\s*\(\s*uint(?:256)?\s*\)\s*\.max", re.IGNORECASE),
    ]

    _PROTECTION_PATTERNS = [
        # require(deadline >= block.timestamp)
        re.compile(r"require\s*\(.*?deadline.*?(?:>=|>).*?block\.timestamp", re.IGNORECASE),
        # deadline parameter used properly
        re.compile(r"(?:deadline|expiry|expiration)\s+deadline", re.IGNORECASE),
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
            body = func.raw_body or ""
            if not body:
                continue

            # هل الدالة تستدعي swap/AMM؟
            if not self._SWAP_CALL_PATTERN.search(body):
                continue

            # هل يوجد حماية deadline صحيحة؟
            has_protection = any(p.search(body) for p in self._PROTECTION_PATTERNS)
            if has_protection:
                continue

            # هل يستخدم block.timestamp كـ deadline (غير فعّال)؟
            has_ineffective = any(p.search(body) for p in self._INEFFECTIVE_DEADLINE)

            if has_ineffective:
                findings.append(
                    self._make_finding(
                        contract,
                        func,
                        f"Function `{fname}` uses `block.timestamp` or `type(uint).max` "
                        f"as the deadline for a DEX interaction. This provides no protection — "
                        f"the transaction can be held by a validator and executed at "
                        f"any later time when the price is unfavorable. "
                        f"Accept a user-provided deadline parameter.",
                        line=func.line_start,
                        extra={"pattern": "ineffective_deadline"},
                    )
                )

        return findings


class SandwichVulnerable(BaseDetector):
    """
    هجوم ساندويتش — عمليات حساسة لترتيب المعاملات.

    Pattern: وظيفة تقرأ سعراً أو رصيداً ثم تنفذ عملية بناءً عليه
    بدون حماية من تغيير الحالة بين القراءة والتنفيذ.

    Detection: Functions that read balanceOf/getReserves then perform
    external calls (swaps/transfers) without access control or commit-reveal.

    Real-world: DEX aggregators, yield strategies, arbitrage bots
    """

    DETECTOR_ID = "SANDWICH-VULNERABLE"
    TITLE = "Transaction ordering dependency (sandwich attack vector)"
    SEVERITY = Severity.MEDIUM
    CONFIDENCE = Confidence.LOW

    _PRICE_READ_PATTERNS = [
        re.compile(r"(?:balanceOf|getReserves|getAmountOut|latestAnswer|slot0|observe)\s*\(", re.IGNORECASE),
        re.compile(r"price|rate|quote|oracle", re.IGNORECASE),
    ]

    _ACTION_AFTER_READ = [
        re.compile(r"\.(?:swap|transfer|send|call)\s*[\({]", re.IGNORECASE),
    ]

    _PROTECTION_PATTERNS = [
        re.compile(r"onlyOwner|onlyKeeper|onlyRelayer|onlyAuthorized", re.IGNORECASE),
        re.compile(r"commit.*?reveal|flashbots|private\s*pool", re.IGNORECASE),
        re.compile(r"require.*?msg\.sender\s*==", re.IGNORECASE),
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

            # هل تقرأ سعراً أو رصيداً؟
            has_price_read = any(p.search(body) for p in self._PRICE_READ_PATTERNS)
            if not has_price_read:
                continue

            # هل تنفذ عملية بعد القراءة؟
            has_action = any(p.search(body) for p in self._ACTION_AFTER_READ)
            if not has_action:
                continue

            # هل محمية؟
            has_protection = any(p.search(body) for p in self._PROTECTION_PATTERNS)
            if has_protection:
                continue
            if func.has_access_control:
                continue

            findings.append(
                self._make_finding(
                    contract,
                    func,
                    f"Function `{fname}` reads on-chain price/balance data and then "
                    f"performs an external call in the same transaction without commit-reveal "
                    f"or access restrictions. This pattern is vulnerable to sandwich attacks "
                    f"where an attacker can frontrun the transaction to manipulate the "
                    f"price/state before it executes.",
                    line=func.line_start,
                    extra={"pattern": "read_then_act_public"},
                )
            )

        return findings
