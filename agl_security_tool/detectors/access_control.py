"""
AGL Access Control Detectors — كاشفات التحكم بالوصول
4 detectors for missing or broken access control:

1. UNPROTECTED-WITHDRAW — ETH/token withdrawal without access control
2. UNPROTECTED-SELFDESTRUCT — selfdestruct without access control
3. TX-ORIGIN-AUTH — tx.origin used for authentication
4. DANGEROUS-DELEGATECALL — delegatecall to user-controlled address
"""

from typing import List
import re
from . import (
    BaseDetector, Finding, Severity, Confidence,
    ParsedContract, ParsedFunction, OpType
)


class UnprotectedWithdraw(BaseDetector):
    """
    سحب غير محمي — دالة تسحب ETH أو tokens بدون فحص الصلاحية.

    Pattern:
        function withdraw() public {
            msg.sender.transfer(address(this).balance);  // لا يوجد require أو modifier
        }

    Checks: No onlyOwner, no require(msg.sender == owner), no access role
    """

    DETECTOR_ID = "UNPROTECTED-WITHDRAW"
    TITLE = "Unprotected withdrawal function"
    SEVERITY = Severity.CRITICAL
    CONFIDENCE = Confidence.HIGH

    # أسماء الدوال المتعلقة بالسحب
    _WITHDRAW_NAMES = {
        'withdraw', 'withdrawAll', 'withdrawETH', 'withdrawToken',
        'withdrawTokens', 'withdrawFunds', 'emergencyWithdraw',
        'drain', 'sweep', 'rugPull', 'collect', 'claim',
        'withdrawBalance', 'withdrawEther', 'withdrawTo',
    }

    def detect(self, contract: ParsedContract, all_contracts: List[ParsedContract]) -> List[Finding]:
        findings = []

        for fname, func in contract.functions.items():
            if func.visibility not in ('public', 'external'):
                continue
            if func.has_access_control:
                continue

            # هل اسم الدالة يدل على سحب؟
            is_withdraw_name = fname.lower() in {n.lower() for n in self._WITHDRAW_NAMES}

            # هل الدالة ترسل ETH أو tokens؟
            sends_value = func.sends_eth or any(
                op.op_type == OpType.EXTERNAL_CALL and op.details in
                ('transfer', 'safeTransfer', 'safeTransferFrom')
                for op in func.operations
            )

            if not sends_value:
                continue

            # تخطي constructor
            if func.is_constructor:
                continue

            confidence = Confidence.HIGH if is_withdraw_name else Confidence.MEDIUM

            findings.append(self._make_finding(
                contract, func,
                f"Function `{fname}` transfers value (ETH or tokens) without "
                f"access control. Any address can call this function to drain funds. "
                f"Add `onlyOwner` modifier or `require(msg.sender == owner)` check.",
                line=func.line_start,
                confidence=confidence,
                extra={
                    "sends_eth": func.sends_eth,
                    "visibility": func.visibility,
                    "has_any_modifier": len(func.modifiers) > 0,
                }
            ))

        return findings


class UnprotectedSelfDestruct(BaseDetector):
    """
    selfdestruct بدون حماية — يمكن لأي شخص تدمير العقد.

    Real-world: Parity Wallet hack ($30M+)
    """

    DETECTOR_ID = "UNPROTECTED-SELFDESTRUCT"
    TITLE = "Unprotected selfdestruct"
    SEVERITY = Severity.CRITICAL
    CONFIDENCE = Confidence.HIGH

    def detect(self, contract: ParsedContract, all_contracts: List[ParsedContract]) -> List[Finding]:
        findings = []

        for fname, func in contract.functions.items():
            if not func.has_selfdestruct:
                continue
            if func.visibility not in ('public', 'external'):
                continue
            if func.has_access_control:
                continue

            findings.append(self._make_finding(
                contract, func,
                f"Function `{fname}` contains `selfdestruct` without access control. "
                f"Anyone can destroy the contract and steal remaining ETH. "
                f"Add strict access control or remove selfdestruct.",
                line=func.line_start,
                extra={"visibility": func.visibility}
            ))

        return findings


class TxOriginAuth(BaseDetector):
    """
    استخدام tx.origin للمصادقة — ثغرة phishing.

    Pattern:
        require(tx.origin == owner)  // ✗ يمكن خداعه
        require(msg.sender == owner) // ✓ آمن

    tx.origin = المرسل الأصلي للمعاملة (EOA)
    msg.sender = المتصل المباشر (قد يكون عقد وسيط)

    Attack: المهاجم يخدع المالك لاستدعاء عقده الخبيث، ثم يستدعي العقد الهدف.
    """

    DETECTOR_ID = "TX-ORIGIN-AUTH"
    TITLE = "Authentication via tx.origin"
    SEVERITY = Severity.HIGH
    CONFIDENCE = Confidence.HIGH

    def detect(self, contract: ParsedContract, all_contracts: List[ParsedContract]) -> List[Finding]:
        findings = []

        for fname, func in contract.functions.items():
            for op in func.operations:
                if op.op_type == OpType.REQUIRE and op.target:
                    if 'tx.origin' in op.target:
                        # تحقق: هل يستخدم tx.origin للمقارنة (مصادقة)
                        if re.search(r'tx\.origin\s*==|==\s*tx\.origin', op.target):
                            findings.append(self._make_finding(
                                contract, func,
                                f"Function `{fname}` uses `tx.origin` for authentication "
                                f"(line {op.line}). This is vulnerable to phishing attacks: "
                                f"an attacker can trick the owner into calling a malicious "
                                f"contract, which then calls your contract with the owner's "
                                f"`tx.origin`. Use `msg.sender` instead.",
                                line=op.line,
                                extra={
                                    "condition": op.target,
                                    "fix": "Replace tx.origin with msg.sender",
                                }
                            ))

                # أيضاً فحص raw_text لأنماط tx.origin خارج require
                if op.raw_text and 'tx.origin' in op.raw_text:
                    if op.op_type not in (OpType.REQUIRE, OpType.ASSERT):
                        if re.search(r'tx\.origin\s*==|==\s*tx\.origin', op.raw_text):
                            findings.append(self._make_finding(
                                contract, func,
                                f"Function `{fname}` compares `tx.origin` outside of "
                                f"require (line {op.line}). Use `msg.sender` for access control.",
                                line=op.line,
                                confidence=Confidence.MEDIUM,
                                extra={"raw": op.raw_text}
                            ))

        return findings


class DangerousDelegatecall(BaseDetector):
    """
    delegatecall إلى عنوان يتحكم فيه المستخدم.

    Pattern:
        function execute(address target) {
            target.delegatecall(data);  // target من معامل المستخدم!
        }

    delegatecall ينفذ كود العنوان الهدف في سياق العقد الحالي.
    إذا كان العنوان من المستخدم، يمكنه تنفيذ كود يسرق الأموال.
    """

    DETECTOR_ID = "DANGEROUS-DELEGATECALL"
    TITLE = "Delegatecall to user-controlled address"
    SEVERITY = Severity.CRITICAL
    CONFIDENCE = Confidence.MEDIUM

    def detect(self, contract: ParsedContract, all_contracts: List[ParsedContract]) -> List[Finding]:
        findings = []

        for fname, func in contract.functions.items():
            if not func.has_delegatecall:
                continue

            # استخراج أسماء معاملات الدالة
            param_names = {p.get("name", "") for p in func.parameters}

            for op in func.operations:
                if op.op_type != OpType.DELEGATECALL:
                    continue

                target = op.target or ""
                target_base = target.split('[')[0].split('.')[0]

                # هل الهدف من معامل الدالة؟
                is_user_controlled = target_base in param_names

                # أو هل هو متغير حالة قابل للتعديل؟
                is_mutable_state = (
                    target_base in contract.state_vars and
                    not contract.state_vars[target_base].is_constant and
                    not contract.state_vars[target_base].is_immutable
                )

                if is_user_controlled or is_mutable_state:
                    severity = Severity.CRITICAL if is_user_controlled else Severity.HIGH

                    findings.append(self._make_finding(
                        contract, func,
                        f"Function `{fname}` uses `delegatecall` to "
                        f"{'user-supplied' if is_user_controlled else 'mutable state'} "
                        f"address `{target}` (line {op.line}). An attacker can point this "
                        f"to a malicious contract that executes arbitrary code in the "
                        f"context of this contract (including stealing all funds). "
                        f"{'Validate the target address against a whitelist.' if is_user_controlled else 'Make the implementation address immutable.'}",
                        line=op.line,
                        severity=severity,
                        extra={
                            "target": target,
                            "source": "parameter" if is_user_controlled else "mutable_state",
                        }
                    ))

        return findings
