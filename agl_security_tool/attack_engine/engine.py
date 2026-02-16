"""
AGL Attack Engine — Main Orchestrator (Layer 3 Engine)
المحرك الرئيسي لمحاكاة الهجمات

═══════════════════════════════════════════════════════════════
Economic Physics Engine — Pipeline:

    1. Load State      ← Layer 1 FinancialGraph → ProtocolState
    2. Convert Actions ← Layer 2 ActionSpace → ExecutableActions
    3. Execute         ← Semantic Execution → StateDelta[]
    4. Compute Profit  ← Profit Calculator → AttackResult
    5. Return          ← SimulationSummary

هذا هو Layer 3: المحرك الذي يجيب على السؤال الوحيد:
    "هل هذه الثغرة يمكن استغلالها لتحقيق ربح؟"
═══════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import time
from typing import Dict, List, Any, Optional, TYPE_CHECKING

from .models import (
    ProtocolState,
    ExecutableAction,
    StateDelta,
    StepResult,
    AttackResult,
    SimulationConfig,
    SimulationSummary,
)
from .protocol_state import ProtocolStateLoader, ATTACKER_ADDRESS
from .state_mutator import StateMutator, StateStack
from .action_executor import ActionExecutor
from .economic_engine import EconomicEngine
from .profit_calculator import ProfitCalculator


WEI_PER_ETH = 10 ** 18


class AttackSimulationEngine:
    """
    محرك محاكاة الهجمات — Layer 3.

    يأخذ نتائج Layer 1 (FinancialGraph) و Layer 2 (ActionSpace)
    ويُحاكي كل تسلسل هجوم لحساب الربح.

    النتيجة النهائية: SimulationSummary مع كل الهجمات المربحة.
    """

    VERSION = "1.0.0"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        sim_config = self._build_config(config or {})
        self.config = sim_config
        self.state_loader = ProtocolStateLoader(sim_config)
        self.executor = ActionExecutor(sim_config)
        self.mutator = StateMutator()
        self.economic = EconomicEngine(sim_config)
        self.profit_calc = ProfitCalculator(sim_config)

    # ═══════════════════════════════════════════════════════
    #  Main Entry: simulate_all
    # ═══════════════════════════════════════════════════════

    def simulate_all(
        self,
        graph: Any,
        action_space: Any,
    ) -> SimulationSummary:
        """
        تشغيل كل سيناريوهات الهجوم.

        Pipeline:
        1. تحميل الحالة الأولية من Layer 1
        2. استخراج تسلسلات الهجوم من Layer 2
        3. محاكاة كل تسلسل
        4. ترتيب النتائج حسب الربح
        5. إرجاع الملخص
        """
        t0 = time.time()
        summary = SimulationSummary(version=self.VERSION)

        # === 1. تحميل الحالة الأولية ===
        try:
            initial_state = self.state_loader.load_from_graph(graph)
        except Exception as e:
            summary.errors.append(f"فشل تحميل الحالة: {str(e)[:200]}")
            return summary

        # === 2. استخراج التسلسلات ===
        sequences = self._extract_sequences(action_space)
        if not sequences:
            summary.warnings.append("لا توجد تسلسلات هجوم للمحاكاة")
            # حاول إنشاء تسلسلات تلقائية
            sequences = self._generate_auto_sequences(action_space)

        summary.total_sequences_tested = len(sequences)

        # === 3. محاكاة كل تسلسل ===
        for i, sequence in enumerate(sequences):
            try:
                result = self.simulate_sequence(
                    sequence, initial_state, sequence_id=f"seq_{i}"
                )
                summary.all_results.append(result)

                if result.is_profitable:
                    summary.profitable_attacks += 1
                    summary.total_profit_usd += result.net_profit_usd

                    # تتبع أنواع الهجمات
                    at = result.attack_type
                    summary.attack_types_found[at] = \
                        summary.attack_types_found.get(at, 0) + 1
                    sev = result.severity
                    summary.severity_distribution[sev] = \
                        summary.severity_distribution.get(sev, 0) + 1

            except Exception as e:
                summary.errors.append(
                    f"خطأ في التسلسل {i}: {str(e)[:200]}"
                )

        # === 4. أفضل هجوم ===
        profitable = [r for r in summary.all_results if r.is_profitable]
        if profitable:
            summary.best_attack = max(profitable, key=lambda r: r.net_profit_usd)

        summary.execution_time_ms = (time.time() - t0) * 1000
        return summary

    # ═══════════════════════════════════════════════════════
    #  Simulate Single Sequence
    # ═══════════════════════════════════════════════════════

    def simulate_sequence(
        self,
        sequence: List[Dict[str, Any]],
        initial_state: ProtocolState,
        sequence_id: str = "",
    ) -> AttackResult:
        """
        محاكاة تسلسل هجوم واحد.

        Pipeline لكل خطوة:
        1. snapshot الحالة
        2. تحويل Step → ExecutableAction
        3. تنفيذ (executor.execute)
        4. إذا نجح → apply delta
        5. إذا فشل → revert to snapshot
        """
        t0 = time.time()

        # لقطة الحالة الأولية
        state_stack = StateStack(initial_state)
        steps_results: List[StepResult] = []
        attack_type = ""

        for step_idx, step_info in enumerate(sequence):
            # === تحويل لـ ExecutableAction ===
            exec_action = self._convert_to_executable(step_info, state_stack.current)

            if not exec_action:
                steps_results.append(StepResult(
                    step_index=step_idx,
                    action_id=step_info.get("action_id", "unknown"),
                    function_name=step_info.get("function_name", "unknown"),
                    success=False,
                    error="تعذر تحويل الخطوة لـ ExecutableAction",
                ))
                continue

            # === Snapshot قبل التنفيذ ===
            snap_id = state_stack.snapshot()

            # === تنفيذ ===
            delta = self.executor.execute(exec_action, state_stack.current)

            if delta.reverted:
                # فشل → تراجع
                state_stack.revert_to(snap_id)
                steps_results.append(StepResult(
                    step_index=step_idx,
                    action_id=exec_action.action_id,
                    function_name=exec_action.function_name,
                    contract_name=exec_action.contract_name,
                    delta=delta,
                    success=False,
                    error=delta.revert_reason,
                    gas_used=delta.gas_used,
                ))
                continue

            # === نجح → تطبيق الدلتا ===
            state_stack.apply(delta)

            # حساب ETH المحولة
            eth_transferred = 0
            reentrancy_calls = 0
            for bc in delta.balance_changes:
                if bc.token == "ETH" and bc.account == ATTACKER_ADDRESS and bc.amount > 0:
                    eth_transferred += bc.amount
            for event in delta.events:
                if "REENTRANCY" in event:
                    # استخراج عدد الاستدعاءات
                    import re
                    m = re.search(r'×\s*(\d+)', event)
                    if m:
                        reentrancy_calls = int(m.group(1))

            # تحديد نوع الهجوم
            if exec_action.has_cei_violation and exec_action.sends_eth:
                attack_type = "reentrancy"
            elif not attack_type:
                attack_type = step_info.get("attack_type", "direct_profit")

            steps_results.append(StepResult(
                step_index=step_idx,
                action_id=exec_action.action_id,
                function_name=exec_action.function_name,
                contract_name=exec_action.contract_name,
                delta=delta,
                success=True,
                gas_used=delta.gas_used,
                eth_transferred=eth_transferred,
                reentrancy_calls=reentrancy_calls,
            ))

        # === حساب الربح ===
        result = self.profit_calc.calculate(
            initial_state=state_stack.base,
            final_state=state_stack.current,
            attacker_address=ATTACKER_ADDRESS,
            steps=steps_results,
            attack_type=attack_type,
            sequence_id=sequence_id,
        )

        result.execution_time_ms = (time.time() - t0) * 1000
        return result

    # ═══════════════════════════════════════════════════════
    #  Sequence Extraction from Layer 2
    # ═══════════════════════════════════════════════════════

    def _extract_sequences(
        self, action_space: Any
    ) -> List[List[Dict[str, Any]]]:
        """استخراج تسلسلات الهجوم من ActionSpace (Layer 2)"""
        sequences = []

        if action_space is None:
            return sequences

        # الحصول على الأفعال من الغراف لتحويل البيانات الكاملة
        graph = getattr(action_space, 'graph', None)
        all_actions = getattr(graph, 'actions', {}) if graph else {}

        # 1. attack_sequences من ActionSpace
        attack_seqs = getattr(action_space, 'attack_sequences', [])
        for seq_info in attack_seqs:
            raw_steps = seq_info.get("steps", [])
            if not raw_steps:
                continue
            resolved_steps = []
            for step in raw_steps:
                # L2 يخزن action_id تحت مفتاح "action"، L3 يتوقع "action_id"
                action_id = step.get("action_id") or step.get("action", "")
                if action_id and action_id in all_actions:
                    # تحويل كامل من كائن Action (يملأ كل الحقول المطلوبة)
                    resolved_steps.append(
                        self._action_to_step_info(all_actions[action_id])
                    )
                else:
                    # fallback: أضف action_id المفقود وأرسل كما هو
                    if "action_id" not in step and "action" in step:
                        step = dict(step, action_id=step["action"])
                    resolved_steps.append(step)
            if resolved_steps:
                sequences.append(resolved_steps)

        # 2. attack_paths من ActionGraph
        if graph:
            attack_paths = graph.get_attack_paths() if hasattr(graph, 'get_attack_paths') else []
            for path in attack_paths:
                # كل path هو [action_id1, action_id2, ...]
                steps = []
                for action_id in path:
                    if action_id in all_actions:
                        steps.append(self._action_to_step_info(all_actions[action_id]))
                if steps:
                    sequences.append(steps)

        return sequences

    def _generate_auto_sequences(
        self, action_space: Any
    ) -> List[List[Dict[str, Any]]]:
        """
        توليد تسلسلات هجوم تلقائية من الأفعال الفردية.
        يُستخدم عندما لا توجد تسلسلات مُعدة.

        الاستراتيجيات:
        1. كل فعل reentrancy → تسلسل deposit+reentrancy_withdraw
        2. كل فعل FUND_OUTFLOW بدون guard → تسلسل deposit+withdraw
        """
        sequences = []

        if action_space is None:
            return sequences

        graph = getattr(action_space, 'graph', None)
        if not graph:
            return sequences

        actions = getattr(graph, 'actions', {})

        # ابحث عن دوال مثيرة للاهتمام
        deposit_actions = []
        vulnerable_withdrawals = []

        for action_id, action in actions.items():
            cat = action.category.value if hasattr(action.category, 'value') else str(action.category)

            if cat == "fund_inflow" and not action.requires_access:
                deposit_actions.append(action)

            if (
                cat == "fund_outflow"
                and not action.requires_access
                and action.has_cei_violation
                and action.sends_eth
                and not action.reentrancy_guarded
            ):
                vulnerable_withdrawals.append(action)
            elif (
                cat == "fund_outflow"
                and not action.requires_access
                and not action.reentrancy_guarded
            ):
                vulnerable_withdrawals.append(action)

        # بناء تسلسلات: deposit → withdraw
        for deposit in deposit_actions:
            for withdraw in vulnerable_withdrawals:
                if deposit.contract_name == withdraw.contract_name:
                    seq = [
                        self._action_to_step_info(deposit),
                        self._action_to_step_info(withdraw),
                    ]
                    sequences.append(seq)

        return sequences

    # ═══════════════════════════════════════════════════════
    #  Action Conversion
    # ═══════════════════════════════════════════════════════

    def _action_to_step_info(self, action: Any) -> Dict[str, Any]:
        """تحويل Layer 2 Action إلى step info dict"""
        cat = action.category.value if hasattr(action.category, 'value') else str(action.category)
        attack_types = [
            at.value if hasattr(at, 'value') else str(at)
            for at in getattr(action, 'attack_types', [])
        ]

        return {
            "action_id": action.action_id,
            "contract_name": action.contract_name,
            "function_name": action.function_name,
            "signature": getattr(action, 'signature', ''),
            "category": cat,
            "attack_type": attack_types[0] if attack_types else "direct_profit",
            "net_delta": dict(action.net_delta),
            "external_calls": list(action.external_calls),
            "sends_eth": action.sends_eth,
            "has_cei_violation": getattr(action, 'has_cei_violation', False),
            "reentrancy_guarded": getattr(action, 'reentrancy_guarded', False),
            "preconditions": list(getattr(action, 'preconditions', [])),
            "state_reads": list(getattr(action, 'state_reads', [])),
            "state_writes": list(getattr(action, 'state_writes', [])),
            "parameters": [
                {
                    "name": p.name,
                    "type": p.param_type,
                    "concrete_values": list(p.concrete_values),
                    "is_amount": p.is_amount,
                }
                for p in getattr(action, 'parameters', [])
            ],
            "msg_value": getattr(action, 'msg_value', None),
        }

    def _convert_to_executable(
        self,
        step_info: Dict[str, Any],
        state: ProtocolState,
    ) -> Optional[ExecutableAction]:
        """تحويل step info dict إلى ExecutableAction"""
        action_id = step_info.get("action_id", "")
        if not action_id:
            return None

        # حل المعاملات إلى قيم محددة
        concrete_params = self._resolve_params(step_info, state)

        # msg_value
        msg_value = 0
        category = step_info.get("category", "")
        raw_msg_value = step_info.get("msg_value")

        if category == "fund_inflow" and raw_msg_value:
            # deposit → المهاجم يرسل ETH
            msg_value = self._resolve_msg_value(raw_msg_value, state)
        elif category == "fund_inflow":
            # إيداع بمبلغ من المعاملات
            amount = concrete_params.get("amount", 0)
            if amount and isinstance(amount, int) and amount > 0:
                msg_value = amount

        exec_action = ExecutableAction(
            action_id=action_id,
            contract_name=step_info.get("contract_name", ""),
            function_name=step_info.get("function_name", ""),
            signature=step_info.get("signature", ""),
            concrete_params=concrete_params,
            msg_sender=ATTACKER_ADDRESS,
            msg_value=msg_value,
            net_delta=step_info.get("net_delta", {}),
            external_calls=step_info.get("external_calls", []),
            has_cei_violation=step_info.get("has_cei_violation", False),
            sends_eth=step_info.get("sends_eth", False),
            category=category,
            preconditions=step_info.get("preconditions", []),
            state_reads=step_info.get("state_reads", []),
            state_writes=step_info.get("state_writes", []),
            reentrancy_guarded=step_info.get("reentrancy_guarded", False),
        )

        return exec_action

    def _resolve_params(
        self,
        step_info: Dict[str, Any],
        state: ProtocolState,
    ) -> Dict[str, Any]:
        """حل المعاملات الرمزية إلى قيم محددة"""
        params = {}
        parameters = step_info.get("parameters", [])

        for p in parameters:
            name = p.get("name", "")
            concrete = p.get("concrete_values", [])
            is_amount = p.get("is_amount", False)

            if not name:
                continue

            # اختر أفضل قيمة معينة
            if concrete:
                # استخدم أول قيمة
                val = concrete[0]
                # حاول حلها
                resolved = self._resolve_symbolic_value(val, state, step_info)
                params[name] = resolved
            elif is_amount:
                # معامل مبلغ بدون قيمة → deposit_amount
                params[name] = self.config.attacker_deposit_amount
            else:
                params[name] = 0

        # إذا لم يكن هناك param "amount" وهذا action مالي → أضفه
        if "amount" not in params:
            category = step_info.get("category", "")
            if category in ("fund_inflow", "fund_outflow"):
                params["amount"] = self.config.attacker_deposit_amount

        return params

    def _resolve_symbolic_value(
        self,
        value: str,
        state: ProtocolState,
        step_info: Dict[str, Any],
    ) -> Any:
        """حل قيمة رمزية واحدة"""
        if not isinstance(value, str):
            return value

        v = value.lower().strip()

        if v == "balance_of_sender":
            contract = step_info.get("contract_name", "")
            storage = state.contract_storage.get(contract, {})
            for var_name, var_val in storage.items():
                if isinstance(var_val, dict) and 'deposit' in var_name.lower():
                    return var_val.get(ATTACKER_ADDRESS, 0)
            return self.config.attacker_deposit_amount

        if v == "contract_balance":
            contract = step_info.get("contract_name", "")
            return state.get_account(contract).eth_balance

        if v in ("uint256_max", "type(uint256).max"):
            return 2**256 - 1

        if v in ("0", "zero"):
            return 0

        if v in ("1", "one"):
            return 1

        if v in ("small_amount", "small"):
            return 1  # 1 wei

        if v in ("large_amount", "large"):
            return self.config.contract_eth_balance

        # حاول كرقم
        try:
            return int(value)
        except ValueError:
            pass

        return value  # أرجعه كما هو

    def _resolve_msg_value(
        self,
        raw: Any,
        state: ProtocolState,
    ) -> int:
        """حل msg.value"""
        if raw is None:
            return 0
        if isinstance(raw, int):
            return raw
        if isinstance(raw, str):
            v = raw.lower().strip()
            if v in ("amount", "msg.value"):
                return self.config.attacker_deposit_amount
            try:
                return int(raw)
            except ValueError:
                return self.config.attacker_deposit_amount
        return 0

    # ═══════════════════════════════════════════════════════
    #  Config Builder
    # ═══════════════════════════════════════════════════════

    @staticmethod
    def _build_config(config: Dict[str, Any]) -> SimulationConfig:
        """بناء SimulationConfig من قاموس"""
        sim = SimulationConfig()
        for key, val in config.items():
            if hasattr(sim, key):
                setattr(sim, key, val)
        return sim
