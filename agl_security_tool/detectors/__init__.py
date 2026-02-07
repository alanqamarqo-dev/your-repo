"""
AGL Detectors — إطار عمل الكاشفات المتخصصة
Specialized Vulnerability Detector Framework

كل detector يبحث عن نمط واحد محدد بدقة عالية.
مبني على تحليل دلالي (semantic) وليس regex سطحي.

Architecture:
    SolidityParser -> ParsedContract -> [Detector1, Detector2, ...] -> [Finding, Finding, ...]
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Tuple
from enum import Enum
from abc import ABC, abstractmethod


# ═══════════════════════════════════════════════════════════
#  نماذج البيانات — Data Models
# ═══════════════════════════════════════════════════════════

class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Confidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class OpType(Enum):
    """أنواع العمليات داخل دالة — ترتيبها مهم للتحليل"""
    STATE_READ = "state_read"
    STATE_WRITE = "state_write"
    EXTERNAL_CALL = "external_call"        # .call, .transfer, .send
    EXTERNAL_CALL_ETH = "external_call_eth"  # .call{value:...}
    DELEGATECALL = "delegatecall"
    STATICCALL = "staticcall"
    INTERNAL_CALL = "internal_call"
    REQUIRE = "require"
    ASSERT = "assert"
    REVERT = "revert"
    EMIT = "emit"
    SELFDESTRUCT = "selfdestruct"
    LOOP_START = "loop_start"
    LOOP_BODY_OP = "loop_body_op"
    LOOP_END = "loop_end"
    RETURN = "return"
    ASSEMBLY = "assembly"
    MAPPING_ACCESS = "mapping_access"
    ARRAY_PUSH = "array_push"
    ARRAY_LENGTH = "array_length"
    ENCODE_PACKED = "encode_packed"


@dataclass
class Operation:
    """عملية واحدة داخل دالة — مرتبة حسب ترتيب التنفيذ"""
    op_type: OpType
    line: int
    target: str = ""          # اسم المتغير أو الهدف
    details: str = ""         # تفاصيل إضافية
    sends_eth: bool = False   # هل يُرسل ETH
    in_loop: bool = False     # هل داخل حلقة
    in_condition: bool = False  # هل داخل شرط
    raw_text: str = ""        # النص الخام


@dataclass
class StateVar:
    """متغير حالة"""
    name: str
    var_type: str
    visibility: str = "internal"
    is_constant: bool = False
    is_immutable: bool = False
    is_mapping: bool = False
    is_array: bool = False
    line: int = 0


@dataclass
class ParsedFunction:
    """دالة محللة — تحتوي على كل المعلومات الدلالية"""
    name: str
    visibility: str = "internal"     # public, external, internal, private
    mutability: str = ""             # view, pure, payable, ""
    modifiers: List[str] = field(default_factory=list)
    parameters: List[Dict] = field(default_factory=list)   # [{name, type}]
    returns: List[Dict] = field(default_factory=list)
    line_start: int = 0
    line_end: int = 0
    raw_body: str = ""

    # ═══ التحليل الدلالي ═══
    operations: List[Operation] = field(default_factory=list)
    state_reads: List[str] = field(default_factory=list)     # أسماء متغيرات الحالة المقروءة
    state_writes: List[str] = field(default_factory=list)    # أسماء متغيرات الحالة المكتوبة
    external_calls: List[Operation] = field(default_factory=list)
    require_checks: List[str] = field(default_factory=list)  # شروط require
    internal_calls: List[str] = field(default_factory=list)  # دوال داخلية مُستدعاة

    # ═══ خصائص محسوبة ═══
    has_reentrancy_guard: bool = False
    has_access_control: bool = False
    sends_eth: bool = False
    modifies_state: bool = False
    has_loops: bool = False
    has_selfdestruct: bool = False
    has_delegatecall: bool = False
    is_constructor: bool = False
    is_initializer: bool = False
    is_fallback: bool = False
    is_receive: bool = False


@dataclass
class ModifierInfo:
    """معلومات modifier"""
    name: str
    params: List[str] = field(default_factory=list)
    body: str = ""
    checks_owner: bool = False
    checks_role: bool = False
    is_reentrancy_guard: bool = False
    is_paused_check: bool = False
    line: int = 0


@dataclass
class ParsedContract:
    """عقد محلل — الوحدة الأساسية للتحليل"""
    name: str
    contract_type: str = "contract"      # contract, interface, library, abstract
    inherits: List[str] = field(default_factory=list)
    state_vars: Dict[str, StateVar] = field(default_factory=dict)
    functions: Dict[str, ParsedFunction] = field(default_factory=dict)
    modifiers: Dict[str, ModifierInfo] = field(default_factory=dict)
    events: List[str] = field(default_factory=list)
    using_for: List[Dict] = field(default_factory=list)    # [{library, type}]
    pragma: str = ""
    license: str = ""
    line_start: int = 0
    line_end: int = 0
    source_file: str = ""

    # خصائص محسوبة
    is_upgradeable: bool = False
    uses_safe_math: bool = False
    solidity_version: str = ""


@dataclass
class Finding:
    """نتيجة كاشف واحد"""
    detector_id: str            # e.g. "REENTRANCY-ETH-001"
    title: str                  # عنوان قصير
    description: str            # شرح تفصيلي
    severity: Severity
    confidence: Confidence
    contract: str               # اسم العقد
    function: str = ""          # اسم الدالة
    line: int = 0
    end_line: int = 0
    snippet: str = ""           # مقطع الكود المعني
    recommendation: str = ""    # التوصية
    references: List[str] = field(default_factory=list)  # روابط مرجعية
    related_locations: List[Dict] = field(default_factory=list)  # مواقع مرتبطة
    extra: Optional[Dict] = field(default_factory=dict)  # بيانات إضافية خاصة بالكاشف

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "detector": self.detector_id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "confidence": self.confidence.value,
            "contract": self.contract,
            "function": self.function,
            "line": self.line,
            "end_line": self.end_line,
            "snippet": self.snippet,
            "recommendation": self.recommendation,
            "references": self.references,
            "related_locations": self.related_locations,
        }
        if self.extra:
            d["extra"] = self.extra
        return d


# ═══════════════════════════════════════════════════════════
#  الكاشف الأساسي — Base Detector
# ═══════════════════════════════════════════════════════════

class BaseDetector(ABC):
    """
    الكلاس الأساسي لكل كاشف.
    كل كاشف يبحث عن نمط واحد محدد.
    """

    @property
    @abstractmethod
    def DETECTOR_ID(self) -> str:
        """معرف فريد: e.g. 'REENTRANCY-ETH'"""
        pass

    @property
    @abstractmethod
    def TITLE(self) -> str:
        """عنوان الكاشف"""
        pass

    @property
    @abstractmethod
    def SEVERITY(self) -> Severity:
        pass

    @property
    @abstractmethod
    def CONFIDENCE(self) -> Confidence:
        pass

    @property
    def DESCRIPTION(self) -> str:
        return ""

    @property
    def RECOMMENDATION(self) -> str:
        return ""

    @property
    def REFERENCES(self) -> List[str]:
        return []

    @abstractmethod
    def detect(self, contract: ParsedContract, all_contracts: List[ParsedContract]) -> List[Finding]:
        """
        تنفيذ الكشف على عقد واحد.

        Args:
            contract: العقد المحلل
            all_contracts: كل العقود في الملف/المشروع (للتحليل العابر)

        Returns:
            قائمة النتائج المكتشفة
        """
        pass

    def _make_finding(self, contract, function="", description: str = "",
                      line: int = 0, snippet: str = "",
                      severity=None, confidence=None,
                      extra: Optional[Dict] = None, **kwargs) -> Finding:
        """
        إنشاء نتيجة مع القيم الافتراضية للكاشف.
        يقبل contract/function كنص أو ككائنات ParsedContract/ParsedFunction.
        """
        # Handle object or string for contract
        if hasattr(contract, 'name'):
            contract_name = contract.name
        else:
            contract_name = str(contract)

        # Handle object or string for function
        if hasattr(function, 'name'):
            func_name = function.name
            if line == 0:
                line = function.line_start
            if not snippet and hasattr(function, 'raw_body') and function.raw_body:
                snippet = function.raw_body[:200]
        else:
            func_name = str(function) if function else ""

        return Finding(
            detector_id=self.DETECTOR_ID,
            title=self.TITLE,
            description=description or self.DESCRIPTION,
            severity=severity or self.SEVERITY,
            confidence=confidence or self.CONFIDENCE,
            contract=contract_name,
            function=func_name,
            line=line,
            end_line=kwargs.get("end_line", 0),
            snippet=snippet,
            recommendation=kwargs.get("recommendation", self.RECOMMENDATION),
            references=self.REFERENCES,
            related_locations=kwargs.get("related_locations", []),
            extra=extra,
        )


# ═══════════════════════════════════════════════════════════
#  محرك التشغيل — Detector Runner
# ═══════════════════════════════════════════════════════════

class DetectorRunner:
    """يشغل كل الكاشفات على مجموعة عقود."""

    def __init__(self):
        self.detectors: List[BaseDetector] = []
        self._register_all_detectors()

    def _register_all_detectors(self):
        """تسجيل كل الكاشفات المتاحة"""
        # Reentrancy family
        from .reentrancy import (
            ReentrancyETH,
            ReentrancyNoETH,
            ReentrancyReadOnly,
            ReentrancyCrossFunction,
        )
        # Access Control
        from .access_control import (
            UnprotectedWithdraw,
            UnprotectedSelfDestruct,
            TxOriginAuth,
            DangerousDelegatecall,
        )
        # DeFi Business Logic
        from .defi import (
            FirstDepositorAttack,
            OracleManipulation,
            PriceStaleCheck,
            DivideBeforeMultiply,
            FlashLoanCallbackValidation,
        )
        # Common patterns
        from .common import (
            UncheckedLowLevelCall,
            UnboundedLoop,
            DuplicateCondition,
            ShadowedStateVariable,
            EncodePacked,
            MissingEventEmission,
        )
        # Token
        from .token import (
            UncheckedERC20Transfer,
            ArbitrarySendERC20,
            FeeOnTransferToken,
        )

        self.detectors = [
            # ═══ Reentrancy (Critical) ═══
            ReentrancyETH(),
            ReentrancyNoETH(),
            ReentrancyReadOnly(),
            ReentrancyCrossFunction(),
            # ═══ Access Control (High) ═══
            UnprotectedWithdraw(),
            UnprotectedSelfDestruct(),
            TxOriginAuth(),
            DangerousDelegatecall(),
            # ═══ DeFi (High/Critical) ═══
            FirstDepositorAttack(),
            OracleManipulation(),
            PriceStaleCheck(),
            DivideBeforeMultiply(),
            FlashLoanCallbackValidation(),
            # ═══ Common (Medium/High) ═══
            UncheckedLowLevelCall(),
            UnboundedLoop(),
            DuplicateCondition(),
            ShadowedStateVariable(),
            EncodePacked(),
            MissingEventEmission(),
            # ═══ Token (High) ═══
            UncheckedERC20Transfer(),
            ArbitrarySendERC20(),
            FeeOnTransferToken(),
        ]

    def run(self, contracts: List[ParsedContract]) -> List[Finding]:
        """تشغيل كل الكاشفات على كل العقود"""
        all_findings = []

        for detector in self.detectors:
            for contract in contracts:
                # تخطي الواجهات والمكتبات
                if contract.contract_type in ("interface",):
                    continue
                try:
                    findings = detector.detect(contract, contracts)
                    all_findings.extend(findings)
                except Exception:
                    pass  # detector فشل — لا نوقف الباقي

        # ترتيب حسب الخطورة ثم السطر
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        all_findings.sort(key=lambda f: (severity_order.get(f.severity.value, 5), f.line))

        return all_findings

    def run_single(self, detector_id: str, contracts: List[ParsedContract]) -> List[Finding]:
        """تشغيل كاشف واحد فقط"""
        for d in self.detectors:
            if d.DETECTOR_ID == detector_id:
                findings = []
                for contract in contracts:
                    if contract.contract_type != "interface":
                        findings.extend(d.detect(contract, contracts))
                return findings
        return []

    def list_detectors(self) -> List[Dict]:
        """قائمة كل الكاشفات المسجلة"""
        return [
            {
                "id": d.DETECTOR_ID,
                "title": d.TITLE,
                "severity": d.SEVERITY.value,
                "confidence": d.CONFIDENCE.value,
                "description": d.DESCRIPTION,
            }
            for d in self.detectors
        ]
