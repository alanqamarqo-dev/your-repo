"""
AGL Action Space — Action Enumerator
استخراج جميع الأفعال الممكنة من العقود المحللة

لكل عقد → لكل دالة public/external → هل المهاجم يستطيع استدعاءها؟
→ إذا نعم: أنشئ Action مع كل المعلومات من Layer 1

هذا المكوّن لا يولّد variants للمعاملات (هذا عمل ParameterGenerator).
يكتفي بإنشاء Action أساسي واحد لكل دالة قابلة للاستدعاء.
"""

from __future__ import annotations

import re
from typing import Dict, List, Any, Optional, Set

from .models import Action, ActionParameter, ActionCategory, ParamDomain

import sys
from pathlib import Path

_TOOL_DIR = Path(__file__).parent.parent.resolve()
if str(_TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOL_DIR))

try:
    from detectors import ParsedContract, ParsedFunction, OpType
except ImportError:
    from agl_security_tool.detectors import ParsedContract, ParsedFunction, OpType

try:
    from state_extraction.models import (
        FunctionEffect, StateMutation, TemporalAnalysis, ExecutionTimeline,
    )
except ImportError:
    from agl_security_tool.state_extraction.models import (
        FunctionEffect, StateMutation, TemporalAnalysis, ExecutionTimeline,
    )


# ═══════════════════════════════════════════════════════════════
#  أدوار المهاجم — ماذا يمكنه استدعاؤه
# ═══════════════════════════════════════════════════════════════

# Modifiers تمنع المهاجم العادي
_ACCESS_MODIFIERS = {
    "onlyOwner", "onlyAdmin", "onlyRole", "onlyGovernance",
    "onlyMinter", "onlyPauser", "onlyOperator", "onlyKeeper",
    "onlyAuthorized", "onlyController", "onlyManager",
    "onlyGuardian", "onlyWhitelisted", "onlyDAO",
    "whenNotPaused", "initializer", "onlyProxy",
}

# الدوال التي لا تحتاج صلاحية عادةً
_PUBLIC_PATTERNS = {
    "deposit", "withdraw", "borrow", "repay", "liquidate",
    "swap", "stake", "unstake", "claim", "redeem", "mint",
    "burn", "transfer", "approve", "flash", "execute",
}


class ActionEnumerator:
    """
    يستخرج كل الأفعال الممكنة (Actions) من العقود المحللة.

    لكل دالة public/external:
    1. يحدد هل المهاجم يستطيع استدعاءها
    2. يستخرج المعاملات مع أنواعها
    3. يعيّن الشروط المسبقة
    4. يربط بيانات FunctionEffect و StateMutation إذا كانت متاحة
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._action_counter = 0

    def enumerate(
        self,
        contracts: List[ParsedContract],
        effects: Optional[List[FunctionEffect]] = None,
        mutations: Optional[List[StateMutation]] = None,
        timelines: Optional[List[ExecutionTimeline]] = None,
    ) -> List[Action]:
        """
        استخراج كل Actions من كل العقود.

        Args:
            contracts: العقود المحللة من SoliditySemanticParser
            effects: FunctionEffect من Layer 1 (اختياري)
            mutations: StateMutation من Layer 1 (اختياري)
            timelines: ExecutionTimeline من Layer 1 (اختياري)

        Returns:
            قائمة كل الأفعال الممكنة
        """
        self._action_counter = 0

        # بناء lookup maps للربط السريع
        effect_map = self._build_effect_map(effects)
        mutation_map = self._build_mutation_map(mutations)
        timeline_map = self._build_timeline_map(timelines)

        all_actions: List[Action] = []

        for contract in contracts:
            # تخطي interfaces و libraries
            if contract.contract_type in ("interface", "library"):
                continue

            for fname, func in contract.functions.items():
                # فقط الدوال القابلة للاستدعاء من الخارج
                if not self._is_externally_callable(func):
                    continue

                action = self._build_action(
                    contract, func, effect_map, mutation_map, timeline_map
                )
                if action:
                    all_actions.append(action)

        return all_actions

    # ═══════════════════════════════════════════════════════════
    #  بناء Action واحد
    # ═══════════════════════════════════════════════════════════

    def _build_action(
        self,
        contract: ParsedContract,
        func: ParsedFunction,
        effect_map: Dict[str, FunctionEffect],
        mutation_map: Dict[str, StateMutation],
        timeline_map: Dict[str, ExecutionTimeline],
    ) -> Optional[Action]:
        """بناء Action كامل من دالة واحدة"""
        self._action_counter += 1
        key = f"{contract.name}.{func.name}"
        action_id = f"{key}#{self._action_counter}"

        # === معاملات الدالة ===
        params = self._extract_parameters(func)

        # === شروط التنفيذ ===
        preconditions = list(func.require_checks) if func.require_checks else []
        access_reqs = self._detect_access_requirements(func, contract)
        requires_access = bool(access_reqs)
        caller = self._determine_caller(func, access_reqs)

        # === تأثير على الحالة (من Layer 1 أو من ParsedFunction) ===
        effect = effect_map.get(key)
        mutation = mutation_map.get(key)
        timeline = timeline_map.get(key)

        state_reads = list(effect.reads) if (effect and effect.reads) else list(func.state_reads)
        state_writes = list(effect.writes) if (effect and effect.writes) else list(func.state_writes)
        net_delta = dict(effect.net_delta) if (effect and effect.net_delta) else {}

        # === External calls ===
        ext_calls = []
        if effect and effect.external_calls:
            ext_calls = list(effect.external_calls)
        elif func.external_calls:
            for op in func.external_calls:
                ext_calls.append({
                    "target": op.target,
                    "type": op.op_type.value if hasattr(op.op_type, 'value') else str(op.op_type),
                    "sends_eth": op.sends_eth,
                    "line": op.line,
                })

        sends_eth = func.sends_eth or (effect.eth_sent if effect else False)
        has_delegatecall = func.has_delegatecall

        # === CEI / Reentrancy من Timeline ===
        has_cei = False
        cei_count = 0
        reentrancy_window = False
        reentrancy_guarded = func.has_reentrancy_guard
        if timeline:
            cei_count = len(timeline.cei_violations)
            has_cei = cei_count > 0
            reentrancy_window = has_cei and not reentrancy_guarded

        # === Cross-function risk ===
        cross_func = False
        if effect:
            cross_func = bool(effect.conflicts_with)

        # === msg.value ===
        msg_value = None
        if func.mutability == "payable":
            msg_value = "msg.value"

        action = Action(
            action_id=action_id,
            contract_name=contract.name,
            function_name=func.name,
            signature=self._build_signature(func),
            parameters=params,
            msg_value=msg_value,
            preconditions=preconditions,
            access_requirements=access_reqs,
            requires_access=requires_access,
            caller_must_be=caller,
            state_reads=state_reads,
            state_writes=state_writes,
            net_delta=net_delta,
            external_calls=ext_calls,
            sends_eth=sends_eth,
            has_delegatecall=has_delegatecall,
            reentrancy_window=reentrancy_window,
            reentrancy_guarded=reentrancy_guarded,
            has_cei_violation=has_cei,
            cei_violation_count=cei_count,
            cross_function_risk=cross_func,
            visibility=func.visibility,
            mutability=func.mutability,
            line_start=func.line_start,
            source_file=contract.source_file,
        )

        # تعطيل الأفعال غير الصالحة
        if requires_access and "anyone" not in caller:
            action.is_valid = False
            action.disabled_reason = f"requires access: {', '.join(access_reqs)}"

        return action

    # ═══════════════════════════════════════════════════════════
    #  Helpers
    # ═══════════════════════════════════════════════════════════

    def _is_externally_callable(self, func: ParsedFunction) -> bool:
        """هل الدالة قابلة للاستدعاء من الخارج"""
        if func.is_constructor or func.is_initializer:
            return False
        if func.visibility in ("public", "external"):
            return True
        if func.is_fallback or func.is_receive:
            return True
        return False

    def _extract_parameters(self, func: ParsedFunction) -> List[ActionParameter]:
        """استخراج معاملات الدالة مع مجال القيم الممكنة"""
        params = []
        for p in func.parameters:
            name = p.get("name", "")
            ptype = p.get("type", "")
            ap = ActionParameter(
                name=name,
                param_type=ptype,
                domains=self._infer_domains(name, ptype),
                is_amount=self._is_amount_param(name, ptype),
                is_address=self._is_address_param(ptype),
                is_token=self._is_token_param(name),
            )
            params.append(ap)
        return params

    def _infer_domains(self, name: str, ptype: str) -> List[ParamDomain]:
        """استنتاج مجال القيم من اسم ونوع المعامل"""
        domains = []
        name_lower = name.lower()

        if "uint" in ptype:
            domains.append(ParamDomain.UINT256_ZERO)
            if any(k in name_lower for k in ("amount", "value", "balance", "shares")):
                domains.extend([
                    ParamDomain.SMALL_AMOUNT,
                    ParamDomain.BALANCE_OF_SENDER,
                    ParamDomain.UINT256_MAX,
                ])
            elif "supply" in name_lower:
                domains.append(ParamDomain.TOTAL_SUPPLY)
            else:
                domains.append(ParamDomain.LARGE_AMOUNT)

        elif ptype == "address":
            domains.append(ParamDomain.ATTACKER_ADDRESS)
            if any(k in name_lower for k in ("to", "recipient", "receiver", "dest")):
                domains.append(ParamDomain.ATTACKER_ADDRESS)
            elif any(k in name_lower for k in ("token", "asset")):
                domains.append(ParamDomain.ANY_TOKEN)
            elif any(k in name_lower for k in ("target", "contract")):
                domains.append(ParamDomain.SELF_ADDRESS)
            domains.append(ParamDomain.ZERO_ADDRESS)

        elif ptype == "bytes" or ptype.startswith("bytes"):
            domains.append(ParamDomain.CUSTOM)

        return domains

    def _is_amount_param(self, name: str, ptype: str) -> bool:
        """هل المعامل يمثل مبلغاً مالياً"""
        if "uint" not in ptype:
            return False
        amount_keywords = {
            "amount", "value", "balance", "shares", "assets",
            "deposit", "withdraw", "borrow", "repay", "stake",
            "qty", "quantity",
        }
        return any(k in name.lower() for k in amount_keywords)

    def _is_address_param(self, ptype: str) -> bool:
        return ptype == "address"

    def _is_token_param(self, name: str) -> bool:
        token_keywords = {"token", "asset", "collateral", "underlying", "erc20"}
        return any(k in name.lower() for k in token_keywords)

    def _detect_access_requirements(
        self, func: ParsedFunction, contract: ParsedContract
    ) -> List[str]:
        """كشف متطلبات الوصول"""
        reqs = []
        for mod in func.modifiers:
            if mod in _ACCESS_MODIFIERS or mod.startswith("only"):
                reqs.append(mod)
            # تحقق إذا modifier يتحقق من owner/role
            if mod in contract.modifiers:
                mod_info = contract.modifiers[mod]
                if mod_info.checks_owner:
                    reqs.append(f"modifier:{mod}(checks_owner)")
                elif mod_info.checks_role:
                    reqs.append(f"modifier:{mod}(checks_role)")
        # تحقق من require في الدالة نفسها
        for req in func.require_checks:
            req_lower = req.lower()
            if any(k in req_lower for k in (
                "msg.sender == owner", "msg.sender == admin",
                "hasrole", "require(owner", "require(admin",
                "onlyowner", "_checkrole",
            )):
                reqs.append(f"require:{req[:60]}")
        return reqs

    def _determine_caller(self, func: ParsedFunction, access_reqs: List[str]) -> str:
        """تحديد من يستطيع استدعاء الدالة"""
        if not access_reqs:
            return "anyone"
        for req in access_reqs:
            if "owner" in req.lower():
                return "owner"
            if "admin" in req.lower():
                return "admin"
            if "role" in req.lower():
                return "role"
        return "restricted"

    def _build_signature(self, func: ParsedFunction) -> str:
        """بناء function signature"""
        types = []
        for p in func.parameters:
            types.append(p.get("type", "unknown"))
        return f"{func.name}({','.join(types)})"

    # ═══════════════════════════════════════════════════════════
    #  Lookup Maps
    # ═══════════════════════════════════════════════════════════

    def _build_effect_map(
        self, effects: Optional[List[FunctionEffect]]
    ) -> Dict[str, FunctionEffect]:
        """بناء map: "Contract.function" → FunctionEffect"""
        if not effects:
            return {}
        m = {}
        for e in effects:
            key = f"{e.contract_name}.{e.function_name}"
            m[key] = e
        return m

    def _build_mutation_map(
        self, mutations: Optional[List[StateMutation]]
    ) -> Dict[str, StateMutation]:
        if not mutations:
            return {}
        m = {}
        for mut in mutations:
            key = f"{mut.contract_name}.{mut.function_name}"
            m[key] = mut
        return m

    def _build_timeline_map(
        self, timelines: Optional[List[ExecutionTimeline]]
    ) -> Dict[str, ExecutionTimeline]:
        if not timelines:
            return {}
        m = {}
        for t in timelines:
            key = f"{t.contract_name}.{t.function_name}"
            m[key] = t
        return m
