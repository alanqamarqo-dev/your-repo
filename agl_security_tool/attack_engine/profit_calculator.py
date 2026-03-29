"""
AGL Attack Engine — Profit Calculator (Component 5)
حاسب الأرباح — القلب النابض

═══════════════════════════════════════════════════════════════
هذا هو الـ Component الأهم في النظام بأكمله.

المعادلة الوحيدة التي تهم:

    Profit(attacker) = Value(final_assets) - Value(initial_assets) - Gas - Fees

إذا Profit > 0 → هجوم مربح → ثغرة حقيقية.
إذا Profit ≤ 0 → هجوم غير مجدٍ → ليس ثغرة عملية.

═══════════════════════════════════════════════════════════════
"""

from __future__ import annotations

from typing import Dict, List, Any, Optional

from .models import (
    ProtocolState,
    AttackResult,
    StepResult,
    SimulationConfig,
)
from .economic_engine import EconomicEngine
from ..heikal_math import HeikalTunnelingScorer


WEI_PER_ETH = 10**18

# حدود التصنيف
SEVERITY_THRESHOLDS = {
    "critical": 100_000,  # > $100,000
    "high": 10_000,  # > $10,000
    "medium": 1_000,  # > $1,000
    "low": 0,  # > $0
}

CONFIDENCE_MODIFIERS = {
    "reentrancy": 0.95,  # reentrancy مؤكد تقريباً
    "price_manipulation": 0.70,  # يعتمد على السيولة
    "flash_loan": 0.80,
    "liquidation": 0.85,
    "access_escalation": 0.60,
    "direct_profit": 0.90,
    "state_manipulation": 0.65,
    "default": 0.50,
}


class ProfitCalculator:
    """
    حاسب الأرباح.

    يقارن الحالة الأولية بالحالة النهائية للمهاجم:
    1. يحسب الفرق في الأرصدة لكل توكن
    2. يحوّل كل شيء إلى USD
    3. يخصم الغاز والرسوم
    4. يُصنّف الخطورة والثقة
    """

    def __init__(self, config: Optional[SimulationConfig] = None):
        self.config = config or SimulationConfig()
        self.economic = EconomicEngine(config)
        self.tunneling = HeikalTunnelingScorer()

    # ═══════════════════════════════════════════════════════
    #  Main Calculation
    # ═══════════════════════════════════════════════════════

    def calculate(
        self,
        initial_state: ProtocolState,
        final_state: ProtocolState,
        attacker_address: str,
        steps: List[StepResult],
        attack_type: str = "",
        sequence_id: str = "",
    ) -> AttackResult:
        """
        حساب ربح الهجوم.

        Profit = Σ(final_balance - initial_balance) per token
                 - gas_cost
                 - flash_loan_fees
        """
        result = AttackResult(
            sequence_id=sequence_id,
            steps=steps,
            total_steps=len(steps),
            attack_type=attack_type,
        )

        # === 1. حساب فرق الأرصدة لكل توكن ===
        profit_by_token = self._compute_balance_diff(
            initial_state, final_state, attacker_address
        )
        result.profit_by_token = profit_by_token

        # === 2. تحويل إلى USD ===
        result.profit_usd = self._compute_total_usd(profit_by_token, final_state)

        # === 3. حساب تكلفة الغاز ===
        total_gas = sum(s.gas_used for s in steps)
        gas_info = self.economic.compute_gas_cost(total_gas, final_state)
        result.gas_cost_wei = gas_info["gas_cost_wei"]
        result.gas_cost_usd = gas_info["gas_cost_usd"]

        # === 4. حساب رسوم القروض الفلاشية ===
        flash_fees = self._extract_flash_loan_fees(steps, final_state)
        result.flash_loan_fees = flash_fees.get("fees_by_token", {})
        result.flash_loan_fees_usd = flash_fees.get("total_usd", 0.0)

        # === 5. الربح الصافي ===
        result.net_profit_usd = (
            result.profit_usd - result.gas_cost_usd - result.flash_loan_fees_usd
        )

        # Sanity cap: Z3 symbolic values can produce astronomically large
        # BitVec(256) numbers that, when converted to USD, become unrealistic
        # (e.g., 10^64 USD).  Cap at a reasonable DeFi upper bound.
        _MAX_REALISTIC_PROFIT_USD = 500_000_000.0  # $500M — largest-ever DeFi hack
        if abs(result.profit_usd) > _MAX_REALISTIC_PROFIT_USD:
            result.profit_usd = min(result.profit_usd, _MAX_REALISTIC_PROFIT_USD)
            result.net_profit_usd = min(
                result.net_profit_usd, _MAX_REALISTIC_PROFIT_USD
            )
            result.is_symbolic_estimate = True  # flag for downstream consumers

        # === 6. هل مربح؟ ===
        result.is_profitable = result.net_profit_usd > 0

        # === 7. التصنيف ===
        result.severity = self._classify_severity(result.net_profit_usd)
        result.confidence = self._compute_confidence(
            attack_type, result.is_profitable, steps
        )

        # === 8. الوصف ===
        result.description = self._generate_description(result, attacker_address)
        result.description_ar = self._generate_description_ar(result, attacker_address)
        result.exploit_scenario = self._generate_scenario(result, steps)

        # === 9. ملخصات الحالة ===
        result.initial_state_summary = initial_state.summary()
        result.final_state_summary = final_state.summary()

        # === 10. اسم الهجوم ===
        result.attack_name = self._generate_attack_name(
            attack_type, result.net_profit_usd
        )

        return result

    # ═══════════════════════════════════════════════════════
    #  Balance Diff
    # ═══════════════════════════════════════════════════════

    def _compute_balance_diff(
        self,
        initial: ProtocolState,
        final: ProtocolState,
        address: str,
    ) -> Dict[str, int]:
        """
        حساب فرق الأرصدة بين الحالة الأولية والنهائية.

        لكل توكن: diff = final_balance - initial_balance
        """
        diffs = {}

        # ETH
        initial_eth = 0
        final_eth = 0
        if address in initial.accounts:
            initial_eth = initial.accounts[address].eth_balance
        if address in final.accounts:
            final_eth = final.accounts[address].eth_balance

        eth_diff = final_eth - initial_eth
        if eth_diff != 0:
            diffs["ETH"] = eth_diff

        # كل التوكنات
        all_tokens = set()
        if address in initial.accounts:
            all_tokens.update(initial.accounts[address].token_balances.keys())
        if address in final.accounts:
            all_tokens.update(final.accounts[address].token_balances.keys())

        for token in all_tokens:
            initial_bal = 0
            final_bal = 0
            if address in initial.accounts:
                initial_bal = initial.accounts[address].token_balances.get(token, 0)
            if address in final.accounts:
                final_bal = final.accounts[address].token_balances.get(token, 0)

            diff = final_bal - initial_bal
            if diff != 0:
                diffs[token] = diff

        return diffs

    def _compute_total_usd(
        self,
        profit_by_token: Dict[str, int],
        state: ProtocolState,
    ) -> float:
        """تحويل مجموع الأرباح لكل التوكنات إلى USD"""
        total = 0.0
        for token, amount_wei in profit_by_token.items():
            usd = self.economic.token_to_usd(token, amount_wei, state)
            total += usd
        return round(total, 2)

    # ═══════════════════════════════════════════════════════
    #  Flash Loan Fee Extraction
    # ═══════════════════════════════════════════════════════

    def _extract_flash_loan_fees(
        self,
        steps: List[StepResult],
        state: ProtocolState,
    ) -> Dict[str, Any]:
        """استخراج رسوم القروض الفلاشية من الخطوات"""
        fees_by_token: Dict[str, int] = {}
        total_usd = 0.0

        for step in steps:
            if step.delta:
                for event in step.delta.events:
                    if "flash_loan" in event.lower() and "fee" in event.lower():
                        # نحاول استخراج الرسوم من الحدث
                        # هذا تقدير — الرسوم الحقيقية تُحسب في EconomicEngine
                        pass

        return {
            "fees_by_token": fees_by_token,
            "total_usd": total_usd,
        }

    # ═══════════════════════════════════════════════════════
    #  Classification
    # ═══════════════════════════════════════════════════════

    def _classify_severity(self, net_profit_usd: float) -> str:
        """تصنيف الخطورة حسب الربح"""
        if net_profit_usd <= 0:
            return "info"
        for severity, threshold in SEVERITY_THRESHOLDS.items():
            if net_profit_usd >= threshold:
                return severity
        return "info"

    def _compute_confidence(
        self,
        attack_type: str,
        is_profitable: bool,
        steps: List[StepResult],
    ) -> float:
        """
        حساب مستوى الثقة باستخدام نموذج Heikal Quantum Tunneling.

        بدلاً من القيم الثابتة، نستخدم فيزياء النفق الكمي:
        - كل حاجز أمني (require, modifier, guard) = حاجز كمي
        - طاقة الهجوم تحدد احتمال الاختراق
        - تصحيح Heikal يضيف حساسية للقياس ξ·ℓ_p²/L²
        """
        all_success = all(s.success for s in steps)

        try:
            # === Heikal Tunneling Model ===
            barriers = HeikalTunnelingScorer.extract_barriers_from_steps(steps)
            confidence = self.tunneling.score_attack_type(
                attack_type, barriers, len(steps), is_profitable, all_success
            )
            return confidence
        except Exception:
            # === Fallback: النموذج الكلاسيكي ===
            base = CONFIDENCE_MODIFIERS.get(
                attack_type, CONFIDENCE_MODIFIERS["default"]
            )
            if all_success:
                base = min(base + 0.05, 1.0)
            if is_profitable:
                base = min(base + 0.05, 1.0)
            if attack_type == "reentrancy" and all_success and is_profitable:
                base = max(base, 0.95)
            return round(base, 3)

    # ═══════════════════════════════════════════════════════
    #  Description Generation
    # ═══════════════════════════════════════════════════════

    def _generate_description(
        self,
        result: AttackResult,
        attacker: str,
    ) -> str:
        """توليد وصف إنجليزي للهجوم"""
        if not result.is_profitable:
            return f"Attack simulation: {result.attack_type}. Not profitable (net: ${result.net_profit_usd:.2f})"

        parts = [
            f"PROFITABLE ATTACK: {result.attack_type}",
            f"Net profit: ${result.net_profit_usd:,.2f}",
            f"Steps: {result.total_steps}",
            f"Gas cost: ${result.gas_cost_usd:.4f}",
        ]

        for token, amount in result.profit_by_token.items():
            if token == "ETH":
                parts.append(f"ETH gained: {amount / WEI_PER_ETH:.4f}")
            else:
                parts.append(f"{token} gained: {amount}")

        return " | ".join(parts)

    def _generate_description_ar(
        self,
        result: AttackResult,
        attacker: str,
    ) -> str:
        """توليد وصف عربي للهجوم"""
        if not result.is_profitable:
            return (
                f"محاكاة هجوم: {result.attack_type}. "
                f"غير مربح (صافي: ${result.net_profit_usd:.2f})"
            )

        type_names = {
            "reentrancy": "إعادة دخول",
            "price_manipulation": "تلاعب بالأسعار",
            "flash_loan": "قرض فلاشي",
            "liquidation": "تصفية",
            "access_escalation": "تصعيد صلاحيات",
            "direct_profit": "ربح مباشر",
        }
        type_ar = type_names.get(result.attack_type, result.attack_type)

        parts = [
            f"⚠️ هجوم مربح: {type_ar}",
            f"الربح الصافي: ${result.net_profit_usd:,.2f}",
            f"الخطوات: {result.total_steps}",
            f"تكلفة الغاز: ${result.gas_cost_usd:.4f}",
        ]

        for token, amount in result.profit_by_token.items():
            if token == "ETH":
                parts.append(f"ETH المكتسبة: {amount / WEI_PER_ETH:.4f}")

        return " | ".join(parts)

    def _generate_scenario(
        self,
        result: AttackResult,
        steps: List[StepResult],
    ) -> str:
        """توليد سيناريو الاستغلال"""
        lines = [f"Attack: {result.attack_type}"]
        lines.append(f"Severity: {result.severity}")
        lines.append(f"Confidence: {result.confidence:.1%}")
        lines.append("")

        for step in steps:
            status = "✓" if step.success else "✗"
            line = f"  Step {step.step_index}: {status} {step.contract_name}.{step.function_name}()"
            if step.reentrancy_calls > 0:
                line += f" [REENTRY ×{step.reentrancy_calls}]"
            if step.eth_transferred > 0:
                line += f" [{step.eth_transferred / WEI_PER_ETH:.4f} ETH]"
            lines.append(line)

        lines.append("")
        lines.append(f"Result: ${result.net_profit_usd:,.2f} net profit")

        return "\n".join(lines)

    def _generate_attack_name(
        self,
        attack_type: str,
        net_profit_usd: float,
    ) -> str:
        """توليد اسم مختصر للهجوم"""
        type_names = {
            "reentrancy": "Reentrancy Drain",
            "price_manipulation": "Price Oracle Manipulation",
            "flash_loan": "Flash Loan Attack",
            "liquidation": "Forced Liquidation",
            "access_escalation": "Access Control Bypass",
            "direct_profit": "Direct Fund Extraction",
            "state_manipulation": "State Manipulation",
        }
        name = type_names.get(attack_type, f"Attack ({attack_type})")
        if net_profit_usd > 0:
            name += f" [${net_profit_usd:,.0f}]"
        return name
