"""
╔══════════════════════════════════════════════════════════════════════╗
║     Resonance Profit Optimizer — مُحسِّن الربح بالرنين                ║
╚══════════════════════════════════════════════════════════════════════╝

الأصل الرياضي:
    من Resonance_Optimizer.py:
    - دالة الاستجابة الرنينية: A(ω) = 1 / √((ω₀² - ω²)² + (γω)²)
    - عند ω ≈ ω₀ → A يصل الذروة (resonance peak)
    - Vectorized batch processing لـ 8M+ قرار/ثانية

التكييف لتحسين أرباح الهجوم:
    بدل Hill Climbing الخطي (multipliers = [1.1, 0.9, 2.0, ...])
    نبحث عن "ترددات رنين" في دالة الربح:

    profit(θ) حيث θ = amount

    الخطوات:
    1. مسح ترددي (frequency sweep): نجرب θ عند ترددات مختلفة
    2. لكل تردد: نحسب A(ω) = استجابة الربح
    3. نكتشف ذروات الرنين (resonance peaks) — القيم المثلى لـ θ
    4. نحسّن عند كل ذروة بدقة عالية

    لماذا أفضل من Hill Climbing؟
    - Hill Climbing يعلق في local maxima
    - Resonance scanning يجد كل القمم (global + local) دفعة واحدة
    - الرنين يكشف "ترددات طبيعية" للعقد (مبالغ يتفاعل معها العقد بشكل أقصى)

    مثال: عقد DeFi فيه threshold عند 100 ETH:
    - Hill Climbing من 1 ETH: يتسلق ببطء... 1.1, 1.21, ... (آلاف المحاولات)
    - Resonance scan: يكتشف ذروة عند ~100 ETH مباشرة (عشرات المحاولات)
"""

from __future__ import annotations

import math
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field


# ═══════════════════════════════════════════════════════════════
#  Constants — from Heikal Resonance_Optimizer
# ═══════════════════════════════════════════════════════════════

HEIKAL_XI = 0.4671  # ξ — ثابت هيكل
RESONANCE_GAMMA = 0.15  # γ — عرض ذروة الرنين (damping)
FREQUENCY_BANDS = 12  # عدد حزم التردد للمسح
FINE_TUNING_STEPS = 5  # خطوات الضبط الدقيق عند كل ذروة
WEI_PER_ETH = 10**18


@dataclass
class ResonancePeak:
    """ذروة رنين واحدة — نقطة مثلى محتملة"""

    frequency: float  # ω — التردد
    amplitude: float  # A(ω) — استجابة الربح
    theta_value: int  # θ — قيمة المعامل (amount/msg_value)
    profit_usd: float  # الربح عند هذه القيمة
    is_global_max: bool = False


@dataclass
class ResonanceOptimizationResult:
    """نتيجة التحسين بالرنين"""

    original_profit: float = 0.0
    best_profit: float = 0.0
    best_theta: int = 0
    improvement_usd: float = 0.0
    improvement_pct: float = 0.0

    peaks_found: int = 0
    peaks: List[ResonancePeak] = field(default_factory=list)
    evaluations_count: int = 0

    natural_frequencies: List[float] = field(default_factory=list)


class ResonanceProfitOptimizer:
    """
    مُحسِّن الربح باستخدام المسح الرنيني.

    يستبدل Hill Climbing في profit_gradient.py:
        بدل multipliers = [1.1, 0.9, 2.0, ...]
        → frequency sweep يكتشف كل القمم دفعة واحدة.

    Usage:
        optimizer = ResonanceProfitOptimizer()
        result = optimizer.optimize_amount(
            current_value=1_000_000_000_000_000_000,  # 1 ETH
            evaluate_fn=lambda val: simulate(val),  # returns profit in USD
        )
        best_value = result.best_theta
        best_profit = result.best_profit
    """

    def __init__(
        self,
        gamma: float = RESONANCE_GAMMA,
        num_bands: int = FREQUENCY_BANDS,
        fine_steps: int = FINE_TUNING_STEPS,
        xi: float = HEIKAL_XI,
    ):
        self.gamma = gamma
        self.num_bands = num_bands
        self.fine_steps = fine_steps
        self.xi = xi

    # ═══════════════════════════════════════════════════════
    #  Main API
    # ═══════════════════════════════════════════════════════

    def optimize_amount(
        self,
        current_value: int,
        evaluate_fn: Callable[[int], float],
        min_value: int = 1,
        max_value: int = 10000 * WEI_PER_ETH,
        known_thresholds: Optional[List[int]] = None,
    ) -> ResonanceOptimizationResult:
        """
        تحسين مبلغ (amount أو msg_value) باستخدام المسح الرنيني.

        Args:
            current_value: القيمة الحالية
            evaluate_fn: دالة تأخذ value وتُرجع profit_usd
            min_value: الحد الأدنى
            max_value: الحد الأقصى
            known_thresholds: عتبات معروفة من التحليل الستاتيكي

        Returns:
            ResonanceOptimizationResult
        """
        result = ResonanceOptimizationResult()
        result.original_profit = evaluate_fn(current_value)
        result.evaluations_count += 1

        # ─── Step 1: حساب الترددات الطبيعية ───
        natural_freqs = self._compute_natural_frequencies(
            current_value, min_value, max_value, known_thresholds
        )
        result.natural_frequencies = natural_freqs

        # ─── Step 2: مسح ترددي (frequency sweep) ───
        peaks = self._frequency_sweep(
            natural_freqs, current_value, evaluate_fn, min_value, max_value, result
        )

        # ─── Step 3: ضبط دقيق عند كل ذروة ───
        refined_peaks = self._fine_tune_peaks(
            peaks, evaluate_fn, min_value, max_value, result
        )

        # ─── Step 4: اختيار أفضل ذروة ───
        result.peaks = refined_peaks
        result.peaks_found = len(refined_peaks)

        if refined_peaks:
            best = max(refined_peaks, key=lambda p: p.profit_usd)
            best.is_global_max = True
            result.best_profit = best.profit_usd
            result.best_theta = best.theta_value
        else:
            result.best_profit = result.original_profit
            result.best_theta = current_value

        result.improvement_usd = result.best_profit - result.original_profit
        if result.original_profit > 0:
            result.improvement_pct = (
                result.improvement_usd / result.original_profit * 100
            )

        return result

    def generate_resonance_multipliers(
        self,
        current_value: int,
        known_thresholds: Optional[List[int]] = None,
    ) -> List[float]:
        """
        API بسيط: يُرجع multipliers محسوبة بالرنين بدل القائمة الثابتة.

        يستبدل مباشرة:
            multipliers = [1.1, 0.9, 2.0, 5.0, 10.0, 0.5, 0.1, 0.01]
        بـ:
            multipliers = resonance.generate_resonance_multipliers(current_value)
        """
        natural_freqs = self._compute_natural_frequencies(
            current_value, 1, current_value * 100, known_thresholds
        )

        multipliers = set()
        for omega in natural_freqs:
            # resonance amplitude
            A = self._resonance_amplitude(omega, natural_freqs)

            # تحويل التردد إلى multiplier
            if omega > 0 and current_value > 0:
                theta = self._frequency_to_value(omega, current_value)
                mult = theta / current_value
                if 0.001 <= mult <= 1000 and mult != 1.0:
                    multipliers.add(round(mult, 4))

        # إضافة multipliers أساسية إذا الرنين لم يجد كثيرًا
        base_multipliers = {1.1, 0.9, 2.0, 0.5, 10.0, 0.1}
        multipliers.update(base_multipliers)

        # ترتيب بالأهمية (أقرب للقيمة الحالية أولاً)
        sorted_mults = sorted(multipliers, key=lambda m: abs(math.log(max(m, 0.001))))

        return sorted_mults[: self.num_bands]

    # ═══════════════════════════════════════════════════════
    #  Natural Frequencies — ترددات العقد الطبيعية
    # ═══════════════════════════════════════════════════════

    def _compute_natural_frequencies(
        self,
        current_value: int,
        min_value: int,
        max_value: int,
        known_thresholds: Optional[List[int]] = None,
    ) -> List[float]:
        """
        حساب الترددات الطبيعية لفضاء البحث.

        اللوغاريتمي: ω_n = e^(n·ln(max/min)/N) × min
        + ترددات إضافية من عتبات معروفة.

        هذا يكافئ: quantized energy levels in a potential well
        """
        freqs = []

        if max_value <= min_value or min_value <= 0:
            return [1.0]

        log_min = math.log(max(min_value, 1))
        log_max = math.log(max(max_value, 2))
        log_range = log_max - log_min

        if log_range <= 0:
            return [1.0]

        # Logarithmic frequency bands
        for n in range(self.num_bands):
            log_omega = log_min + (n + 0.5) * log_range / self.num_bands
            omega = math.exp(log_omega)
            freqs.append(omega)

        # إضافة التردد الحالي
        freqs.append(float(max(current_value, 1)))

        # إضافة ترددات من عتبات معروفة
        if known_thresholds:
            for threshold in known_thresholds:
                if min_value <= threshold <= max_value:
                    freqs.append(float(threshold))
                    # إضافة harmonics (توافقيات)
                    for harmonic in [0.5, 0.99, 1.01, 2.0]:
                        h_val = threshold * harmonic
                        if min_value <= h_val <= max_value:
                            freqs.append(h_val)

        # Heikal correction: إضافة ترددات مشتقة من ثابت هيكل
        xi_freq = current_value * (1.0 + self.xi)
        if min_value <= xi_freq <= max_value:
            freqs.append(xi_freq)

        # إزالة التكرارات وترتيب
        freqs = sorted(set(freqs))
        return freqs

    # ═══════════════════════════════════════════════════════
    #  Frequency Sweep — المسح الترددي
    # ═══════════════════════════════════════════════════════

    def _frequency_sweep(
        self,
        natural_freqs: List[float],
        current_value: int,
        evaluate_fn: Callable[[int], float],
        min_value: int,
        max_value: int,
        result: ResonanceOptimizationResult,
    ) -> List[ResonancePeak]:
        """
        مسح ترددي: تقييم الربح عند كل تردد طبيعي.

        لكل ω_n:
            1. θ_n = self._frequency_to_value(ω_n)
            2. profit_n = evaluate_fn(θ_n)
            3. A_n = resonance_amplitude(ω_n)
            4. إذا profit_n > 0 → ذروة محتملة
        """
        peaks = []

        for omega in natural_freqs:
            theta = self._frequency_to_value(omega, current_value)
            theta = max(min_value, min(theta, max_value))
            theta = int(theta)

            if theta <= 0:
                continue

            profit = evaluate_fn(theta)
            result.evaluations_count += 1

            amplitude = self._resonance_amplitude(omega, natural_freqs)

            if profit > 0 or amplitude > 2.0:
                peaks.append(
                    ResonancePeak(
                        frequency=omega,
                        amplitude=amplitude,
                        theta_value=theta,
                        profit_usd=profit,
                    )
                )

        return peaks

    # ═══════════════════════════════════════════════════════
    #  Fine Tuning — ضبط دقيق عند الذروات
    # ═══════════════════════════════════════════════════════

    def _fine_tune_peaks(
        self,
        peaks: List[ResonancePeak],
        evaluate_fn: Callable[[int], float],
        min_value: int,
        max_value: int,
        result: ResonanceOptimizationResult,
    ) -> List[ResonancePeak]:
        """
        ضبط دقيق عند كل ذروة رنين.

        يُضيّق نطاق البحث حول كل ذروة ويبحث عن القيمة المثلى.
        هذا يشبه "zoom into resonance peak" — بدل مسح عريض، نركّز.
        """
        refined = []

        # ترتيب بالربح (أفضل أولاً)
        sorted_peaks = sorted(peaks, key=lambda p: p.profit_usd, reverse=True)

        # ضبط أفضل 5 ذروات فقط (budget)
        for peak in sorted_peaks[:5]:
            best_theta = peak.theta_value
            best_profit = peak.profit_usd

            # نطاق الضبط: ±20% حول الذروة
            for step in range(self.fine_steps):
                # تضييق متزايد: ±20%, ±10%, ±5%, ±2.5%, ±1.25%
                shrink = 0.2 / (2**step)

                # جرب أعلى وأدنى
                for direction in [1, -1]:
                    delta = max(1, int(best_theta * shrink * direction))
                    candidate = best_theta + delta
                    candidate = max(min_value, min(candidate, max_value))

                    if candidate <= 0 or candidate == best_theta:
                        continue

                    profit = evaluate_fn(candidate)
                    result.evaluations_count += 1

                    if profit > best_profit:
                        best_profit = profit
                        best_theta = candidate

            refined.append(
                ResonancePeak(
                    frequency=peak.frequency,
                    amplitude=peak.amplitude,
                    theta_value=best_theta,
                    profit_usd=best_profit,
                )
            )

        return refined

    # ═══════════════════════════════════════════════════════
    #  Resonance Amplitude — دالة الاستجابة الرنينية
    # ═══════════════════════════════════════════════════════

    def _resonance_amplitude(self, omega: float, natural_freqs: List[float]) -> float:
        """
        A(ω) = Σ_n 1 / √((ω_n² - ω²)² + (γω)²)

        حيث:
            ω = التردد الحالي
            ω_n = الترددات الطبيعية
            γ = معامل التخميد

        عند ω ≈ ω_n → A يصل الذروة (resonance)
        """
        total = 0.0

        for omega_n in natural_freqs:
            if omega_n <= 0:
                continue

            delta_sq = (omega_n**2 - omega**2) ** 2
            damping_sq = (self.gamma * omega) ** 2
            denominator = math.sqrt(delta_sq + damping_sq)

            if denominator > 0:
                total += 1.0 / denominator
            else:
                total += 10.0  # perfect resonance

        return min(total, 50.0)  # clamp

    # ═══════════════════════════════════════════════════════
    #  Helpers
    # ═══════════════════════════════════════════════════════

    @staticmethod
    def _frequency_to_value(omega: float, reference: int) -> int:
        """تحويل تردد إلى قيمة (amount)"""
        if omega <= 0:
            return reference
        # ω ∝ √(value) → value ∝ ω²
        # لكن في المجال اللوغاريتمي: value ≈ omega (مباشر)
        return max(1, int(omega))
