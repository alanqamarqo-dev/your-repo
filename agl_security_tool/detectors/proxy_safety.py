"""
AGL Proxy Safety Detectors — كاشفات أمان البروكسي
3 detectors for proxy/upgradeable contract vulnerabilities:

1. UNINITIALIZED-PROXY — Implementation not initialized after deployment
2. STORAGE-COLLISION — Storage slot conflicts in proxy patterns
3. UNSAFE-UPGRADE — upgradeTo without proper authorization or checks
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


class UninitializedProxy(BaseDetector):
    """
    بروكسي غير مهيأ — العقد القابل للترقية لم يُنفّذ عليه initialize.

    Pattern:
        contract MyImpl is Initializable, UUPSUpgradeable {
            function initialize() initializer public { ... }
            // ✗ إذا استُدعي constructor بدلاً من initialize
            // ✗ أو لا يوجد initializer modifier
        }

    Detection: Contract inherits proxy patterns but has no initializer function,
    or has a constructor that sets state (which won't run in proxy context).

    Real-world: Wormhole uninitialized proxy ($320M), Audius governance
    """

    DETECTOR_ID = "UNINITIALIZED-PROXY"
    TITLE = "Upgradeable contract may be uninitialized"
    SEVERITY = Severity.CRITICAL
    CONFIDENCE = Confidence.MEDIUM

    _PROXY_BASES = {
        "initializable", "upgradeable", "uupsproxy", "uupsupgradeable",
        "transparentupgradeableproxy", "beacon", "beaconproxy",
        "erc1967", "proxy", "openzeppelinupgradeable",
    }

    _INIT_PATTERNS = [
        re.compile(r"function\s+initialize\s*\(", re.IGNORECASE),
        re.compile(r"function\s+__\w+_init\s*\(", re.IGNORECASE),
        re.compile(r"initializer\b", re.IGNORECASE),
    ]

    _CONSTRUCTOR_STATE_WRITE = re.compile(
        r"constructor\s*\([^)]*\)\s*\{[^}]*(?:\w+\s*=\s*|_\w+\s*=\s*)", re.DOTALL
    )

    def detect(
        self, contract: ParsedContract, all_contracts: List[ParsedContract]
    ) -> List[Finding]:
        findings = []

        if contract.contract_type in ("interface", "library", "abstract"):
            return findings

        # هل يرث من بروكسي/upgradeable؟
        is_proxy = any(
            base.lower().replace(" ", "") in self._PROXY_BASES
            or "upgradeable" in base.lower()
            or "proxy" in base.lower()
            for base in contract.inherits
        )
        if not is_proxy:
            return findings

        # هل لديه initialize مع initializer modifier؟
        # Check function names, modifiers, AND bodies
        has_initializer = False
        for func_name, func_obj in contract.functions.items():
            # Check if function is named initialize/__xxx_init
            if re.match(r"initialize|__\w+_init", func_name, re.IGNORECASE):
                has_initializer = True
                break
            # Check if function has 'initializer' modifier
            if any("initializer" in m.lower() for m in func_obj.modifiers):
                has_initializer = True
                break
            # Check raw body for initializer patterns
            body = func_obj.raw_body or ""
            if any(p.search(body) for p in self._INIT_PATTERNS):
                has_initializer = True
                break

        if not has_initializer:
            findings.append(
                self._make_finding(
                    contract,
                    "",
                    f"Contract `{contract.name}` inherits from upgradeable/proxy patterns "
                    f"({', '.join(contract.inherits[:3])}) but has no `initialize()` function "
                    f"with the `initializer` modifier. In proxy patterns, the constructor "
                    f"runs only on the implementation — not on the proxy. State must be "
                    f"initialized via an `initialize()` function. Without this, the proxy "
                    f"may operate with uninitialized state, allowing takeover.",
                    extra={"bases": contract.inherits},
                )
            )

        # هل يكتب state في constructor؟ (لن يعمل عبر البروكسي)
        for fname, func in contract.functions.items():
            if fname != "constructor":
                continue
            body = func.raw_body or ""
            if func.state_writes:
                findings.append(
                    self._make_finding(
                        contract,
                        func,
                        f"Contract `{contract.name}` is upgradeable but sets state "
                        f"variables in the constructor ({', '.join(func.state_writes[:3])}). "
                        f"Constructor code does not execute in the proxy context — "
                        f"these state variables will remain at their default values "
                        f"when accessed through the proxy. Move initialization to "
                        f"an `initialize()` function.",
                        line=func.line_start,
                        confidence=Confidence.HIGH,
                        extra={"state_writes": func.state_writes[:5]},
                    )
                )

        return findings


class StorageCollision(BaseDetector):
    """
    تصادم التخزين — متغيرات حالة في مواقع خاطئة في البروكسي.

    Pattern:
        contract ProxyV2 is ProxyV1 {
            uint256 newVar;  // ✗ قد يتصادم مع slot موجود
        }

    Detection: Upgradeable contracts that declare state variables
    without using storage gaps or ERC-7201 namespaced storage.

    Real-world: OpenZeppelin storage collisions in early upgrades
    """

    DETECTOR_ID = "STORAGE-COLLISION"
    TITLE = "Potential storage collision in upgradeable contract"
    SEVERITY = Severity.HIGH
    CONFIDENCE = Confidence.MEDIUM

    _GAP_PATTERN = re.compile(r"__gap|__storage_gap|_gap\b", re.IGNORECASE)
    _NAMESPACE_PATTERN = re.compile(
        r"erc7201|StorageSlot|keccak256.*?\.slot|bytes32\s+(?:private\s+)?constant\s+\w*(?:SLOT|POSITION|LOCATION)",
        re.IGNORECASE,
    )

    def detect(
        self, contract: ParsedContract, all_contracts: List[ParsedContract]
    ) -> List[Finding]:
        findings = []

        if contract.contract_type in ("interface", "library", "abstract"):
            return findings

        if not contract.is_upgradeable:
            # أيضاً نفحص إذا كان يرث من upgradeable
            is_upgradeable = any(
                "upgradeable" in base.lower() or "proxy" in base.lower()
                for base in contract.inherits
            )
            if not is_upgradeable:
                return findings

        # هل يستخدم gaps أو namespaced storage؟
        full_source = ""
        for func in contract.functions.values():
            full_source += (func.raw_body or "") + "\n"

        has_gap = False
        has_namespace = False
        for var_name, var in contract.state_vars.items():
            if self._GAP_PATTERN.search(var_name):
                has_gap = True
            raw_type = var.var_type or ""
            if "StorageSlot" in raw_type or self._NAMESPACE_PATTERN.search(var_name):
                has_namespace = True

        if self._NAMESPACE_PATTERN.search(full_source):
            has_namespace = True

        # أيضاً نفحص العقود الأب — قد يكون __gap معرّف في الأب
        # Also check parent contracts for gaps (parser may not extract
        # array state vars like uint256[50] __gap)
        if not has_gap:
            parent_names = {b.lower() for b in contract.inherits}
            for pc in all_contracts:
                if pc.name.lower() in parent_names or pc.name == contract.name:
                    for vn in pc.state_vars:
                        if self._GAP_PATTERN.search(vn):
                            has_gap = True
                            break
                    # Also scan function bodies of self for __gap declaration
                    for func_obj in pc.functions.values():
                        body = func_obj.raw_body or ""
                        if "__gap" in body or "__storage_gap" in body:
                            has_gap = True
                            break
                if has_gap:
                    break

        if has_gap or has_namespace:
            return findings  # محمي

        # كم عدد المتغيرات المُعلنة؟
        non_constant_vars = [
            name for name, var in contract.state_vars.items()
            if not var.is_constant and not var.is_immutable
        ]

        if len(non_constant_vars) > 0 and len(contract.inherits) > 0:
            findings.append(
                self._make_finding(
                    contract,
                    "",
                    f"Contract `{contract.name}` is upgradeable with {len(non_constant_vars)} "
                    f"state variables but uses no storage gaps (`__gap`) or ERC-7201 "
                    f"namespaced storage. Adding new state variables in future versions "
                    f"may overwrite existing storage slots in inherited contracts. "
                    f"Add `uint256[50] private __gap;` at the end of state variables, "
                    f"or migrate to ERC-7201 namespaced storage.",
                    extra={
                        "state_vars": non_constant_vars[:5],
                        "bases": contract.inherits[:3],
                    },
                )
            )

        return findings


class UnsafeUpgrade(BaseDetector):
    """
    ترقية غير آمنة — upgradeTo/upgradeToAndCall بدون حماية.

    Pattern:
        function upgradeTo(address newImpl) public {
            _upgradeTo(newImpl);  // ✗ أي شخص يقدر يغير التنفيذ
        }

    Safe:
        function upgradeTo(address newImpl) public onlyOwner {
            _upgradeTo(newImpl);  // ✓ محمي
        }

    Real-world: Audius governance takeover, Wormhole
    """

    DETECTOR_ID = "UNSAFE-UPGRADE"
    TITLE = "Upgrade function without proper access control"
    SEVERITY = Severity.CRITICAL
    CONFIDENCE = Confidence.HIGH

    _UPGRADE_NAMES = {
        "upgradeto", "upgradetoandcall", "upgradeable", "setimplementation",
        "updateimplementation", "changeimplementation",
    }

    def detect(
        self, contract: ParsedContract, all_contracts: List[ParsedContract]
    ) -> List[Finding]:
        findings = []

        if contract.contract_type in ("interface", "library"):
            return findings

        for fname, func in contract.functions.items():
            if fname.lower() not in self._UPGRADE_NAMES:
                continue
            if func.visibility not in ("public", "external"):
                continue

            # هل محمي بـ access control؟
            if func.has_access_control:
                continue

            # فحص require(msg.sender == ...) في الجسم
            body = func.raw_body or ""
            has_sender_check = re.search(
                r"require\s*\(.*?msg\.sender\s*==", body
            )
            has_role_check = re.search(
                r"(?:onlyRole|hasRole|onlyProxy|_checkOwner|_authorizeUpgrade)", body
            )

            if has_sender_check or has_role_check:
                continue

            findings.append(
                self._make_finding(
                    contract,
                    func,
                    f"Function `{fname}` can change the contract implementation "
                    f"but has no access control. Any address can call this function "
                    f"and redirect the proxy to a malicious implementation, taking "
                    f"over the contract and all its funds. Add `onlyOwner` modifier "
                    f"or implement `_authorizeUpgrade()` properly.",
                    line=func.line_start,
                    extra={"visibility": func.visibility},
                )
            )

        return findings
