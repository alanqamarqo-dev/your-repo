"""
AGL Advanced Attacks Detectors — كاشفات الهجمات المتقدمة
2 detectors for sophisticated attack patterns:

1. RETURN-BOMB — Unbounded returndata copy from external call
2. GOVERNANCE-FLASH — Flash loan + governance vote in same transaction
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


class ReturnBomb(BaseDetector):
    """
    قنبلة البيانات المرجعة — نسخ بيانات مرجعة بحجم غير محدود.

    Pattern:
        (bool success, bytes memory data) = target.call(payload);
        // ✗ إذا target أرجع 100KB+ بيانات → gas يُستنزف في النسخ

    Safe:
        (bool success, ) = target.call(payload);  // ✓ تجاهل returndata
        // أو:
        assembly { success := call(gas(), target, 0, ..., 0, 0) }  // ✓ لا نسخ

    Detection: .call() where returndata is captured as bytes memory
    without size limiting.

    Real-world: Gelato resolver gas griefing, multicall patterns
    """

    DETECTOR_ID = "RETURN-BOMB"
    TITLE = "Returndata bomb (unbounded external return copy)"
    SEVERITY = Severity.MEDIUM
    CONFIDENCE = Confidence.MEDIUM

    # .call() مع نسخ bytes memory
    _RETURN_CAPTURE = re.compile(
        r"\(\s*bool\s+\w+\s*,\s*bytes\s+memory\s+\w+\s*\)\s*=\s*\w+\.call",
        re.IGNORECASE,
    )

    # أنماط آمنة
    _SAFE_PATTERNS = [
        # تجاهل returndata
        re.compile(r"\(\s*bool\s+\w+\s*,\s*\)\s*=", re.IGNORECASE),
        # Assembly call بدون returndatacopy
        re.compile(r"assembly\s*\{[^}]*call\s*\(", re.IGNORECASE),
        # ExcessivelySafeCall library
        re.compile(r"excessivelySafeCall|safecall|_maxReturnBytes", re.IGNORECASE),
        # returndatasize check
        re.compile(r"returndatasize\s*\(\s*\)\s*(?:<|<=|>)", re.IGNORECASE),
    ]

    def detect(
        self, contract: ParsedContract, all_contracts: List[ParsedContract]
    ) -> List[Finding]:
        findings = []

        if contract.contract_type in ("interface", "library"):
            return findings

        for fname, func in contract.functions.items():
            body = func.raw_body or ""
            if not body:
                continue

            # هل تلتقط returndata كـ bytes memory؟
            if not self._RETURN_CAPTURE.search(body):
                continue

            # هل محمية؟
            has_protection = any(p.search(body) for p in self._SAFE_PATTERNS)
            if has_protection:
                continue

            # هل الاستدعاء لعنوان يتحكم فيه المستخدم (أخطر)؟
            has_user_target = any(
                param_name in body
                for param in (func.parameters or [])
                for param_name in [param.strip().split()[-1]]
                if "address" in param.lower()
            )

            findings.append(
                self._make_finding(
                    contract,
                    func,
                    f"Function `{fname}` captures returndata as `bytes memory` from "
                    f"an external `.call()`. A malicious callee can return an "
                    f"arbitrarily large payload, causing the caller to spend "
                    f"excessive gas on memory expansion and `returndatacopy`. "
                    f"Either ignore the returndata `(bool ok, ) = target.call(...)` "
                    f"or use assembly to limit the copied size.",
                    line=func.line_start,
                    confidence=Confidence.HIGH if has_user_target else Confidence.MEDIUM,
                    extra={"user_controlled_target": has_user_target},
                )
            )

        return findings


class GovernanceFlashLoan(BaseDetector):
    """
    قرض فوري + تصويت حوكمة — نمط هجوم الحوكمة.

    Pattern: عقد حوكمة يسمح بالتصويت بناءً على الرصيد الحالي
    بدون snapshot أو timelock.

    Detection: Vote/propose functions that read balanceOf without
    snapshot, or allow vote + delegate in same block.

    Real-world: Beanstalk ($182M), Build Finance, Tornado Cash governance
    """

    DETECTOR_ID = "GOVERNANCE-FLASH"
    TITLE = "Flash loan governance attack vector"
    SEVERITY = Severity.HIGH
    CONFIDENCE = Confidence.LOW

    _GOVERNANCE_PATTERNS = [
        re.compile(r"function\s+(?:vote|castVote|propose|delegate)\s*\(", re.IGNORECASE),
        re.compile(r"votingPower|getVotes|quorum|ballot", re.IGNORECASE),
    ]

    _BALANCE_READ_IN_VOTE = [
        re.compile(r"balanceOf\s*\(\s*msg\.sender\s*\)", re.IGNORECASE),
        re.compile(r"balanceOf\s*\(\s*voter\s*\)", re.IGNORECASE),
        # القراءة المباشرة من mapping
        re.compile(r"_balances\s*\[\s*msg\.sender\s*\]", re.IGNORECASE),
    ]

    _SAFE_PATTERNS = [
        # Snapshot-based voting
        re.compile(r"snapshot|getPastVotes|getPriorVotes|checkpoints", re.IGNORECASE),
        # Timelock protection
        re.compile(r"timelock|TimelockController|delay|lockDuration", re.IGNORECASE),
        # Block-based restriction
        re.compile(r"block\.number\s*(?:-|>)\s*\w*(?:start|created|proposal)", re.IGNORECASE),
        # ERC20Votes (OpenZeppelin) — already has snapshots
        re.compile(r"ERC20Votes|GovernorVotes|GovernorCountingSimple", re.IGNORECASE),
    ]

    def detect(
        self, contract: ParsedContract, all_contracts: List[ParsedContract]
    ) -> List[Finding]:
        findings = []

        if contract.contract_type in ("interface", "library"):
            return findings

        # هل هذا عقد حوكمة؟ — نفحص أسماء الدوال + الأجسام
        full_source = ""
        func_names = " ".join(contract.functions.keys())
        for func in contract.functions.values():
            full_source += (func.raw_body or "") + "\n"

        # Check both function names and bodies for governance patterns
        is_governance = any(
            p.search(full_source) or p.search(func_names)
            for p in self._GOVERNANCE_PATTERNS
        )
        # Also check if any function name matches governance keywords directly
        if not is_governance:
            is_governance = bool(re.search(
                r"vote|castVote|propose|delegate|governance|ballot",
                func_names, re.IGNORECASE
            ))
        if not is_governance:
            return findings

        # هل محمي بـ snapshot أو timelock؟
        has_protection = any(p.search(full_source) for p in self._SAFE_PATTERNS)
        if has_protection:
            return findings

        for fname, func in contract.functions.items():
            body = func.raw_body or ""

            # هل هذه دالة تصويت تقرأ الرصيد الحالي؟
            is_vote_func = re.search(
                r"vote|castVote|propose|delegate", fname, re.IGNORECASE
            )
            if not is_vote_func:
                continue

            reads_current_balance = any(
                p.search(body) for p in self._BALANCE_READ_IN_VOTE
            )
            if not reads_current_balance:
                continue

            findings.append(
                self._make_finding(
                    contract,
                    func,
                    f"Function `{fname}` reads the current token balance for voting "
                    f"power without using snapshots or checkpoints. An attacker can "
                    f"take a flash loan to temporarily inflate their balance, vote, "
                    f"then repay — all in one transaction. Use ERC20Votes "
                    f"`getPastVotes(account, blockNumber)` or implement a snapshot "
                    f"mechanism.",
                    line=func.line_start,
                    extra={"pattern": "current_balance_vote"},
                )
            )

        return findings
