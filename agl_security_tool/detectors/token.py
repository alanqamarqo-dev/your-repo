"""
AGL Token Detectors — كاشفات ثغرات التوكنات
3 detectors for ERC20/token-related vulnerabilities:

1. UNCHECKED-ERC20 — ERC20 transfer/approve without return value check
2. ARBITRARY-SEND-ERC20 — transferFrom with user-controlled `from` address
3. FEE-ON-TRANSFER — Token interactions that don't account for fee-on-transfer
"""

from typing import List
import re
from . import (
    BaseDetector, Finding, Severity, Confidence,
    ParsedContract, ParsedFunction, OpType
)


class UncheckedERC20Transfer(BaseDetector):
    """
    نقل ERC20 بدون فحص القيمة المرجعة.

    Pattern:
        token.transfer(to, amount);        // ✗ بعض ERC20s ترجع false بدل revert
        // الطريقة الصحيحة:
        require(token.transfer(to, amount)); // ✓
        // أو:
        token.safeTransfer(to, amount);      // ✓ OpenZeppelin SafeERC20

    Problem: Some ERC20 tokens (like USDT) return false instead of reverting.
    If you don't check the return value, the transfer silently fails.

    Real-world: USDT, BNB, and many non-standard ERC20 tokens
    """

    DETECTOR_ID = "UNCHECKED-ERC20"
    TITLE = "Unchecked ERC20 transfer return value"
    SEVERITY = Severity.HIGH
    CONFIDENCE = Confidence.HIGH

    _UNSAFE_CALLS = {'transfer', 'transferFrom', 'approve'}
    _SAFE_CALLS = {'safeTransfer', 'safeTransferFrom', 'safeApprove', 'safeIncreaseAllowance'}

    def detect(self, contract: ParsedContract, all_contracts: List[ParsedContract]) -> List[Finding]:
        findings = []

        # هل يستخدم SafeERC20؟
        uses_safe = any(
            'SafeERC20' in u.get('library', '') for u in contract.using_for
        )

        for fname, func in contract.functions.items():
            for op in func.operations:
                if op.op_type != OpType.EXTERNAL_CALL:
                    continue
                if not op.details:
                    continue

                method = op.details
                if method not in self._UNSAFE_CALLS:
                    continue

                raw = op.raw_text or ""

                # هل القيمة المرجعة مفحوصة؟
                is_checked = (
                    raw.strip().startswith('require') or
                    raw.strip().startswith('if') or
                    re.match(r'bool\s+\w+\s*=', raw.strip()) or
                    re.match(r'\(bool', raw.strip()) or
                    'safe' in method.lower()
                )

                if is_checked or uses_safe:
                    continue

                findings.append(self._make_finding(
                    contract, func,
                    f"Function `{fname}` calls `{op.target}.{method}()` (line {op.line}) "
                    f"without checking the return value. Some ERC20 tokens (USDT, BNB) "
                    f"return `false` instead of reverting on failure. The token transfer "
                    f"may silently fail. Use OpenZeppelin's `SafeERC20` library: "
                    f"`using SafeERC20 for IERC20; token.safeTransfer(...)`",
                    line=op.line,
                    extra={
                        "token": op.target,
                        "method": method,
                        "fix": "Use SafeERC20 library",
                    }
                ))

        return findings


class ArbitrarySendERC20(BaseDetector):
    """
    transferFrom مع عنوان `from` يتحكم فيه المستخدم.

    Pattern:
        function steal(address token, address from, uint amount) {
            IERC20(token).transferFrom(from, address(this), amount);
            // ✗ المهاجم يحدد `from` — يمكنه سحب من أي شخص أعطى approve
        }

    Safe pattern:
        IERC20(token).transferFrom(msg.sender, address(this), amount);
        // ✓ msg.sender فقط — لا يمكن استغلاله

    Detection: transferFrom where the `from` argument is a function parameter
    (user-controlled) rather than msg.sender.
    """

    DETECTOR_ID = "ARBITRARY-SEND-ERC20"
    TITLE = "Arbitrary ERC20 transferFrom (user-controlled `from`)"
    SEVERITY = Severity.HIGH
    CONFIDENCE = Confidence.MEDIUM

    def detect(self, contract: ParsedContract, all_contracts: List[ParsedContract]) -> List[Finding]:
        findings = []

        for fname, func in contract.functions.items():
            if func.visibility not in ('public', 'external'):
                continue

            param_names = {p.get("name", "") for p in func.parameters}
            body = func.raw_body or ""

            # البحث عن transferFrom(from, to, amount)
            for m in re.finditer(
                r'\.transferFrom\s*\(\s*(\w+)',
                body
            ):
                from_arg = m.group(1).strip()

                # هل الـ from هو msg.sender أو address(this)؟
                if from_arg in ('msg.sender', 'address(this)', 'sender'):
                    continue  # آمن

                # هل هو معامل دالة؟
                if from_arg in param_names:
                    # هل هناك فحص أن from == msg.sender؟
                    has_sender_check = any(
                        from_arg in check and 'msg.sender' in check
                        for check in func.require_checks
                    )

                    if not has_sender_check:
                        findings.append(self._make_finding(
                            contract, func,
                            f"Function `{fname}` calls `transferFrom` with "
                            f"user-controlled `from` parameter `{from_arg}`. "
                            f"An attacker can pass any address that has approved this "
                            f"contract, stealing their tokens. "
                            f"Either use `msg.sender` as the `from` address, or add "
                            f"`require({from_arg} == msg.sender)`.",
                            line=func.line_start,
                            extra={
                                "from_param": from_arg,
                                "fix": f"Use msg.sender or require({from_arg} == msg.sender)",
                            }
                        ))

        return findings


class FeeOnTransferToken(BaseDetector):
    """
    تفاعل مع توكنات fee-on-transfer بدون حساب الرسوم.

    Pattern:
        function deposit(uint amount) {
            token.transferFrom(msg.sender, address(this), amount);
            balances[msg.sender] += amount;  // ✗ amount != المبلغ الفعلي المستلم!
        }

    Some tokens deduct a fee on transfer: if you transfer 100, the recipient
    gets 97 (3% fee). Recording `amount` instead of the actual received amount
    creates an accounting discrepancy.

    Safe pattern:
        uint before = token.balanceOf(address(this));
        token.transferFrom(msg.sender, address(this), amount);
        uint received = token.balanceOf(address(this)) - before;
        balances[msg.sender] += received;  // ✓

    Detection: transferFrom followed by using the original amount parameter
    for accounting, without balanceOf before/after check.
    """

    DETECTOR_ID = "FEE-ON-TRANSFER"
    TITLE = "Fee-on-transfer token not handled"
    SEVERITY = Severity.MEDIUM
    CONFIDENCE = Confidence.MEDIUM

    _DEPOSIT_NAMES = {
        'deposit', 'stake', 'supply', 'addLiquidity', 'provide',
        'join', 'invest', 'lock', 'wrap',
    }

    def detect(self, contract: ParsedContract, all_contracts: List[ParsedContract]) -> List[Finding]:
        findings = []

        for fname, func in contract.functions.items():
            body = func.raw_body or ""

            # هل الدالة تستقبل tokens عبر transferFrom؟
            tf_match = re.search(
                r'\.(?:transferFrom|safeTransferFrom)\s*\(\s*\w+\s*,\s*(?:address\(this\)|address\s*\(\s*this\s*\))\s*,\s*(\w+)',
                body
            )
            if not tf_match:
                continue

            amount_var = tf_match.group(1)

            # هل يستخدم balanceOf before/after pattern؟
            has_balance_check = bool(
                re.search(r'balanceOf\s*\(\s*address\s*\(\s*this\s*\)', body)
            )

            if has_balance_check:
                continue

            # هل يستخدم amount_var مباشرة في حساب بعد التحويل
            # (مثل: balances[user] += amount)
            after_transfer = body[tf_match.end():]
            uses_amount_directly = bool(
                re.search(r'\b' + re.escape(amount_var) + r'\b', after_transfer)
            )

            if uses_amount_directly:
                # هل الاسم يدل على إيداع؟
                is_deposit = fname.lower() in {n.lower() for n in self._DEPOSIT_NAMES}

                findings.append(self._make_finding(
                    contract, func,
                    f"Function `{fname}` uses `transferFrom` to receive tokens and then "
                    f"uses the original `{amount_var}` for accounting. If the token has "
                    f"a fee-on-transfer mechanism (like SafeMoon, PAXG), the contract "
                    f"will receive less than `{amount_var}`, creating an accounting mismatch. "
                    f"Use balanceOf before/after pattern: "
                    f"`uint before = token.balanceOf(address(this)); "
                    f"token.transferFrom(...); "
                    f"uint received = token.balanceOf(address(this)) - before;`",
                    line=func.line_start,
                    confidence=Confidence.HIGH if is_deposit else Confidence.MEDIUM,
                    extra={
                        "amount_var": amount_var,
                        "function": fname,
                        "pattern": "fee-on-transfer",
                    }
                ))

        return findings
