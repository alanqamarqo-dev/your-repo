"""
AGL Search Engine — Profit Gradient Engine (Component 4)
محرك تدرج الربح — أعط الصاروخ اتجاهاً أدق

═══════════════════════════════════════════════════════════════
Profit Gradient Engine

بعد أن وجدنا تسلسلاً واعداً (مثلاً deposit → withdraw يعطي $50K):
    - هل يمكن زيادة الربح بتغيير المبلغ؟
    - هل مبلغ 1 ETH أفضل أم 10 ETH أم 100 ETH؟
    - هل إضافة خطوة وسيطة تزيد الربح؟

المبدأ: Hill Climbing على دالة الربح
    profit(θ) حيث θ = {amounts, msg_value, parameter choices}

    في كل خطوة:
        1. غيّر θ بنسبة ±step%
        2. حاكِ بـ Layer 3
        3. إذا الربح زاد → تابع
        4. إذا انخفض → ارجع
        5. كرر حتى الثبات

═══════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import copy
import time
from typing import Dict, List, Any, Optional, Callable, Tuple

from .models import CandidateSequence, SearchStats


class ProfitGradientEngine:
    """
    محرك تحسين الربح — يأخذ تسلسلات واعدة ويحسّن معاملاتها.

    Integration:
        - يأخذ CandidateSequence من GuidedSearchEngine
        - يعدّل الـ parameters (amounts، msg_value)
        - يُقيّم كل تعديل بـ simulate_fn من Layer 3
        - يُرجع النسخة المحسّنة
    """

    def __init__(
        self,
        gradient_steps: int = 20,
        amount_step_pct: float = 0.1,
        min_improvement_usd: float = 10.0,
    ):
        self.gradient_steps = gradient_steps
        self.amount_step_pct = amount_step_pct
        self.min_improvement_usd = min_improvement_usd

    # ═══════════════════════════════════════════════════════
    #  Main Entry
    # ═══════════════════════════════════════════════════════

    def optimize(
        self,
        candidates: List[CandidateSequence],
        simulate_fn: Callable,
        initial_state: Any,
        stats: Optional[SearchStats] = None,
    ) -> List[CandidateSequence]:
        """
        تحسين قائمة المرشحين.

        يُحسّن فقط التسلسلات التي:
        - تمت محاكاتها بنجاح
        - ربحها > 0 أو قريبة من الربح

        Returns:
            نفس القائمة مع تحسينات
        """
        optimized: List[CandidateSequence] = []

        for candidate in candidates:
            if not candidate.simulated:
                optimized.append(candidate)
                continue

            # حسّن إذا كان مربحاً أو قريباً من الربح
            if candidate.actual_profit_usd > -200:
                improved = self._optimize_candidate(
                    candidate, simulate_fn, initial_state, stats
                )
                optimized.append(improved)
            else:
                optimized.append(candidate)

        # رتّب بالربح
        optimized.sort(key=lambda c: c.actual_profit_usd, reverse=True)
        return optimized

    # ═══════════════════════════════════════════════════════
    #  Single Candidate Optimization
    # ═══════════════════════════════════════════════════════

    def _optimize_candidate(
        self,
        candidate: CandidateSequence,
        simulate_fn: Callable,
        initial_state: Any,
        stats: Optional[SearchStats] = None,
    ) -> CandidateSequence:
        """
        Hill climbing على معاملات التسلسل.

        Optimizes:
        1. msg_value (ETH sent with each step)
        2. Parameter amounts (concrete_values for is_amount params)
        """
        best = candidate
        best.profit_before_optimization = candidate.actual_profit_usd
        current_profit = candidate.actual_profit_usd
        iteration_count = 0

        for step_idx in range(len(best.steps)):
            step = best.steps[step_idx]

            # === 1. Optimize msg_value ===
            improved, profit = self._optimize_msg_value(
                best, step_idx, simulate_fn, initial_state
            )
            if profit > current_profit + self.min_improvement_usd:
                best = improved
                current_profit = profit
                iteration_count += 1
                if stats:
                    stats.gradient_steps_taken += 1

            # === 2. Optimize parameter amounts ===
            params = step.get("parameters", [])
            for param_idx, param in enumerate(params):
                if param.get("is_amount", False):
                    improved, profit = self._optimize_param_amount(
                        best, step_idx, param_idx,
                        simulate_fn, initial_state
                    )
                    if profit > current_profit + self.min_improvement_usd:
                        best = improved
                        current_profit = profit
                        iteration_count += 1
                        if stats:
                            stats.gradient_steps_taken += 1

        if iteration_count > 0:
            best.optimized = True
            best.optimization_iterations = iteration_count
            if stats:
                improvement = current_profit - best.profit_before_optimization
                if improvement > 0:
                    stats.improved_by_gradient += 1
                    stats.total_improvement_usd += improvement

        return best

    # ═══════════════════════════════════════════════════════
    #  msg_value Optimization
    # ═══════════════════════════════════════════════════════

    def _optimize_msg_value(
        self,
        candidate: CandidateSequence,
        step_idx: int,
        simulate_fn: Callable,
        initial_state: Any,
    ) -> Tuple[CandidateSequence, float]:
        """
        Hill climbing على msg_value لخطوة معينة.

        يجرب:
        - msg_value × (1 + step%)
        - msg_value × (1 - step%)
        - msg_value × 2
        - msg_value × 10
        - msg_value / 2
        - very small value (1 wei)
        """
        step = candidate.steps[step_idx]
        original_value = step.get("msg_value", "0")

        try:
            original_int = int(original_value)
        except (ValueError, TypeError):
            original_int = 0

        if original_int == 0:
            # Try adding msg_value
            original_int = 10 ** 18  # 1 ETH

        best_candidate = candidate
        best_profit = candidate.actual_profit_usd

        # Variations to try
        multipliers = [
            1 + self.amount_step_pct,
            1 - self.amount_step_pct,
            2.0,
            5.0,
            10.0,
            0.5,
            0.1,
            0.01,
        ]

        for mult in multipliers:
            new_value = max(1, int(original_int * mult))
            if new_value == original_int:
                continue

            # Create modified candidate
            modified = self._clone_with_msg_value(
                candidate, step_idx, str(new_value)
            )

            # Simulate
            profit = self._simulate_candidate(
                modified, simulate_fn, initial_state
            )

            if profit > best_profit + self.min_improvement_usd:
                best_candidate = modified
                best_profit = profit

        return best_candidate, best_profit

    # ═══════════════════════════════════════════════════════
    #  Parameter Amount Optimization
    # ═══════════════════════════════════════════════════════

    def _optimize_param_amount(
        self,
        candidate: CandidateSequence,
        step_idx: int,
        param_idx: int,
        simulate_fn: Callable,
        initial_state: Any,
    ) -> Tuple[CandidateSequence, float]:
        """
        Hill climbing على concrete_values لمعامل كمّي.
        """
        step = candidate.steps[step_idx]
        params = step.get("parameters", [])
        if param_idx >= len(params):
            return candidate, candidate.actual_profit_usd

        param = params[param_idx]
        concrete = param.get("concrete_values", [])
        if not concrete:
            return candidate, candidate.actual_profit_usd

        best_candidate = candidate
        best_profit = candidate.actual_profit_usd

        for cv_idx, cv in enumerate(concrete):
            try:
                original = int(cv)
            except (ValueError, TypeError):
                continue

            if original == 0:
                continue

            for mult in [1.5, 2.0, 5.0, 0.5, 0.1]:
                new_val = max(1, int(original * mult))
                if new_val == original:
                    continue

                modified = self._clone_with_param(
                    candidate, step_idx, param_idx, cv_idx, new_val
                )

                profit = self._simulate_candidate(
                    modified, simulate_fn, initial_state
                )

                if profit > best_profit + self.min_improvement_usd:
                    best_candidate = modified
                    best_profit = profit

        return best_candidate, best_profit

    # ═══════════════════════════════════════════════════════
    #  Clone + Simulate Helpers
    # ═══════════════════════════════════════════════════════

    def _clone_with_msg_value(
        self,
        candidate: CandidateSequence,
        step_idx: int,
        new_value: str,
    ) -> CandidateSequence:
        """Clone candidate with modified msg_value at step_idx"""
        new_steps = [dict(s) for s in candidate.steps]
        new_steps[step_idx] = dict(new_steps[step_idx])
        new_steps[step_idx]["msg_value"] = new_value

        return CandidateSequence(
            candidate_id=f"{candidate.candidate_id}_opt",
            steps=new_steps,
            action_ids=list(candidate.action_ids),
            source=candidate.source,
            estimated_profit_usd=candidate.estimated_profit_usd,
            simulated=False,
        )

    def _clone_with_param(
        self,
        candidate: CandidateSequence,
        step_idx: int,
        param_idx: int,
        cv_idx: int,
        new_value: int,
    ) -> CandidateSequence:
        """Clone candidate with modified parameter value"""
        new_steps = []
        for i, step in enumerate(candidate.steps):
            new_step = dict(step)
            if i == step_idx:
                params = [dict(p) for p in new_step.get("parameters", [])]
                if param_idx < len(params):
                    cvs = list(params[param_idx].get("concrete_values", []))
                    if cv_idx < len(cvs):
                        cvs[cv_idx] = new_value
                        params[param_idx] = dict(params[param_idx])
                        params[param_idx]["concrete_values"] = cvs
                new_step["parameters"] = params
            new_steps.append(new_step)

        return CandidateSequence(
            candidate_id=f"{candidate.candidate_id}_opt",
            steps=new_steps,
            action_ids=list(candidate.action_ids),
            source=candidate.source,
            estimated_profit_usd=candidate.estimated_profit_usd,
            simulated=False,
        )

    def _simulate_candidate(
        self,
        candidate: CandidateSequence,
        simulate_fn: Callable,
        initial_state: Any,
    ) -> float:
        """Simulate a candidate and return profit"""
        try:
            result = simulate_fn(
                candidate.steps, initial_state,
                f"grad_{candidate.candidate_id}"
            )
            profit = getattr(result, 'net_profit_usd', 0.0)

            candidate.simulated = True
            candidate.actual_profit_usd = profit
            candidate.simulation_success = getattr(result, 'is_profitable', False)
            candidate.attack_type = getattr(result, 'attack_type', '')
            candidate.severity = getattr(result, 'severity', '')

            return profit
        except Exception:
            candidate.simulated = True
            candidate.actual_profit_usd = 0.0
            return 0.0
