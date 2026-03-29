"""
AGL Action Space — Data Models
نماذج البيانات لـ Layer 2: بناء مساحة الهجوم

كل Action يمثل خطوة واحدة قابلة للتنفيذ (مثل حركة شطرنج).
ActionGraph يمثل كل التسلسلات الممكنة.

الاعتماديات:
    Layer 1: FinancialGraph, TemporalAnalysis, FunctionEffect, StateMutation
    detectors: ParsedContract, ParsedFunction, Operation, OpType
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Set


# ═══════════════════════════════════════════════════════════════
#  Enums
# ═══════════════════════════════════════════════════════════════

class AttackType(Enum):
    """تصنيف أنواع الهجمات المحتملة"""
    DIRECT_PROFIT = "direct_profit"              # سحب/اقتراض/تصفية → ربح مباشر
    STATE_MANIPULATION = "state_manipulation"     # تغيير δState لخلق فرصة لاحقة
    REENTRANCY = "reentrancy"                    # CEI violation → إعادة دخول
    CROSS_FUNCTION = "cross_function"            # reentrancy عبر دوال مختلفة
    PRICE_MANIPULATION = "price_manipulation"    # تلاعب أوراكل/TWAP
    FLASH_LOAN = "flash_loan"                    # قرض فلاش → تلاعب → سداد
    ACCESS_ESCALATION = "access_escalation"      # تجاوز صلاحيات
    GOVERNANCE = "governance"                    # تلاعب حوكمة
    FRONT_RUNNING = "front_running"              # سبق المعاملات
    SANDWICH = "sandwich"                        # ساندويتش هجوم
    LIQUIDATION = "liquidation"                  # تصفية
    DONATION = "donation"                        # تبرع لتلاعب exchange rate
    GRIEFING = "griefing"                        # إيذاء بدون ربح


class ActionCategory(Enum):
    """فئة Action حسب تأثيرها على الحالة"""
    FUND_INFLOW = "fund_inflow"          # إيداع/إرسال أموال (deposit, transfer_in)
    FUND_OUTFLOW = "fund_outflow"        # سحب/إرسال أموال (withdraw, transfer_out)
    BORROW = "borrow"                    # اقتراض
    REPAY = "repay"                      # سداد
    SWAP = "swap"                        # مبادلة
    LIQUIDATE = "liquidate"              # تصفية
    STAKE = "stake"                      # staking
    UNSTAKE = "unstake"                  # unstaking
    CLAIM = "claim"                      # مطالبة مكافأة
    GOVERNANCE_VOTE = "governance_vote"  # تصويت
    ADMIN = "admin"                      # عمليات إدارية
    ORACLE_UPDATE = "oracle_update"      # تحديث أوراكل
    FLASH_LOAN = "flash_loan"           # قرض فلاش
    APPROVAL = "approval"               # موافقة/إذن
    STATE_CHANGE = "state_change"       # تغيير حالة عام
    VIEW = "view"                       # قراءة فقط
    UNKNOWN = "unknown"


class ParamDomain(Enum):
    """مجال القيم الممكنة لمعامل"""
    UINT256_MAX = "uint256_max"          # 2^256 - 1
    UINT256_ZERO = "uint256_zero"        # 0
    BALANCE_OF_SENDER = "balance_of_sender"  # balances[msg.sender]
    TOTAL_SUPPLY = "total_supply"        # إجمالي العرض
    CONTRACT_BALANCE = "contract_balance" # رصيد العقد
    SMALL_AMOUNT = "small_amount"        # مبلغ صغير (1 wei, 1 token)
    LARGE_AMOUNT = "large_amount"        # مبلغ كبير (pool reserves)
    ZERO_ADDRESS = "zero_address"        # address(0)
    SELF_ADDRESS = "self_address"        # عنوان العقد نفسه
    ATTACKER_ADDRESS = "attacker_address" # عنوان المهاجم
    VICTIM_ADDRESS = "victim_address"    # عنوان الضحية
    ANY_TOKEN = "any_token"              # أي توكن مُكتَشَف
    CUSTOM = "custom"                    # قيمة مخصصة


# ═══════════════════════════════════════════════════════════════
#  Parameter — معامل دالة مع مجال القيم
# ═══════════════════════════════════════════════════════════════

@dataclass
class ActionParameter:
    """
    معامل لـ Action مع مجال القيم الممكنة.
    لكل معامل Solidity، نحدد القيم الاستراتيجية التي قد تسبب ثغرة.
    """
    name: str                              # اسم المعامل
    param_type: str                        # نوع Solidity: uint256, address, bytes, ...
    domains: List[ParamDomain] = field(default_factory=list)  # القيم الممكنة
    concrete_values: List[str] = field(default_factory=list)  # قيم محددة
    is_amount: bool = False                # هل يمثل مبلغاً مالياً
    is_address: bool = False               # هل يمثل عنواناً
    is_token: bool = False                 # هل يمثل توكن
    constraints: List[str] = field(default_factory=list)  # قيود (from require)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "param_type": self.param_type,
            "domains": [d.value for d in self.domains],
            "concrete_values": self.concrete_values,
            "is_amount": self.is_amount,
            "is_address": self.is_address,
            "is_token": self.is_token,
            "constraints": self.constraints,
        }


# ═══════════════════════════════════════════════════════════════
#  Action — حركة واحدة في مساحة الهجوم
# ═══════════════════════════════════════════════════════════════

@dataclass
class Action:
    """
    وحدة واحدة قابلة للتنفيذ — حركة شطرنج واحدة.

    تمثل استدعاء دالة واحدة مع معاملاتها، شروطها، وتأثيرها على الحالة.
    كل Action يجب أن يكون قابلاً للمحاكاة مباشرة في Layer 3.
    """
    action_id: str                         # معرف فريد: "Contract.function#variant_idx"
    contract_name: str                     # العقد المستهدف
    function_name: str                     # الدالة المستهدفة
    signature: str = ""                    # "function(type1,type2)"

    # === Parameters (المعاملات) ===
    parameters: List[ActionParameter] = field(default_factory=list)
    msg_value: Optional[str] = None        # قيمة ETH المرسلة (إذا payable)

    # === Preconditions — شروط التنفيذ ===
    preconditions: List[str] = field(default_factory=list)     # require checks
    access_requirements: List[str] = field(default_factory=list)  # onlyOwner, roles
    requires_access: bool = False          # هل تحتاج صلاحية
    caller_must_be: str = ""               # "anyone" / "owner" / "role:ADMIN"

    # === State Effect — تأثير على الحالة ===
    state_reads: List[str] = field(default_factory=list)       # متغيرات تُقرأ
    state_writes: List[str] = field(default_factory=list)      # متغيرات تُكتب
    net_delta: Dict[str, str] = field(default_factory=dict)    # {var: ±expr}

    # === External Calls ===
    external_calls: List[Dict[str, Any]] = field(default_factory=list)
    sends_eth: bool = False
    has_delegatecall: bool = False

    # === Temporal Constraints — قيود زمنية ===
    temporal_constraints: List[str] = field(default_factory=list)  # أوصاف القيود الزمنية
    must_execute_before: List[str] = field(default_factory=list)  # action_ids يجب تنفيذها قبل
    must_execute_after: List[str] = field(default_factory=list)   # action_ids يجب تنفيذها بعد
    reentrancy_window: bool = False        # هل يفتح نافذة reentry

    # === Classification — تصنيف ===
    category: ActionCategory = ActionCategory.UNKNOWN
    attack_types: List[AttackType] = field(default_factory=list)
    severity: str = "INFO"                 # CRITICAL / HIGH / MEDIUM / LOW / INFO
    profit_potential: str = "none"         # high / medium / low / none
    is_profitable: bool = False            # هل يمكن أن تُنتج ربح مباشر

    # === Financial Impact ===
    balance_effects: Dict[str, str] = field(default_factory=dict)  # {entity: ±expr}
    tokens_involved: List[str] = field(default_factory=list)
    estimated_value_flow: str = ""         # تقدير تدفق القيمة

    # === Metadata ===
    reentrancy_guarded: bool = False
    has_cei_violation: bool = False
    cei_violation_count: int = 0
    cross_function_risk: bool = False
    visibility: str = "external"
    mutability: str = ""
    line_start: int = 0
    source_file: str = ""

    # === Enabled/Valid ===
    is_valid: bool = True                  # هل الشروط المسبقة قابلة للتحقيق
    disabled_reason: str = ""              # سبب التعطيل

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "contract_name": self.contract_name,
            "function_name": self.function_name,
            "signature": self.signature,
            "parameters": [p.to_dict() for p in self.parameters],
            "msg_value": self.msg_value,
            "preconditions": self.preconditions,
            "access_requirements": self.access_requirements,
            "requires_access": self.requires_access,
            "caller_must_be": self.caller_must_be,
            "state_reads": self.state_reads,
            "state_writes": self.state_writes,
            "net_delta": self.net_delta,
            "external_calls": self.external_calls,
            "sends_eth": self.sends_eth,
            "has_delegatecall": self.has_delegatecall,
            "temporal_constraints": self.temporal_constraints,
            "must_execute_before": self.must_execute_before,
            "must_execute_after": self.must_execute_after,
            "reentrancy_window": self.reentrancy_window,
            "category": self.category.value,
            "attack_types": [a.value for a in self.attack_types],
            "severity": self.severity,
            "profit_potential": self.profit_potential,
            "is_profitable": self.is_profitable,
            "balance_effects": self.balance_effects,
            "tokens_involved": self.tokens_involved,
            "estimated_value_flow": self.estimated_value_flow,
            "reentrancy_guarded": self.reentrancy_guarded,
            "has_cei_violation": self.has_cei_violation,
            "cei_violation_count": self.cei_violation_count,
            "cross_function_risk": self.cross_function_risk,
            "visibility": self.visibility,
            "mutability": self.mutability,
            "line_start": self.line_start,
            "source_file": self.source_file,
            "is_valid": self.is_valid,
            "disabled_reason": self.disabled_reason,
        }


# ═══════════════════════════════════════════════════════════════
#  ActionEdge — ضلع في رسم الأفعال
# ═══════════════════════════════════════════════════════════════

@dataclass
class ActionEdge:
    """
    ضلع يربط بين Action و Action آخر يمكن تنفيذه بعده.

    أنواع الأضلاع:
    - state_enables: Action A يغير حالة تفتح precondition لـ Action B
    - temporal_order: ترتيب زمني فرضته Temporal Graph
    - reentrancy: A يفتح نافذة reentry يمكن لـ B استغلالها
    - conflict: A و B يكتبان نفس المتغير
    - profit_chain: A يُمهد و B يحقق الربح
    """
    edge_id: str
    source_action: str                     # action_id المصدر
    target_action: str                     # action_id الهدف
    edge_type: str = "state_enables"       # state_enables / temporal / reentrancy / conflict / profit_chain
    shared_variable: str = ""              # المتغير المشترك
    description: str = ""
    weight: float = 1.0                    # أهمية هذا الضلع للبحث
    is_attack_path: bool = False           # هل هذا ضلع في مسار هجوم محتمل

    def to_dict(self) -> Dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "source_action": self.source_action,
            "target_action": self.target_action,
            "edge_type": self.edge_type,
            "shared_variable": self.shared_variable,
            "description": self.description,
            "weight": self.weight,
            "is_attack_path": self.is_attack_path,
        }


# ═══════════════════════════════════════════════════════════════
#  ActionGraph — رسم الأفعال الكامل
# ═══════════════════════════════════════════════════════════════

@dataclass
class ActionGraph:
    """
    الرسم البياني لمساحة الهجوم:
        Nodes = كل الأفعال الممكنة (Actions)
        Edges = ترتيب/اعتماديات بين الأفعال

    هذا هو ما سيستخدمه Layer 3 (Attack Simulator) للبحث عن
    تسلسلات هجوم مربحة.
    """
    actions: Dict[str, Action] = field(default_factory=dict)   # action_id → Action
    edges: Dict[str, ActionEdge] = field(default_factory=dict) # edge_id → ActionEdge

    # === Adjacency ===
    successors: Dict[str, List[str]] = field(default_factory=dict)    # action → [edge_ids out]
    predecessors: Dict[str, List[str]] = field(default_factory=dict)  # action → [edge_ids in]

    def add_action(self, action: Action) -> None:
        """إضافة Action للرسم"""
        self.actions[action.action_id] = action
        if action.action_id not in self.successors:
            self.successors[action.action_id] = []
        if action.action_id not in self.predecessors:
            self.predecessors[action.action_id] = []

    def add_edge(self, edge: ActionEdge) -> None:
        """إضافة ضلع للرسم"""
        self.edges[edge.edge_id] = edge
        if edge.source_action not in self.successors:
            self.successors[edge.source_action] = []
        self.successors[edge.source_action].append(edge.edge_id)
        if edge.target_action not in self.predecessors:
            self.predecessors[edge.target_action] = []
        self.predecessors[edge.target_action].append(edge.edge_id)

    def get_successors(self, action_id: str) -> List[Action]:
        """الأفعال التي يمكن تنفيذها بعد action_id"""
        result = []
        for eid in self.successors.get(action_id, []):
            if eid in self.edges:
                target_id = self.edges[eid].target_action
                if target_id in self.actions:
                    result.append(self.actions[target_id])
        return result

    def get_predecessors(self, action_id: str) -> List[Action]:
        """الأفعال التي يجب تنفيذها قبل action_id"""
        result = []
        for eid in self.predecessors.get(action_id, []):
            if eid in self.edges:
                source_id = self.edges[eid].source_action
                if source_id in self.actions:
                    result.append(self.actions[source_id])
        return result

    def get_attack_paths(self, max_paths: int = 200, max_depth: int = 12) -> List[List[str]]:
        """استخراج مسارات الهجوم المحتملة (أضلاع is_attack_path=True)

        Args:
            max_paths: الحد الأقصى لعدد المسارات المُرجعة
            max_depth: الحد الأقصى لعمق كل مسار (عدد الخطوات)
        """
        attack_edges = {
            eid: e for eid, e in self.edges.items() if e.is_attack_path
        }
        if not attack_edges:
            return []

        # بناء adjacency من أضلاع الهجوم فقط
        adj: Dict[str, List[str]] = {}
        targets = set()
        for e in attack_edges.values():
            adj.setdefault(e.source_action, []).append(e.target_action)
            targets.add(e.target_action)

        # نقاط البداية: actions ليست targets في أي ضلع هجوم
        starts = set(adj.keys()) - targets
        if not starts:
            starts = set(adj.keys())

        paths: List[List[str]] = []
        for start in starts:
            if len(paths) >= max_paths:
                break
            self._dfs_attack_paths(start, [start], set(), adj, paths, max_paths, max_depth)
        return paths

    def _dfs_attack_paths(
        self, node: str, path: List[str], visited: Set[str],
        adj: Dict[str, List[str]], all_paths: List[List[str]],
        max_paths: int = 200, max_depth: int = 12,
    ) -> None:
        """DFS لبناء مسارات الهجوم مع حماية من التكرار اللانهائي"""
        # حماية: توقف إذا وصلنا للحد الأقصى من المسارات أو العمق
        if len(all_paths) >= max_paths:
            return
        if len(path) > max_depth:
            if len(path) > 1:
                all_paths.append(path)
            return

        visited.add(node)
        has_next = False
        for nxt in adj.get(node, []):
            if nxt not in visited:
                has_next = True
                self._dfs_attack_paths(
                    nxt, path + [nxt], visited | {nxt}, adj, all_paths,
                    max_paths, max_depth,
                )
                if len(all_paths) >= max_paths:
                    return
        if not has_next and len(path) > 1:
            all_paths.append(path)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "actions": {k: v.to_dict() for k, v in self.actions.items()},
            "edges": {k: v.to_dict() for k, v in self.edges.items()},
            "stats": self.stats(),
        }

    def stats(self) -> Dict[str, Any]:
        """إحصائيات الرسم"""
        categories = {}
        attack_types_count = {}
        severities = {}
        for a in self.actions.values():
            cat = a.category.value
            categories[cat] = categories.get(cat, 0) + 1
            sev = a.severity
            severities[sev] = severities.get(sev, 0) + 1
            for at in a.attack_types:
                atv = at.value
                attack_types_count[atv] = attack_types_count.get(atv, 0) + 1

        edge_types = {}
        attack_edge_count = 0
        for e in self.edges.values():
            et = e.edge_type
            edge_types[et] = edge_types.get(et, 0) + 1
            if e.is_attack_path:
                attack_edge_count += 1

        return {
            "total_actions": len(self.actions),
            "total_edges": len(self.edges),
            "valid_actions": sum(1 for a in self.actions.values() if a.is_valid),
            "invalid_actions": sum(1 for a in self.actions.values() if not a.is_valid),
            "profitable_actions": sum(1 for a in self.actions.values() if a.is_profitable),
            "attack_edges": attack_edge_count,
            "categories": categories,
            "attack_types": attack_types_count,
            "severities": severities,
            "edge_types": edge_types,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


# ═══════════════════════════════════════════════════════════════
#  ActionSpace — المخرج النهائي
# ═══════════════════════════════════════════════════════════════

@dataclass
class ActionSpace:
    """
    النتيجة النهائية لـ Layer 2.
    تحتوي:
    - ActionGraph (الرسم الكامل)
    - ملخص الهجمات المحتملة
    - مسارات الهجوم المرتبة بالأولوية
    """
    graph: ActionGraph = field(default_factory=ActionGraph)
    build_time: float = 0.0
    version: str = "1.0.0"
    source_files: List[str] = field(default_factory=list)

    # === Attack Summary ===
    attack_surfaces: List[Dict[str, Any]] = field(default_factory=list)
    high_value_targets: List[Dict[str, Any]] = field(default_factory=list)
    attack_sequences: List[Dict[str, Any]] = field(default_factory=list)

    # === Errors/Warnings ===
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "build_time_ms": round(self.build_time * 1000, 2),
            "source_files": self.source_files,
            "graph": self.graph.to_dict(),
            "attack_surfaces": self.attack_surfaces,
            "high_value_targets": self.high_value_targets,
            "attack_sequences": self.attack_sequences,
            "errors": self.errors,
            "warnings": self.warnings,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
