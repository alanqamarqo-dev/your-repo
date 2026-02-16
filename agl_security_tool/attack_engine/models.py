"""
AGL Attack Engine — Data Models (Layer 3)
نماذج البيانات لمحرك الفيزياء الاقتصادية

═══════════════════════════════════════════════════════════════
هذا ليس EVM Simulator.
هذا محرك تنفيذ دلالي (Semantic Execution Engine) يحسب:
    Profit(attacker) = Value(final_assets) - Value(initial_assets) - Gas - Fees

يعمل على مستوى المعنى المالي، لا على مستوى opcodes.
═══════════════════════════════════════════════════════════════

الاعتماديات:
    Layer 1: FinancialGraph, Entity, BalanceEntry, FundFlow
    Layer 2: Action, ActionSpace, ActionGraph, AttackType
"""

from __future__ import annotations

import copy
import json
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Set, Tuple


# ═══════════════════════════════════════════════════════════════
#  Enums
# ═══════════════════════════════════════════════════════════════

class TokenSymbol(Enum):
    """رموز التوكنات المعروفة"""
    ETH = "ETH"
    WETH = "WETH"
    USDC = "USDC"
    USDT = "USDT"
    DAI = "DAI"
    WBTC = "WBTC"
    NATIVE = "NATIVE"    # العملة الأصلية للشبكة
    UNKNOWN = "UNKNOWN"


class RevertReason(Enum):
    """أسباب فشل المعاملة"""
    INSUFFICIENT_BALANCE = "insufficient_balance"
    INSUFFICIENT_ALLOWANCE = "insufficient_allowance"
    ACCESS_DENIED = "access_denied"
    REENTRANCY_GUARD = "reentrancy_guard"
    PAUSED = "paused"
    ZERO_AMOUNT = "zero_amount"
    OVERFLOW = "overflow"
    CUSTOM_REQUIRE = "custom_require"
    OUT_OF_GAS = "out_of_gas"
    NONE = "none"


class SimulationMode(Enum):
    """وضع المحاكاة"""
    SINGLE_TX = "single_tx"          # معاملة واحدة
    SEQUENCE = "sequence"             # تسلسل معاملات
    REENTRANCY = "reentrancy"         # هجوم إعادة دخول
    FLASH_LOAN = "flash_loan"         # قرض فلاش
    SANDWICH = "sandwich"             # ساندويتش هجوم
    MULTI_BLOCK = "multi_block"       # عبر عدة بلوكات


# ═══════════════════════════════════════════════════════════════
#  Account State — حالة حساب واحد
# ═══════════════════════════════════════════════════════════════

@dataclass
class AccountState:
    """
    حالة حساب مالي واحد (EOA أو عقد).
    يتتبع الأرصدة والصلاحيات والتخزين.
    """
    address: str                                   # معرف الحساب
    eth_balance: int = 0                           # رصيد ETH بالـ wei
    token_balances: Dict[str, int] = field(default_factory=dict)  # token → balance
    allowances: Dict[str, Dict[str, int]] = field(default_factory=dict)  # token → {spender: amount}
    storage_vars: Dict[str, Any] = field(default_factory=dict)   # contract storage
    is_contract: bool = False
    nonce: int = 0
    code_hash: str = ""

    def get_balance(self, token: str) -> int:
        """الحصول على رصيد توكن (أو ETH)"""
        if token in ("ETH", "NATIVE", "eth"):
            return self.eth_balance
        return self.token_balances.get(token, 0)

    def set_balance(self, token: str, amount: int) -> None:
        """تعيين رصيد توكن"""
        if token in ("ETH", "NATIVE", "eth"):
            self.eth_balance = amount
        else:
            self.token_balances[token] = amount

    def get_storage(self, var_name: str, default: Any = 0) -> Any:
        """الحصول على قيمة متغير تخزين"""
        return self.storage_vars.get(var_name, default)

    def set_storage(self, var_name: str, value: Any) -> None:
        """تعيين قيمة متغير تخزين"""
        self.storage_vars[var_name] = value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "address": self.address,
            "eth_balance": self.eth_balance,
            "token_balances": dict(self.token_balances),
            "allowances": {k: dict(v) for k, v in self.allowances.items()},
            "storage_vars": dict(self.storage_vars),
            "is_contract": self.is_contract,
            "nonce": self.nonce,
        }


# ═══════════════════════════════════════════════════════════════
#  Token State — حالة توكن
# ═══════════════════════════════════════════════════════════════

@dataclass
class TokenState:
    """حالة توكن واحد في البروتوكول"""
    address: str                       # عنوان/معرف التوكن
    symbol: str = ""
    name: str = ""
    total_supply: int = 0
    decimals: int = 18
    price_usd: float = 0.0            # سعر وحدة واحدة بالدولار
    is_native: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "address": self.address,
            "symbol": self.symbol,
            "name": self.name,
            "total_supply": self.total_supply,
            "decimals": self.decimals,
            "price_usd": self.price_usd,
            "is_native": self.is_native,
        }


# ═══════════════════════════════════════════════════════════════
#  Pool State — حالة مجمع سيولة
# ═══════════════════════════════════════════════════════════════

@dataclass
class PoolState:
    """حالة مجمع AMM (مثل Uniswap V2)"""
    address: str
    token0: str = ""
    token1: str = ""
    reserve0: int = 0
    reserve1: int = 0
    fee_bps: int = 30                  # 0.3% = 30 bps
    total_lp: int = 0
    k_value: int = 0                   # x * y = k

    def get_price(self, token_in: str) -> float:
        """سعر token_in بالنسبة للآخر"""
        if self.reserve0 == 0 or self.reserve1 == 0:
            return 0.0
        if token_in == self.token0:
            return self.reserve1 / self.reserve0
        return self.reserve0 / self.reserve1

    def get_amount_out(self, amount_in: int, token_in: str) -> int:
        """حساب كمية الخروج (CPMM: x * y = k)"""
        if amount_in <= 0:
            return 0
        fee = amount_in * self.fee_bps // 10000
        amount_in_after_fee = amount_in - fee
        if token_in == self.token0:
            r_in, r_out = self.reserve0, self.reserve1
        else:
            r_in, r_out = self.reserve1, self.reserve0
        if r_in == 0:
            return 0
        return (amount_in_after_fee * r_out) // (r_in + amount_in_after_fee)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "address": self.address,
            "token0": self.token0,
            "token1": self.token1,
            "reserve0": self.reserve0,
            "reserve1": self.reserve1,
            "fee_bps": self.fee_bps,
            "total_lp": self.total_lp,
            "k_value": self.k_value,
        }


# ═══════════════════════════════════════════════════════════════
#  Lending State — حالة سوق إقراض
# ═══════════════════════════════════════════════════════════════

@dataclass
class LendingState:
    """حالة سوق إقراض (مثل Aave, Compound)"""
    market: str
    underlying: str = ""               # التوكن الأساسي
    total_deposits: int = 0
    total_borrows: int = 0
    interest_rate_bps: int = 0         # سعر الفائدة السنوي (bps)
    collateral_factor_bps: int = 8000  # 80% = 8000 bps
    liquidation_bonus_bps: int = 500   # 5% = 500 bps
    borrowers: Dict[str, int] = field(default_factory=dict)     # address → debt
    depositors: Dict[str, int] = field(default_factory=dict)    # address → deposit

    @property
    def utilization_rate(self) -> float:
        """نسبة الاستخدام"""
        if self.total_deposits == 0:
            return 0.0
        return self.total_borrows / self.total_deposits

    def to_dict(self) -> Dict[str, Any]:
        return {
            "market": self.market,
            "underlying": self.underlying,
            "total_deposits": self.total_deposits,
            "total_borrows": self.total_borrows,
            "interest_rate_bps": self.interest_rate_bps,
            "collateral_factor_bps": self.collateral_factor_bps,
            "liquidation_bonus_bps": self.liquidation_bonus_bps,
            "utilization_rate": round(self.utilization_rate, 4),
        }


# ═══════════════════════════════════════════════════════════════
#  Oracle State — حالة أوراكل
# ═══════════════════════════════════════════════════════════════

@dataclass
class OracleState:
    """حالة أوراكل سعر"""
    feed: str                          # معرف مصدر السعر
    token: str = ""
    price: float = 0.0                 # السعر الحالي
    last_update_block: int = 0
    decimals: int = 8
    min_answer: float = 0.0
    max_answer: float = float('inf')

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feed": self.feed,
            "token": self.token,
            "price": self.price,
            "last_update_block": self.last_update_block,
            "decimals": self.decimals,
        }


# ═══════════════════════════════════════════════════════════════
#  Protocol State — الحالة الكاملة للبروتوكول
# ═══════════════════════════════════════════════════════════════

@dataclass
class ProtocolState:
    """
    نموذج الحالة الشاملة للبروتوكول.

    هذا هو "عالم" المحاكاة:
        State(t+1) = State(t) + Σ(deltas)

    يدعم:
    - حالات متعددة للحسابات (EOA + عقود)
    - حالات السيولة والإقراض والأوراكل
    - تخزين العقود (storage variables)
    - لقطات غير قابلة للتغيير + تكديس الدلتا للتراجع
    """
    block_number: int = 0
    timestamp: int = 0
    chain_id: int = 1
    gas_price_wei: int = 20_000_000_000  # 20 gwei

    # === Core Financial State ===
    accounts: Dict[str, AccountState] = field(default_factory=dict)
    tokens: Dict[str, TokenState] = field(default_factory=dict)
    pools: Dict[str, PoolState] = field(default_factory=dict)
    markets: Dict[str, LendingState] = field(default_factory=dict)
    oracles: Dict[str, OracleState] = field(default_factory=dict)

    # === Contract Storage (explicit) ===
    contract_storage: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # === ETH price for gas calculations ===
    eth_price_usd: float = 2000.0

    def get_account(self, address: str) -> AccountState:
        """الحصول على حساب أو إنشاؤه"""
        if address not in self.accounts:
            self.accounts[address] = AccountState(address=address)
        return self.accounts[address]

    def get_storage(self, contract: str, var: str, default: Any = 0) -> Any:
        """قراءة متغير تخزين عقد — يدعم صيغة mappings مثل deposits[attacker]"""
        storage = self.contract_storage.get(contract, {})
        # Direct lookup first
        if var in storage:
            return storage[var]
        # Handle mapping syntax: "deposits[attacker]" → deposits["attacker"]
        m = re.match(r'^(\w+)\[(.+)\]$', var)
        if m:
            mapping_name = m.group(1)
            key = m.group(2)
            mapping = storage.get(mapping_name, {})
            if isinstance(mapping, dict):
                return mapping.get(key, default)
        return default

    def set_storage(self, contract: str, var: str, value: Any) -> None:
        """كتابة متغير تخزين عقد — يدعم صيغة mappings مثل deposits[attacker]"""
        if contract not in self.contract_storage:
            self.contract_storage[contract] = {}
        # Handle mapping syntax: "deposits[attacker]" → update deposits["attacker"]
        m = re.match(r'^(\w+)\[(.+)\]$', var)
        if m:
            mapping_name = m.group(1)
            key = m.group(2)
            if mapping_name not in self.contract_storage[contract]:
                self.contract_storage[contract][mapping_name] = {}
            mapping = self.contract_storage[contract][mapping_name]
            if isinstance(mapping, dict):
                mapping[key] = value
                return
        self.contract_storage[contract][var] = value

    def get_token_price(self, token: str) -> float:
        """الحصول على سعر توكن بالدولار"""
        if token in ("ETH", "NATIVE", "eth"):
            return self.eth_price_usd
        if token in self.tokens:
            return self.tokens[token].price_usd
        # ابحث عن أوراكل
        for oracle in self.oracles.values():
            if oracle.token == token:
                return oracle.price
        return 0.0

    def snapshot(self) -> 'ProtocolState':
        """إنشاء لقطة عميقة غير قابلة للتغيير"""
        return copy.deepcopy(self)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "block_number": self.block_number,
            "timestamp": self.timestamp,
            "chain_id": self.chain_id,
            "gas_price_wei": self.gas_price_wei,
            "eth_price_usd": self.eth_price_usd,
            "accounts": {k: v.to_dict() for k, v in self.accounts.items()},
            "tokens": {k: v.to_dict() for k, v in self.tokens.items()},
            "pools": {k: v.to_dict() for k, v in self.pools.items()},
            "markets": {k: v.to_dict() for k, v in self.markets.items()},
            "oracles": {k: v.to_dict() for k, v in self.oracles.items()},
            "contract_storage": self.contract_storage,
        }

    def summary(self) -> Dict[str, Any]:
        """ملخص موجز"""
        total_eth = sum(a.eth_balance for a in self.accounts.values())
        return {
            "accounts": len(self.accounts),
            "tokens": len(self.tokens),
            "pools": len(self.pools),
            "markets": len(self.markets),
            "oracles": len(self.oracles),
            "total_eth_wei": total_eth,
            "storage_vars": sum(len(v) for v in self.contract_storage.values()),
        }


# ═══════════════════════════════════════════════════════════════
#  State Delta — تغيير الحالة
# ═══════════════════════════════════════════════════════════════

@dataclass
class BalanceChange:
    """تغيير رصيد واحد"""
    account: str
    token: str                         # "ETH" للعملة الأصلية
    amount: int                        # موجب = استلام، سالب = إرسال
    reason: str = ""                   # "transfer", "mint", "burn", "fee", "reentrancy_drain"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "account": self.account,
            "token": self.token,
            "amount": self.amount,
            "reason": self.reason,
        }


@dataclass
class StorageChange:
    """تغيير متغير تخزين واحد"""
    contract: str
    variable: str
    old_value: Any = None
    new_value: Any = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contract": self.contract,
            "variable": self.variable,
            "old_value": self.old_value,
            "new_value": self.new_value,
        }


@dataclass
class StateDelta:
    """
    دلتا الحالة: الفرق بين State(t) و State(t+1).

    State(t+1) = State(t) + StateDelta

    كل دالة تُنتج StateDelta واحدة.
    تسلسل هجوم = مجموعة StateDelta مرتبة.
    """
    balance_changes: List[BalanceChange] = field(default_factory=list)
    storage_changes: List[StorageChange] = field(default_factory=list)
    reserve_changes: Dict[str, Dict[str, int]] = field(default_factory=dict)
    supply_changes: Dict[str, int] = field(default_factory=dict)
    price_impacts: Dict[str, float] = field(default_factory=dict)
    gas_used: int = 21000
    reverted: bool = False
    revert_reason: str = ""
    events: List[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        """هل الدلتا فارغة؟"""
        return (
            not self.balance_changes
            and not self.storage_changes
            and not self.reserve_changes
            and not self.supply_changes
            and not self.price_impacts
        )

    def net_balance_change(self, account: str, token: str) -> int:
        """صافي تغيير الرصيد لحساب وتوكن معينين"""
        total = 0
        for bc in self.balance_changes:
            if bc.account == account and bc.token == token:
                total += bc.amount
        return total

    def to_dict(self) -> Dict[str, Any]:
        return {
            "balance_changes": [bc.to_dict() for bc in self.balance_changes],
            "storage_changes": [sc.to_dict() for sc in self.storage_changes],
            "reserve_changes": self.reserve_changes,
            "supply_changes": self.supply_changes,
            "price_impacts": self.price_impacts,
            "gas_used": self.gas_used,
            "reverted": self.reverted,
            "revert_reason": self.revert_reason,
            "events": self.events,
        }


# ═══════════════════════════════════════════════════════════════
#  Executable Action — فعل جاهز للتنفيذ
# ═══════════════════════════════════════════════════════════════

@dataclass
class ExecutableAction:
    """
    Action من Layer 2 بعد تحويله لشكل قابل للتنفيذ.

    الفرق عن Action الأصلي:
    - المعاملات محلولة (concrete, not symbolic)
    - msg.sender و msg.value محددان
    - عمق إعادة الدخول محسوب
    """
    action_id: str                     # من Layer 2
    action: Any = None                 # reference to Layer 2 Action object
    contract_name: str = ""
    function_name: str = ""
    signature: str = ""

    # === Resolved Parameters ===
    concrete_params: Dict[str, Any] = field(default_factory=dict)
    msg_sender: str = ""               # عنوان المُرسل
    msg_value: int = 0                 # ETH المرسلة (wei)

    # === Execution Context ===
    reentrancy_depth: int = 0          # 0 = لا إعادة دخول
    block_number: int = 0
    timestamp: int = 0
    gas_limit: int = 3_000_000

    # === From Layer 2 (cached) ===
    net_delta: Dict[str, str] = field(default_factory=dict)
    external_calls: List[Dict[str, Any]] = field(default_factory=list)
    has_cei_violation: bool = False
    sends_eth: bool = False
    category: str = ""
    preconditions: List[str] = field(default_factory=list)
    state_reads: List[str] = field(default_factory=list)
    state_writes: List[str] = field(default_factory=list)
    reentrancy_guarded: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "contract_name": self.contract_name,
            "function_name": self.function_name,
            "signature": self.signature,
            "concrete_params": self.concrete_params,
            "msg_sender": self.msg_sender,
            "msg_value": self.msg_value,
            "reentrancy_depth": self.reentrancy_depth,
            "net_delta": self.net_delta,
            "has_cei_violation": self.has_cei_violation,
            "sends_eth": self.sends_eth,
            "category": self.category,
        }


# ═══════════════════════════════════════════════════════════════
#  Step Result — نتيجة خطوة واحدة
# ═══════════════════════════════════════════════════════════════

@dataclass
class StepResult:
    """نتيجة تنفيذ خطوة واحدة في تسلسل الهجوم"""
    step_index: int
    action_id: str
    function_name: str = ""
    contract_name: str = ""
    delta: Optional[StateDelta] = None
    success: bool = True
    error: str = ""
    gas_used: int = 21000
    eth_transferred: int = 0           # ETH المحولة في هذه الخطوة
    reentrancy_calls: int = 0          # عدد استدعاءات إعادة الدخول

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "step_index": self.step_index,
            "action_id": self.action_id,
            "function_name": self.function_name,
            "contract_name": self.contract_name,
            "success": self.success,
            "error": self.error,
            "gas_used": self.gas_used,
            "eth_transferred": self.eth_transferred,
            "reentrancy_calls": self.reentrancy_calls,
        }
        if self.delta:
            result["delta"] = self.delta.to_dict()
        return result


# ═══════════════════════════════════════════════════════════════
#  Attack Result — نتيجة الهجوم النهائية
# ═══════════════════════════════════════════════════════════════

@dataclass
class AttackResult:
    """
    النتيجة النهائية لمحاكاة هجوم واحد.

    هذا هو ما يجب أن يُنتجه Layer 3:
        Profit(attacker) = Value(final) - Value(initial) - Gas - Fees

    إذا net_profit_usd > 0 → الهجوم مربح → ثغرة حقيقية.
    """
    sequence_id: str = ""
    attack_name: str = ""
    steps: List[StepResult] = field(default_factory=list)
    total_steps: int = 0

    # === السؤال الوحيد المهم: الربح ===
    profit_by_token: Dict[str, int] = field(default_factory=dict)  # token → profit (wei)
    profit_usd: float = 0.0            # ربح إجمالي بالدولار
    gas_cost_wei: int = 0              # تكلفة الغاز الإجمالية
    gas_cost_usd: float = 0.0         # تكلفة الغاز بالدولار
    flash_loan_fees: Dict[str, int] = field(default_factory=dict)  # token → fee
    flash_loan_fees_usd: float = 0.0
    net_profit_usd: float = 0.0       # الربح الصافي = profit - gas - fees

    # === التصنيف ===
    is_profitable: bool = False
    attack_type: str = ""              # reentrancy, price_manipulation, ...
    severity: str = ""                 # critical, high, medium, low
    confidence: float = 0.0            # 0.0-1.0

    # === الوصف ===
    description: str = ""
    description_ar: str = ""           # الوصف بالعربية
    exploit_scenario: str = ""         # سيناريو الاستغلال

    # === Meta ===
    initial_state_summary: Dict[str, Any] = field(default_factory=dict)
    final_state_summary: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sequence_id": self.sequence_id,
            "attack_name": self.attack_name,
            "total_steps": self.total_steps,
            "steps": [s.to_dict() for s in self.steps],
            # --- الربح ---
            "profit_by_token": self.profit_by_token,
            "profit_usd": round(self.profit_usd, 2),
            "gas_cost_wei": self.gas_cost_wei,
            "gas_cost_usd": round(self.gas_cost_usd, 4),
            "flash_loan_fees": self.flash_loan_fees,
            "flash_loan_fees_usd": round(self.flash_loan_fees_usd, 4),
            "net_profit_usd": round(self.net_profit_usd, 2),
            # --- التصنيف ---
            "is_profitable": self.is_profitable,
            "attack_type": self.attack_type,
            "severity": self.severity,
            "confidence": round(self.confidence, 3),
            # --- الوصف ---
            "description": self.description,
            "description_ar": self.description_ar,
            "exploit_scenario": self.exploit_scenario,
            # --- Meta ---
            "initial_state_summary": self.initial_state_summary,
            "final_state_summary": self.final_state_summary,
            "execution_time_ms": round(self.execution_time_ms, 2),
            "errors": self.errors,
            "warnings": self.warnings,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


# ═══════════════════════════════════════════════════════════════
#  Simulation Config — إعدادات المحاكاة
# ═══════════════════════════════════════════════════════════════

@dataclass
class SimulationConfig:
    """إعدادات محرك المحاكاة"""
    # === Initial State ===
    attacker_eth_balance: int = 10 * 10**18        # 10 ETH
    contract_eth_balance: int = 100 * 10**18       # 100 ETH
    attacker_deposit_amount: int = 1 * 10**18      # 1 ETH deposited
    default_token_price_usd: float = 2000.0        # ETH price

    # === Execution Limits ===
    max_reentrancy_depth: int = 100                # حد أقصى لإعادة الدخول
    max_sequence_length: int = 20                  # حد أقصى لطول التسلسل
    max_gas_per_tx: int = 30_000_000               # حد الغاز لكل معاملة
    gas_price_wei: int = 20_000_000_000            # 20 gwei

    # === Economic ===
    flash_loan_fee_bps: int = 9                    # 0.09% (Aave)
    liquidation_bonus_bps: int = 500               # 5%
    eth_price_usd: float = 2000.0

    # === Gas Costs (تقديرات) ===
    base_gas: int = 21000
    transfer_gas: int = 21000
    storage_write_gas: int = 20000
    storage_read_gas: int = 2100
    external_call_gas: int = 2600
    reentrancy_call_gas: int = 30000               # غاز لكل reentrant call

    # === Modes ===
    mode: SimulationMode = SimulationMode.SEQUENCE
    include_failed_sequences: bool = False
    compute_all_variants: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attacker_eth_balance": self.attacker_eth_balance,
            "contract_eth_balance": self.contract_eth_balance,
            "attacker_deposit_amount": self.attacker_deposit_amount,
            "max_reentrancy_depth": self.max_reentrancy_depth,
            "max_sequence_length": self.max_sequence_length,
            "gas_price_wei": self.gas_price_wei,
            "flash_loan_fee_bps": self.flash_loan_fee_bps,
            "eth_price_usd": self.eth_price_usd,
            "mode": self.mode.value,
        }


# ═══════════════════════════════════════════════════════════════
#  Simulation Summary — ملخص المحاكاة الكاملة
# ═══════════════════════════════════════════════════════════════

@dataclass
class SimulationSummary:
    """ملخص تشغيل كل السيناريوهات"""
    total_sequences_tested: int = 0
    profitable_attacks: int = 0
    total_profit_usd: float = 0.0
    best_attack: Optional[AttackResult] = None
    all_results: List[AttackResult] = field(default_factory=list)
    execution_time_ms: float = 0.0
    version: str = "1.0.0"

    # === Classification ===
    attack_types_found: Dict[str, int] = field(default_factory=dict)
    severity_distribution: Dict[str, int] = field(default_factory=dict)

    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "total_sequences_tested": self.total_sequences_tested,
            "profitable_attacks": self.profitable_attacks,
            "total_profit_usd": round(self.total_profit_usd, 2),
            "best_attack": self.best_attack.to_dict() if self.best_attack else None,
            "results": [r.to_dict() for r in self.all_results],
            "attack_types_found": self.attack_types_found,
            "severity_distribution": self.severity_distribution,
            "execution_time_ms": round(self.execution_time_ms, 2),
            "errors": self.errors,
            "warnings": self.warnings,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
