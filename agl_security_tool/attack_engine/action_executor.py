"""
AGL Attack Engine — Action Executor (Component 2)
محرك التنفيذ الدلالي

═══════════════════════════════════════════════════════════════
⚠️ هذا ليس EVM Simulator ⚠️

هذا محرك تنفيذ دلالي (Semantic Execution Engine):
- لا يشغّل opcodes
- لا يحاكي EVM كاملًا
- يفهم المعنى المالي لكل دالة
- يحسب ΔState = f(action, current_state)

المدخل: ExecutableAction + ProtocolState
المخرج: StateDelta

═══════════════════════════════════════════════════════════════
نمذجة إعادة الدخول (Reentrancy):

    withdraw(amount):
        require(deposits[sender] >= amount)   ← CHECK
        sender.call{value: amount}("")        ← INTERACTION (sends ETH)
        deposits[sender] -= amount            ← EFFECT (too late!)

    في CEI violation:
    1. الفحص يمر (deposits[sender] >= amount)
    2. ETH يُرسل → يُفعّل receive() المهاجم
    3. المهاجم يعيد استدعاء withdraw() — الحالة لم تتغير بعد!
    4. يتكرر حتى ينفد رصيد العقد
    5. أخيراً: deposits[sender] -= amount (مرة واحدة فقط!)

    depth = floor(contract_balance / amount)
    drain = depth × amount
    state_update = 1 × amount (مرة واحدة)
═══════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import re
from typing import Dict, List, Any, Optional, Tuple

from .models import (
    ProtocolState,
    ExecutableAction,
    StateDelta,
    BalanceChange,
    StorageChange,
    SimulationConfig,
)

# ═══════════════════════════════════════════════════════════════
#  Constants
# ═══════════════════════════════════════════════════════════════

ATTACKER_ADDRESS = "attacker"
WEI_PER_ETH = 10 ** 18

# تقديرات الغاز لكل نوع عملية
GAS_COSTS = {
    "base": 21000,
    "storage_read": 2100,
    "storage_write": 20000,
    "external_call": 2600,
    "eth_transfer": 9000,
    "reentrancy_call": 30000,
    "computation": 5000,
}


class ActionExecutor:
    """
    محرك التنفيذ الدلالي.

    لكل Action من Layer 2، يحسب StateDelta بناءً على:
    1. net_delta (تأثيرات الحالة من Layer 2)
    2. external_calls (الاستدعاءات الخارجية)
    3. has_cei_violation + sends_eth → نمذجة إعادة الدخول
    4. preconditions → فحص الشروط المسبقة

    لا يُشغّل كود — يفسّر المعنى المالي.
    """

    def __init__(self, config: Optional[SimulationConfig] = None):
        self.config = config or SimulationConfig()

    # ═══════════════════════════════════════════════════════
    #  Main Execution
    # ═══════════════════════════════════════════════════════

    def execute(
        self,
        action: ExecutableAction,
        state: ProtocolState,
    ) -> StateDelta:
        """
        تنفيذ دلالي لـ Action واحد.

        Pipeline:
        1. فحص الشروط المسبقة (preconditions)
        2. فحص رسوم الغاز
        3. حساب الدلتا الأساسية من net_delta
        4. إذا CEI violation + sends_eth → نمذجة إعادة الدخول
        5. حساب تكلفة الغاز
        """
        # === 1. فحص الشروط المسبقة ===
        revert_reason = self._check_preconditions(action, state)
        if revert_reason:
            return StateDelta(
                reverted=True,
                revert_reason=revert_reason,
                gas_used=GAS_COSTS["base"],
            )

        # === 2. هل هناك CEI violation مع إرسال ETH؟ ===
        if (
            action.has_cei_violation
            and action.sends_eth
            and not action.reentrancy_guarded
        ):
            return self._execute_reentrancy(action, state)

        # === 3. تنفيذ عادي ===
        return self._execute_normal(action, state)

    # ═══════════════════════════════════════════════════════
    #  Normal Execution (بدون إعادة دخول)
    # ═══════════════════════════════════════════════════════

    def _execute_normal(
        self,
        action: ExecutableAction,
        state: ProtocolState,
    ) -> StateDelta:
        """تنفيذ عادي — يحسب StateDelta من net_delta + external_calls"""
        delta = StateDelta()

        # === حساب تأثيرات التخزين من net_delta ===
        self._apply_net_delta(action, state, delta)

        # === حساب تحويلات ETH ===
        self._apply_eth_transfers(action, state, delta)

        # === حساب تحويلات Token ===
        self._apply_token_transfers(action, state, delta)

        # === msg.value handling ===
        if action.msg_value > 0:
            delta.balance_changes.append(BalanceChange(
                account=action.msg_sender,
                token="ETH",
                amount=-action.msg_value,
                reason="msg_value_sent",
            ))
            delta.balance_changes.append(BalanceChange(
                account=action.contract_name,
                token="ETH",
                amount=action.msg_value,
                reason="msg_value_received",
            ))

        # === حساب الغاز ===
        delta.gas_used = self._estimate_gas(action, delta)

        # === الأحداث ===
        delta.events.append(
            f"{action.contract_name}.{action.function_name}"
            f"({', '.join(f'{k}={v}' for k, v in action.concrete_params.items())})"
        )

        return delta

    # ═══════════════════════════════════════════════════════
    #  Reentrancy Execution
    # ═══════════════════════════════════════════════════════

    def _execute_reentrancy(
        self,
        action: ExecutableAction,
        state: ProtocolState,
    ) -> StateDelta:
        """
        نمذجة هجوم إعادة الدخول.

        ═══════════════════════════════════════════
        التسلسل الحقيقي:
        1. CHECK: require(deposits[sender] >= amount) ← يمر
        2. INTERACTION: sender.call{value: amount}  ← يرسل ETH
        3. المهاجم يعيد الدخول → يعود لـ 1
        4. يتكرر depth مرات
        5. EFFECT: deposits[sender] -= amount       ← مرة واحدة فقط!

        النتيجة:
        - ETH المسحوبة = depth × amount
        - تغيير deposits = amount فقط (مرة واحدة)
        - الربح = (depth - 1) × amount
        ═══════════════════════════════════════════
        """
        delta = StateDelta()
        contract = action.contract_name

        # كم ETH يُرسل في كل استدعاء؟
        amount_per_call = self._resolve_eth_amount(action, state)
        if amount_per_call <= 0:
            return self._execute_normal(action, state)

        # رصيد العقد
        contract_balance = state.get_account(contract).eth_balance

        # عمق إعادة الدخول
        if action.reentrancy_depth > 0:
            depth = min(action.reentrancy_depth, self.config.max_reentrancy_depth)
        else:
            depth = self._estimate_reentrancy_depth(
                amount_per_call, contract_balance
            )

        if depth <= 0:
            return self._execute_normal(action, state)

        total_drained = amount_per_call * depth

        # === تحويلات ETH: العقد يفقد، المهاجم يكسب ===
        delta.balance_changes.append(BalanceChange(
            account=contract,
            token="ETH",
            amount=-total_drained,
            reason=f"reentrancy_drain_{depth}_calls",
        ))
        delta.balance_changes.append(BalanceChange(
            account=action.msg_sender,
            token="ETH",
            amount=total_drained,
            reason=f"reentrancy_receive_{depth}_calls",
        ))

        # === تغيير التخزين: مرة واحدة فقط (هذا جوهر الثغرة!) ===
        self._apply_net_delta(action, state, delta)

        # === الغاز: كل reentry تكلف غاز إضافي ===
        delta.gas_used = (
            GAS_COSTS["base"]
            + GAS_COSTS["storage_read"] * 2  # قراءة deposits + totalDeposits
            + GAS_COSTS["storage_write"] * 2  # كتابة (مرة واحدة)
            + GAS_COSTS["reentrancy_call"] * depth
        )

        # === الأحداث ===
        delta.events.append(
            f"REENTRANCY: {contract}.{action.function_name} × {depth} calls"
        )
        delta.events.append(
            f"DRAIN: {total_drained} wei ({total_drained / WEI_PER_ETH:.4f} ETH)"
        )

        return delta

    # ═══════════════════════════════════════════════════════
    #  Precondition Checking
    # ═══════════════════════════════════════════════════════

    def _check_preconditions(
        self,
        action: ExecutableAction,
        state: ProtocolState,
    ) -> str:
        """
        فحص الشروط المسبقة.
        يرجع "" إذا كل الشروط متحققة، أو سبب الـ revert.
        """
        # === فحص الصلاحيات ===
        if action.preconditions:
            for precond in action.preconditions:
                result = self._evaluate_precondition(
                    precond, action, state
                )
                if result:
                    return result

        # === فحص msg.value للدوال payable ===
        if action.msg_value > 0:
            sender_balance = state.get_account(action.msg_sender).eth_balance
            if sender_balance < action.msg_value:
                return f"insufficient ETH: need {action.msg_value}, have {sender_balance}"

        return ""  # كل الشروط متحققة

    def _evaluate_precondition(
        self,
        precondition: str,
        action: ExecutableAction,
        state: ProtocolState,
    ) -> str:
        """
        تقييم شرط مسبق واحد.
        يرجع "" إذا تحقق، أو سبب الفشل.
        """
        precond_lower = precondition.lower()
        contract = action.contract_name

        # === onlyOwner / require(msg.sender == owner) ===
        if 'owner' in precond_lower or 'onlyowner' in precond_lower:
            owner = state.get_storage(contract, "_owner", None)
            if owner and owner != action.msg_sender:
                return f"access_denied: onlyOwner (owner={owner}, sender={action.msg_sender})"

        # === require(amount > 0) ===
        if 'amount > 0' in precond_lower or 'amount != 0' in precond_lower:
            amount = action.concrete_params.get('amount', 0)
            if amount is not None:
                try:
                    if int(amount) <= 0:
                        return "zero_amount"
                except (ValueError, TypeError):
                    pass

        # === Balance checks: require(balances[sender] >= amount) ===
        if '>=' in precondition and ('balance' in precond_lower or 'deposit' in precond_lower):
            # حاول استخراج المتغير والقيمة
            amount = self._get_param_value(action, 'amount', state)
            # ابحث عن رصيد المستخدم في التخزين
            user_balance = self._find_user_balance(
                action.msg_sender, contract, state
            )
            if user_balance is not None and amount is not None:
                try:
                    if int(user_balance) < int(amount):
                        return f"insufficient_balance: have {user_balance}, need {amount}"
                except (ValueError, TypeError):
                    pass

        # === nonReentrant ===
        if 'nonreentrant' in precond_lower or 'reentrancy' in precond_lower:
            # إذا guard مفعّل → لا يمكن إعادة الدخول
            # لكن هذا يُفحص أصلاً عبر reentrancy_guarded
            pass

        return ""  # الشرط متحقق

    # ═══════════════════════════════════════════════════════
    #  Net Delta Application
    # ═══════════════════════════════════════════════════════

    def _apply_net_delta(
        self,
        action: ExecutableAction,
        state: ProtocolState,
        delta: StateDelta,
    ) -> None:
        """
        تطبيق net_delta من Layer 2 على StateDelta.

        net_delta format: {"variable": "±expression"}
        مثال: {"deposits[msg.sender]": "-amount", "totalDeposits": "-amount"}
        """
        for var_expr, change_expr in action.net_delta.items():
            contract = action.contract_name
            resolved_change = self._resolve_expression(
                change_expr, action, state
            )

            # حل اسم المتغير (استبدال msg.sender بالعنوان الفعلي)
            resolved_var = self._resolve_variable_name(
                var_expr, action
            )

            # القيمة الحالية
            current_value = self._get_storage_value(
                contract, resolved_var, state
            )

            # حساب القيمة الجديدة
            try:
                new_value = int(current_value) + int(resolved_change)
            except (ValueError, TypeError):
                new_value = resolved_change

            delta.storage_changes.append(StorageChange(
                contract=contract,
                variable=resolved_var,
                old_value=current_value,
                new_value=new_value,
            ))

    def _apply_eth_transfers(
        self,
        action: ExecutableAction,
        state: ProtocolState,
        delta: StateDelta,
    ) -> None:
        """حساب تحويلات ETH من external_calls"""
        if not action.sends_eth:
            return

        for ext_call in action.external_calls:
            if not ext_call.get("sends_eth", False):
                continue

            # كم ETH يُرسل؟
            amount = self._resolve_eth_amount(action, state)
            if amount <= 0:
                continue

            target = ext_call.get("target", action.msg_sender)
            target = self._resolve_address(target, action)

            # العقد يفقد ETH
            delta.balance_changes.append(BalanceChange(
                account=action.contract_name,
                token="ETH",
                amount=-amount,
                reason=f"external_call_to_{target}",
            ))
            # الهدف يكسب ETH
            delta.balance_changes.append(BalanceChange(
                account=target,
                token="ETH",
                amount=amount,
                reason=f"received_from_{action.contract_name}",
            ))

    def _apply_token_transfers(
        self,
        action: ExecutableAction,
        state: ProtocolState,
        delta: StateDelta,
    ) -> None:
        """حساب تحويلات Token من balance_effects"""
        # تحقق من balance_effects في الـ action object
        action_obj = action.action
        if not action_obj:
            return

        balance_effects = getattr(action_obj, 'balance_effects', {})
        for entity, expr in balance_effects.items():
            # حل التعبير
            amount = self._resolve_expression(expr, action, state)
            if amount == 0:
                continue

            tokens = getattr(action_obj, 'tokens_involved', [])
            token = tokens[0] if tokens else "ETH"

            delta.balance_changes.append(BalanceChange(
                account=entity,
                token=token,
                amount=amount,
                reason=f"balance_effect_{action.function_name}",
            ))

    # ═══════════════════════════════════════════════════════
    #  Expression Resolution
    # ═══════════════════════════════════════════════════════

    def _resolve_expression(
        self,
        expr: str,
        action: ExecutableAction,
        state: ProtocolState,
    ) -> int:
        """
        حل تعبير رياضي إلى قيمة محددة.

        يدعم:
        - "+amount", "-amount" → ±concrete_params['amount']
        - "+msg.value", "-msg.value" → ±msg_value
        - "balance_of_sender" → رصيد المُرسل في العقد
        - "contract_balance" → رصيد العقد
        - أرقام محددة
        """
        if not expr:
            return 0

        expr = str(expr).strip()

        # إشارة
        sign = 1
        clean_expr = expr
        if expr.startswith('+'):
            clean_expr = expr[1:]
        elif expr.startswith('-'):
            sign = -1
            clean_expr = expr[1:]

        # هل هو رقم مباشر؟
        try:
            return sign * int(clean_expr)
        except ValueError:
            pass

        clean_lower = clean_expr.strip().lower()

        # msg.value
        if clean_lower in ('msg.value', 'msgvalue', 'value'):
            return sign * action.msg_value

        # amount (من المعاملات)
        if clean_lower in ('amount', '_amount'):
            val = self._get_param_value(action, 'amount', state)
            return sign * val if val else 0

        # أي معامل بالاسم
        param_val = action.concrete_params.get(clean_expr)
        if param_val is not None:
            try:
                return sign * int(param_val)
            except (ValueError, TypeError):
                pass

        # balance_of_sender
        if 'balance_of_sender' in clean_lower:
            bal = self._find_user_balance(
                action.msg_sender, action.contract_name, state
            )
            return sign * (int(bal) if bal else 0)

        # contract_balance / address(this).balance
        if 'contract_balance' in clean_lower or 'address(this)' in clean_lower:
            account = state.get_account(action.contract_name)
            return sign * account.eth_balance

        # type(uint256).max
        if 'type(uint256).max' in clean_lower or 'uint256_max' in clean_lower:
            return sign * (2**256 - 1)

        # total_supply
        if 'total_supply' in clean_lower:
            storage = state.contract_storage.get(action.contract_name, {})
            ts = storage.get('totalSupply', storage.get('_totalSupply', 0))
            return sign * int(ts) if ts else 0

        # حاول كمرجع إلى متغير تخزين
        val = self._get_storage_value(
            action.contract_name, clean_expr, state
        )
        if val != 0:
            try:
                return sign * int(val)
            except (ValueError, TypeError):
                pass

        return 0

    def _resolve_variable_name(
        self, var_expr: str, action: ExecutableAction
    ) -> str:
        """حل اسم المتغير (استبدال msg.sender بالعنوان)"""
        result = var_expr
        result = result.replace("msg.sender", action.msg_sender)
        result = result.replace("_msgSender()", action.msg_sender)
        return result

    def _resolve_address(
        self, target: str, action: ExecutableAction
    ) -> str:
        """حل عنوان هدف"""
        if target in ("msg.sender", "sender"):
            return action.msg_sender
        if target in ("address(this)", "this"):
            return action.contract_name
        return target

    def _resolve_eth_amount(
        self,
        action: ExecutableAction,
        state: ProtocolState,
    ) -> int:
        """حساب كمية ETH المُرسلة في external call"""
        # أولاً: ابحث في المعاملات
        amount = self._get_param_value(action, 'amount', state)
        if amount and amount > 0:
            return amount

        # ثانياً: msg.value
        if action.msg_value > 0:
            return action.msg_value

        # ثالثاً: ابحث في net_delta عن أي تعبير amount
        for var, expr in action.net_delta.items():
            resolved = self._resolve_expression(expr, action, state)
            if resolved < 0:  # سحب → الكمية المسحوبة
                return abs(resolved)

        return 0

    # ═══════════════════════════════════════════════════════
    #  Reentrancy Depth Estimation
    # ═══════════════════════════════════════════════════════

    def _estimate_reentrancy_depth(
        self,
        amount_per_call: int,
        contract_balance: int,
    ) -> int:
        """
        تقدير عمق إعادة الدخول.
        depth = floor(contract_balance / amount_per_call)
        محدود بـ max_reentrancy_depth
        """
        if amount_per_call <= 0:
            return 0
        depth = contract_balance // amount_per_call
        return min(depth, self.config.max_reentrancy_depth)

    # ═══════════════════════════════════════════════════════
    #  Gas Estimation
    # ═══════════════════════════════════════════════════════

    def _estimate_gas(
        self,
        action: ExecutableAction,
        delta: StateDelta,
    ) -> int:
        """تقدير تكلفة الغاز"""
        gas = GAS_COSTS["base"]

        # قراءات التخزين
        gas += len(action.state_reads) * GAS_COSTS["storage_read"]

        # كتابات التخزين
        gas += len(delta.storage_changes) * GAS_COSTS["storage_write"]

        # استدعاءات خارجية
        gas += len(action.external_calls) * GAS_COSTS["external_call"]

        # تحويلات ETH
        eth_transfers = sum(
            1 for bc in delta.balance_changes if bc.token == "ETH"
        ) // 2  # كل تحويل = اثنين (sender + receiver)
        gas += eth_transfers * GAS_COSTS["eth_transfer"]

        return min(gas, self.config.max_gas_per_tx)

    # ═══════════════════════════════════════════════════════
    #  Helpers
    # ═══════════════════════════════════════════════════════

    def _get_param_value(
        self,
        action: ExecutableAction,
        param_name: str,
        state: ProtocolState,
    ) -> Optional[int]:
        """الحصول على قيمة معامل محدد"""
        val = action.concrete_params.get(param_name)
        if val is not None:
            # حل القيم الرمزية
            if isinstance(val, str):
                if val == "balance_of_sender":
                    return self._find_user_balance(
                        action.msg_sender, action.contract_name, state
                    ) or 0
                elif val == "contract_balance":
                    return state.get_account(action.contract_name).eth_balance
                try:
                    return int(val)
                except ValueError:
                    return 0
            return int(val) if val else 0
        return None

    def _find_user_balance(
        self,
        user: str,
        contract: str,
        state: ProtocolState,
    ) -> Optional[int]:
        """البحث عن رصيد المستخدم في تخزين العقد"""
        storage = state.contract_storage.get(contract, {})

        # ابحث في كل mappings عن رصيد المستخدم
        for var_name, var_value in storage.items():
            var_lower = var_name.lower()
            if isinstance(var_value, dict) and any(
                k in var_lower for k in ('balance', 'deposit', 'staked', 'shares')
            ):
                if user in var_value:
                    return var_value[user]

        # ابحث عن var[user] مباشرة
        for var_name, var_value in storage.items():
            key = f"{var_name}[{user}]"
            if key in storage:
                return storage[key]

        return None

    def _get_storage_value(
        self,
        contract: str,
        var_expr: str,
        state: ProtocolState,
    ) -> Any:
        """الحصول على قيمة متغير تخزين (يدعم mappings)"""
        storage = state.contract_storage.get(contract, {})

        # مباشر
        if var_expr in storage:
            val = storage[var_expr]
            # إذا كان mapping وليس قيمة
            if isinstance(val, dict):
                return val
            return val

        # mapping access: "deposits[attacker]"
        m = re.match(r'^(\w+)\[(.+)\]$', var_expr)
        if m:
            mapping_name = m.group(1)
            key = m.group(2)
            mapping = storage.get(mapping_name, {})
            if isinstance(mapping, dict):
                return mapping.get(key, 0)

        return 0
