"""
Known Pattern Filter — تصنيف النتائج حسب حالة المعرفة المسبقة
Known Pattern Filter — Classifies findings as new, known-design, or intended-feature

This filter runs AFTER deduplication and enrichment, BEFORE final output.
It adds two fields to each finding:
  - "known_status": "new" | "known_risk" | "intended_feature"
  - "known_reason": Human-readable explanation (bilingual AR/EN)

Without this filter, the pipeline reports flash swaps, sandwich attacks, and skim()
as vulnerabilities — but these are known behaviors documented by Uniswap itself.

Usage:
    from agl_security_tool.known_pattern_filter import classify_findings
    classified = classify_findings(unified_findings, contract_source)
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

# ═══════════════════════════════════════════════════════════════════
#  Classification Categories / فئات التصنيف
# ═══════════════════════════════════════════════════════════════════

STATUS_NEW = "new"  # ثغرة جديدة غير معروفة — يجب الإبلاغ عنها
STATUS_KNOWN_RISK = "known_risk"  # مخاطر تصميمية معروفة ومُوثّقة — لها حماية جزئية
STATUS_INTENDED = "intended_feature"  # ميزة مقصودة — ليست ثغرة


# ═══════════════════════════════════════════════════════════════════
#  Protocol Pattern Database / قاعدة بيانات أنماط البروتوكولات
# ═══════════════════════════════════════════════════════════════════

# Each entry: {
#   "pattern_id": unique ID,
#   "protocol": protocol name (or "*" for universal),
#   "match": callable(finding, source) -> bool,
#   "status": STATUS_*,
#   "reason_en": English explanation,
#   "reason_ar": Arabic explanation,
#   "protection": What protection exists (if any),
#   "references": list of documentation URLs,
#   "severity_override": optional new severity (e.g. downgrade CRITICAL → INFO)
# }

KNOWN_PATTERNS: List[Dict] = []


def _register(pattern: Dict) -> Dict:
    """Register a pattern in the database."""
    KNOWN_PATTERNS.append(pattern)
    return pattern


# ═══════════════════════════════════════════════════════════════════
#  Matching Helpers / دوال المطابقة المساعدة
#  (defined before patterns so lambdas can reference them)
# ═══════════════════════════════════════════════════════════════════

def _title_matches(finding: Dict, pattern: str) -> bool:
    """Check if finding title or description matches regex pattern."""
    title = str(finding.get("title", ""))
    desc = str(finding.get("description", ""))
    combined = f"{title} {desc}".lower()
    return bool(re.search(pattern, combined, re.IGNORECASE))


def _func_matches(finding: Dict, pattern: str) -> bool:
    """Check if finding function name matches pattern."""
    func = str(finding.get("function", ""))
    return bool(re.search(pattern, func, re.IGNORECASE))


def _source_has(source: str, pattern: str) -> bool:
    """Check if contract source contains pattern."""
    if not source:
        return True  # If no source available, don't block the match
    return bool(re.search(pattern, source, re.IGNORECASE))


def _source_has_guard(source: str) -> bool:
    """Check if source has reentrancy guard pattern."""
    if not source:
        return False
    guards = [
        r"modifier\s+lock\s*\(",
        r"modifier\s+lock\s*\{",
        r"modifier\s+nonReentrant",
        r"ReentrancyGuard",
        r"unlocked\s*==\s*1",
        r"_status\s*!=\s*_ENTERED",
    ]
    return any(re.search(g, source) for g in guards)


def _func_has_callback(finding: Dict, source: str) -> bool:
    """Check if the finding's function has a callback pattern in source."""
    if not source:
        return False
    func = str(finding.get("function", "")).lower()
    if not func:
        return False
    callback_patterns = [
        r"uniswapV2Call|uniswapV3.*Callback|pancakeCall",
        r"IFlashLoan.*\.onFlashLoan",
        r"\.call\{.*\}\(",
        r"data\.length\s*>\s*0.*\bcall\b",
    ]
    return any(re.search(p, source) for p in callback_patterns)


# ─── Universal AMM Patterns (apply to Uniswap V2/V3, SushiSwap, PancakeSwap, etc.) ───

_register({
    "pattern_id": "AMM-FLASH-SWAP",
    "protocol": "*-amm",
    "match": lambda f, src: (
        _title_matches(f, r"flash.*(?:swap|loan)|callback.*before.*(?:check|invariant)")
        or (_title_matches(f, r"reentr") and _func_has_callback(f, src))
    ) and _source_has(src, r"uniswapV2Call|uniswapV3.*Callback|pancakeCall|flashLoan"),
    "status": STATUS_INTENDED,
    "reason_en": "Flash swaps are an intentional feature. The callback executes BEFORE the K invariant check, "
                 "but the transaction reverts atomically if repayment is insufficient. "
                 "Documented: https://docs.uniswap.org/contracts/v2/concepts/core-concepts/flash-swaps",
    "reason_ar": "المبادلات الفورية (Flash Swaps) ميزة مقصودة. الـ callback يُنفَّذ قبل فحص K invariant، "
                 "لكن المعاملة تفشل ذريًا إذا لم يُسدَّد المبلغ الكافي.",
    "protection": "K invariant check after callback — transaction reverts if not satisfied",
    "references": [
        "https://docs.uniswap.org/contracts/v2/concepts/core-concepts/flash-swaps",
    ],
    "severity_override": "INFO",
})

_register({
    "pattern_id": "AMM-SANDWICH-MEV",
    "protocol": "*-amm",
    "match": lambda f, src: (
        _title_matches(f, r"sandwich|frontrun|front.?run|back.?run|mev|jit.*liquidity|sniping")
    ) and _source_has(src, r"function swap\("),
    "status": STATUS_KNOWN_RISK,
    "reason_en": "Sandwich/MEV attacks are a known and documented risk of AMM design. "
                 "Uniswap explicitly excludes them from bug bounty: 'Known MEV Strategies are not eligible'. "
                 "Protection relies on integration-level slippage controls (Router).",
    "reason_ar": "هجمات Sandwich/MEV مخاطر معروفة ومُوثّقة في تصميم AMM. "
                 "Uniswap يستبعدها صراحة من Bug Bounty. الحماية تعتمد على Router مع slippage.",
    "protection": "Router slippage protection + deadline parameter + private mempools (Flashbots)",
    "references": [
        "https://docs.uniswap.org/contracts/v2/concepts/advanced-topics/security",
        "https://cantina.xyz/bounties/f9df94db-c7b1-434b-bb06-d1360abdd1be",
    ],
    "severity_override": "INFO",
})

_register({
    "pattern_id": "AMM-SKIM-DESIGN",
    "protocol": "*-amm",
    "match": lambda f, src: (
        _title_matches(f, r"skim.*exploit|excess.*token|unauthorized.*fund.*extract")
        or (_func_matches(f, r"^skim$") and _title_matches(f, r"access|unauthor|extract"))
    ) and _source_has(src, r"function skim\(address"),
    "status": STATUS_INTENDED,
    "reason_en": "skim() is an intentional function to handle excess tokens (fee-on-transfer dust, "
                 "accidental transfers). No access control is by design — anyone can call it to "
                 "align balances with reserves. Direct token sends without mint() lose funds by design.",
    "reason_ar": "skim() دالة مقصودة للتعامل مع التوكنات الفائضة. عدم وجود تحكم وصول مقصود — "
                 "أي شخص يمكنه تنظيف الفائض. من يرسل tokens مباشرة بدون mint() يفقدها بالتصميم.",
    "protection": "By design — excess tokens are unowned; skim() is a cleanup function",
    "references": [
        "https://github.com/Uniswap/v2-core/blob/master/contracts/UniswapV2Pair.sol",
    ],
    "severity_override": "INFO",
})

_register({
    "pattern_id": "AMM-TWAP-ORACLE",
    "protocol": "*-amm",
    "match": lambda f, src: (
        _title_matches(f, r"oracle.*manip|price.*manip|twap|price.*oracle")
    ) and _source_has(src, r"price\d?CumulativeLast"),
    "status": STATUS_KNOWN_RISK,
    "reason_en": "Spot price manipulation is a known risk. Uniswap V2 provides TWAP accumulators "
                 "(price0CumulativeLast/price1CumulativeLast) as mitigation. "
                 "Single-block manipulation is possible, but multi-block TWAP manipulation cost "
                 "increases linearly with liquidity and averaging period. "
                 "Only a novel bypass of the TWAP mechanism qualifies for bug bounty.",
    "reason_ar": "التلاعب بالسعر اللحظي مخاطرة معروفة. Uniswap V2 يوفر TWAP accumulators كحماية. "
                 "التلاعب عبر block واحد ممكن، لكن تكلفة التلاعب بـ TWAP تزداد مع السيولة وفترة المتوسط.",
    "protection": "TWAP price accumulators — manipulation cost = arbitrage loss × blocks × liquidity",
    "references": [
        "https://docs.uniswap.org/contracts/v2/concepts/core-concepts/oracles",
    ],
    "severity_override": None,  # Keep original — may be valid in specific contexts
})

_register({
    "pattern_id": "AMM-REENTRANCY-GUARD",
    "protocol": "*-amm",
    "match": lambda f, src: (
        _title_matches(f, r"reentr")
        and not _title_matches(f, r"flash|callback|cross.?contract")
        and _source_has_guard(src)
        and not _func_has_callback(f, src)
    ),
    "status": STATUS_KNOWN_RISK,
    "reason_en": "The contract has a reentrancy guard (lock modifier / ReentrancyGuard). "
                 "Direct reentrancy into the same contract is blocked. "
                 "Only cross-contract reentrancy via callbacks may be exploitable.",
    "reason_ar": "العقد يحتوي على حماية من إعادة الدخول (lock modifier). "
                 "إعادة الدخول المباشرة للعقد نفسه محظورة. فقط إعادة الدخول عبر عقود أخرى قد تكون ممكنة.",
    "protection": "lock modifier / nonReentrant — prevents same-contract reentrancy",
    "references": [],
    "severity_override": "LOW",
})

# ─── ERC20 Token Patterns ───

_register({
    "pattern_id": "ERC20-APPROVE-FRONTRUN",
    "protocol": "*",
    "match": lambda f, src: (
        _title_matches(f, r"approve.*frontrun|approve.*race|erc20.*approv")
    ) and _source_has(src, r"function approve\("),
    "status": STATUS_KNOWN_RISK,
    "reason_en": "The ERC20 approve() race condition is a known, well-documented issue since 2017. "
                 "Mitigations: increaseAllowance()/decreaseAllowance() or permit() (EIP-2612).",
    "reason_ar": "مشكلة سباق approve() في ERC20 معروفة ومُوثّقة منذ 2017. "
                 "الحلول: increaseAllowance()/decreaseAllowance() أو permit() (EIP-2612).",
    "protection": "increaseAllowance/decreaseAllowance pattern or EIP-2612 permit",
    "references": [
        "https://github.com/ethereum/EIPs/issues/20#issuecomment-263524729",
    ],
    "severity_override": "INFO",
})

# ─── Timestamp Dependency ───

_register({
    "pattern_id": "BLOCK-TIMESTAMP",
    "protocol": "*",
    "match": lambda f, src: (
        _title_matches(f, r"block.*timestamp|timestamp.*depend")
        and not _title_matches(f, r"manipulat.*deadline|expired")
    ),
    "status": STATUS_KNOWN_RISK,
    "reason_en": "Block.timestamp dependency is a known low-risk pattern. "
                 "Miners can manipulate timestamp by ~15 seconds. This is only critical "
                 "for time-locked operations with tight deadlines.",
    "reason_ar": "الاعتماد على block.timestamp مخاطرة معروفة منخفضة. "
                 "المعدّنون يمكنهم التلاعب بالتوقيت بـ ~15 ثانية فقط.",
    "protection": "~15 second manipulation window; significant for tight deadlines only",
    "references": [],
    "severity_override": "INFO",
})

# ─── Low-level call patterns in mature protocols ───

_register({
    "pattern_id": "SAFE-TRANSFER-PATTERN",
    "protocol": "*",
    "match": lambda f, src: (
        _title_matches(f, r"low.?level.*call|unchecked.*return")
        and _source_has(src, r"_safeTransfer|safeTransfer")
        and _source_has(src, r"require\(success")
    ),
    "status": STATUS_INTENDED,
    "reason_en": "Low-level call with return value checked via require(success). "
                 "This is the standard safe transfer pattern used by Uniswap/OpenZeppelin.",
    "reason_ar": "استدعاء منخفض المستوى مع فحص القيمة المُرجعة عبر require(success). "
                 "هذا هو نمط التحويل الآمن المعتمد من Uniswap/OpenZeppelin.",
    "protection": "Return value checked + require(success && (data.length == 0 || abi.decode))",
    "references": [],
    "severity_override": "INFO",
})


# ═══════════════════════════════════════════════════════════════════
#  Main Classification Function / دالة التصنيف الرئيسية
# ═══════════════════════════════════════════════════════════════════

def classify_findings(
    findings: List[Dict],
    contract_sources: Optional[Dict[str, str]] = None,
) -> Tuple[List[Dict], Dict]:
    """
    Classify each finding as new, known_risk, or intended_feature.
    تصنيف كل نتيجة كجديدة، مخاطرة معروفة، أو ميزة مقصودة.

    Args:
        findings: List of finding dicts from the pipeline
        contract_sources: Optional {contract_name: source_code} for source-level checks

    Returns:
        (classified_findings, stats) where each finding has added fields:
          - known_status: "new" | "known_risk" | "intended_feature"
          - known_reason: Bilingual explanation
          - known_protection: What protection exists
          - known_references: Documentation links
          - original_severity: Original severity before any override
    """
    if contract_sources is None:
        contract_sources = {}

    # Build combined source for pattern matching
    all_source = "\n".join(contract_sources.values()) if contract_sources else ""

    stats = {
        "total": len(findings),
        "new": 0,
        "known_risk": 0,
        "intended_feature": 0,
        "severity_overrides": 0,
    }

    classified = []
    for f in findings:
        contract_name = f.get("contract", "")
        source = contract_sources.get(contract_name, all_source)

        matched_pattern = None
        for pattern in KNOWN_PATTERNS:
            try:
                if pattern["match"](f, source):
                    matched_pattern = pattern
                    break
            except Exception:
                continue

        if matched_pattern:
            f["known_status"] = matched_pattern["status"]
            f["known_reason"] = (
                f"{matched_pattern['reason_ar']}\n---\n{matched_pattern['reason_en']}"
            )
            f["known_pattern_id"] = matched_pattern["pattern_id"]
            f["known_protection"] = matched_pattern.get("protection", "")
            f["known_references"] = matched_pattern.get("references", [])

            # Severity override if specified
            override = matched_pattern.get("severity_override")
            if override and str(f.get("severity", "")).upper() != override.upper():
                f["original_severity"] = str(f.get("severity", ""))
                f["severity"] = override
                stats["severity_overrides"] += 1
        else:
            f["known_status"] = STATUS_NEW
            f["known_reason"] = ""
            f["known_pattern_id"] = ""

        stats[f["known_status"]] += 1
        classified.append(f)

    return classified, stats


# ═══════════════════════════════════════════════════════════════════
#  Summary Printer / طباعة الملخص
# ═══════════════════════════════════════════════════════════════════

def print_classification_summary(stats: Dict, findings: List[Dict]) -> None:
    """Print a summary of classification results."""
    print(f"\n  ╔═══ Known Pattern Filter Results / نتائج فلتر الأنماط المعروفة ═══╗")
    print(f"  ║  Total findings:          {stats['total']:>4}")
    print(f"  ║  ✘ New (unreported):       {stats['new']:>4}  ← ثغرات جديدة تحتاج مراجعة")
    print(f"  ║  ⚠ Known risks:            {stats['known_risk']:>4}  ← مخاطر معروفة بحماية جزئية")
    print(f"  ║  ✓ Intended features:      {stats['intended_feature']:>4}  ← ميزات مقصودة")
    print(f"  ║  ↓ Severity overrides:     {stats['severity_overrides']:>4}")
    print(f"  ╚═══════════════════════════════════════════════════════════════════╝")

    # Show intended features that were downgraded
    intended = [f for f in findings if f.get("known_status") == STATUS_INTENDED]
    if intended:
        print(f"\n  Intended features (not vulnerabilities):")
        for f in intended:
            orig = f.get("original_severity", "")
            sev_note = f" (was {orig})" if orig else ""
            title = f.get("title", "")[:60]
            print(f"    ✓ {title}{sev_note} — {f.get('known_pattern_id', '')}")

    # Show known risks
    known = [f for f in findings if f.get("known_status") == STATUS_KNOWN_RISK]
    if known:
        print(f"\n  Known design risks (have protection):")
        for f in known:
            orig = f.get("original_severity", "")
            sev_note = f" (was {orig})" if orig else ""
            title = f.get("title", "")[:60]
            prot = f.get("known_protection", "")[:50]
            print(f"    ⚠ {title}{sev_note}")
            if prot:
                print(f"      Protection: {prot}")
