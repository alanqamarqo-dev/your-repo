"""
AGL State Extraction — Data Models
نماذج البيانات الأساسية لمحرك استخراج الحالة المالية

يعرّف كل أنواع الكيانات والعلاقات والعقد والأضلاع في الرسم البياني المالي.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Any, Optional, Set, Tuple


# ═══════════════════════════════════════════════════════════════
#  Enums — أنواع الكيانات والعلاقات
# ═══════════════════════════════════════════════════════════════

class EntityType(Enum):
    """أنواع الكيانات المالية المستخرجة من العقود"""
    TOKEN = "token"                    # ERC20, ERC721, ERC1155
    POOL = "pool"                      # AMM Pool, Lending Pool
    VAULT = "vault"                    # ERC4626, Yield Vault
    LENDING_MARKET = "lending_market"  # Aave, Compound market
    ORACLE = "oracle"                  # Price feed, TWAP
    GOVERNANCE = "governance"          # DAO, Timelock, Governor
    STAKING = "staking"               # Staking contract
    BRIDGE = "bridge"                  # Cross-chain bridge
    ROUTER = "router"                  # DEX router, aggregator
    PROXY = "proxy"                    # Proxy contract (UUPS, Transparent)
    ACCOUNT = "account"               # EOA or contract account
    COLLATERAL = "collateral"          # Collateral position
    DEBT = "debt"                      # Debt position
    REWARD = "reward"                  # Reward distributor
    TREASURY = "treasury"             # Treasury, fee collector
    GENERIC_CONTRACT = "generic_contract"


class RelationType(Enum):
    """أنواع العلاقات بين الكيانات"""
    # === Fund Flow (تدفق الأموال) ===
    TRANSFERS_TO = "transfers_to"          # A.transfer(B, amount)
    MINTS_TO = "mints_to"                  # mint(to, amount)
    BURNS_FROM = "burns_from"              # burn(from, amount)
    DEPOSITS_INTO = "deposits_into"        # deposit into vault/pool
    WITHDRAWS_FROM = "withdraws_from"      # withdraw from vault/pool
    BORROWS_FROM = "borrows_from"          # borrow from lending
    REPAYS_TO = "repays_to"                # repay to lending
    LIQUIDATES = "liquidates"              # liquidation
    SWAPS_THROUGH = "swaps_through"        # swap through pool
    STAKES_IN = "stakes_in"                # stake in protocol
    CLAIMS_FROM = "claims_from"            # claim rewards
    COLLATERALIZES = "collateralizes"      # provide collateral
    BRIDGES_TO = "bridges_to"              # cross-chain transfer
    FEE_TO = "fee_to"                      # fee payment

    # === Access Control (صلاحيات الوصول) ===
    OWNS = "owns"                          # owner relationship
    ADMIN_OF = "admin_of"                  # admin role
    CAN_CALL = "can_call"                  # function call permission
    CAN_PAUSE = "can_pause"                # pause capability
    CAN_UPGRADE = "can_upgrade"            # upgrade capability
    ROLE_GRANTS = "role_grants"            # role granting
    GOVERNS = "governs"                    # governance control

    # === Price/Oracle Dependencies (تبعيات الأسعار) ===
    PRICE_FEED_FOR = "price_feed_for"      # oracle → token price
    READS_PRICE_FROM = "reads_price_from"  # contract → oracle
    TWAP_SOURCE = "twap_source"            # TWAP oracle source

    # === Structural (هيكلي) ===
    INHERITS_FROM = "inherits_from"        # contract inheritance
    DELEGATES_TO = "delegates_to"          # delegatecall
    PROXIED_BY = "proxied_by"             # proxy → implementation
    USES_LIBRARY = "uses_library"          # using SafeMath for uint256
    WRAPS = "wraps"                        # wrapper around asset
    BACKED_BY = "backed_by"                # asset backed by collateral


class NodeType(Enum):
    """نوع العقدة في الرسم البياني"""
    ADDRESS = "address"            # EOA/contract address
    TOKEN = "token"                # Token entity
    POOL = "pool"                  # Liquidity pool
    VAULT = "vault"                # Vault
    ORACLE = "oracle"              # Oracle
    GOVERNANCE = "governance"      # Governance
    PROTOCOL = "protocol"          # Protocol-level node
    FUNCTION = "function"          # Function-level node
    STATE_VARIABLE = "state_var"   # State variable node


class EdgeType(Enum):
    """نوع الضلع في الرسم البياني"""
    FUND_FLOW = "fund_flow"            # تحويل أموال
    ACCESS_CONTROL = "access_control"  # صلاحية
    PRICE_DEPENDENCY = "price_dep"     # تبعية سعر
    STRUCTURAL = "structural"          # هيكلي
    DATA_FLOW = "data_flow"            # تدفق بيانات
    TEMPORAL = "temporal"               # زمني — ترتيب التنفيذ


# ═══════════════════════════════════════════════════════════════
#  Execution Semantics — دلالات التنفيذ
# ═══════════════════════════════════════════════════════════════

@dataclass
class ExecutionStep:
    """
    خطوة تنفيذ واحدة في timeline دالة.
    كل عملية في الكود تصبح خطوة مرقمة بالترتيب.
    """
    step_index: int                    # ترتيب التنفيذ (0, 1, 2, ...)
    op_type: str                       # نوع العملية (OpType value)
    target: str = ""                   # المتغير أو العنوان الهدف
    details: str = ""                  # تفاصيل إضافية
    line: int = 0                      # رقم السطر
    function_name: str = ""
    contract_name: str = ""
    is_external_call: bool = False     # هل استدعاء خارجي
    is_state_write: bool = False       # هل كتابة حالة
    is_state_read: bool = False        # هل قراءة حالة
    sends_eth: bool = False            # هل يرسل ETH
    in_loop: bool = False              # هل داخل حلقة
    in_condition: bool = False         # هل داخل شرط
    raw_text: str = ""                 # النص الخام

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_index": self.step_index,
            "op_type": self.op_type,
            "target": self.target,
            "details": self.details,
            "line": self.line,
            "function_name": self.function_name,
            "contract_name": self.contract_name,
            "is_external_call": self.is_external_call,
            "is_state_write": self.is_state_write,
            "is_state_read": self.is_state_read,
            "sends_eth": self.sends_eth,
            "in_loop": self.in_loop,
            "in_condition": self.in_condition,
            "raw_text": self.raw_text,
        }


@dataclass
class CEIViolation:
    """
    انتهاك نمط Checks-Effects-Interactions.
    يحدث عندما يكون استدعاء خارجي قبل تحديث حالة.
    """
    call_step: int                     # خطوة الاستدعاء الخارجي
    write_step: int                    # خطوة كتابة الحالة (بعد الاستدعاء)
    call_target: str = ""              # هدف الاستدعاء
    call_line: int = 0
    write_target: str = ""             # المتغير المكتوب
    write_line: int = 0
    sends_eth: bool = False            # هل يرسل ETH
    violation_type: str = "classic"    # classic / read_only / cross_function
    severity: str = "critical"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "call_step": self.call_step,
            "write_step": self.write_step,
            "call_target": self.call_target,
            "call_line": self.call_line,
            "write_target": self.write_target,
            "write_line": self.write_line,
            "sends_eth": self.sends_eth,
            "violation_type": self.violation_type,
            "severity": self.severity,
        }


@dataclass
class ExecutionTimeline:
    """
    timeline تنفيذ كامل لدالة واحدة — يوضح بالضبط ماذا يحدث وبأي ترتيب.
    هنا يتم كشف ثغرات إعادة الدخول والترتيب الخاطئ.
    """
    function_name: str
    contract_name: str
    visibility: str = ""
    mutability: str = ""
    has_reentrancy_guard: bool = False
    steps: List[ExecutionStep] = field(default_factory=list)

    # === Critical Ordering Analysis ===
    cei_violations: List[CEIViolation] = field(default_factory=list)
    external_calls_before_writes: int = 0      # عدد الاستدعاءات قبل الكتابة
    state_reads_before_calls: int = 0          # قراءات قبل استدعاء → read-only reentrancy
    writes_in_loops: int = 0                   # كتابات حالة داخل حلقات
    delegatecalls_count: int = 0               # عدد delegatecall

    def to_dict(self) -> Dict[str, Any]:
        return {
            "function_name": self.function_name,
            "contract_name": self.contract_name,
            "visibility": self.visibility,
            "mutability": self.mutability,
            "has_reentrancy_guard": self.has_reentrancy_guard,
            "total_steps": len(self.steps),
            "steps": [s.to_dict() for s in self.steps],
            "cei_violations": [v.to_dict() for v in self.cei_violations],
            "external_calls_before_writes": self.external_calls_before_writes,
            "state_reads_before_calls": self.state_reads_before_calls,
            "writes_in_loops": self.writes_in_loops,
            "delegatecalls_count": self.delegatecalls_count,
        }


# ═══════════════════════════════════════════════════════════════
#  State Mutation — نموذج تحول الحالة
# ═══════════════════════════════════════════════════════════════

@dataclass
class StateDelta:
    """
    تغيير حالة واحد: State(t+1) = State(t) ± delta.
    يمثل عملية كتابة واحدة على متغير حالة.
    """
    delta_index: int                   # ترتيب التغيير في التسلسل
    variable: str                      # اسم المتغير
    operation: str = "="               # "=" / "+=" / "-=" / "delete" / "push" / "custom"
    expression: str = ""               # التعبير الرياضي للتغيير
    preconditions: List[str] = field(default_factory=list)  # require/if قبل هذا التغيير
    depends_on_reads: List[str] = field(default_factory=list)  # متغيرات مقروءة مسبقاً
    line: int = 0
    step_index: int = 0                # إحالة إلى ExecutionStep
    in_loop: bool = False
    conditional: bool = False          # هل داخل شرط if

    def to_dict(self) -> Dict[str, Any]:
        return {
            "delta_index": self.delta_index,
            "variable": self.variable,
            "operation": self.operation,
            "expression": self.expression,
            "preconditions": self.preconditions,
            "depends_on_reads": self.depends_on_reads,
            "line": self.line,
            "step_index": self.step_index,
            "in_loop": self.in_loop,
            "conditional": self.conditional,
        }


@dataclass
class ExternalCallPoint:
    """
    نقطة استدعاء خارجي في تسلسل التحولات.
    مهم جداً — هذه هي النقطة التي يمكن فيها إعادة الدخول.
    """
    call_index: int                    # ترتيبها بين deltas
    target: str = ""                   # هدف الاستدعاء
    call_type: str = ""                # call / delegatecall / transfer / send
    sends_eth: bool = False
    value_expression: str = ""         # المبلغ المرسل
    line: int = 0
    step_index: int = 0
    deltas_before: int = 0             # عدد التغييرات قبل هذا الاستدعاء
    deltas_after: int = 0              # عدد التغييرات بعد هذا الاستدعاء
    reads_consumed: List[str] = field(default_factory=list)  # قراءات قبل الاستدعاء

    def to_dict(self) -> Dict[str, Any]:
        return {
            "call_index": self.call_index,
            "target": self.target,
            "call_type": self.call_type,
            "sends_eth": self.sends_eth,
            "value_expression": self.value_expression,
            "line": self.line,
            "step_index": self.step_index,
            "deltas_before": self.deltas_before,
            "deltas_after": self.deltas_after,
            "reads_consumed": self.reads_consumed,
        }


@dataclass
class StateMutation:
    """
    نموذج التحول الكامل لدالة واحدة:
        State(t+1) = State(t) + Σ(deltas)

    يحتوي على:
    - الشروط المسبقة (preconditions: require checks)
    - القراءات (ما يُقرأ من الحالة)
    - التغييرات المرتبة (deltas بالترتيب الدقيق)
    - نقاط الاستدعاء الخارجي (أين تحدث الاستدعاءات بين التغييرات)
    - الحالة الناتجة (postconditions)
    """
    function_name: str
    contract_name: str

    # === Pre-state ===
    preconditions: List[str] = field(default_factory=list)      # require checks
    state_reads: List[str] = field(default_factory=list)        # متغيرات مقروءة

    # === Delta Sequence ===
    deltas: List[StateDelta] = field(default_factory=list)      # التغييرات المرتبة

    # === External Call Points ===
    call_points: List[ExternalCallPoint] = field(default_factory=list)

    # === Post-state ===
    state_writes: List[str] = field(default_factory=list)       # متغيرات مكتوبة (ملخص)
    net_effect: Dict[str, str] = field(default_factory=dict)    # {var: "+amount" / "-amount" / "=expr"}

    # === Risk Indicators ===
    calls_between_deltas: bool = False     # هل يوجد استدعاء بين تغييرين → reentrancy
    writes_after_calls: bool = False       # كتابة بعد استدعاء → CEI violation
    reads_before_calls: bool = False       # قراءة قبل استدعاء → stale read

    def to_dict(self) -> Dict[str, Any]:
        return {
            "function_name": self.function_name,
            "contract_name": self.contract_name,
            "preconditions": self.preconditions,
            "state_reads": self.state_reads,
            "deltas": [d.to_dict() for d in self.deltas],
            "call_points": [c.to_dict() for c in self.call_points],
            "state_writes": self.state_writes,
            "net_effect": self.net_effect,
            "calls_between_deltas": self.calls_between_deltas,
            "writes_after_calls": self.writes_after_calls,
            "reads_before_calls": self.reads_before_calls,
        }


# ═══════════════════════════════════════════════════════════════
#  Function Effect — نموذج تأثير الدالة
# ═══════════════════════════════════════════════════════════════

@dataclass
class FunctionEffect:
    """
    ΔState = f(inputs) — نموذج تأثير دالة واحدة على الحالة الكاملة.

    يصف:
    - ماذا تأخذ الدالة (inputs)
    - ماذا تقرأ من الحالة (reads)
    - ماذا تكتب في الحالة (writes + net delta)
    - ماذا تؤثر على الخارج (external effects)
    - تبعيات مع دوال أخرى (which functions read what we write)
    """
    function_name: str
    contract_name: str
    signature: str = ""                # "withdraw(address,uint256)"

    # === Inputs ===
    parameters: List[Dict[str, str]] = field(default_factory=list)  # [{name, type}]
    msg_value_used: bool = False       # هل تستخدم msg.value
    msg_sender_used: bool = False      # هل تستخدم msg.sender

    # === State Reads ===
    reads: List[str] = field(default_factory=list)               # متغيرات مقروءة
    reads_from_external: List[str] = field(default_factory=list) # قراءات من عقود خارجية

    # === State Writes (Net Delta) ===
    writes: List[str] = field(default_factory=list)              # متغيرات مكتوبة
    net_delta: Dict[str, str] = field(default_factory=dict)      # {var: change_expression}

    # === External Effects ===
    external_calls: List[Dict[str, Any]] = field(default_factory=list)  # [{target, type, value}]
    eth_sent: bool = False
    events_emitted: List[str] = field(default_factory=list)

    # === Access Requirements ===
    requires_access: bool = False
    access_roles: List[str] = field(default_factory=list)        # modifiers / require owner
    reentrancy_guarded: bool = False

    # === Cross-Function Dependencies ===
    conflicts_with: List[str] = field(default_factory=list)      # دوال تقرأ نفس المتغيرات
    depends_on: List[str] = field(default_factory=list)          # دوال تكتب ما نقرأه

    def to_dict(self) -> Dict[str, Any]:
        return {
            "function_name": self.function_name,
            "contract_name": self.contract_name,
            "signature": self.signature,
            "parameters": self.parameters,
            "msg_value_used": self.msg_value_used,
            "msg_sender_used": self.msg_sender_used,
            "reads": self.reads,
            "reads_from_external": self.reads_from_external,
            "writes": self.writes,
            "net_delta": self.net_delta,
            "external_calls": self.external_calls,
            "eth_sent": self.eth_sent,
            "events_emitted": self.events_emitted,
            "requires_access": self.requires_access,
            "access_roles": self.access_roles,
            "reentrancy_guarded": self.reentrancy_guarded,
            "conflicts_with": self.conflicts_with,
            "depends_on": self.depends_on,
        }


# ═══════════════════════════════════════════════════════════════
#  Temporal Edge — ضلع زمني في الرسم البياني
# ═══════════════════════════════════════════════════════════════

@dataclass
class TemporalEdge:
    """
    ضلع زمني يمثل علاقة ترتيب بين حدثين.

    أنواع التبعيات:
    - happens_before: A ينفذ قبل B
    - reads_then_writes: A قرأ ثم B يكتب (stale read خطر)
    - call_then_update: استدعاء خارجي ثم تحديث (reentrancy)
    - cross_function: تبعية بين دوال مختلفة
    - write_write: كلاهما يكتب نفس المتغير (race condition)
    """
    edge_id: str
    source_function: str               # "Contract.function" المصدر
    target_function: str               # "Contract.function" الهدف
    source_step: int = 0               # خطوة التنفيذ المصدر
    target_step: int = 0               # خطوة التنفيذ الهدف
    dependency_type: str = "happens_before"
    shared_variable: str = ""          # المتغير المشترك
    description: str = ""

    # === Vulnerability Detection ===
    is_vulnerability: bool = False
    vulnerability_type: str = ""       # reentrancy / stale_read / cross_function_reentrancy / write_conflict
    vulnerability_severity: str = ""   # critical / high / medium / low

    def to_dict(self) -> Dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "source_function": self.source_function,
            "target_function": self.target_function,
            "source_step": self.source_step,
            "target_step": self.target_step,
            "dependency_type": self.dependency_type,
            "shared_variable": self.shared_variable,
            "description": self.description,
            "is_vulnerability": self.is_vulnerability,
            "vulnerability_type": self.vulnerability_type,
            "vulnerability_severity": self.vulnerability_severity,
        }


@dataclass
class TemporalAnalysis:
    """
    نتيجة التحليل الزمني الكاملة — تجمع كل المعلومات الزمنية.
    """
    timelines: List[ExecutionTimeline] = field(default_factory=list)
    mutations: List[StateMutation] = field(default_factory=list)
    effects: List[FunctionEffect] = field(default_factory=list)
    temporal_edges: List[TemporalEdge] = field(default_factory=list)

    # === Summary ===
    total_cei_violations: int = 0
    total_reentrancy_risks: int = 0
    total_cross_function_deps: int = 0
    total_write_conflicts: int = 0
    vulnerability_candidates: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timelines": [t.to_dict() for t in self.timelines],
            "mutations": [m.to_dict() for m in self.mutations],
            "effects": [e.to_dict() for e in self.effects],
            "temporal_edges": [e.to_dict() for e in self.temporal_edges],
            "summary": {
                "total_cei_violations": self.total_cei_violations,
                "total_reentrancy_risks": self.total_reentrancy_risks,
                "total_cross_function_deps": self.total_cross_function_deps,
                "total_write_conflicts": self.total_write_conflicts,
            },
            "vulnerability_candidates": self.vulnerability_candidates,
        }


# ═══════════════════════════════════════════════════════════════
#  Entity — كيان مالي مستخرج
# ═══════════════════════════════════════════════════════════════

@dataclass
class Entity:
    """كيان مالي واحد مستخرج من العقد الذكي"""
    entity_id: str                             # معرف فريد: "contract:Token" أو "var:balances"
    entity_type: EntityType
    name: str                                  # اسم الكيان
    contract_name: str = ""                    # العقد المحتوي
    source_file: str = ""                      # الملف المصدري

    # === Attributes (سمات الكيان) ===
    token_type: str = ""                       # ERC20, ERC721, ERC1155, native
    token_symbol: str = ""                     # رمز التوكن
    decimals: int = 18                         # عدد المنازل العشرية
    is_mintable: bool = False
    is_burnable: bool = False
    is_pausable: bool = False
    is_upgradeable: bool = False
    total_supply_var: str = ""                 # متغير العرض الكلي

    # === Financial Attributes ===
    collateralization_ratio: Optional[float] = None  # نسبة الضمان
    oracle_link: str = ""                      # رابط أوراكل السعر
    interest_rate_var: str = ""                # متغير سعر الفائدة
    fee_percentage_var: str = ""               # متغير نسبة الرسوم

    # === Permissions ===
    owner_var: str = ""                        # متغير المالك
    admin_roles: List[str] = field(default_factory=list)  # أدوار الإدارة
    access_modifiers: List[str] = field(default_factory=list)  # معدّلات الوصول

    # === State Variables Owned ===
    state_vars: Dict[str, str] = field(default_factory=dict)  # {name: type}
    balance_vars: List[str] = field(default_factory=list)  # متغيرات الأرصدة

    # === Metadata ===
    line_start: int = 0
    line_end: int = 0
    confidence: float = 1.0                    # ثقة التصنيف

    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس للتصدير JSON"""
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type.value,
            "name": self.name,
            "contract_name": self.contract_name,
            "source_file": self.source_file,
            "token_type": self.token_type,
            "token_symbol": self.token_symbol,
            "decimals": self.decimals,
            "is_mintable": self.is_mintable,
            "is_burnable": self.is_burnable,
            "is_pausable": self.is_pausable,
            "is_upgradeable": self.is_upgradeable,
            "total_supply_var": self.total_supply_var,
            "collateralization_ratio": self.collateralization_ratio,
            "oracle_link": self.oracle_link,
            "interest_rate_var": self.interest_rate_var,
            "fee_percentage_var": self.fee_percentage_var,
            "owner_var": self.owner_var,
            "admin_roles": self.admin_roles,
            "access_modifiers": self.access_modifiers,
            "state_vars": self.state_vars,
            "balance_vars": self.balance_vars,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "confidence": self.confidence,
        }


# ═══════════════════════════════════════════════════════════════
#  Relationship — علاقة بين كيانين
# ═══════════════════════════════════════════════════════════════

@dataclass
class Relationship:
    """علاقة بين كيانين ماليين"""
    source_id: str                     # معرف الكيان المصدر
    target_id: str                     # معرف الكيان الهدف
    relation_type: RelationType
    function_name: str = ""            # الدالة التي تنفذ العلاقة
    condition: str = ""                # شرط التنفيذ (require/modifier)
    line: int = 0
    confidence: float = 1.0

    # === Financial Details ===
    token_involved: str = ""           # التوكن المتضمن
    amount_expression: str = ""        # تعبير المبلغ
    fee_expression: str = ""           # تعبير الرسوم

    # === Access Details ===
    required_role: str = ""            # الدور المطلوب
    modifier_guard: str = ""           # المعدّل الحارس

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type.value,
            "function_name": self.function_name,
            "condition": self.condition,
            "line": self.line,
            "confidence": self.confidence,
            "token_involved": self.token_involved,
            "amount_expression": self.amount_expression,
            "fee_expression": self.fee_expression,
            "required_role": self.required_role,
            "modifier_guard": self.modifier_guard,
        }


# ═══════════════════════════════════════════════════════════════
#  Graph Nodes & Edges — عقد وأضلاع الرسم البياني
# ═══════════════════════════════════════════════════════════════

@dataclass
class GraphNode:
    """عقدة في الرسم البياني المالي"""
    node_id: str                       # معرف فريد
    node_type: NodeType
    label: str                         # التسمية المعروضة
    entity_ref: str = ""               # إحالة إلى Entity.entity_id

    # === Node Attributes (حسب النوع) ===
    attributes: Dict[str, Any] = field(default_factory=dict)
    # يمكن أن تحتوي:
    #   token_type, amount, permissions, oracle_link,
    #   collateralization_ratio, interest_rate, fee_rate,
    #   is_paused, total_supply, owner, roles

    # === Balance State (حالة الرصيد) ===
    balances: Dict[str, str] = field(default_factory=dict)  # {token: amount_expr}

    # === Metadata ===
    contract_name: str = ""
    source_file: str = ""
    line: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "label": self.label,
            "entity_ref": self.entity_ref,
            "attributes": self.attributes,
            "balances": self.balances,
            "contract_name": self.contract_name,
            "source_file": self.source_file,
            "line": self.line,
        }


@dataclass
class GraphEdge:
    """ضلع في الرسم البياني المالي"""
    edge_id: str                       # معرف فريد
    source_node: str                   # node_id المصدر
    target_node: str                   # node_id الهدف
    edge_type: EdgeType
    label: str = ""                    # وصف الضلع

    # === Edge Attributes ===
    attributes: Dict[str, Any] = field(default_factory=dict)
    # يمكن أن تحتوي:
    #   amount, token, function, condition, role,
    #   price_impact, fee, direction, frequency

    # === Financial Details ===
    token: str = ""                    # التوكن المنقول
    amount_expr: str = ""              # تعبير المبلغ
    fee_expr: str = ""                 # تعبير الرسوم
    direction: str = "unidirectional"  # unidirectional / bidirectional

    # === Access Control ===
    required_role: str = ""            # الدور المطلوب
    guarded_by: str = ""               # الحارس (modifier)

    # === Metadata ===
    function_name: str = ""
    line: int = 0
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "source_node": self.source_node,
            "target_node": self.target_node,
            "edge_type": self.edge_type.value,
            "label": self.label,
            "attributes": self.attributes,
            "token": self.token,
            "amount_expr": self.amount_expr,
            "fee_expr": self.fee_expr,
            "direction": self.direction,
            "required_role": self.required_role,
            "guarded_by": self.guarded_by,
            "function_name": self.function_name,
            "line": self.line,
            "confidence": self.confidence,
        }


# ═══════════════════════════════════════════════════════════════
#  Balance & Fund Flow — أرصدة وتدفقات مالية
# ═══════════════════════════════════════════════════════════════

@dataclass
class BalanceEntry:
    """سجل رصيد لحساب واحد"""
    account_id: str                    # معرف الحساب/العقد
    token_id: str                      # معرف التوكن
    balance_var: str                   # اسم متغير الرصيد (e.g., "balances[addr]")
    balance_type: str = "balance"      # balance / collateral / debt / staked / rewards
    expression: str = ""               # تعبير الرصيد الرياضي

    def to_dict(self) -> Dict[str, Any]:
        return {
            "account_id": self.account_id,
            "token_id": self.token_id,
            "balance_var": self.balance_var,
            "balance_type": self.balance_type,
            "expression": self.expression,
        }


@dataclass
class FundFlow:
    """تدفق مالي واحد بين نقطتين"""
    flow_id: str
    source_account: str
    target_account: str
    token_id: str
    amount_expr: str                   # تعبير المبلغ
    function_name: str = ""            # الدالة المسؤولة
    flow_type: str = "transfer"        # transfer / mint / burn / swap / borrow / repay
    fee_expr: str = ""                 # تعبير الرسوم المخصومة
    condition: str = ""                # شرط التنفيذ
    line: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "flow_id": self.flow_id,
            "source_account": self.source_account,
            "target_account": self.target_account,
            "token_id": self.token_id,
            "amount_expr": self.amount_expr,
            "function_name": self.function_name,
            "flow_type": self.flow_type,
            "fee_expr": self.fee_expr,
            "condition": self.condition,
            "line": self.line,
        }


# ═══════════════════════════════════════════════════════════════
#  Validation — نتائج التحقق
# ═══════════════════════════════════════════════════════════════

@dataclass
class ValidationIssue:
    """مشكلة تناسق واحدة"""
    issue_type: str                    # balance_mismatch, illogical_cycle, orphan_node, ...
    severity: str = "warning"          # error, warning, info
    description: str = ""
    involved_nodes: List[str] = field(default_factory=list)
    involved_edges: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_type": self.issue_type,
            "severity": self.severity,
            "description": self.description,
            "involved_nodes": self.involved_nodes,
            "involved_edges": self.involved_edges,
            "details": self.details,
        }


@dataclass
class ValidationResult:
    """نتيجة التحقق الشامل"""
    is_consistent: bool = True
    issues: List[ValidationIssue] = field(default_factory=list)
    balance_conservation_ok: bool = True
    no_illogical_cycles: bool = True
    all_nodes_connected: bool = True
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_consistent": self.is_consistent,
            "balance_conservation_ok": self.balance_conservation_ok,
            "no_illogical_cycles": self.no_illogical_cycles,
            "all_nodes_connected": self.all_nodes_connected,
            "issues_count": len(self.issues),
            "issues": [i.to_dict() for i in self.issues],
            "summary": self.summary,
        }


# ═══════════════════════════════════════════════════════════════
#  Financial Graph — الرسم البياني المالي الديناميكي
# ═══════════════════════════════════════════════════════════════

@dataclass
class FinancialGraph:
    """
    الرسم البياني المالي الديناميكي — النتيجة الأساسية لمحرك الاستخراج.
    قابل للتحديث أثناء المحاكاة (add/remove/update nodes & edges).
    """
    # === Core Graph ===
    nodes: Dict[str, GraphNode] = field(default_factory=dict)   # node_id → GraphNode
    edges: Dict[str, GraphEdge] = field(default_factory=dict)   # edge_id → GraphEdge

    # === Entity Registry ===
    entities: Dict[str, Entity] = field(default_factory=dict)   # entity_id → Entity
    relationships: List[Relationship] = field(default_factory=list)

    # === Financial State ===
    balances: List[BalanceEntry] = field(default_factory=list)
    fund_flows: List[FundFlow] = field(default_factory=list)

    # === Validation ===
    validation: Optional[ValidationResult] = None

    # === Temporal Analysis (Dynamic State Transition Model) ===
    temporal_analysis: Optional[TemporalAnalysis] = None

    # === Action Space (Layer 2) ===
    action_space: Optional[Any] = None  # ActionSpace from action_space module

    # === Attack Simulation (Layer 3) ===
    attack_simulation: Optional[Any] = None  # SimulationSummary from attack_engine module

    # === Search Results (Layer 4) ===
    search_results: Optional[Any] = None  # SearchResult from search_engine module

    # === Adjacency (for traversal) ===
    adjacency_out: Dict[str, List[str]] = field(default_factory=dict)  # node → [edge_ids outgoing]
    adjacency_in: Dict[str, List[str]] = field(default_factory=dict)   # node → [edge_ids incoming]

    # === Metadata ===
    source_files: List[str] = field(default_factory=list)
    extraction_time: float = 0.0
    engine_version: str = "1.0.0"

    # ─── Dynamic Operations (عمليات ديناميكية) ───

    def add_node(self, node: GraphNode) -> None:
        """إضافة عقدة إلى الرسم البياني"""
        self.nodes[node.node_id] = node
        if node.node_id not in self.adjacency_out:
            self.adjacency_out[node.node_id] = []
        if node.node_id not in self.adjacency_in:
            self.adjacency_in[node.node_id] = []

    def remove_node(self, node_id: str) -> None:
        """حذف عقدة وكل أضلاعها"""
        if node_id not in self.nodes:
            return
        # حذف الأضلاع المتصلة
        edges_to_remove = set()
        edges_to_remove.update(self.adjacency_out.get(node_id, []))
        edges_to_remove.update(self.adjacency_in.get(node_id, []))
        for eid in edges_to_remove:
            self.remove_edge(eid)
        del self.nodes[node_id]
        self.adjacency_out.pop(node_id, None)
        self.adjacency_in.pop(node_id, None)

    def add_edge(self, edge: GraphEdge) -> None:
        """إضافة ضلع إلى الرسم البياني"""
        self.edges[edge.edge_id] = edge
        # تحديث الجوار
        if edge.source_node not in self.adjacency_out:
            self.adjacency_out[edge.source_node] = []
        self.adjacency_out[edge.source_node].append(edge.edge_id)
        if edge.target_node not in self.adjacency_in:
            self.adjacency_in[edge.target_node] = []
        self.adjacency_in[edge.target_node].append(edge.edge_id)

    def remove_edge(self, edge_id: str) -> None:
        """حذف ضلع"""
        if edge_id not in self.edges:
            return
        edge = self.edges[edge_id]
        # تنظيف الجوار
        out_list = self.adjacency_out.get(edge.source_node, [])
        if edge_id in out_list:
            out_list.remove(edge_id)
        in_list = self.adjacency_in.get(edge.target_node, [])
        if edge_id in in_list:
            in_list.remove(edge_id)
        del self.edges[edge_id]

    def update_node_balance(self, node_id: str, token: str, amount: str) -> None:
        """تحديث رصيد عقدة (للمحاكاة الديناميكية)"""
        if node_id in self.nodes:
            self.nodes[node_id].balances[token] = amount

    def update_node_attribute(self, node_id: str, key: str, value: Any) -> None:
        """تحديث سمة عقدة"""
        if node_id in self.nodes:
            self.nodes[node_id].attributes[key] = value

    def update_edge_attribute(self, edge_id: str, key: str, value: Any) -> None:
        """تحديث سمة ضلع"""
        if edge_id in self.edges:
            self.edges[edge_id].attributes[key] = value

    def get_neighbors(self, node_id: str, direction: str = "both") -> List[str]:
        """الحصول على العقد المجاورة"""
        neighbors = set()
        if direction in ("out", "both"):
            for eid in self.adjacency_out.get(node_id, []):
                if eid in self.edges:
                    neighbors.add(self.edges[eid].target_node)
        if direction in ("in", "both"):
            for eid in self.adjacency_in.get(node_id, []):
                if eid in self.edges:
                    neighbors.add(self.edges[eid].source_node)
        return list(neighbors)

    def get_edges_between(self, source: str, target: str) -> List[GraphEdge]:
        """الحصول على كل الأضلاع بين عقدتين"""
        result = []
        for eid in self.adjacency_out.get(source, []):
            if eid in self.edges and self.edges[eid].target_node == target:
                result.append(self.edges[eid])
        return result

    def get_fund_flow_paths(self, token: str) -> List[List[str]]:
        """تتبع مسارات تدفق توكن معين عبر الرسم"""
        paths = []
        # نجد كل أضلاع التدفق المالي لهذا التوكن
        token_edges = [
            e for e in self.edges.values()
            if e.edge_type == EdgeType.FUND_FLOW and e.token == token
        ]
        if not token_edges:
            return paths

        # BFS لبناء المسارات
        source_nodes = set()
        for e in token_edges:
            source_nodes.add(e.source_node)
        # نجد العقد التي تبدأ منها التدفقات (لا يأتي إليها هذا التوكن)
        target_nodes = {e.target_node for e in token_edges}
        start_nodes = source_nodes - target_nodes
        if not start_nodes:
            start_nodes = source_nodes  # دورة — نبدأ من أي عقدة

        for start in start_nodes:
            self._dfs_paths(start, token, [], set(), paths)
        return paths

    def _dfs_paths(self, node: str, token: str, current_path: List[str],
                   visited: Set[str], all_paths: List[List[str]]) -> None:
        """DFS لبناء مسارات التدفق"""
        current_path.append(node)
        visited.add(node)

        has_next = False
        for eid in self.adjacency_out.get(node, []):
            if eid in self.edges:
                edge = self.edges[eid]
                if edge.edge_type == EdgeType.FUND_FLOW and edge.token == token:
                    if edge.target_node not in visited:
                        has_next = True
                        self._dfs_paths(edge.target_node, token,
                                        current_path.copy(), visited.copy(), all_paths)

        if not has_next and len(current_path) > 1:
            all_paths.append(current_path)

    def subgraph(self, node_ids: Set[str]) -> "FinancialGraph":
        """استخراج رسم بياني فرعي يحتوي فقط على العقد المحددة"""
        sub = FinancialGraph()
        for nid in node_ids:
            if nid in self.nodes:
                sub.add_node(self.nodes[nid])
        for eid, edge in self.edges.items():
            if edge.source_node in node_ids and edge.target_node in node_ids:
                sub.add_edge(edge)
        return sub

    # ─── Statistics (إحصائيات) ───

    def stats(self) -> Dict[str, Any]:
        """إحصائيات الرسم البياني"""
        node_types = {}
        for n in self.nodes.values():
            t = n.node_type.value
            node_types[t] = node_types.get(t, 0) + 1

        edge_types = {}
        for e in self.edges.values():
            t = e.edge_type.value
            edge_types[t] = edge_types.get(t, 0) + 1

        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "total_entities": len(self.entities),
            "total_relationships": len(self.relationships),
            "total_balances": len(self.balances),
            "total_fund_flows": len(self.fund_flows),
            "node_types": node_types,
            "edge_types": edge_types,
            "source_files": self.source_files,
            "extraction_time_ms": round(self.extraction_time * 1000, 2),
        }

    # ─── Serialization (تصدير) ───

    def to_dict(self) -> Dict[str, Any]:
        """تحويل الرسم البياني الكامل إلى JSON-ready dict"""
        return {
            "metadata": {
                "engine_version": self.engine_version,
                "extraction_time_ms": round(self.extraction_time * 1000, 2),
                "source_files": self.source_files,
                "timestamp": time.time(),
            },
            "stats": self.stats(),
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges.values()],
            "entities": [ent.to_dict() for ent in self.entities.values()],
            "relationships": [r.to_dict() for r in self.relationships],
            "balances": [b.to_dict() for b in self.balances],
            "fund_flows": [f.to_dict() for f in self.fund_flows],
            "validation": self.validation.to_dict() if self.validation else None,
            "temporal_analysis": self.temporal_analysis.to_dict() if self.temporal_analysis else None,
            "action_space": self.action_space.to_dict() if self.action_space and hasattr(self.action_space, 'to_dict') else None,
            "attack_simulation": self.attack_simulation.to_dict() if self.attack_simulation and hasattr(self.attack_simulation, 'to_dict') else None,
            "search_results": self.search_results.to_dict() if self.search_results and hasattr(self.search_results, 'to_dict') else None,
        }

    def to_json(self, indent: int = 2) -> str:
        """تصدير JSON كاملاً"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FinancialGraph":
        """إعادة بناء الرسم من dict (للاستيراد)"""
        graph = cls()
        graph.engine_version = data.get("metadata", {}).get("engine_version", "1.0.0")
        graph.source_files = data.get("metadata", {}).get("source_files", [])

        # Rebuild nodes
        for nd in data.get("nodes", []):
            node = GraphNode(
                node_id=nd["node_id"],
                node_type=NodeType(nd["node_type"]),
                label=nd["label"],
                entity_ref=nd.get("entity_ref", ""),
                attributes=nd.get("attributes", {}),
                balances=nd.get("balances", {}),
                contract_name=nd.get("contract_name", ""),
                source_file=nd.get("source_file", ""),
                line=nd.get("line", 0),
            )
            graph.add_node(node)

        # Rebuild edges
        for ed in data.get("edges", []):
            edge = GraphEdge(
                edge_id=ed["edge_id"],
                source_node=ed["source_node"],
                target_node=ed["target_node"],
                edge_type=EdgeType(ed["edge_type"]),
                label=ed.get("label", ""),
                attributes=ed.get("attributes", {}),
                token=ed.get("token", ""),
                amount_expr=ed.get("amount_expr", ""),
                fee_expr=ed.get("fee_expr", ""),
                direction=ed.get("direction", "unidirectional"),
                required_role=ed.get("required_role", ""),
                guarded_by=ed.get("guarded_by", ""),
                function_name=ed.get("function_name", ""),
                line=ed.get("line", 0),
                confidence=ed.get("confidence", 1.0),
            )
            graph.add_edge(edge)

        return graph


# ═══════════════════════════════════════════════════════════════
#  Extraction Result — نتيجة الاستخراج
# ═══════════════════════════════════════════════════════════════

@dataclass
class ExtractionResult:
    """النتيجة الشاملة لعملية الاستخراج"""
    success: bool = True
    graph: Optional[FinancialGraph] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # === Extraction Summary ===
    contracts_parsed: int = 0
    entities_found: int = 0
    relationships_found: int = 0
    fund_flows_found: int = 0
    validation_issues: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "summary": {
                "contracts_parsed": self.contracts_parsed,
                "entities_found": self.entities_found,
                "relationships_found": self.relationships_found,
                "fund_flows_found": self.fund_flows_found,
                "validation_issues": self.validation_issues,
            },
            "errors": self.errors,
            "warnings": self.warnings,
            "graph": self.graph.to_dict() if self.graph else None,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
