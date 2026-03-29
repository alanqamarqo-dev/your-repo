"""
AGL State Extraction — Function Effect Model
نموذج تأثير الدالة — ΔState = f(inputs)

لكل دالة يبني وصفاً كاملاً لتأثيرها على الحالة:
  - ماذا تأخذ (parameters, msg.value, msg.sender)
  - ماذا تقرأ من الحالة (state reads)
  - ماذا تكتب في الحالة (state writes + net delta)
  - ماذا تؤثر على الخارج (external calls, ETH sent, events)
  - تبعيات مع دوال أخرى (who reads what we write, who writes what we read)

هذا النموذج يمكّن من:
  1. كشف cross-function reentrancy (دالة A تكتب ما تقرأه دالة B)
  2. كشف write-write conflicts (دالتان تكتبان نفس المتغير)
  3. كشف stale reads (دالة تقرأ متغيراً يمكن أن يتغير أثناء external call)
  4. فهم attack surface (أي دوال يمكن أن تؤثر على سلامة المال)
"""

from typing import List, Dict, Set, Optional, Any

from .models import (
    FunctionEffect, StateMutation,
)

# Import parser types
import sys
from pathlib import Path
_TOOL_DIR = Path(__file__).parent.parent.resolve()
if str(_TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOL_DIR))

try:
    from detectors import ParsedContract, ParsedFunction, Operation, OpType
except ImportError:
    from agl_security_tool.detectors import ParsedContract, ParsedFunction, Operation, OpType


def _safe_op_value(op_type) -> str:
    """استخراج القيمة النصية من OpType بشكل آمن — يتجنب dual-module identity bug"""
    return op_type.value if hasattr(op_type, 'value') else str(op_type)


# String values for safe comparison
_STATE_READ_VALUES = {OpType.STATE_READ.value, OpType.MAPPING_ACCESS.value}
_STATE_WRITE_VALUE = OpType.STATE_WRITE.value
_EXTERNAL_CALL_VALUES = {OpType.EXTERNAL_CALL.value, OpType.EXTERNAL_CALL_ETH.value, OpType.DELEGATECALL.value}
_EMIT_VALUE = OpType.EMIT.value


class FunctionEffectModeler:
    """
    يبني نموذج ΔState = f(inputs) لكل دالة.

    يأخذ:
    - ParsedContracts (من الـ parser)
    - StateMutations (من StateMutationTracker)

    ويبني:
    - FunctionEffect لكل دالة مع:
      - تبعيات cross-function
      - تعارضات write-write
      - attack surface analysis

    Usage:
        modeler = FunctionEffectModeler()
        effects = modeler.model(contracts, mutations)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    # ═══════════════════════════════════════════════════════════
    #  Main API
    # ═══════════════════════════════════════════════════════════

    def model(
        self,
        contracts: List[ParsedContract],
        mutations: Optional[List[StateMutation]] = None,
    ) -> List[FunctionEffect]:
        """
        بناء نماذج تأثير لكل الدوال.

        Args:
            contracts: العقود المحللة
            mutations: نماذج التحول (اختياري — لتحسين net_delta)

        Returns:
            قائمة FunctionEffect واحدة لكل دالة
        """
        effects = []
        mutation_map: Dict[str, StateMutation] = {}

        # بناء خريطة mutations للوصول السريع
        if mutations:
            for m in mutations:
                key = f"{m.contract_name}.{m.function_name}"
                mutation_map[key] = m

        for contract in contracts:
            if contract.contract_type in ("interface", "library"):
                continue
            for fname, func in contract.functions.items():
                effect = self._build_effect(
                    contract, func,
                    mutation_map.get(f"{contract.name}.{fname}"),
                )
                effects.append(effect)

        # ─── Cross-function dependency analysis ───
        self._resolve_cross_function_deps(effects, contracts)

        return effects

    # ═══════════════════════════════════════════════════════════
    #  Effect Construction
    # ═══════════════════════════════════════════════════════════

    def _build_effect(
        self,
        contract: ParsedContract,
        func: ParsedFunction,
        mutation: Optional[StateMutation] = None,
    ) -> FunctionEffect:
        """
        بناء FunctionEffect واحد لدالة.
        """
        # بناء signature
        param_types = [p.get("type", "?") for p in func.parameters]
        sig = f"{func.name}({','.join(param_types)})"

        effect = FunctionEffect(
            function_name=func.name,
            contract_name=contract.name,
            signature=sig,
            parameters=[
                {"name": p.get("name", ""), "type": p.get("type", "")}
                for p in func.parameters
            ],
            reentrancy_guarded=func.has_reentrancy_guard,
        )

        # ─── Analyze function body ───
        self._extract_reads_writes(effect, func, contract)
        self._extract_external_effects(effect, func)
        self._extract_access_requirements(effect, func)

        # ─── Use mutation data for net_delta if available ───
        if mutation:
            effect.net_delta = mutation.net_effect.copy()
            # تحسين reads/writes من mutation
            for r in mutation.state_reads:
                if r not in effect.reads:
                    effect.reads.append(r)
            for w in mutation.state_writes:
                if w not in effect.writes:
                    effect.writes.append(w)

        return effect

    def _extract_reads_writes(
        self, effect: FunctionEffect,
        func: ParsedFunction, contract: ParsedContract,
    ) -> None:
        """
        استخراج القراءات والكتابات من عمليات الدالة.
        """
        state_var_names = set(contract.state_vars.keys())

        for op in func.operations:
            op_val = _safe_op_value(op.op_type)
            # State reads
            if op_val in _STATE_READ_VALUES:
                if op.target and op.target not in effect.reads:
                    effect.reads.append(op.target)

            # State writes
            elif op_val == _STATE_WRITE_VALUE:
                if op.target and op.target not in effect.writes:
                    effect.writes.append(op.target)

                # بناء net_delta بسيط إذا لم يكن هناك mutation
                if not effect.net_delta and op.target:
                    raw = op.raw_text.strip().rstrip(';')
                    if '+=' in raw:
                        parts = raw.split('+=', 1)
                        effect.net_delta[op.target] = f"+{parts[1].strip()}"
                    elif '-=' in raw:
                        parts = raw.split('-=', 1)
                        effect.net_delta[op.target] = f"-{parts[1].strip()}"
                    elif '=' in raw:
                        parts = raw.split('=', 1)
                        effect.net_delta[op.target] = f"= {parts[1].strip()}"

        # msg.value / msg.sender detection from raw body
        body = func.raw_body or ""
        if 'msg.value' in body:
            effect.msg_value_used = True
        if 'msg.sender' in body:
            effect.msg_sender_used = True

        # Reads from copy for state_reads list
        effect.reads = list(set(effect.reads) | set(func.state_reads))
        effect.writes = list(set(effect.writes) | set(func.state_writes))

    def _extract_external_effects(
        self, effect: FunctionEffect, func: ParsedFunction,
    ) -> None:
        """
        استخراج التأثيرات الخارجية (calls, ETH, events).
        """
        for op in func.operations:
            op_val = _safe_op_value(op.op_type)
            # External calls
            if op_val in _EXTERNAL_CALL_VALUES:
                call_info = {
                    "target": op.target,
                    "type": op.op_type.value,
                    "sends_eth": op.sends_eth,
                    "line": op.line,
                }

                # External reads (e.g., calling oracle.getPrice())
                if op_val == OpType.STATICCALL.value or (
                    not op.sends_eth and 'get' in (op.target or '').lower()
                ):
                    if op.target not in effect.reads_from_external:
                        effect.reads_from_external.append(op.target)

                effect.external_calls.append(call_info)
                if op.sends_eth:
                    effect.eth_sent = True

            # Events
            elif op_val == _EMIT_VALUE:
                if op.target and op.target not in effect.events_emitted:
                    effect.events_emitted.append(op.target)

    def _extract_access_requirements(
        self, effect: FunctionEffect, func: ParsedFunction,
    ) -> None:
        """
        استخراج متطلبات الوصول.
        """
        if func.has_access_control:
            effect.requires_access = True
            effect.access_roles = func.modifiers.copy()

        # Check require statements for access patterns
        for req in func.require_checks:
            req_lower = req.lower()
            if any(k in req_lower for k in ['msg.sender', 'owner', 'admin', 'role', 'auth']):
                effect.requires_access = True
                if req not in effect.access_roles:
                    effect.access_roles.append(req)

    # ═══════════════════════════════════════════════════════════
    #  Cross-Function Dependency Resolution
    # ═══════════════════════════════════════════════════════════

    def _resolve_cross_function_deps(
        self,
        effects: List[FunctionEffect],
        contracts: List[ParsedContract],
    ) -> None:
        """
        حل التبعيات بين الدوال:
        1. conflicts_with: دوال تكتب نفس المتغير الذي نكتبه (write-write conflict)
        2. depends_on: دوال تكتب ما نقرأه (read-after-write dependency)
        """
        # بناء خريطة: (contract, var) → writers / readers
        var_writers: Dict[str, List[str]] = {}  # "Contract.var" → ["func1", "func2"]
        var_readers: Dict[str, List[str]] = {}

        for effect in effects:
            for var in effect.writes:
                key = f"{effect.contract_name}.{var}"
                var_writers.setdefault(key, []).append(effect.function_name)
            for var in effect.reads:
                key = f"{effect.contract_name}.{var}"
                var_readers.setdefault(key, []).append(effect.function_name)

        # Cross-reference
        for effect in effects:
            # ─── Write-Write conflicts ───
            for var in effect.writes:
                key = f"{effect.contract_name}.{var}"
                other_writers = var_writers.get(key, [])
                for w in other_writers:
                    if w != effect.function_name and w not in effect.conflicts_with:
                        effect.conflicts_with.append(w)

            # ─── Read-After-Write dependencies ───
            for var in effect.reads:
                key = f"{effect.contract_name}.{var}"
                writers = var_writers.get(key, [])
                for w in writers:
                    if w != effect.function_name and w not in effect.depends_on:
                        effect.depends_on.append(w)

    # ═══════════════════════════════════════════════════════════
    #  Attack Surface Analysis
    # ═══════════════════════════════════════════════════════════

    def analyze_attack_surface(
        self, effects: List[FunctionEffect]
    ) -> Dict[str, Any]:
        """
        تحليل سطح الهجوم — أي دوال مكشوفة يمكن أن تؤثر على المال.

        Returns:
            {
                "exposed_financial": [...],    # دوال public تكتب balances
                "unguarded_writes": [...],     # دوال بدون access control تكتب حالة
                "eth_senders": [...],          # دوال ترسل ETH
                "delegatecall_risks": [...],   # دوال تستخدم delegatecall
                "high_impact": [...],          # دوال تكتب أكثر من 3 متغيرات
            }
        """
        surface = {
            "exposed_financial": [],
            "unguarded_writes": [],
            "eth_senders": [],
            "delegatecall_risks": [],
            "high_impact": [],
        }

        for effect in effects:
            fn_ref = f"{effect.contract_name}.{effect.function_name}"

            # Exposed financial functions (write balances without guard)
            balance_writes = [
                w for w in effect.writes
                if any(kw in w.lower() for kw in [
                    'balance', 'amount', 'supply', 'reserve',
                    'collateral', 'debt', 'stake', 'reward',
                ])
            ]
            if balance_writes and not effect.requires_access:
                surface["exposed_financial"].append({
                    "function": fn_ref,
                    "writes": balance_writes,
                    "guarded": effect.reentrancy_guarded,
                })

            # Unguarded state writes
            if effect.writes and not effect.requires_access:
                surface["unguarded_writes"].append({
                    "function": fn_ref,
                    "writes": effect.writes,
                })

            # ETH senders
            if effect.eth_sent:
                surface["eth_senders"].append({
                    "function": fn_ref,
                    "guarded": effect.reentrancy_guarded,
                    "access_required": effect.requires_access,
                })

            # Delegatecall
            for call in effect.external_calls:
                if call.get("type") == "delegatecall":
                    surface["delegatecall_risks"].append({
                        "function": fn_ref,
                        "target": call.get("target", "unknown"),
                    })

            # High impact (many state writes)
            if len(effect.writes) > 3:
                surface["high_impact"].append({
                    "function": fn_ref,
                    "write_count": len(effect.writes),
                    "writes": effect.writes,
                })

        return surface
