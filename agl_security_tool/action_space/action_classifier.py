"""
AGL Action Space — Action Classifier
تصنيف الأفعال حسب نوع الهجوم المحتمل

التصنيف ثلاثي:
1. ActionCategory — فئة وظيفية (deposit, withdraw, borrow, ...)
2. AttackType — نوع الهجوم المحتمل (reentrancy, flash_loan, ...)
3. severity + profit_potential — تقييم الخطورة والربحية

يعتمد على بيانات Layer 1 (CEI violations, net_delta, external_calls)
+ تحليل اسم الدالة وأنماطها.
"""

from __future__ import annotations

import re
from typing import Dict, List, Any, Optional

from .models import Action, ActionCategory, AttackType


# ═══════════════════════════════════════════════════════════════
#  أنماط تصنيف الدوال
# ═══════════════════════════════════════════════════════════════

_CATEGORY_PATTERNS: Dict[ActionCategory, List[str]] = {
    ActionCategory.FUND_INFLOW: [
        "deposit", "supply", "addLiquidity", "provide", "fund",
        "receive", "contribute", "pay",
    ],
    ActionCategory.FUND_OUTFLOW: [
        "withdraw", "redeem", "removeLiquidity", "drain", "pull",
    ],
    ActionCategory.BORROW: [
        "borrow", "flashLoan", "flashBorrow", "leverage",
    ],
    ActionCategory.REPAY: [
        "repay", "payBack", "close", "settle",
    ],
    ActionCategory.SWAP: [
        "swap", "exchange", "trade", "convert",
    ],
    ActionCategory.LIQUIDATE: [
        "liquidate", "liquidation", "seize", "auction",
    ],
    ActionCategory.STAKE: [
        "stake", "delegate", "lock", "bond",
    ],
    ActionCategory.UNSTAKE: [
        "unstake", "undelegate", "unlock", "unbond",
    ],
    ActionCategory.CLAIM: [
        "claim", "harvest", "collect", "getReward",
    ],
    ActionCategory.GOVERNANCE_VOTE: [
        "vote", "propose", "castVote", "queue", "execute",
    ],
    ActionCategory.ADMIN: [
        "setOwner", "transferOwnership", "setAdmin", "pause", "unpause",
        "setFee", "setParameter", "updateConfig", "upgrade", "initialize",
    ],
    ActionCategory.ORACLE_UPDATE: [
        "updatePrice", "setPrice", "updateOracle", "submitAnswer",
    ],
    ActionCategory.FLASH_LOAN: [
        "flashLoan", "flash", "flashBorrow",
    ],
    ActionCategory.APPROVAL: [
        "approve", "setApproval", "increaseAllowance", "decreaseAllowance",
        "permit",
    ],
}


class ActionClassifier:
    """
    يصنف كل Action بناءً على:
    1. اسم الدالة → ActionCategory
    2. بيانات Layer 1 (CEI, external_calls, net_delta) → AttackType
    3. الخطورة والربحية
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def classify(self, actions: List[Action]) -> List[Action]:
        """
        تصنيف كل Action في القائمة.

        Args:
            actions: قائمة الأفعال

        Returns:
            نفس القائمة مع category, attack_types, severity, profit_potential
        """
        for action in actions:
            # 1. تصنيف الفئة
            action.category = self._classify_category(action)

            # 2. تصنيف أنماط الهجوم
            action.attack_types = self._classify_attack_types(action)

            # 3. تقييم الخطورة
            action.severity = self._assess_severity(action)

            # 4. تقييم الربحية
            action.profit_potential = self._assess_profit(action)
            action.is_profitable = action.profit_potential in ("high", "medium")

        return actions

    # ═══════════════════════════════════════════════════════════
    #  1. Category Classification
    # ═══════════════════════════════════════════════════════════

    def _classify_category(self, action: Action) -> ActionCategory:
        """تصنيف الفئة الوظيفية"""
        name = action.function_name.lower()

        # تحقق من الأنماط المعروفة
        for category, patterns in _CATEGORY_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in name:
                    return category

        # تصنيف بناءً على التأثير
        if action.sends_eth and action.state_writes:
            return ActionCategory.FUND_OUTFLOW

        if action.mutability == "payable":
            return ActionCategory.FUND_INFLOW

        if action.state_writes and not action.external_calls:
            return ActionCategory.STATE_CHANGE

        if not action.state_writes and action.mutability in ("view", "pure"):
            return ActionCategory.VIEW

        if action.state_writes:
            return ActionCategory.STATE_CHANGE

        return ActionCategory.UNKNOWN

    # ═══════════════════════════════════════════════════════════
    #  2. Attack Type Classification
    # ═══════════════════════════════════════════════════════════

    def _classify_attack_types(self, action: Action) -> List[AttackType]:
        """كشف أنماط الهجوم المحتملة بناء على بيانات Layer 1"""
        attacks = []

        # === Reentrancy ===
        if action.has_cei_violation and not action.reentrancy_guarded:
            attacks.append(AttackType.REENTRANCY)

        # === Cross-function ===
        if action.cross_function_risk and action.reentrancy_window:
            attacks.append(AttackType.CROSS_FUNCTION)

        # === Direct Profit ===
        if self._is_direct_profit(action):
            attacks.append(AttackType.DIRECT_PROFIT)

        # === State Manipulation ===
        if self._is_state_manipulation(action):
            attacks.append(AttackType.STATE_MANIPULATION)

        # === Flash Loan ===
        if action.category == ActionCategory.FLASH_LOAN:
            attacks.append(AttackType.FLASH_LOAN)
        elif self._could_use_flash_loan(action):
            attacks.append(AttackType.FLASH_LOAN)

        # === Price Manipulation ===
        if self._is_price_manipulation(action):
            attacks.append(AttackType.PRICE_MANIPULATION)

        # === Liquidation ===
        if action.category == ActionCategory.LIQUIDATE:
            attacks.append(AttackType.LIQUIDATION)

        # === Access Escalation ===
        if self._is_access_escalation(action):
            attacks.append(AttackType.ACCESS_ESCALATION)

        # === Governance ===
        if action.category == ActionCategory.GOVERNANCE_VOTE:
            attacks.append(AttackType.GOVERNANCE)

        # === Front-Running ===
        if self._is_front_runnable(action):
            attacks.append(AttackType.FRONT_RUNNING)

        # === Donation Attack ===
        if self._is_donation_attack(action):
            attacks.append(AttackType.DONATION)

        # === Griefing ===
        if self._is_griefing(action):
            attacks.append(AttackType.GRIEFING)

        return attacks

    def _is_direct_profit(self, action: Action) -> bool:
        """هل يمكن تحقيق ربح مباشر"""
        # سحب أو تصفية أو مطالبة بدون access control
        if action.category in (
            ActionCategory.FUND_OUTFLOW,
            ActionCategory.LIQUIDATE,
            ActionCategory.CLAIM,
        ) and not action.requires_access:
            return True
        # يرسل ETH بدون شروط صعبة
        if action.sends_eth and not action.requires_access and action.is_valid:
            return True
        return False

    def _is_state_manipulation(self, action: Action) -> bool:
        """هل تؤثر على δState بطريقة قد تخلق فرص"""
        if not action.state_writes:
            return False
        # تكتب variables حساسة
        sensitive_vars = {"balance", "reserve", "price", "rate", "supply", "debt", "collateral"}
        for var in action.state_writes:
            if any(k in var.lower() for k in sensitive_vars):
                return True
        return False

    def _could_use_flash_loan(self, action: Action) -> bool:
        """هل يمكن استخدام flash loan لتضخيم هذا الـ Action"""
        # إذا الدالة تعتمد على مبلغ كبير + ليست payable
        name_lower = action.function_name.lower()
        if any(k in name_lower for k in ("liquidat", "swap", "borrow")):
            return True
        # إذا المعاملات تتضمن مبالغ كبيرة
        for p in action.parameters:
            if p.is_amount:
                return True
        return False

    def _is_price_manipulation(self, action: Action) -> bool:
        """هل يمكن تلاعب بالسعر"""
        name_lower = action.function_name.lower()
        if any(k in name_lower for k in ("price", "oracle", "update", "twap")):
            return True
        # إذا تكتب price-related vars
        for var in action.state_writes:
            if any(k in var.lower() for k in ("price", "rate", "oracle", "reserve")):
                return True
        return False

    def _is_access_escalation(self, action: Action) -> bool:
        """هل يمكن تجاوز صلاحيات"""
        if action.has_delegatecall and not action.requires_access:
            return True
        name_lower = action.function_name.lower()
        if any(k in name_lower for k in (
            "initialize", "init", "setup",
        )) and not action.requires_access:
            return True
        return False

    def _is_front_runnable(self, action: Action) -> bool:
        """هل يمكن front-running"""
        # الدوال التي تعتمد على ترتيب المعاملات
        name_lower = action.function_name.lower()
        if any(k in name_lower for k in (
            "swap", "liquidat", "approve", "permit",
        )):
            return not action.requires_access
        return False

    def _is_donation_attack(self, action: Action) -> bool:
        """هل يمكن هجوم تبرع (vault inflation)"""
        name_lower = action.function_name.lower()
        if "deposit" in name_lower and action.mutability == "payable":
            # إذا الكود يكتب share/supply vars
            for var in action.state_writes:
                if any(k in var.lower() for k in ("share", "supply", "totalasset")):
                    return True
        return False

    def _is_griefing(self, action: Action) -> bool:
        """هل يمكن إيذاء بدون ربح (gas griefing, DoS)"""
        # استدعاء loops أو unbounded operations
        if action.has_cei_violation and action.reentrancy_guarded:
            return False  # محمي
        # إذا sends ETH في loop
        for ext in action.external_calls:
            if ext.get("sends_eth") and action.reentrancy_window:
                return True
        return False

    # ═══════════════════════════════════════════════════════════
    #  3. Severity Assessment
    # ═══════════════════════════════════════════════════════════

    def _assess_severity(self, action: Action) -> str:
        """تقييم خطورة الـ Action"""
        if not action.attack_types:
            return "info"

        # Critical
        if AttackType.REENTRANCY in action.attack_types and action.sends_eth:
            return "critical"
        if AttackType.ACCESS_ESCALATION in action.attack_types:
            return "critical"
        if action.has_delegatecall and not action.requires_access:
            return "critical"

        # High
        if AttackType.REENTRANCY in action.attack_types:
            return "high"
        if AttackType.CROSS_FUNCTION in action.attack_types:
            return "high"
        if AttackType.DIRECT_PROFIT in action.attack_types and action.sends_eth:
            return "high"
        if AttackType.FLASH_LOAN in action.attack_types and AttackType.PRICE_MANIPULATION in action.attack_types:
            return "high"

        # Medium
        if AttackType.PRICE_MANIPULATION in action.attack_types:
            return "medium"
        if AttackType.STATE_MANIPULATION in action.attack_types:
            return "medium"
        if AttackType.FRONT_RUNNING in action.attack_types:
            return "medium"
        if AttackType.DONATION in action.attack_types:
            return "medium"

        # Low
        if AttackType.GRIEFING in action.attack_types:
            return "low"
        if AttackType.DIRECT_PROFIT in action.attack_types:
            return "low"

        return "info"

    # ═══════════════════════════════════════════════════════════
    #  4. Profit Assessment
    # ═══════════════════════════════════════════════════════════

    def _assess_profit(self, action: Action) -> str:
        """تقييم إمكانية الربح"""
        if not action.is_valid:
            return "none"

        # High profit
        if action.sends_eth and action.has_cei_violation:
            return "high"
        if action.category in (ActionCategory.LIQUIDATE, ActionCategory.FLASH_LOAN):
            return "high"
        if AttackType.REENTRANCY in action.attack_types and action.sends_eth:
            return "high"

        # Medium profit
        if AttackType.DIRECT_PROFIT in action.attack_types:
            return "medium"
        if action.sends_eth and not action.requires_access:
            return "medium"
        if AttackType.PRICE_MANIPULATION in action.attack_types:
            return "medium"

        # Low profit
        if action.category in (ActionCategory.CLAIM, ActionCategory.UNSTAKE):
            return "low"
        if AttackType.FRONT_RUNNING in action.attack_types:
            return "low"

        return "none"
