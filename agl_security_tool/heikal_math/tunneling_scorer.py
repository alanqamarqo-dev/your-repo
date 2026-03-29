"""
╔══════════════════════════════════════════════════════════════════════╗
║     Heikal Quantum Tunneling Scorer — تقييم اختراق حواجز الأمان      ║
╚══════════════════════════════════════════════════════════════════════╝

الأصل الرياضي:
    من خوارزمية InfoQuantum Lattice Tunneling في Resonance_Optimizer.py
    P_Heikal = P_WKB × (1 + ξ × ℓ_p² / L²)

الفكرة:
    كل عقد ذكي لديه "حواجز أمان" (require, modifier, guard).
    بدل تقييم الثقة بأرقام ثابتة (0.95 لـ reentrancy, 0.70 لـ price...)
    نستخدم نموذج النفق الكمومي:

    كل حاجز i لديه:
        - V_i = ارتفاع الحاجز (صعوبة تجاوزه)
        - d_i = سماكة الحاجز (عدد الشروط)

    احتمال اختراق حاجز واحد:
        T_i = exp(-2κ_i × d_i)
        حيث κ_i = √(2m(V_i - E)) / ℏ

    التحسين الأصلي (Heikal):
        T_Heikal = T_WKB × (1 + ξ × ℓ_p² / L²)

        حيث:
        - ξ = ثابت هيكل (coupling المعلومات بالبنية الكمومية)
        - ℓ_p = أصغر بنية قابلة للاستغلال (Planck-scale للثغرة)
        - L = طول سلسلة الهجوم (عدد الخطوات)

    احتمال اختراق كل الحواجز:
        P_total = ∏ T_Heikal(i) × R(E)

        حيث R(E) = معامل الرنين عند طاقات معينة (quantized energy levels)

    الابتكار:
        - ℓ_p² / L² يعطي bonus للثغرات المركّزة (قصيرة الخطوات)
        - طاقات الرنين تكتشف "ترددات طبيعية" في بنية العقد
          (حالات يتطابق فيها مسار الهجوم مع البنية → احتمال اختراق أعلى)
"""

from __future__ import annotations

import math
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field


# ═══════════════════════════════════════════════════════════════
#  ثوابت هيكل الفيزيائية (مُكيَّفة لمجال الأمان)
# ═══════════════════════════════════════════════════════════════

HEIKAL_XI = 0.4671  # ξ — ثابت هيكل الأصلي (coupling constant)
PLANCK_SCALE = 0.316  # ℓ_p — أصغر بنية قابلة للاستغلال (ℓ_p² ≈ 0.1)
BARRIER_MASS = 1.0  # m — كتلة فعّالة (وحدات مختزلة)
HBAR = 1.0  # ℏ — ثابت بلانك المختزل (وحدات طبيعية)
RESONANCE_GAMMA = 0.1  # γ — عرض ذروة الرنين


@dataclass
class SecurityBarrier:
    """حاجز أمان واحد في العقد الذكي"""

    barrier_type: str  # "require", "modifier", "guard", "access_control", "invariant"
    height: float  # V — ارتفاع الحاجز (0.0 - 1.0)
    thickness: float  # d — سماكة الحاجز (عدد الشروط)
    bypassable: bool = False  # هل يمكن تجاوزه (CEI violation, etc.)
    source: str = ""  # وصف


@dataclass
class TunnelingResult:
    """نتيجة حساب النفق الكمومي"""

    # الاحتمالات
    p_wkb: float = 0.0  # احتمال WKB الكلاسيكي
    p_heikal: float = 0.0  # احتمال هيكل المحسّن
    p_resonance: float = 0.0  # معامل الرنين
    p_total: float = 0.0  # الاحتمال النهائي

    # التفاصيل
    barriers_analyzed: int = 0
    barriers_penetrable: int = 0
    resonance_detected: bool = False
    resonance_energy: float = 0.0

    # لكل حاجز
    per_barrier: List[Dict[str, float]] = field(default_factory=list)

    # الثقة المحوّلة (0.0 - 1.0)
    confidence: float = 0.0


class HeikalTunnelingScorer:
    """
    حاسب احتمال اختراق حواجز الأمان باستخدام نموذج النفق الكمومي.

    يستبدل الأرقام الثابتة (confidence modifiers) بنموذج فيزيائي:
        P_Heikal = P_WKB × (1 + ξ × ℓ_p² / L²) × R(E)

    Usage:
        scorer = HeikalTunnelingScorer()
        result = scorer.compute(barriers, attack_energy, chain_length)
        confidence = result.confidence
    """

    def __init__(
        self,
        xi: float = HEIKAL_XI,
        planck_scale: float = PLANCK_SCALE,
        gamma: float = RESONANCE_GAMMA,
    ):
        self.xi = xi
        self.planck_scale = planck_scale
        self.gamma = gamma

    # ═══════════════════════════════════════════════════════
    #  Main API
    # ═══════════════════════════════════════════════════════

    def compute(
        self,
        barriers: List[SecurityBarrier],
        attack_energy: float = 0.5,
        chain_length: int = 2,
    ) -> TunnelingResult:
        """
        حساب احتمال اختراق سلسلة حواجز أمان.

        Args:
            barriers: قائمة حواجز الأمان المكتشفة
            attack_energy: طاقة الهجوم E (0.0-1.0) — تعتمد على نوع الهجوم
            chain_length: طول سلسلة الهجوم L (عدد الخطوات)

        Returns:
            TunnelingResult مع الاحتمالات والثقة
        """
        result = TunnelingResult()
        result.barriers_analyzed = len(barriers)

        if not barriers:
            # لا حواجز → اختراق مضمون
            result.p_wkb = 1.0
            result.p_heikal = 1.0
            result.p_total = 1.0
            result.confidence = 0.98
            return result

        # ─── Step 1: WKB لكل حاجز ───
        p_wkb_total = 1.0
        for barrier in barriers:
            t_wkb = self._wkb_transmission(barrier, attack_energy)
            p_wkb_total *= t_wkb
            result.per_barrier.append(
                {
                    "type": barrier.barrier_type,
                    "height": barrier.height,
                    "thickness": barrier.thickness,
                    "t_wkb": t_wkb,
                }
            )
            if t_wkb > 0.01:
                result.barriers_penetrable += 1

        result.p_wkb = p_wkb_total

        # ─── Step 2: تصحيح هيكل ───
        L = max(chain_length, 1)
        heikal_factor = 1.0 + self.xi * (self.planck_scale**2) / (L**2)
        result.p_heikal = min(p_wkb_total * heikal_factor, 1.0)

        # ─── Step 3: معامل الرنين ───
        result.p_resonance, result.resonance_energy = self._resonance_factor(
            barriers, attack_energy
        )
        if result.p_resonance > 1.2:
            result.resonance_detected = True

        # ─── Step 4: الاحتمال النهائي ───
        result.p_total = min(result.p_heikal * result.p_resonance, 1.0)

        # ─── Step 5: تحويل إلى ثقة ───
        result.confidence = self._probability_to_confidence(result.p_total)

        return result

    def score_attack_type(
        self,
        attack_type: str,
        barriers: List[SecurityBarrier],
        steps_count: int = 2,
        is_profitable: bool = False,
        all_steps_success: bool = False,
    ) -> float:
        """
        API مباشر: يعطي confidence score لنوع هجوم + حواجز.

        يستبدل CONFIDENCE_MODIFIERS في profit_calculator.py
        """
        # طاقة الهجوم تعتمد على النوع
        energy_map = {
            "reentrancy": 0.85,  # طاقة عالية — هجوم مؤكد تقريبًا
            "flash_loan": 0.75,
            "price_manipulation": 0.60,
            "liquidation": 0.70,
            "access_escalation": 0.50,
            "direct_profit": 0.80,
            "state_manipulation": 0.55,
        }
        energy = energy_map.get(attack_type, 0.45)

        # إذا كل الخطوات نجحت → طاقة أعلى
        if all_steps_success:
            energy = min(energy + 0.10, 0.99)

        # إذا مربح → طاقة أعلى
        if is_profitable:
            energy = min(energy + 0.05, 0.99)

        result = self.compute(barriers, energy, steps_count)
        return result.confidence

    # ═══════════════════════════════════════════════════════
    #  WKB Approximation — أساس النفق الكمومي
    # ═══════════════════════════════════════════════════════

    def _wkb_transmission(
        self,
        barrier: SecurityBarrier,
        energy: float,
    ) -> float:
        """
        معامل نقل WKB لحاجز واحد:
            T = exp(-2κd)
            κ = √(2m(V-E)) / ℏ

        إذا E ≥ V → T ≈ 1 (energy أعلى من الحاجز)
        إذا الحاجز bypassable → T متزايد (الحاجز مثقوب)
        """
        V = barrier.height
        d = barrier.thickness

        # إذا الطاقة تساوي أو تتجاوز الحاجز → نفاذية عالية
        if energy >= V:
            return min(0.95 + 0.05 * (energy - V), 1.0)

        # κ = √(2m(V-E)) / ℏ
        delta_V = V - energy
        kappa = math.sqrt(2.0 * BARRIER_MASS * delta_V) / HBAR

        # T_WKB = exp(-2κd)
        exponent = -2.0 * kappa * d
        t_wkb = math.exp(max(exponent, -50))  # clamp لمنع underflow

        # إذا الحاجز قابل للتجاوز (CEI violation, etc.) → moderate bonus
        if barrier.bypassable:
            t_wkb = max(t_wkb, 0.15)  # minimum 15% penetration (↓ from 0.3)
            t_wkb = min(t_wkb * 1.5, 0.80)  # moderate amplify (↓ from 2.5/0.95)

        return t_wkb

    # ═══════════════════════════════════════════════════════
    #  Resonance Factor — ترددات طبيعية في بنية العقد
    # ═══════════════════════════════════════════════════════

    def _resonance_factor(
        self,
        barriers: List[SecurityBarrier],
        energy: float,
    ) -> Tuple[float, float]:
        """
        حساب معامل الرنين R(E).

        عندما تتطابق طاقة الهجوم مع "تردد طبيعي" لبنية الحواجز
        → احتمال الاختراق يرتفع بشكل حاد (resonant tunneling).

        الترددات الطبيعية:
            ω_n = nπ / (Σ d_i)    (quantized levels)

        معامل الرنين (Breit-Wigner):
            R(E) = 1 / √((ω₀² - ω²)² + (γω)²)

        حيث ω = √(2E/m) وω₀ = أقرب تردد طبيعي.
        """
        if not barriers:
            return 1.0, 0.0

        # حساب الترددات الطبيعية
        total_thickness = sum(b.thickness for b in barriers)
        if total_thickness <= 0:
            return 1.0, 0.0

        # تردد الهجوم
        omega = math.sqrt(2.0 * max(energy, 0.01) / BARRIER_MASS)

        # أول 5 ترددات طبيعية (quantized energy levels)
        best_resonance = 1.0
        best_energy = 0.0

        for n in range(1, 6):
            omega_n = n * math.pi / total_thickness

            # Lorentzian resonance profile
            delta_omega_sq = (omega_n**2 - omega**2) ** 2
            damping = (self.gamma * omega) ** 2
            denominator = math.sqrt(delta_omega_sq + damping)

            if denominator > 0:
                R = 1.0 / denominator
            else:
                R = 10.0  # perfect resonance

            # clamp
            R = min(R, 5.0)

            if R > best_resonance:
                best_resonance = R
                best_energy = 0.5 * BARRIER_MASS * omega_n**2

        return best_resonance, best_energy

    # ═══════════════════════════════════════════════════════
    #  Helpers
    # ═══════════════════════════════════════════════════════

    def _probability_to_confidence(self, p: float) -> float:
        """
        تحويل احتمال النفق إلى ثقة (0.0 - 1.0).

        يستخدم sigmoid-like mapping:
            confidence = 1 / (1 + e^(-k(p - p₀)))

        حيث:
            k = حدة التحول (steepness)
            p₀ = نقطة المنتصف
        """
        k = 8.0  # steepness — sharper transition for security scoring
        p0 = 0.02  # midpoint — product of barrier transmissions is typically 0.001-0.1

        raw = 1.0 / (1.0 + math.exp(-k * (p - p0)))

        # Scale to (0.05 - 0.99) range
        return round(0.05 + raw * 0.94, 4)

    # ═══════════════════════════════════════════════════════
    #  Barrier Extraction from Security Context
    # ═══════════════════════════════════════════════════════

    @staticmethod
    def extract_barriers_from_action(action: Any) -> List[SecurityBarrier]:
        """
        استخراج حواجز الأمان من كائن Action (Layer 2).

        يحوّل خصائص Action إلى SecurityBarrier:
            - require → barrier(height=0.5, thickness=1)
            - nonReentrant → barrier(height=0.9, thickness=2)
            - onlyOwner → barrier(height=0.8, thickness=1)
            - CEI violation → barrier.bypassable = True
        """
        barriers = []

        # Guard modifiers
        if getattr(action, "reentrancy_guarded", False):
            barriers.append(
                SecurityBarrier(
                    barrier_type="guard",
                    height=0.9,
                    thickness=2.0,
                    bypassable=False,
                    source="nonReentrant modifier",
                )
            )

        # Access control
        if getattr(action, "requires_access", False):
            caller = getattr(action, "caller_must_be", "")
            if caller:
                barriers.append(
                    SecurityBarrier(
                        barrier_type="access_control",
                        height=0.8,
                        thickness=1.5,
                        bypassable=False,
                        source=f"requires: {caller}",
                    )
                )
            else:
                barriers.append(
                    SecurityBarrier(
                        barrier_type="access_control",
                        height=0.6,
                        thickness=1.0,
                        bypassable=False,
                        source="access control",
                    )
                )

        # Preconditions (require statements)
        preconditions = getattr(action, "preconditions", [])
        for pc in preconditions:
            # كل require هو حاجز بارتفاع وسط
            barriers.append(
                SecurityBarrier(
                    barrier_type="require",
                    height=0.5,
                    thickness=1.0,
                    bypassable=False,
                    source=str(pc)[:80],
                )
            )

        # CEI violation → الحواجز المالية قابلة للتجاوز
        if getattr(action, "has_cei_violation", False):
            # الحواجز بعد الاستدعاء الخارجي يمكن تجاوزها
            for b in barriers:
                if b.barrier_type == "require":
                    b.bypassable = True
                    b.height *= 0.5  # الحاجز أضعف بسبب CEI violation

        return barriers

    @staticmethod
    def extract_barriers_from_steps(steps: List[Any]) -> List[SecurityBarrier]:
        """
        استخراج حواجز الأمان من خطوات الهجوم (StepResult).
        يُستخدم في profit_calculator بعد المحاكاة.
        """
        barriers = []
        for step in steps:
            if not step.success:
                # خطوة فاشلة = حاجز لم يُخترق
                barriers.append(
                    SecurityBarrier(
                        barrier_type="execution_failure",
                        height=0.95,
                        thickness=3.0,
                        bypassable=False,
                        source=getattr(step, "error", "execution failed"),
                    )
                )
            else:
                # خطوة ناجحة مع reentrancy = حاجز ضعيف
                if getattr(step, "reentrancy_calls", 0) > 0:
                    barriers.append(
                        SecurityBarrier(
                            barrier_type="reentrancy_window",
                            height=0.15,
                            thickness=0.5,
                            bypassable=True,
                            source=f"reentrancy ×{step.reentrancy_calls}",
                        )
                    )
        return barriers
