"""
AGL Action Space — Parameter Generator
توليد variants للمعاملات — كل مدخل يمكن أن يكون "action variant"

لكل Action أساسي من ActionEnumerator:
  → توليد نسخ متعددة بمعاملات مختلفة استراتيجياً
  → كل variant يمثل سيناريو هجوم مختلف

مثال:
  withdraw(amount) → variants:
    withdraw(0)                    → edge case
    withdraw(1)                    → minimum
    withdraw(balance_of_sender)    → كل الرصيد
    withdraw(uint256.max)          → overflow attempt
    withdraw(balance_of_sender+1)  → أكثر من الرصيد
"""

from __future__ import annotations

import copy
from typing import Dict, List, Any, Optional

from .models import (
    Action, ActionParameter, ParamDomain,
)


class ParameterGenerator:
    """
    يولد Action variants بمعاملات استراتيجية.

    الاستراتيجية:
    1. لكل Action أساسي → ينسخه عدة مرات بمعاملات مختلفة
    2. يختار القيم بناءً على ParamDomain
    3. يحدد concrete_values لكل variant
    4. يمكن تحديد حدود لعدد الـ variants
    """

    # الحد الأقصى للـ variants لكل دالة
    MAX_VARIANTS_PER_FUNCTION = 8

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.max_variants = self.config.get(
            "max_variants", self.MAX_VARIANTS_PER_FUNCTION
        )

    def generate(self, actions: List[Action]) -> List[Action]:
        """
        لكل Action أساسي، أنشئ variants بمعاملات استراتيجية.

        Returns:
            قائمة موسعة تحتوي الأصليين + المتغيرات
        """
        all_actions: List[Action] = []
        for action in actions:
            variants = self._generate_variants(action)
            all_actions.extend(variants)
        return all_actions

    def _generate_variants(self, action: Action) -> List[Action]:
        """توليد variants لـ Action واحد"""
        # إذا لا معاملات → variant واحد فقط (الأصلي)
        if not action.parameters:
            return [action]

        # توليد مجموعات القيم الاستراتيجية
        param_value_sets = self._compute_strategic_values(action)

        if not param_value_sets:
            return [action]

        variants = []
        for idx, value_set in enumerate(param_value_sets[:self.max_variants]):
            variant = self._create_variant(action, value_set, idx)
            variants.append(variant)

        return variants

    def _compute_strategic_values(
        self, action: Action
    ) -> List[List[Dict[str, str]]]:
        """
        حساب القيم الاستراتيجية لكل معامل.

        كل entry في الناتج هي قائمة من {param_name: value} لكل المعاملات.
        """
        # لكل معامل، حدد القيم الاستراتيجية
        param_strategies: List[List[Dict[str, str]]] = []

        for param in action.parameters:
            strategies = self._values_for_param(param, action)
            param_strategies.append(strategies)

        if not param_strategies:
            return []

        # بدلاً من Cartesian product (ينفجر)، نأخذ:
        # 1. كل معامل بقيمته "الافتراضية" مع تغيير واحد في كل مرة
        # 2. + حالات حافّة مهمة (all max, all zero, boundary)
        value_sets = self._smart_combine(param_strategies, action.parameters)

        return value_sets

    def _values_for_param(
        self, param: ActionParameter, action: Action
    ) -> List[Dict[str, str]]:
        """القيم الاستراتيجية لمعامل واحد"""
        values = []
        name = param.name

        if param.is_amount:
            # مبلغ مالي → قيم حدية
            values.extend([
                {"value": "0", "label": "zero", "reason": "edge_case"},
                {"value": "1", "label": "minimum", "reason": "dust_amount"},
                {"value": "balance_of_sender", "label": "full_balance",
                 "reason": "drain_all"},
                {"value": "type(uint256).max", "label": "uint256_max",
                 "reason": "overflow_attempt"},
                {"value": "balance_of_sender + 1", "label": "exceed_balance",
                 "reason": "underflow_attempt"},
            ])

            # إذا الدالة payable → حاول مع contract balance
            if action.mutability == "payable":
                values.append({
                    "value": "address(this).balance",
                    "label": "contract_balance",
                    "reason": "drain_contract",
                })

        elif param.is_address:
            values.extend([
                {"value": "attacker", "label": "attacker_address",
                 "reason": "self_benefit"},
                {"value": "address(0)", "label": "zero_address",
                 "reason": "burn_or_error"},
                {"value": "address(this)", "label": "self_address",
                 "reason": "self_call"},
            ])

            if param.is_token:
                values.append({
                    "value": "malicious_token", "label": "fake_token",
                    "reason": "token_substitution",
                })

        elif param.param_type in ("bytes", "bytes32") or param.param_type.startswith("bytes"):
            values.extend([
                {"value": "0x", "label": "empty_bytes", "reason": "empty_data"},
                {"value": "custom_payload", "label": "custom",
                 "reason": "crafted_calldata"},
            ])

        elif param.param_type == "bool":
            values.extend([
                {"value": "true", "label": "true", "reason": "boolean_true"},
                {"value": "false", "label": "false", "reason": "boolean_false"},
            ])

        else:
            # نوع عام → قيمة واحدة default
            values.append({
                "value": "default", "label": "default", "reason": "generic",
            })

        return values

    def _smart_combine(
        self,
        param_strategies: List[List[Dict[str, str]]],
        parameters: List[ActionParameter],
    ) -> List[List[Dict[str, str]]]:
        """
        دمج ذكي بدون Cartesian product.

        الاستراتيجية:
        1. variant "default" — أول قيمة لكل معامل
        2. لكل معامل: variant يغير فيه هذا المعامل مع إبقاء الباقي default
        3. variant "edge" — كل المعاملات بقيم حدية
        4. variant "attack" — أخطر قيمة لكل معامل
        """
        if not param_strategies:
            return []

        num_params = len(param_strategies)
        variants = []

        # 1. Default variant — أول قيمة لكل معامل
        default_set = []
        for i in range(num_params):
            if param_strategies[i]:
                default_set.append(param_strategies[i][0])
            else:
                default_set.append({"value": "default", "label": "default", "reason": "fallback"})
        variants.append(default_set)

        # 2. One-at-a-time — تغيير كل معامل على حدة
        for pi in range(num_params):
            for vi, val in enumerate(param_strategies[pi]):
                if vi == 0:
                    continue  # already in default
                variant = list(default_set)
                variant[pi] = val
                variants.append(variant)

        # 3. Attack variant — أخطر قيمة لكل معامل
        attack_set = []
        for i in range(num_params):
            vals = param_strategies[i]
            # اختيار أخطر قيمة
            best = vals[0]
            for v in vals:
                if v.get("reason") in (
                    "drain_all", "overflow_attempt", "underflow_attempt",
                    "self_benefit", "drain_contract",
                ):
                    best = v
                    break
            attack_set.append(best)
        if attack_set != default_set:
            variants.append(attack_set)

        # 4. Edge case — كل المعاملات بـ zero/min
        edge_set = []
        for i in range(num_params):
            vals = param_strategies[i]
            zero_val = next(
                (v for v in vals if v.get("reason") == "edge_case" or v.get("label") == "zero"),
                vals[0]
            )
            edge_set.append(zero_val)
        if edge_set != default_set and edge_set != attack_set:
            variants.append(edge_set)

        return variants

    def _create_variant(
        self, action: Action, value_set: List[Dict[str, str]], variant_idx: int
    ) -> Action:
        """إنشاء نسخة variant من Action مع قيم محددة"""
        variant = Action(
            action_id=f"{action.contract_name}.{action.function_name}#v{variant_idx}",
            contract_name=action.contract_name,
            function_name=action.function_name,
            signature=action.signature,
            parameters=[],
            msg_value=action.msg_value,
            preconditions=list(action.preconditions),
            access_requirements=list(action.access_requirements),
            requires_access=action.requires_access,
            caller_must_be=action.caller_must_be,
            state_reads=list(action.state_reads),
            state_writes=list(action.state_writes),
            net_delta=dict(action.net_delta),
            external_calls=list(action.external_calls),
            sends_eth=action.sends_eth,
            has_delegatecall=action.has_delegatecall,
            reentrancy_window=action.reentrancy_window,
            reentrancy_guarded=action.reentrancy_guarded,
            has_cei_violation=action.has_cei_violation,
            cei_violation_count=action.cei_violation_count,
            cross_function_risk=action.cross_function_risk,
            visibility=action.visibility,
            mutability=action.mutability,
            line_start=action.line_start,
            source_file=action.source_file,
            is_valid=action.is_valid,
            disabled_reason=action.disabled_reason,
        )

        # تعيين concrete values لكل معامل
        for i, orig_param in enumerate(action.parameters):
            new_param = ActionParameter(
                name=orig_param.name,
                param_type=orig_param.param_type,
                domains=list(orig_param.domains),
                is_amount=orig_param.is_amount,
                is_address=orig_param.is_address,
                is_token=orig_param.is_token,
                constraints=list(orig_param.constraints),
            )
            if i < len(value_set):
                val_info = value_set[i]
                new_param.concrete_values = [val_info.get("value", "default")]
            variant.parameters.append(new_param)

        return variant
