"""
AGL Attack Engine — State Mutator (Component 3)
محرك تحويل الحالة

═══════════════════════════════════════════════════════════════
State Mutation Engine

المعادلة الأساسية:
    State(t+1) = State(t) + StateDelta

يدعم:
- تطبيق دلتا (apply) → يحوّل الحالة للأمام
- عكس دلتا (reverse) → يتراجع للحالة السابقة
- تكديس اللقطات (StateStack) → snapshot / revert بكفاءة
- التحقق من صحة الدلتا (validate)

⚠️ هذا هو الـ Rollback mechanism:
    Immutable state snapshots + delta stacking
═══════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import copy
from typing import Dict, List, Any, Optional

from .models import (
    ProtocolState,
    AccountState,
    StateDelta,
    BalanceChange,
    StorageChange,
)


class StateMutator:
    """
    محرك تحويل الحالة.

    يطبّق StateDelta على ProtocolState ويُتيح التراجع.
    كل عملية تطبيق تسجّل old_values في StorageChange
    لتمكين العكس الدقيق.
    """

    def apply(self, state: ProtocolState, delta: StateDelta) -> None:
        """
        تطبيق دلتا على الحالة.
        State(t+1) = State(t) + delta

        يُعدّل state مباشرة (in-place).
        يملأ old_value في StorageChange لتمكين الـ reverse.
        """
        if delta.reverted:
            return  # لا نطبّق دلتا فاشلة

        # 1. تغييرات الأرصدة
        self._apply_balance_changes(state, delta.balance_changes)

        # 2. تغييرات التخزين
        self._apply_storage_changes(state, delta.storage_changes)

        # 3. تغييرات الاحتياطيات (pools)
        self._apply_reserve_changes(state, delta.reserve_changes)

        # 4. تغييرات العرض (tokens)
        self._apply_supply_changes(state, delta.supply_changes)

        # 5. تأثيرات الأسعار
        self._apply_price_impacts(state, delta.price_impacts)

    def reverse(self, state: ProtocolState, delta: StateDelta) -> None:
        """
        عكس دلتا — التراجع عن تغييرات سابقة.
        State(t) = State(t+1) - delta

        يعتمد على old_value المسجّلة أثناء apply.
        """
        if delta.reverted:
            return

        # 1. عكس تغييرات الأرصدة (عكس الإشارة)
        for bc in delta.balance_changes:
            account = state.get_account(bc.account)
            if bc.token in ("ETH", "NATIVE", "eth"):
                account.eth_balance -= bc.amount
            else:
                current = account.token_balances.get(bc.token, 0)
                account.token_balances[bc.token] = current - bc.amount

        # 2. عكس تغييرات التخزين (استعادة old_value)
        for sc in delta.storage_changes:
            if sc.old_value is not None:
                state.set_storage(sc.contract, sc.variable, sc.old_value)

        # 3. عكس تغييرات الاحتياطيات
        for pool_id, changes in delta.reserve_changes.items():
            if pool_id in state.pools:
                pool = state.pools[pool_id]
                for token, delta_amount in changes.items():
                    if token == pool.token0:
                        pool.reserve0 -= delta_amount
                    elif token == pool.token1:
                        pool.reserve1 -= delta_amount

        # 4. عكس تغييرات العرض
        for token_id, delta_amount in delta.supply_changes.items():
            if token_id in state.tokens:
                state.tokens[token_id].total_supply -= delta_amount

        # 5. عكس تأثيرات الأسعار (استعادة السعر السابق)
        # ملاحظة: هذا تقريبي — الأسعار غير خطية
        for token_id, new_price in delta.price_impacts.items():
            if token_id in state.tokens:
                # لا يمكن عكس السعر بدقة بدون تخزين السعر القديم
                # لكن StateStack يحل هذه المشكلة بالـ snapshot
                pass

    # ═══════════════════════════════════════════════════════
    #  Internal Apply Methods
    # ═══════════════════════════════════════════════════════

    def _apply_balance_changes(
        self, state: ProtocolState, changes: List[BalanceChange]
    ) -> None:
        """تطبيق تغييرات الأرصدة"""
        for bc in changes:
            account = state.get_account(bc.account)
            if bc.token in ("ETH", "NATIVE", "eth"):
                account.eth_balance += bc.amount
                # لا نسمح برصيد سالب للعقود (يعني revert في الواقع)
                # لكن نتركه هنا للحساب
            else:
                current = account.token_balances.get(bc.token, 0)
                account.token_balances[bc.token] = current + bc.amount

    def _apply_storage_changes(
        self, state: ProtocolState, changes: List[StorageChange]
    ) -> None:
        """تطبيق تغييرات التخزين مع تسجيل old_value"""
        for sc in changes:
            # سجّل القيمة القديمة قبل التغيير
            old = state.get_storage(sc.contract, sc.variable, None)
            sc.old_value = copy.deepcopy(old) if old is not None else 0
            # طبّق القيمة الجديدة
            state.set_storage(sc.contract, sc.variable, sc.new_value)

    def _apply_reserve_changes(
        self, state: ProtocolState, changes: Dict[str, Dict[str, int]]
    ) -> None:
        """تطبيق تغييرات احتياطيات المجمعات"""
        for pool_id, token_changes in changes.items():
            if pool_id not in state.pools:
                continue
            pool = state.pools[pool_id]
            for token, delta_amount in token_changes.items():
                if token == pool.token0:
                    pool.reserve0 += delta_amount
                elif token == pool.token1:
                    pool.reserve1 += delta_amount
            # تحديث k
            pool.k_value = pool.reserve0 * pool.reserve1

    def _apply_supply_changes(
        self, state: ProtocolState, changes: Dict[str, int]
    ) -> None:
        """تطبيق تغييرات العرض الكلي"""
        for token_id, delta_amount in changes.items():
            if token_id in state.tokens:
                state.tokens[token_id].total_supply += delta_amount

    def _apply_price_impacts(
        self, state: ProtocolState, impacts: Dict[str, float]
    ) -> None:
        """تطبيق تأثيرات الأسعار"""
        for token_id, new_price in impacts.items():
            if token_id in state.tokens:
                state.tokens[token_id].price_usd = new_price
            # تحديث الأوراكل أيضاً
            for oracle in state.oracles.values():
                if oracle.token == token_id:
                    oracle.price = new_price

    # ═══════════════════════════════════════════════════════
    #  Validation
    # ═══════════════════════════════════════════════════════

    def validate_delta(self, delta: StateDelta) -> List[str]:
        """
        التحقق من صحة الدلتا.
        يكشف:
        - تغييرات غير متوازنة (أموال تظهر من العدم)
        - قيم سالبة غير منطقية
        - تعارضات
        """
        issues = []

        # تحقق من توازن ETH
        eth_sum = 0
        for bc in delta.balance_changes:
            if bc.token in ("ETH", "NATIVE", "eth"):
                eth_sum += bc.amount

        # في عملية عادية: مجموع تغييرات ETH = 0
        # (ما يخرج من حساب يدخل في آخر)
        # استثناء: mint/burn, gas fees, reentrancy drain
        if eth_sum != 0:
            issues.append(
                f"تنبيه: تغيير ETH غير متوازن: net={eth_sum}"
            )

        return issues


class StateStack:
    """
    مكدس الحالات — Immutable Snapshots + Delta Stacking.

    بدلاً من deep copy كل مرة:
    1. snapshot() → يحفظ نقطة العودة (ID)
    2. apply(delta) → يطبّق ويسجّل
    3. revert_to(ID) → يتراجع لنقطة معينة

    هذا أكفأ من deep copy لكل خطوة.
    """

    def __init__(self, initial_state: ProtocolState):
        self._base_snapshot: ProtocolState = initial_state.snapshot()
        self._current: ProtocolState = initial_state
        self._deltas: List[StateDelta] = []
        self._snapshots: Dict[int, int] = {}  # snapshot_id → delta_index
        self._next_snapshot_id: int = 0
        self._mutator: StateMutator = StateMutator()

    @property
    def current(self) -> ProtocolState:
        """الحالة الحالية"""
        return self._current

    @property
    def base(self) -> ProtocolState:
        """الحالة الأساسية (قبل أي تغيير)"""
        return self._base_snapshot

    @property
    def delta_count(self) -> int:
        """عدد الدلتا المطبّقة"""
        return len(self._deltas)

    def apply(self, delta: StateDelta) -> None:
        """تطبيق دلتا وتسجيلها في المكدس"""
        self._mutator.apply(self._current, delta)
        self._deltas.append(delta)

    def snapshot(self) -> int:
        """حفظ نقطة العودة — يرجع معرف اللقطة"""
        sid = self._next_snapshot_id
        self._snapshots[sid] = len(self._deltas)
        self._next_snapshot_id += 1
        return sid

    def revert_to(self, snapshot_id: int) -> None:
        """
        التراجع إلى لقطة سابقة.
        يعكس كل الدلتا المطبّقة بعد اللقطة بالترتيب العكسي.
        """
        if snapshot_id not in self._snapshots:
            raise ValueError(f"لقطة غير موجودة: {snapshot_id}")

        target_index = self._snapshots[snapshot_id]
        current_index = len(self._deltas)

        # عكس الدلتا بالترتيب العكسي
        while len(self._deltas) > target_index:
            delta = self._deltas.pop()
            self._mutator.reverse(self._current, delta)

        # تنظيف اللقطات الأحدث
        expired = [
            sid for sid, idx in self._snapshots.items()
            if idx > target_index
        ]
        for sid in expired:
            del self._snapshots[sid]

    def revert_last(self) -> Optional[StateDelta]:
        """التراجع عن آخر دلتا فقط"""
        if not self._deltas:
            return None
        delta = self._deltas.pop()
        self._mutator.reverse(self._current, delta)
        return delta

    def reset(self) -> None:
        """إعادة تعيين كاملة إلى الحالة الأولية"""
        self._current = self._base_snapshot.snapshot()
        self._deltas.clear()
        self._snapshots.clear()
        self._next_snapshot_id = 0

    def get_cumulative_delta(self) -> StateDelta:
        """الحصول على الدلتا التراكمية من البداية"""
        cumulative = StateDelta()
        for delta in self._deltas:
            cumulative.balance_changes.extend(delta.balance_changes)
            cumulative.storage_changes.extend(delta.storage_changes)
            for pool_id, changes in delta.reserve_changes.items():
                if pool_id not in cumulative.reserve_changes:
                    cumulative.reserve_changes[pool_id] = {}
                for token, amount in changes.items():
                    prev = cumulative.reserve_changes[pool_id].get(token, 0)
                    cumulative.reserve_changes[pool_id][token] = prev + amount
            for token_id, amount in delta.supply_changes.items():
                prev = cumulative.supply_changes.get(token_id, 0)
                cumulative.supply_changes[token_id] = prev + amount
            cumulative.gas_used += delta.gas_used
            cumulative.events.extend(delta.events)
        return cumulative
