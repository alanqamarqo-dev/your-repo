"""
AGL Crypto Operations Detectors — كاشفات العمليات التشفيرية
3 detectors for cryptographic vulnerabilities:

1. SIGNATURE-REPLAY — Missing nonce/chainId in signature verification
2. ECRECOVER-ZERO — ecrecover returns address(0) without check
3. WEAK-RANDOMNESS — Using block.timestamp/prevrandao for randomness
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


class SignatureReplay(BaseDetector):
    """
    إعادة استخدام التوقيع — توقيع بدون nonce أو chainId.

    Pattern:
        bytes32 hash = keccak256(abi.encodePacked(to, amount));
        address signer = ecrecover(hash, v, r, s);
        // ✗ لا يوجد nonce → يمكن إعادة استخدام نفس التوقيع
        // ✗ لا يوجد chainId → يعمل على كل الشبكات

    Safe:
        bytes32 hash = keccak256(abi.encodePacked(to, amount, nonce, block.chainid));
        nonces[signer]++;
        // ✓ محمي من الإعادة

    Detection: ecrecover/ECDSA.recover usage without nonce tracking or EIP-712.

    Real-world: Wintermute ($20M), multiple DeFi signature replays
    """

    DETECTOR_ID = "SIGNATURE-REPLAY"
    TITLE = "Signature replay vulnerability (missing nonce/chainId)"
    SEVERITY = Severity.CRITICAL
    CONFIDENCE = Confidence.MEDIUM

    _SIGNATURE_PATTERNS = [
        re.compile(r"ecrecover\s*\(", re.IGNORECASE),
        re.compile(r"ECDSA\.(?:recover|tryRecover)\s*\(", re.IGNORECASE),
        re.compile(r"SignatureChecker\.", re.IGNORECASE),
    ]

    _REPLAY_PROTECTION = [
        # nonce tracking
        re.compile(r"nonce(?:s)?\s*\[", re.IGNORECASE),
        re.compile(r"nonce\s*\+\+|nonce\s*\+=\s*1|\+\+\s*nonce", re.IGNORECASE),
        # EIP-712 domain separator (includes chainId)
        re.compile(r"DOMAIN_SEPARATOR|_domainSeparatorV4|EIP712|eip712", re.IGNORECASE),
        # Signature used/invalidated mapping
        re.compile(r"usedSignature|signatureUsed|executed\s*\[|invalidated", re.IGNORECASE),
        # block.chainid in hash
        re.compile(r"block\.chainid|chainId", re.IGNORECASE),
        # Permit (EIP-2612) standard
        re.compile(r"_useNonce|_nonces\[", re.IGNORECASE),
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

            # إزالة التعليقات قبل الفحص — لتجنب مطابقة كلمات في التعليقات
            # Strip single-line and multi-line comments
            body_no_comments = re.sub(r"//[^\n]*", "", body)
            body_no_comments = re.sub(r"/\*.*?\*/", "", body_no_comments, flags=re.DOTALL)

            # هل تستخدم التحقق من التوقيع؟
            has_sig = any(p.search(body_no_comments) for p in self._SIGNATURE_PATTERNS)
            if not has_sig:
                continue

            # هل محمية من الإعادة؟
            has_replay_protection = any(
                p.search(body_no_comments) for p in self._REPLAY_PROTECTION
            )
            if has_replay_protection:
                continue

            # فحص مستوى العقد أيضاً (nonces قد تكون في دالة أخرى)
            full_source = ""
            for f in contract.functions.values():
                fb = f.raw_body or ""
                fb = re.sub(r"//[^\n]*", "", fb)
                fb = re.sub(r"/\*.*?\*/", "", fb, flags=re.DOTALL)
                full_source += fb + "\n"
            has_contract_nonce = re.search(
                r"nonce(?:s)?\s*\[.*?\]\s*(?:\+\+|=)", full_source
            )
            if has_contract_nonce:
                continue

            findings.append(
                self._make_finding(
                    contract,
                    func,
                    f"Function `{fname}` verifies a signature using "
                    f"ecrecover/ECDSA.recover but has no replay protection. "
                    f"No nonce tracking, no EIP-712 domain separator, and no "
                    f"signature invalidation was found. An attacker can reuse "
                    f"a valid signature multiple times or across chains. "
                    f"Implement nonce tracking with EIP-712 typed data.",
                    line=func.line_start,
                    extra={"pattern": "no_nonce_no_domain"},
                )
            )

        return findings


class EcrecoverZeroAddress(BaseDetector):
    """
    ecrecover ترجع address(0) — بدون فحص.

    Pattern:
        address signer = ecrecover(hash, v, r, s);
        require(signer == expectedSigner);
        // ✗ إذا التوقيع خاطئ، ecrecover ترجع address(0)
        // وإذا expectedSigner = address(0) → يتجاوز الفحص

    Safe:
        address signer = ecrecover(hash, v, r, s);
        require(signer != address(0), "invalid signature");
        // ✓

    Detection: ecrecover without address(0) check.

    Real-world: Multiple auth bypass vulnerabilities
    """

    DETECTOR_ID = "ECRECOVER-ZERO"
    TITLE = "ecrecover result not checked for address(0)"
    SEVERITY = Severity.HIGH
    CONFIDENCE = Confidence.HIGH

    _ECRECOVER = re.compile(r"ecrecover\s*\(", re.IGNORECASE)

    _ZERO_CHECK = [
        re.compile(r"require\s*\([^)]*!=\s*address\s*\(\s*0\s*\)", re.IGNORECASE),
        re.compile(r"if\s*\([^)]*==\s*address\s*\(\s*0\s*\)\s*\)\s*revert", re.IGNORECASE),
        # ECDSA.recover already checks (safe wrapper)
        re.compile(r"ECDSA\.(?:recover|tryRecover)", re.IGNORECASE),
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

            if not self._ECRECOVER.search(body):
                continue

            # هل يستخدم ECDSA wrapper بدل ecrecover المباشر؟
            uses_safe_wrapper = re.search(
                r"ECDSA\.(?:recover|tryRecover)", body
            )
            if uses_safe_wrapper:
                continue

            # هل يفحص address(0)؟
            has_zero_check = any(p.search(body) for p in self._ZERO_CHECK)
            if has_zero_check:
                continue

            findings.append(
                self._make_finding(
                    contract,
                    func,
                    f"Function `{fname}` uses raw `ecrecover()` without checking "
                    f"if the returned address is `address(0)`. When given invalid "
                    f"signature parameters, `ecrecover` returns `address(0)` instead "
                    f"of reverting. If the expected signer happens to be uninitialized "
                    f"(`address(0)`), the check passes for any invalid signature. "
                    f"Add: `require(signer != address(0))` or use OZ `ECDSA.recover()`.",
                    line=func.line_start,
                    extra={"pattern": "raw_ecrecover_no_zero_check"},
                )
            )

        return findings


class WeakRandomness(BaseDetector):
    """
    عشوائية ضعيفة — استخدام block.timestamp/prevrandao كمصدر عشوائي.

    Pattern:
        uint256 random = uint256(keccak256(abi.encodePacked(block.timestamp, msg.sender)));
        // ✗ المُعدّن يتحكم بـ block.timestamp و block.prevrandao

    Safe:
        // Chainlink VRF
        requestId = COORDINATOR.requestRandomWords(...);
        // ✓

    Detection: keccak256 of block.timestamp/difficulty/prevrandao used as
    randomness source without Chainlink VRF or commit-reveal.

    Real-world: Lottery/gaming contract exploits
    """

    DETECTOR_ID = "WEAK-RANDOMNESS"
    TITLE = "Weak randomness source (block variables)"
    SEVERITY = Severity.HIGH
    CONFIDENCE = Confidence.MEDIUM

    _WEAK_SOURCES = re.compile(
        r"block\.(?:timestamp|difficulty|prevrandao|number|coinbase)"
        r"|blockhash\s*\(",
        re.IGNORECASE,
    )

    _RANDOMNESS_USE = re.compile(
        r"(?:random|rand|seed|entropy|lottery|winner|dice|roll|shuffle|pick)",
        re.IGNORECASE,
    )

    _SAFE_PATTERNS = [
        # Chainlink VRF
        re.compile(r"VRF(?:Coordinator|Consumer)|requestRandomWords|fulfillRandom", re.IGNORECASE),
        # Commit-reveal scheme
        re.compile(r"commit.*?reveal|reveal.*?commit", re.IGNORECASE),
        # External oracle randomness
        re.compile(r"randomness(?:Oracle|Provider|Request)", re.IGNORECASE),
    ]

    def detect(
        self, contract: ParsedContract, all_contracts: List[ParsedContract]
    ) -> List[Finding]:
        findings = []

        if contract.contract_type in ("interface", "library"):
            return findings

        # هل العقد يستخدم VRF أو commit-reveal على المستوى الكلي؟
        full_source = ""
        for func in contract.functions.values():
            full_source += (func.raw_body or "") + "\n"

        uses_safe_random = any(p.search(full_source) for p in self._SAFE_PATTERNS)
        if uses_safe_random:
            return findings

        for fname, func in contract.functions.items():
            body = func.raw_body or ""
            if not body:
                continue

            # هل تستخدم block variables كمصدر عشوائي؟
            has_weak_source = self._WEAK_SOURCES.search(body)
            if not has_weak_source:
                continue

            # هل السياق يوحي بالعشوائية (اسم الدالة أو المتغيرات)؟
            is_randomness_context = self._RANDOMNESS_USE.search(body) or \
                self._RANDOMNESS_USE.search(fname)

            # أو keccak256 مع block variables (نمط شائع للعشوائية الزائفة)
            has_hash_pattern = re.search(
                r"keccak256\s*\(\s*abi\.encode(?:Packed)?\s*\([^)]*block\.",
                body,
                re.IGNORECASE,
            )

            if is_randomness_context or has_hash_pattern:
                findings.append(
                    self._make_finding(
                        contract,
                        func,
                        f"Function `{fname}` uses block variables "
                        f"(timestamp/prevrandao/difficulty) as a randomness source. "
                        f"Miners/validators can influence these values, making the "
                        f"randomness predictable. For gaming, lotteries, or any "
                        f"value-bearing random selection, use Chainlink VRF or a "
                        f"commit-reveal scheme.",
                        line=func.line_start,
                        extra={"weak_source": has_weak_source.group()},
                    )
                )

        return findings
