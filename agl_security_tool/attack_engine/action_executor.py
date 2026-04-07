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
           أو: token.transfer(msg.sender, amount)   ← يرسل Token
        3. المهاجم يعيد الدخول → يعود لـ 1
        4. يتكرر depth مرات
        5. EFFECT: deposits[sender] -= amount       ← مرة واحدة فقط!

        النتيجة:
        - القيمة المسحوبة = depth × amount
        - تغيير deposits = amount فقط (مرة واحدة)
        - الربح = (depth - 1) × amount
        ═══════════════════════════════════════════
        """
        delta = StateDelta()
        contract = action.contract_name

        # كم يُرسل في كل استدعاء؟
        amount_per_call = self._resolve_transfer_amount(action, state)
        if amount_per_call <= 0:
            return self._execute_normal(action, state)

        # === تحديد نوع القيمة المُرسلة (ETH أو Token) ===
        is_erc20 = False
        token_name = "ETH"
        for ext_call in action.external_calls:
            if ext_call.get("sends_eth", False):
                target_name = ext_call.get("target", "")
                raw_text = ext_call.get("raw_text", "")
                call_type = ext_call.get("type", "")
                is_erc20 = self._is_erc20_transfer(
                    target_name, call_type, raw_text, action, state
                )
                if is_erc20 and action.tokens_involved:
                    token_name = action.tokens_involved[0]
                break

        # رصيد العقد (ETH أو Token)
        if is_erc20:
            # لتحويلات Token: نستخدم ETH كتقدير (العقد يملك 100 ETH افتراضياً)
            # الرصيد الفعلي للتوكن غير معروف — نستخدم ETH balance كتقدير
            contract_balance = state.get_account(contract).eth_balance
        else:
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

        # === تحويلات: العقد يفقد، المهاجم يكسب ===
        delta.balance_changes.append(BalanceChange(
            account=contract,
            token=token_name,
            amount=-total_drained,
            reason=f"reentrancy_drain_{depth}_calls",
        ))
        delta.balance_changes.append(BalanceChange(
            account=action.msg_sender,
            token=token_name,
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
        """
        حساب تحويلات القيمة (ETH أو Token) من external_calls.

        ═══════════════════════════════════════════════════════════
        التمييز بين أنواع التحويلات:

        1. ETH الحقيقي    — .call{value:...}  / payable(x).transfer(amt)
           → نوع العملية: external_call_eth
           → يقرأ raw_text لتحديد المستلم الفعلي

        2. ERC20 Token     — token.transfer(to, amount)
           → نوع العملية: external_call (ليس _eth)
           → أو external_call_eth بسبب تداخل regex مع .transfer()
           → الدليل: target هو متغير حالة (مثل "token") وليس عنوان

        القاعدة الأساسية لتحديد المستلم:
        - في fund_outflow (withdraw): العقد يُرسل → المهاجم يستلم
        - في fund_inflow (deposit): المهاجم يُرسل → العقد يستلم
        - المستلم الحقيقي يُستنتج من الفئة (category) وليس من target
        ═══════════════════════════════════════════════════════════
        """
        if not action.sends_eth:
            return

        for ext_call in action.external_calls:
            if not ext_call.get("sends_eth", False):
                continue

            raw_text = ext_call.get("raw_text", "")
            target_name = ext_call.get("target", "")
            call_type = ext_call.get("type", "")

            # === تصنيف نوع التحويل ===
            is_erc20 = self._is_erc20_transfer(
                target_name, call_type, raw_text, action, state
            )

            if is_erc20:
                # === تحويل ERC20 Token ===
                self._apply_erc20_transfer(
                    action, state, delta, ext_call, target_name, raw_text
                )
            else:
                # === تحويل ETH حقيقي ===
                self._apply_native_eth_transfer(
                    action, state, delta, ext_call, raw_text
                )

    def _is_erc20_transfer(
        self,
        target_name: str,
        call_type: str,
        raw_text: str,
        action: ExecutableAction,
        state: ProtocolState,
    ) -> bool:
        """
        هل هذا الاستدعاء الخارجي هو تحويل ERC20 وليس ETH حقيقي؟

        الأدلة على أنه ERC20:
        1. target هو متغير حالة (state var) وليس عنوان مباشر
        2. النص يحتوي .transfer(arg1, arg2) بمعاملين (ERC20 signature)
        3. target في tokens_involved
        4. ليس .call{value:...} (الذي هو ETH دائماً)
        """
        # .call{value:...} هو ETH حقيقي دائماً
        if 'call{' in raw_text or 'call {' in raw_text:
            return False
        if call_type == "external_call" and "transfer" not in raw_text.lower():
            return False

        # إذا target هو متغير حالة في العقد → ERC20
        if target_name in action.state_reads:
            return True

        # إذا الاسم يشبه متغير حالة (ليس عنوان)
        storage = state.contract_storage.get(action.contract_name, {})
        if target_name in storage:
            return True

        # تحقق من .transfer(addr, amount) بمعاملين → ERC20
        # مقابل .transfer(amount) بمعامل واحد → ETH
        transfer_match = re.search(
            r'\.transfer\s*\(([^)]*)\)', raw_text
        )
        if transfer_match:
            args = transfer_match.group(1)
            # عدّ الفواصل خارج الأقواس
            comma_count = self._count_top_level_commas(args)
            if comma_count >= 1:
                # معاملين+ → ERC20 (transfer(to, amount))
                return True

        # إذا target يشبه اسم توكن أو واجهة
        target_lower = target_name.lower()
        token_hints = ('token', 'erc20', 'ierc20', 'usdc', 'usdt',
                       'weth', 'dai', 'wbtc', 'asset', 'coin',
                       'reward', 'underlying')
        if any(h in target_lower for h in token_hints):
            return True

        # إذا target في tokens_involved
        for tok in action.tokens_involved:
            if target_name in tok or tok in target_name:
                return True

        return False

    def _count_top_level_commas(self, s: str) -> int:
        """عدّ الفواصل خارج الأقواس المتداخلة"""
        depth = 0
        count = 0
        for c in s:
            if c in ('(', '[', '{'):
                depth += 1
            elif c in (')', ']', '}'):
                depth -= 1
            elif c == ',' and depth == 0:
                count += 1
        return count

    def _apply_native_eth_transfer(
        self,
        action: ExecutableAction,
        state: ProtocolState,
        delta: StateDelta,
        ext_call: Dict[str, Any],
        raw_text: str,
    ) -> None:
        """
        تنفيذ تحويل ETH حقيقي.
        المستلم يُحدد من سياق الدالة:
        - fund_outflow → العقد يُرسل للمهاجم (msg.sender)
        - fund_inflow → المهاجم يُرسل للعقد (handled by msg.value)
        """
        amount = self._resolve_eth_amount(action, state)
        if amount <= 0:
            return

        # تحديد المستلم الحقيقي
        recipient = self._determine_transfer_recipient(
            action, ext_call, raw_text
        )

        # العقد يفقد ETH
        delta.balance_changes.append(BalanceChange(
            account=action.contract_name,
            token="ETH",
            amount=-amount,
            reason=f"eth_transfer_to_{recipient}",
        ))
        # المستلم يكسب ETH
        delta.balance_changes.append(BalanceChange(
            account=recipient,
            token="ETH",
            amount=amount,
            reason=f"eth_received_from_{action.contract_name}",
        ))

    def _apply_erc20_transfer(
        self,
        action: ExecutableAction,
        state: ProtocolState,
        delta: StateDelta,
        ext_call: Dict[str, Any],
        token_var: str,
        raw_text: str,
    ) -> None:
        """
        تنفيذ تحويل ERC20 Token.
        يحدد التوكن والمستلم والمبلغ من السياق.
        """
        amount = self._resolve_transfer_amount(action, state)
        if amount <= 0:
            return

        # اسم التوكن (من tokens_involved أو target)
        token_name = token_var
        if action.tokens_involved:
            token_name = action.tokens_involved[0]

        # تحديد المستلم الحقيقي
        recipient = self._determine_transfer_recipient(
            action, ext_call, raw_text
        )

        # العقد يُرسل توكنات
        delta.balance_changes.append(BalanceChange(
            account=action.contract_name,
            token=token_name,
            amount=-amount,
            reason=f"token_transfer_to_{recipient}",
        ))
        # المستلم يكسب توكنات
        delta.balance_changes.append(BalanceChange(
            account=recipient,
            token=token_name,
            amount=amount,
            reason=f"token_received_from_{action.contract_name}",
        ))

    def _determine_transfer_recipient(
        self,
        action: ExecutableAction,
        ext_call: Dict[str, Any],
        raw_text: str,
    ) -> str:
        """
        تحديد المستلم الحقيقي للتحويل.

        الأولوية:
        1. إذا raw_text يحتوي msg.sender → المهاجم
        2. إذا category = fund_outflow → المهاجم (العقد يُرسل للمستخدم)
        3. إذا raw_text يحتوي عنوان محدد → ذلك العنوان
        4. fallback → msg_sender (المهاجم)
        """
        raw_lower = raw_text.lower() if raw_text else ""

        # هل النص يُشير صراحة لـ msg.sender؟
        if 'msg.sender' in raw_lower or '_msgsender()' in raw_lower:
            return action.msg_sender

        # هل الدالة من نوع سحب/إرسال للمستخدم؟
        cat = action.category.lower() if action.category else ""
        func_lower = action.function_name.lower()

        outflow_cats = ("fund_outflow", "withdrawal", "transfer_out")
        outflow_funcs = ("withdraw", "redeem", "claim", "exit",
                         "emergencywithdraw", "unstake", "harvest")

        if cat in outflow_cats or any(f in func_lower for f in outflow_funcs):
            return action.msg_sender

        # هل target في ext_call هو عنوان قابل للحل؟
        target = ext_call.get("target", "")
        resolved = self._resolve_address(target, action)
        # إذا لم يتحول (أي ليس msg.sender/this) والهدف يشبه عنوان
        if resolved != target:
            return resolved

        # fallback — في أغلب الحالات المهاجم هو المستلم
        return action.msg_sender

    def _resolve_transfer_amount(
        self,
        action: ExecutableAction,
        state: ProtocolState,
    ) -> int:
        """
        حساب مبلغ التحويل (ETH أو Token).
        يبحث في المعاملات ثم net_delta ثم balance_effects.
        """
        # 1. معامل amount المحدد
        amount = self._get_param_value(action, 'amount', state)
        if amount and amount > 0:
            return amount

        # 2. balance (لـ emergencyWithdraw وما شابه)
        balance = self._get_param_value(action, 'balance', state)
        if balance and balance > 0:
            return balance

        # 3. استنتاج من net_delta (القيم السالبة = سحب)
        for var, expr in action.net_delta.items():
            resolved = self._resolve_expression(expr, action, state)
            if resolved < 0:
                return abs(resolved)

        # 4. من balance_effects
        for entity, expr in action.balance_effects.items():
            resolved = self._resolve_expression(expr, action, state)
            if resolved < 0:
                return abs(resolved)

        # 5. رصيد المهاجم في العقد
        user_balance = self._find_user_balance(
            action.msg_sender, action.contract_name, state
        )
        if user_balance and user_balance > 0:
            return user_balance

        return 0

    def _apply_token_transfers(
        self,
        action: ExecutableAction,
        state: ProtocolState,
        delta: StateDelta,
    ) -> None:
        """
        حساب تحويلات Token من balance_effects.
        يستخدم balance_effects و tokens_involved مباشرة
        من ExecutableAction (بدون الحاجة لمرجع L2 Action).

        يتخطى الإدخالات التي هي متغيرات تخزين (موجودة في net_delta)
        أو التي تشير لعلاقات بين كيانات (تحتوي →).
        """
        if not action.balance_effects:
            return

        token_name = "ETH"
        if action.tokens_involved:
            token_name = action.tokens_involved[0]

        # جمع أسماء متغيرات التخزين للتخطي
        storage_vars = set(action.net_delta.keys())
        storage_vars.update(action.state_writes)

        for entity, expr in action.balance_effects.items():
            # تخطي متغيرات التخزين — هذه تُعالج بواسطة _apply_net_delta
            if entity in storage_vars:
                continue
            # تخطي علاقات الكيانات (مثل "account:X→account:Y")
            if '→' in entity or '->' in entity:
                continue

            amount = self._resolve_expression(expr, action, state)
            if amount == 0:
                continue

            delta.balance_changes.append(BalanceChange(
                account=entity,
                token=token_name,
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
        """
        حساب كمية ETH المُرسلة في external call.

        الترتيب:
        1. معامل amount المحدد
        2. msg.value
        3. net_delta (القيم السالبة = سحب)
        4. رصيد المهاجم في العقد (لـ withdraw(balance))
        """
        return self._resolve_transfer_amount(action, state)

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
