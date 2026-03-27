"""
AGL Attack Engine — Protocol State Loader (Component 1)
محمّل الحالة الأولية للبروتوكول

═══════════════════════════════════════════════════════════════
Global Protocol State Model

يحوّل بيانات Layer 1 (FinancialGraph) إلى ProtocolState قابل للمحاكاة:
- entities → accounts + tokens
- balances → token_balances + storage_vars
- fund_flows → flow patterns
- relationships → permissions + oracle links

يُنشئ حساب المهاجم بأرصدة أولية قابلة للتعديل.
═══════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import copy
from typing import Dict, List, Any, Optional, TYPE_CHECKING

from .models import (
    ProtocolState,
    AccountState,
    TokenState,
    PoolState,
    LendingState,
    OracleState,
    SimulationConfig,
)

if TYPE_CHECKING:
    from agl_security_tool.state_extraction.models import (
        FinancialGraph, Entity, BalanceEntry, FundFlow, Relationship,
    )


# ═══════════════════════════════════════════════════════════════
#  Constants
# ═══════════════════════════════════════════════════════════════

ATTACKER_ADDRESS = "attacker"
WEI_PER_ETH = 10 ** 18

# تعيين EntityType إلى نوع الحساب
_ENTITY_CONTRACT_TYPES = {
    "vault", "pool", "lending_market", "staking",
    "bridge", "router", "proxy", "generic_contract",
    "treasury", "reward",
}
_ENTITY_TOKEN_TYPES = {"token"}
_ENTITY_ORACLE_TYPES = {"oracle"}


class ProtocolStateLoader:
    """
    يحمّل الحالة الأولية للبروتوكول من Layer 1.

    Pipeline:
        FinancialGraph → _load_entities → _load_balances → _load_storage
                       → _load_relationships → _create_attacker → ProtocolState
    """

    def __init__(self, config: Optional[SimulationConfig] = None):
        self.config = config or SimulationConfig()

    # ═══════════════════════════════════════════════════════
    #  Main Entry
    # ═══════════════════════════════════════════════════════

    def load_from_graph(self, graph: Any) -> ProtocolState:
        """
        تحميل الحالة الأولية من FinancialGraph.
        يُنشئ بيئة محاكاة كاملة مع:
        - كل الكيانات محولة لحسابات/توكنات
        - الأرصدة منسوخة
        - متغيرات التخزين مهيأة
        - حساب المهاجم جاهز
        """
        state = ProtocolState(
            block_number=1,
            timestamp=1700000000,
            gas_price_wei=self.config.gas_price_wei,
            eth_price_usd=self.config.eth_price_usd,
        )

        # 1. تحميل الكيانات → حسابات + توكنات + أوراكل
        self._load_entities(state, graph)

        # 2. تحميل الأرصدة
        self._load_balances(state, graph)

        # 3. تحميل متغيرات التخزين من العقد المحللة
        self._load_storage_from_entities(state, graph)

        # 4. تحميل العلاقات (صلاحيات + أوراكل)
        self._load_relationships(state, graph)

        # 5. إنشاء حساب المهاجم
        self._create_attacker(state, graph)

        # 6. ضبط أرصدة العقود الافتراضية
        self._set_default_balances(state)

        return state

    def load_minimal(
        self,
        contract_name: str,
        functions: Dict[str, Any],
    ) -> ProtocolState:
        """
        تحميل حالة بسيطة بدون FinancialGraph.
        مفيد للاختبار السريع.
        """
        state = ProtocolState(
            block_number=1,
            timestamp=1700000000,
            gas_price_wei=self.config.gas_price_wei,
            eth_price_usd=self.config.eth_price_usd,
        )

        # إنشاء حساب العقد
        contract_account = AccountState(
            address=contract_name,
            eth_balance=self.config.contract_eth_balance,
            is_contract=True,
        )
        state.accounts[contract_name] = contract_account

        # إنشاء حساب المهاجم
        attacker = AccountState(
            address=ATTACKER_ADDRESS,
            eth_balance=self.config.attacker_eth_balance,
            is_contract=True,  # المهاجم عقد ذكي (لإعادة الدخول)
        )
        state.accounts[ATTACKER_ADDRESS] = attacker

        # تهيئة تخزين العقد
        state.contract_storage[contract_name] = {}

        return state

    # ═══════════════════════════════════════════════════════
    #  Entity Loading
    # ═══════════════════════════════════════════════════════

    def _load_entities(self, state: ProtocolState, graph: Any) -> None:
        """تحويل الكيانات إلى حسابات أو توكنات أو أوراكل"""
        entities = getattr(graph, 'entities', {})
        if not entities:
            return

        for entity_id, entity in entities.items():
            etype = entity.entity_type.value if hasattr(entity.entity_type, 'value') else str(entity.entity_type)

            if etype in _ENTITY_TOKEN_TYPES:
                # === Token ===
                token = TokenState(
                    address=entity_id,
                    symbol=getattr(entity, 'token_symbol', '') or entity.name,
                    name=entity.name,
                    decimals=getattr(entity, 'decimals', 18),
                )
                state.tokens[entity_id] = token

            elif etype in _ENTITY_ORACLE_TYPES:
                # === Oracle ===
                oracle = OracleState(
                    feed=entity_id,
                    token=getattr(entity, 'oracle_link', '') or '',
                )
                state.oracles[entity_id] = oracle

            elif etype in _ENTITY_CONTRACT_TYPES:
                # === Contract Account ===
                account = AccountState(
                    address=entity_id,
                    is_contract=True,
                )
                state.accounts[entity_id] = account

                # هل هو مجمع سيولة؟
                if etype == "pool":
                    pool = PoolState(address=entity_id)
                    state.pools[entity_id] = pool

                # هل هو سوق إقراض؟
                elif etype == "lending_market":
                    market = LendingState(market=entity_id)
                    state.markets[entity_id] = market

            else:
                # أي كيان آخر → حساب عام
                if entity_id not in state.accounts:
                    state.accounts[entity_id] = AccountState(
                        address=entity_id,
                        is_contract=(etype != "account"),
                    )

    # ═══════════════════════════════════════════════════════
    #  Balance Loading
    # ═══════════════════════════════════════════════════════

    def _load_balances(self, state: ProtocolState, graph: Any) -> None:
        """تحميل الأرصدة من BalanceEntry list"""
        balances = getattr(graph, 'balances', [])
        if not balances:
            return

        for entry in balances:
            account_id = entry.account_id
            token_id = entry.token_id
            balance_type = getattr(entry, 'balance_type', 'balance')

            # تأكد من وجود الحساب
            account = state.get_account(account_id)

            # حاول استخراج رقم من expression
            expression = getattr(entry, 'expression', '')
            balance_var = getattr(entry, 'balance_var', '')

            # سجّل في التخزين
            if balance_var:
                if account_id not in state.contract_storage:
                    state.contract_storage[account_id] = {}
                state.contract_storage[account_id][balance_var] = 0

    # ═══════════════════════════════════════════════════════
    #  Storage Loading
    # ═══════════════════════════════════════════════════════

    def _load_storage_from_entities(self, state: ProtocolState, graph: Any) -> None:
        """تحميل متغيرات التخزين من بيانات الكيانات"""
        entities = getattr(graph, 'entities', {})
        for entity_id, entity in entities.items():
            state_vars = getattr(entity, 'state_vars', {})
            balance_vars = getattr(entity, 'balance_vars', [])
            contract_name = getattr(entity, 'contract_name', '') or entity_id

            if not state_vars and not balance_vars:
                continue

            if contract_name not in state.contract_storage:
                state.contract_storage[contract_name] = {}

            # كل state variable → قيمة افتراضية
            for var_name, var_type in state_vars.items():
                if var_name not in state.contract_storage[contract_name]:
                    default = self._default_for_type(var_type)
                    state.contract_storage[contract_name][var_name] = default

            # متغيرات الأرصدة → mapping = {}
            for bvar in balance_vars:
                if bvar not in state.contract_storage[contract_name]:
                    state.contract_storage[contract_name][bvar] = {}

    def _default_for_type(self, solidity_type: str) -> Any:
        """القيمة الافتراضية لنوع Solidity"""
        t = solidity_type.lower().strip()
        if 'uint' in t or 'int' in t:
            return 0
        elif t == 'bool':
            return False
        elif t == 'address':
            return "0x0000000000000000000000000000000000000000"
        elif 'bytes' in t:
            return "0x"
        elif 'string' in t:
            return ""
        elif 'mapping' in t:
            return {}
        else:
            return 0

    # ═══════════════════════════════════════════════════════
    #  Relationship Loading
    # ═══════════════════════════════════════════════════════

    def _load_relationships(self, state: ProtocolState, graph: Any) -> None:
        """تحميل العلاقات (صلاحيات + أوراكل) من الرسم البياني"""
        relationships = getattr(graph, 'relationships', [])
        for rel in relationships:
            rtype = rel.relation_type.value if hasattr(rel.relation_type, 'value') else str(rel.relation_type)

            if rtype == "price_feed_for":
                # ربط أوراكل بتوكن
                if rel.source_id in state.oracles:
                    state.oracles[rel.source_id].token = rel.target_id
            elif rtype == "reads_price_from":
                # عقد يقرأ سعر من أوراكل
                pass  # محفوظ للمحاكاة المتقدمة
            elif rtype in ("owns", "admin_of"):
                # سجّل المالك في storage
                source = rel.source_id
                target = rel.target_id
                if target in state.contract_storage:
                    state.contract_storage[target]["_owner"] = source

    # ═══════════════════════════════════════════════════════
    #  Attacker Setup
    # ═══════════════════════════════════════════════════════

    def _create_attacker(self, state: ProtocolState, graph: Any) -> None:
        """إنشاء حساب المهاجم مع الأرصدة الأولية"""
        attacker = AccountState(
            address=ATTACKER_ADDRESS,
            eth_balance=self.config.attacker_eth_balance,
            is_contract=True,  # المهاجم عقد ذكي (لتنفيذ الـ callback)
            nonce=0,
        )
        state.accounts[ATTACKER_ADDRESS] = attacker

        # إيداع أولي للمهاجم في كل العقود التي تقبل إيداع
        for contract_id, storage in state.contract_storage.items():
            for var_name, var_value in storage.items():
                if isinstance(var_value, dict) and any(
                    k in var_name.lower() for k in ('deposit', 'balance', 'staked')
                ):
                    # هذا mapping → أضف إيداع المهاجم
                    storage[var_name][ATTACKER_ADDRESS] = self.config.attacker_deposit_amount

    # ═══════════════════════════════════════════════════════
    #  Default Balances
    # ═══════════════════════════════════════════════════════

    def _set_default_balances(self, state: ProtocolState) -> None:
        """ضبط أرصدة افتراضية للعقود التي ليس لها رصيد"""
        for account_id, account in state.accounts.items():
            if account_id == ATTACKER_ADDRESS:
                continue
            if account.is_contract and account.eth_balance == 0:
                account.eth_balance = self.config.contract_eth_balance

            # تحديث totalDeposits إذا كان موجوداً
            if account_id in state.contract_storage:
                storage = state.contract_storage[account_id]
                for var_name in list(storage.keys()):
                    if 'totaldeposit' in var_name.lower() or 'total_deposit' in var_name.lower():
                        # مجموع كل الإيداعات
                        deposit_var = None
                        for k, v in storage.items():
                            if isinstance(v, dict) and 'deposit' in k.lower():
                                deposit_var = k
                                break
                        if deposit_var and isinstance(storage[deposit_var], dict):
                            storage[var_name] = sum(storage[deposit_var].values())

    # ═══════════════════════════════════════════════════════
    #  Utilities
    # ═══════════════════════════════════════════════════════

    def configure_state(
        self,
        state: ProtocolState,
        contract_name: str,
        deposits: Optional[Dict[str, int]] = None,
        total_deposits: Optional[int] = None,
        contract_balance: Optional[int] = None,
        attacker_balance: Optional[int] = None,
    ) -> ProtocolState:
        """
        ضبط يدوي لحالة المحاكاة.
        مفيد لتعيين سيناريو محدد قبل المحاكاة.
        """
        if contract_balance is not None:
            account = state.get_account(contract_name)
            account.eth_balance = contract_balance

        if attacker_balance is not None:
            attacker = state.get_account(ATTACKER_ADDRESS)
            attacker.eth_balance = attacker_balance

        if deposits is not None:
            if contract_name not in state.contract_storage:
                state.contract_storage[contract_name] = {}
            # ابحث عن متغير الإيداعات
            deposit_var = None
            for k, v in state.contract_storage[contract_name].items():
                if isinstance(v, dict) and 'deposit' in k.lower():
                    deposit_var = k
                    break
            if deposit_var is None:
                deposit_var = "deposits"
                state.contract_storage[contract_name][deposit_var] = {}
            for addr, amount in deposits.items():
                state.contract_storage[contract_name][deposit_var][addr] = amount

        if total_deposits is not None:
            if contract_name not in state.contract_storage:
                state.contract_storage[contract_name] = {}
            state.contract_storage[contract_name]["totalDeposits"] = total_deposits

        return state
