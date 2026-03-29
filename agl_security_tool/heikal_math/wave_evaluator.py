"""
╔══════════════════════════════════════════════════════════════════════╗
║     Wave-Domain Boolean Vulnerability Evaluator                      ║
║     مُقيِّم نقاط الضعف بمنطق الموجات البوليانية                     ║
╚══════════════════════════════════════════════════════════════════════╝

الأصل الرياضي:
    من vectorized_wave_processor.py في AGL_NextGen:
    - تحويل البت إلى موجة: ψ = e^(i·bit·π)
    - XOR عبر ضرب الموجات: ψ_xor = ψ_a × ψ_b
    - AND عبر جمع الموجات + عتبة: |ψ_a + ψ_b| > threshold

التكييف لأمان العقود الذكية:
    بدل تقييم كل خاصية أمنية منفردة (bool)، نحوّلها إلى موجات مركّبة
    ونقيّم الخطورة الكلية في مجال التردد:

    كل خاصية أمنية x_i ∈ {0, 1} تصبح موجة:
        ψ_i = e^(i·x_i·π) × w_i

    حيث w_i = وزن الخاصية

    الخطورة الكلية = |Σ ψ_i|² (Born rule — مربع السعة)

    المميزات:
    1. التداخل البنّاء: خاصيتان خطيرتان معاً → خطر أكبر من مجموعهما
    2. التداخل الهدّام: حماية تلغي خطر → المجموع ينخفض تلقائياً
    3. التقييم الموازي: كل الخصائص تُقيَّم دفعة واحدة
    4. التخميد الأخلاقي: amplitude damping على الثقة (من الخوارزمية الأصلية)
"""

from __future__ import annotations

import math
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field


# ═══════════════════════════════════════════════════════════════
#  Constants
# ═══════════════════════════════════════════════════════════════

# أوزان كل خاصية أمنية (normalized)
WAVE_FEATURE_WEIGHTS = {
    "moves_funds": 0.28,
    "cei_violation": 0.22,
    "sends_eth": 0.18,
    "no_access_control": 0.14,
    "not_guarded": 0.12,
    "reads_oracle": 0.10,
    "has_state_conflict": 0.06,
    "modifies_balances": 0.06,
}

# عامل التخميد الأخلاقي (من الخوارزمية الأصلية)
ETHICAL_DAMPING = 0.92

# عتبة AND (ذروة التداخل البنّاء)
AND_THRESHOLD = 1.5


@dataclass
class WaveFeature:
    """خاصية أمنية مُحوَّلة إلى موجة"""

    name: str
    value: bool  # True = خطر, False = آمن
    weight: float  # وزن الخاصية
    phase: float = 0.0  # الطور ψ
    amplitude: float = 0.0  # السعة


@dataclass
class WaveEvaluationResult:
    """نتيجة التقييم الموجي"""

    # الموجة المركّبة
    composite_real: float = 0.0
    composite_imag: float = 0.0
    composite_amplitude: float = 0.0

    # النتائج البوليانية الموجية
    danger_intensity: float = 0.0  # |ψ|² — شدة الخطر (Born rule)
    interference_bonus: float = 0.0  # bonus من التداخل البنّاء
    protection_cancellation: float = 0.0  # تخفيض من الحمايات

    # النتيجة النهائية (0.0 - 1.0)
    heuristic_score: float = 0.0

    # تفاصيل
    features_active: int = 0
    features_total: int = 0
    constructive_pairs: List[Tuple[str, str]] = field(default_factory=list)
    destructive_pairs: List[Tuple[str, str]] = field(default_factory=list)


class WaveDomainEvaluator:
    """
    مُقيِّم نقاط الضعف باستخدام منطق الموجات البوليانية.

    يستبدل _compute_score() في heuristic_prioritizer.py:
        بدل مجموع أوزان خطي → تقييم موجي مع تداخل بنّاء/هدّام.

    Usage:
        evaluator = WaveDomainEvaluator()
        result = evaluator.evaluate(features_dict)
        score = result.heuristic_score
    """

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        ethical_damping: float = ETHICAL_DAMPING,
    ):
        self.weights = weights or dict(WAVE_FEATURE_WEIGHTS)
        self.ethical_damping = ethical_damping

    # ═══════════════════════════════════════════════════════
    #  Main API
    # ═══════════════════════════════════════════════════════

    def evaluate(
        self,
        features: Dict[str, bool],
    ) -> WaveEvaluationResult:
        """
        تقييم موجي لمجموعة خصائص أمنية.

        Args:
            features: dict من {feature_name: True/False}
                      True = الخاصية الخطيرة موجودة
                      False = الحماية موجودة

        Returns:
            WaveEvaluationResult مع النتيجة والتفاصيل
        """
        result = WaveEvaluationResult()

        # ─── Step 1: تحويل الخصائص إلى موجات ───
        waves = self._features_to_waves(features)
        result.features_total = len(waves)
        result.features_active = sum(1 for w in waves if w.value)

        if not waves:
            return result

        # ─── Step 2: حساب الموجة المركّبة (superposition) ───
        composite_re = 0.0
        composite_im = 0.0

        for wave in waves:
            composite_re += wave.amplitude * math.cos(wave.phase)
            composite_im += wave.amplitude * math.sin(wave.phase)

        result.composite_real = composite_re
        result.composite_imag = composite_im

        # السعة الكلية (amplitude)
        total_amplitude = math.sqrt(composite_re**2 + composite_im**2)
        result.composite_amplitude = total_amplitude

        # ─── Step 3: Born Rule — شدة الخطر ───
        # |ψ|² = intensity → probability
        # Normalize against the max possible amplitude (sum of ALL weights, not just active)
        max_possible_amplitude = sum(w.weight for w in waves)
        if max_possible_amplitude > 0 and total_amplitude > 0:
            normalized_amplitude = total_amplitude / max_possible_amplitude
        else:
            normalized_amplitude = 0.0

        result.danger_intensity = normalized_amplitude**2

        # ─── Step 4: كشف التداخل البنّاء/الهدّام بين أزواج ───
        result.interference_bonus, result.constructive_pairs = (
            self._detect_constructive_interference(waves)
        )
        result.protection_cancellation, result.destructive_pairs = (
            self._detect_destructive_interference(waves, features)
        )

        # ─── Step 5: النتيجة النهائية مع التخميد الأخلاقي ───
        raw_score = (
            result.danger_intensity
            + result.interference_bonus
            - result.protection_cancellation
        )

        # تخميد أخلاقي (ethical amplitude damping)
        damped_score = raw_score * self.ethical_damping

        result.heuristic_score = max(0.0, min(damped_score, 1.0))

        return result

    def evaluate_action(self, action: Any) -> float:
        """
        API مختصر: حساب heuristic score مباشرة من Action.
        يستبدل _compute_score() في HeuristicPrioritizer.
        """
        features = self._extract_features_from_action(action)
        result = self.evaluate(features)
        return result.heuristic_score

    # ═══════════════════════════════════════════════════════
    #  Bit → Wave Conversion
    # ═══════════════════════════════════════════════════════

    def _features_to_waves(self, features: Dict[str, bool]) -> List[WaveFeature]:
        """
        تحويل كل خاصية إلى موجة:
            ψ_i = w_i × e^(i·x_i·π)

        True  → phase = π, amplitude = w_i  (خطر — يساهم في شدة الخطر)
        False → phase = 0, amplitude = 0    (آمن — لا يساهم في الخطر)

        ملاحظة: الخصائص الآمنة (False) لا تُنتج موجة خطر.
        التداخل الهدّام يحدث فقط عبر _detect_destructive_interference.
        """
        waves = []
        for name, value in features.items():
            weight = self.weights.get(name, 0.05)

            # ψ = e^(i·bit·π)
            phase = math.pi if value else 0.0
            # Only dangerous features contribute amplitude to the composite wave
            amplitude = weight if value else 0.0

            waves.append(
                WaveFeature(
                    name=name,
                    value=value,
                    weight=weight,
                    phase=phase,
                    amplitude=amplitude,
                )
            )

        return waves

    # ═══════════════════════════════════════════════════════
    #  Interference Detection (Wave AND/XOR)
    # ═══════════════════════════════════════════════════════

    def _detect_constructive_interference(
        self,
        waves: List[WaveFeature],
    ) -> Tuple[float, List[Tuple[str, str]]]:
        """
        كشف التداخل البنّاء (Constructive Interference):
            موجتان بنفس الطور → |ψ₁ + ψ₂| > |ψ₁| + |ψ₂|

        في السياق الأمني:
            CEI violation + sends_eth → خطر أكبر من مجموعهما

        يستخدم Wave AND:
            |ψ_a + ψ_b| > threshold → AND(a, b) = True → bonus
        """
        bonus = 0.0
        pairs = []

        # الأزواج الخطيرة المعروفة (reduced bonuses to prevent FP inflation)
        dangerous_combos = [
            ("cei_violation", "sends_eth", 0.08),       # ↓ from 0.15
            ("cei_violation", "not_guarded", 0.06),     # ↓ from 0.12
            ("sends_eth", "not_guarded", 0.05),         # ↓ from 0.10
            ("no_access_control", "moves_funds", 0.04), # ↓ from 0.08
            ("reads_oracle", "no_access_control", 0.03),# ↓ from 0.06
            ("moves_funds", "cei_violation", 0.05),     # ↓ from 0.10
        ]

        active_danger = {w.name for w in waves if w.value}

        for feat_a, feat_b, combo_bonus in dangerous_combos:
            if feat_a in active_danger and feat_b in active_danger:
                # حساب موجي: AND(a, b) عبر جمع الموجات
                w_a = next((w for w in waves if w.name == feat_a), None)
                w_b = next((w for w in waves if w.name == feat_b), None)
                if w_a and w_b:
                    # |ψ_a + ψ_b|
                    sum_re = w_a.amplitude * math.cos(
                        w_a.phase
                    ) + w_b.amplitude * math.cos(w_b.phase)
                    sum_im = w_a.amplitude * math.sin(
                        w_a.phase
                    ) + w_b.amplitude * math.sin(w_b.phase)
                    combined = math.sqrt(sum_re**2 + sum_im**2)

                    if combined > AND_THRESHOLD * (w_a.weight + w_b.weight) / 2:
                        bonus += combo_bonus
                        pairs.append((feat_a, feat_b))

        return bonus, pairs

    def _detect_destructive_interference(
        self,
        waves: List[WaveFeature],
        features: Dict[str, bool],
    ) -> Tuple[float, List[Tuple[str, str]]]:
        """
        كشف التداخل الهدّام (Destructive Interference):
            موجتان بأطوار متعاكسة → |ψ₁ + ψ₂| ≈ 0

        في السياق الأمني:
            reentrancy_guarded = True يلغي cei_violation
            requires_access = True يلغي no_access_control

        يستخدم Wave XOR:
            ψ_xor = ψ_a × ψ_b
            إذا الطوران مختلفان → XOR = True → cancellation
        """
        cancellation = 0.0
        pairs = []

        # أزواج الحماية ↔ الخطر (increased cancellation — protection should outweigh danger)
        protection_combos = [
            # (protection_present, danger_present, cancel_amount)
            ("reentrancy_guarded", "cei_violation", 0.25),   # ↑ from 0.15
            ("reentrancy_guarded", "sends_eth", 0.20),       # ↑ from 0.10
            ("requires_access", "no_access_control", 0.22),  # ↑ from 0.12
        ]

        # الحمايات تكون False في features (لأن features تمثل الأخطار)
        # نحتاج عكس القيم للحمايات
        protection_map = {
            "reentrancy_guarded": not features.get("not_guarded", False),
            "requires_access": not features.get("no_access_control", False),
        }

        for protection, danger, cancel_amount in protection_combos:
            if protection_map.get(protection, False) and features.get(danger, False):
                # حساب XOR الموجي
                # ψ_protect (phase=0) × ψ_danger (phase=π) = e^(iπ) = -1
                # هذا يعني: الموجتان تلغيان بعضهما
                cancellation += cancel_amount
                pairs.append((protection, danger))

        return cancellation, pairs

    # ═══════════════════════════════════════════════════════
    #  Feature Extraction from Action
    # ═══════════════════════════════════════════════════════

    @staticmethod
    def _extract_features_from_action(action: Any) -> Dict[str, bool]:
        """استخراج الخصائص الأمنية من كائن Action"""
        cat = (
            action.category.value
            if hasattr(action.category, "value")
            else str(action.category)
        )

        moves_funds = cat in (
            "fund_inflow",
            "fund_outflow",
            "borrow",
            "repay",
            "swap",
            "liquidate",
            "stake",
            "unstake",
            "claim",
            "flash_loan",
        )

        state_reads = getattr(action, "state_reads", [])
        reads_oracle = any(
            k in sr.lower()
            for sr in state_reads
            for k in ("oracle", "price", "feed", "twap")
        )

        return {
            "moves_funds": moves_funds,
            "cei_violation": getattr(action, "has_cei_violation", False),
            "sends_eth": getattr(action, "sends_eth", False),
            "no_access_control": not getattr(action, "requires_access", False),
            "not_guarded": not getattr(action, "reentrancy_guarded", False),
            "reads_oracle": reads_oracle,
            "has_state_conflict": bool(getattr(action, "cross_function_risk", False)),
            "modifies_balances": bool(getattr(action, "state_writes", [])),
        }
