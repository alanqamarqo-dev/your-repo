"""
AGL Attack Engine — Economic Engine (Component 4)
محرك الأحداث الاقتصادية

═══════════════════════════════════════════════════════════════
Economic Event Engine

يحسب التأثيرات الاقتصادية التي لا تأتي من تنفيذ كود مباشرة:
- تأثير السعر (Price Impact) عند swap كبير
- انزلاق السعر (Slippage)
- تراكم الفوائد (Interest Accrual)
- رسوم القروض الفلاشية (Flash Loan Fees)
- مكافأة التصفية (Liquidation Bonus)
- التلاعب بالأوراكل (Oracle Manipulation)

هذا يُمكّن المحرك من حساب:
    Profit = drain - gas - flash_loan_fee - slippage
═══════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import math
from typing import Dict, List, Any, Optional

from .models import (
    ProtocolState,
    StateDelta,
    BalanceChange,
    StorageChange,
    SimulationConfig,
    PoolState,
    LendingState,
)


WEI_PER_ETH = 10 ** 18


class EconomicEngine:
    """
    محرك الفيزياء الاقتصادية.

    يحسب التأثيرات الاقتصادية للعمليات المالية:
    - كل الحسابات بالـ wei (أعداد صحيحة)
    - الأسعار بالـ USD (أعداد عشرية)
    """

    def __init__(self, config: Optional[SimulationConfig] = None):
        self.config = config or SimulationConfig()

    # ═══════════════════════════════════════════════════════
    #  Price Impact — تأثير السعر
    # ═══════════════════════════════════════════════════════

    def compute_price_impact(
        self,
        pool: PoolState,
        amount_in: int,
        token_in: str,
    ) -> Dict[str, Any]:
        """
        حساب تأثير swap على سعر المجمع.

        CPMM: x * y = k
        - سعر قبل: reserve1 / reserve0
        - كمية الخروج: (amount_in * reserve_out) / (reserve_in + amount_in)
        - سعر بعد: new_reserve1 / new_reserve0
        - price_impact = (price_after - price_before) / price_before
        """
        if amount_in <= 0 or pool.reserve0 <= 0 or pool.reserve1 <= 0:
            return {
                "amount_out": 0,
                "price_before": 0.0,
                "price_after": 0.0,
                "price_impact_pct": 0.0,
                "slippage_pct": 0.0,
            }

        # تحديد الاحتياطيات
        if token_in == pool.token0:
            r_in, r_out = pool.reserve0, pool.reserve1
        else:
            r_in, r_out = pool.reserve1, pool.reserve0

        # الرسوم
        fee = amount_in * pool.fee_bps // 10000
        amount_after_fee = amount_in - fee

        # CPMM formula
        amount_out = (amount_after_fee * r_out) // (r_in + amount_after_fee)

        # الأسعار
        price_before = r_out / r_in if r_in > 0 else 0
        new_r_in = r_in + amount_in
        new_r_out = r_out - amount_out
        price_after = new_r_out / new_r_in if new_r_in > 0 else 0

        # تأثير السعر
        price_impact = 0.0
        if price_before > 0:
            price_impact = abs(price_after - price_before) / price_before

        # الانزلاق: الفرق بين السعر المتوقع والفعلي
        expected_out = amount_after_fee * r_out // r_in if r_in > 0 else 0
        slippage = 0.0
        if expected_out > 0:
            slippage = (expected_out - amount_out) / expected_out

        return {
            "amount_out": amount_out,
            "fee_paid": fee,
            "price_before": price_before,
            "price_after": price_after,
            "price_impact_pct": round(price_impact * 100, 4),
            "slippage_pct": round(slippage * 100, 4),
            "new_reserve_in": new_r_in,
            "new_reserve_out": new_r_out,
        }

    # ═══════════════════════════════════════════════════════
    #  Flash Loan Fee — رسوم القروض الفلاشية
    # ═══════════════════════════════════════════════════════

    def compute_flash_loan_fee(
        self,
        amount: int,
        fee_bps: Optional[int] = None,
    ) -> int:
        """
        حساب رسوم القرض الفلاشي.

        Aave V3: 0.09% = 9 bps
        dYdX: 0 (مجاني)
        Uniswap V3: 0.3% = 30 bps
        """
        bps = fee_bps if fee_bps is not None else self.config.flash_loan_fee_bps
        return amount * bps // 10000

    def compute_flash_loan_delta(
        self,
        borrower: str,
        lender: str,
        token: str,
        amount: int,
        fee_bps: Optional[int] = None,
    ) -> StateDelta:
        """
        إنشاء StateDelta للقرض الفلاشي.

        الخطوة 1 (بداية): المهاجم يستلم amount
        الخطوة الأخيرة (نهاية): المهاجم يسدد amount + fee
        """
        fee = self.compute_flash_loan_fee(amount, fee_bps)

        delta = StateDelta()

        # استلام القرض
        delta.balance_changes.append(BalanceChange(
            account=borrower,
            token=token,
            amount=amount,
            reason="flash_loan_borrow",
        ))
        delta.balance_changes.append(BalanceChange(
            account=lender,
            token=token,
            amount=-amount,
            reason="flash_loan_lend",
        ))

        delta.events.append(
            f"FLASH_LOAN: {borrower} borrows {amount} {token} from {lender} (fee: {fee})"
        )

        return delta

    def compute_flash_loan_repay_delta(
        self,
        borrower: str,
        lender: str,
        token: str,
        amount: int,
        fee_bps: Optional[int] = None,
    ) -> StateDelta:
        """StateDelta لسداد القرض الفلاشي"""
        fee = self.compute_flash_loan_fee(amount, fee_bps)
        repay = amount + fee

        delta = StateDelta()

        # سداد القرض + الرسوم
        delta.balance_changes.append(BalanceChange(
            account=borrower,
            token=token,
            amount=-repay,
            reason="flash_loan_repay",
        ))
        delta.balance_changes.append(BalanceChange(
            account=lender,
            token=token,
            amount=repay,
            reason="flash_loan_receive_repay",
        ))

        delta.events.append(
            f"FLASH_LOAN_REPAY: {borrower} repays {repay} {token} ({amount} + {fee} fee)"
        )

        return delta

    # ═══════════════════════════════════════════════════════
    #  Interest Accrual — تراكم الفوائد
    # ═══════════════════════════════════════════════════════

    def compute_interest_accrual(
        self,
        market: LendingState,
        blocks_elapsed: int,
    ) -> StateDelta:
        """
        حساب الفوائد المتراكمة.

        interest = total_borrows * rate * blocks / blocks_per_year
        """
        if market.total_borrows <= 0 or market.interest_rate_bps <= 0:
            return StateDelta()

        # ~2_628_000 blocks/year (12s per block)
        blocks_per_year = 2_628_000
        interest = (
            market.total_borrows
            * market.interest_rate_bps
            * blocks_elapsed
            // (10000 * blocks_per_year)
        )

        delta = StateDelta()
        if interest > 0:
            # الفائدة تُضاف على الديون والإيداعات
            delta.storage_changes.append(StorageChange(
                contract=market.market,
                variable="totalBorrows",
                new_value=market.total_borrows + interest,
            ))
            delta.events.append(
                f"INTEREST: {interest} accrued on {market.market} "
                f"({blocks_elapsed} blocks)"
            )

        return delta

    # ═══════════════════════════════════════════════════════
    #  Liquidation — التصفية
    # ═══════════════════════════════════════════════════════

    def compute_liquidation_profit(
        self,
        market: LendingState,
        borrower: str,
        debt_to_repay: int,
        state: ProtocolState,
    ) -> Dict[str, Any]:
        """
        حساب ربح التصفية.

        المُصفّي يسدد جزء من الدين ويحصل على ضمان + مكافأة.
        bonus = debt_repaid * (1 + liquidation_bonus)
        profit = bonus - debt_repaid
        """
        bonus_bps = market.liquidation_bonus_bps or self.config.liquidation_bonus_bps

        # الضمان المحصول عليه
        collateral_received = debt_to_repay * (10000 + bonus_bps) // 10000
        profit = collateral_received - debt_to_repay

        return {
            "debt_repaid": debt_to_repay,
            "collateral_received": collateral_received,
            "bonus_bps": bonus_bps,
            "profit": profit,
            "profit_pct": round(bonus_bps / 100, 2),
        }

    # ═══════════════════════════════════════════════════════
    #  Oracle Manipulation — التلاعب بالأوراكل
    # ═══════════════════════════════════════════════════════

    def compute_oracle_manipulation_impact(
        self,
        pool: PoolState,
        manipulation_amount: int,
        token_manipulated: str,
        state: ProtocolState,
    ) -> Dict[str, Any]:
        """
        حساب تأثير التلاعب بالأوراكل عبر swap كبير.

        1. Swap كبير → يغيّر السعر في المجمع
        2. الأوراكل يقرأ السعر الجديد
        3. البروتوكولات تعتمد على السعر الخاطئ
        """
        impact = self.compute_price_impact(
            pool, manipulation_amount, token_manipulated
        )

        # حجم التلاعب
        manip_pct = impact["price_impact_pct"]

        return {
            "price_before": impact["price_before"],
            "price_after": impact["price_after"],
            "manipulation_pct": manip_pct,
            "swap_cost": manipulation_amount,
            "slippage_cost": impact.get("slippage_pct", 0),
            "is_significant": manip_pct > 1.0,  # > 1% يعتبر مهم
        }

    # ═══════════════════════════════════════════════════════
    #  Gas Cost — تكلفة الغاز
    # ═══════════════════════════════════════════════════════

    def compute_gas_cost(
        self,
        gas_used: int,
        state: ProtocolState,
    ) -> Dict[str, Any]:
        """حساب تكلفة الغاز بالـ wei و USD"""
        gas_cost_wei = gas_used * state.gas_price_wei
        gas_cost_usd = (gas_cost_wei / WEI_PER_ETH) * state.eth_price_usd

        return {
            "gas_used": gas_used,
            "gas_price_wei": state.gas_price_wei,
            "gas_cost_wei": gas_cost_wei,
            "gas_cost_eth": gas_cost_wei / WEI_PER_ETH,
            "gas_cost_usd": round(gas_cost_usd, 4),
        }

    # ═══════════════════════════════════════════════════════
    #  Value Conversion — تحويل القيمة
    # ═══════════════════════════════════════════════════════

    def token_to_usd(
        self,
        token: str,
        amount_wei: int,
        state: ProtocolState,
        decimals: int = 18,
    ) -> float:
        """تحويل كمية توكن إلى USD"""
        price = state.get_token_price(token)
        if price <= 0:
            return 0.0
        amount_normalized = amount_wei / (10 ** decimals)
        return amount_normalized * price

    def usd_to_token(
        self,
        token: str,
        usd_amount: float,
        state: ProtocolState,
        decimals: int = 18,
    ) -> int:
        """تحويل USD إلى كمية توكن"""
        price = state.get_token_price(token)
        if price <= 0:
            return 0
        amount_normalized = usd_amount / price
        return int(amount_normalized * (10 ** decimals))
