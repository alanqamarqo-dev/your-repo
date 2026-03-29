"""
╔══════════════════════════════════════════════════════════════════════╗
║     Holographic Vulnerability Memory                                 ║
║     ذاكرة هولوغرافية لأنماط الثغرات                                ║
╚══════════════════════════════════════════════════════════════════════╝

الأصل الرياضي:
    من AGL_Holographic_Memory.py و Heikal_Holographic_Memory.py:
    - تشفير عبر التفاف دائري في فضاء فوريه
    - تعديل الطور: hologram[k] = data[k] × e^(i·noise[k]·2π)

التكييف لأمان العقود الذكية:
    بدل تخزين أنماط ذاكرة عصبية → نخزّن "أنماط ثغرات" مشفّرة بالتفاف دائري.

    كل ثغرة معروفة (reentrancy, flash_loan, etc.) تُخزَّن كمتجه هولوغرافي:
        H_pattern = FFT⁻¹(FFT(signature) × FFT(label))

    عند مواجهة عقد جديد:
        similarity = |FFT⁻¹(FFT(input) × conj(FFT(H_pattern)))|

    إذا similarity > threshold → مطابقة → نعرف نوع الثغرة مسبقاً.

    المميزات:
    1. تطابق جزئي: لا نحتاج تطابق 100% — الهولوغرام يعمل مع أجزاء
    2. سعة فائقة: يمكن تخزين عشرات الأنماط في متجه واحد (superposition)
    3. مقاومة للضوضاء: تغييرات طفيفة في الكود لا تُضيّع المطابقة
    4. التشفير بالطور: الأنماط محمية ضد reverse engineering
"""

from __future__ import annotations

import math
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

try:
    import numpy as np

    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False


# ═══════════════════════════════════════════════════════════════
#  Constants
# ═══════════════════════════════════════════════════════════════

# عدد الأبعاد للمتجه الهولوغرافي
HOLOGRAM_DIM = 64

# عتبة التطابق
MATCH_THRESHOLD = 0.25

# عامل تشفير الطور (phase modulation key)
PHASE_KEY = 0.4671  # ξ — ثابت هيكل


@dataclass
class VulnerabilitySignature:
    """بصمة ثغرة واحدة — متجه خصائص"""

    name: str
    vector: List[float]  # المتجه الهولوغرافي
    severity: str = "medium"
    confidence: float = 0.5
    description: str = ""
    description_ar: str = ""


@dataclass
class PatternMatch:
    """نتيجة مطابقة نمط ثغرة"""

    pattern_name: str
    similarity: float  # 0.0 - 1.0
    severity: str = "medium"
    confidence: float = 0.0
    description: str = ""
    description_ar: str = ""


class HolographicVulnerabilityMemory:
    """
    ذاكرة هولوغرافية لأنماط الثغرات.

    تخزن أنماط ثغرات معروفة كهولوغرامات وتطابقها مع عقود جديدة
    باستخدام الالتفاف الدائري في فضاء فوريه.

    Usage:
        memory = HolographicVulnerabilityMemory()
        matches = memory.match(contract_features)
    """

    def __init__(self, dim: int = HOLOGRAM_DIM):
        self.dim = dim
        self._patterns: Dict[str, VulnerabilitySignature] = {}
        self._hologram: List[complex] = [complex(0.0, 0.0)] * dim

        # تهيئة الأنماط المعروفة
        self._initialize_known_patterns()

    # ═══════════════════════════════════════════════════════
    #  Main API
    # ═══════════════════════════════════════════════════════

    def match(
        self,
        contract_features: Dict[str, Any],
    ) -> List[PatternMatch]:
        """
        مطابقة خصائص عقد جديد مع أنماط الثغرات المخزّنة.

        Args:
            contract_features: خصائص العقد (من Action أو AST analysis)

        Returns:
            قائمة PatternMatch مرتبة بالتشابه
        """
        # تحويل الخصائص إلى متجه
        input_vector = self._features_to_vector(contract_features)

        # مطابقة مع كل نمط مخزّن
        matches = []
        for name, pattern in self._patterns.items():
            similarity = self._holographic_recall(input_vector, pattern.vector)

            if similarity >= MATCH_THRESHOLD:
                matches.append(
                    PatternMatch(
                        pattern_name=name,
                        similarity=similarity,
                        severity=pattern.severity,
                        confidence=similarity * pattern.confidence,
                        description=pattern.description,
                        description_ar=pattern.description_ar,
                    )
                )

        # ترتيب بالتشابه
        matches.sort(key=lambda m: m.similarity, reverse=True)
        return matches

    def store_pattern(
        self,
        name: str,
        features: Dict[str, Any],
        severity: str = "MEDIUM",
        confidence: float = 0.5,
        description: str = "",
        description_ar: str = "",
    ) -> None:
        """تخزين نمط ثغرة جديد في الذاكرة الهولوغرافية"""
        vector = self._features_to_vector(features)

        self._patterns[name] = VulnerabilitySignature(
            name=name,
            vector=vector,
            severity=severity,
            confidence=confidence,
            description=description,
            description_ar=description_ar,
        )

        # إضافة إلى الهولوغرام المركّب (superposition)
        self._encode_into_hologram(name, vector)

    def match_from_action(self, action: Any) -> List[PatternMatch]:
        """API مختصر: مطابقة مباشرة من كائن Action"""
        features = self._extract_features(action)
        return self.match(features)

    # ═══════════════════════════════════════════════════════
    #  Holographic Encoding — التفاف دائري في فضاء فوريه
    # ═══════════════════════════════════════════════════════

    def _encode_into_hologram(self, label: str, data_vector: List[float]) -> None:
        """
        تشفير هولوغرافي:
            H = IFFT(FFT(data) × FFT(label_vector))
            + phase modulation: H[k] *= e^(i·phase_key·k)

        هذا يسمح بتخزين أنماط متعددة في نفس الهولوغرام
        (superposition of patterns).
        """
        label_vec = self._label_to_vector(label)

        # FFT for data and label (simplified DFT)
        fft_data = self._dft(data_vector)
        fft_label = self._dft(label_vec)

        # Element-wise multiplication in frequency domain = convolution in time domain
        fft_product = [fft_data[k] * fft_label[k] for k in range(self.dim)]

        # Phase modulation (Heikal encryption)
        for k in range(self.dim):
            phase = PHASE_KEY * k * 2 * math.pi / self.dim
            fft_product[k] *= complex(math.cos(phase), math.sin(phase))

        # IFFT → hologram
        encoded = self._idft(fft_product)

        # Superpose into main hologram
        for k in range(self.dim):
            self._hologram[k] += encoded[k]

    def _holographic_recall(
        self, input_vector: List[float], pattern_vector: List[float]
    ) -> float:
        """
        استدعاء هولوغرافي:
            similarity = |IFFT(FFT(input) × conj(FFT(pattern)))| / norm

        هذا هو cross-correlation في فضاء فوريه:
        يقيس التشابه حتى مع انزياحات (shift-invariant matching).
        """
        if len(input_vector) != len(pattern_vector):
            # Pad to same length
            max_len = max(len(input_vector), len(pattern_vector))
            input_vector = self._pad_vector(input_vector, max_len)
            pattern_vector = self._pad_vector(pattern_vector, max_len)

        dim = len(input_vector)

        # FFT
        fft_input = self._dft(input_vector)
        fft_pattern = self._dft(pattern_vector)

        # Cross-correlation: FFT(input) × conj(FFT(pattern))
        cross = [fft_input[k] * fft_pattern[k].conjugate() for k in range(dim)]

        # IFFT
        correlation = self._idft(cross)

        # Maximum magnitude = similarity
        max_corr = max(abs(c) for c in correlation) if correlation else 0.0

        # Normalize
        norm_input = math.sqrt(sum(x * x for x in input_vector)) or 1.0
        norm_pattern = math.sqrt(sum(x * x for x in pattern_vector)) or 1.0
        normalizer = norm_input * norm_pattern

        similarity = max_corr / normalizer if normalizer > 0 else 0.0

        return min(similarity, 1.0)

    # ═══════════════════════════════════════════════════════
    #  DFT / IDFT (numpy FFT preferred, pure Python fallback)
    # ═══════════════════════════════════════════════════════

    @staticmethod
    def _dft(signal: List[float]) -> List[complex]:
        """Discrete Fourier Transform"""
        if _HAS_NUMPY:
            return list(np.fft.fft(signal))
        N = len(signal)
        result = []
        for k in range(N):
            s = complex(0.0, 0.0)
            for n in range(N):
                angle = -2.0 * math.pi * k * n / N
                s += signal[n] * complex(math.cos(angle), math.sin(angle))
            result.append(s)
        return result

    @staticmethod
    def _idft(spectrum: List[complex]) -> List[complex]:
        """Inverse Discrete Fourier Transform"""
        if _HAS_NUMPY:
            return list(np.fft.ifft(spectrum))
        N = len(spectrum)
        result = []
        for n in range(N):
            s = complex(0.0, 0.0)
            for k in range(N):
                angle = 2.0 * math.pi * k * n / N
                s += spectrum[k] * complex(math.cos(angle), math.sin(angle))
            result.append(s / N)
        return result

    @staticmethod
    def _pad_vector(vec: List[float], target_len: int) -> List[float]:
        """Pad vector with zeros to target length"""
        if len(vec) >= target_len:
            return vec[:target_len]
        return vec + [0.0] * (target_len - len(vec))

    # ═══════════════════════════════════════════════════════
    #  Feature → Vector Conversion
    # ═══════════════════════════════════════════════════════

    def _features_to_vector(self, features: Dict[str, Any]) -> List[float]:
        """
        تحويل خصائص العقد إلى متجه رقمي بأبعاد ثابتة.

        الترتيب:
        [0-7]   خصائص أمنية بوليانية (8 features)
        [8-15]  عدّادات (عدد الاستدعاءات, الكتابات, etc.)
        [16-23] نسب (CEI count / total ops, etc.)
        [24-31] أنواع الهجوم (one-hot)
        [32-63] reserved / padding
        """
        vec = [0.0] * self.dim

        # Boolean features (0 or 1)
        bool_features = [
            "has_cei_violation",
            "sends_eth",
            "reentrancy_guarded",
            "requires_access",
            "moves_funds",
            "reads_oracle",
            "has_delegatecall",
            "has_state_conflict",
        ]
        for i, feat in enumerate(bool_features):
            val = features.get(feat, False)
            vec[i] = 1.0 if val else 0.0

        # Count features (normalized)
        count_features = [
            ("external_call_count", 10),
            ("state_write_count", 20),
            ("state_read_count", 20),
            ("precondition_count", 10),
            ("cei_violation_count", 5),
            ("parameter_count", 10),
            ("reentrancy_calls", 5),
            ("cross_function_count", 5),
        ]
        for i, (feat, max_val) in enumerate(count_features):
            raw = features.get(feat, 0)
            if isinstance(raw, (int, float)):
                vec[8 + i] = min(float(raw) / max_val, 1.0)

        # Ratio features
        ratio_features = [
            "cei_ratio",
            "guard_ratio",
            "public_ratio",
            "fund_flow_ratio",
            "oracle_dependency_ratio",
            "complexity_ratio",
            "attack_surface_ratio",
            "protection_ratio",
        ]
        for i, feat in enumerate(ratio_features):
            val = features.get(feat, 0.0)
            if isinstance(val, (int, float)):
                vec[16 + i] = min(float(val), 1.0)

        # Attack type one-hot
        attack_types = [
            "reentrancy",
            "flash_loan",
            "price_manipulation",
            "access_control",
            "liquidation",
            "state_manipulation",
            "first_depositor",
            "donation_attack",
        ]
        for i, at in enumerate(attack_types):
            if features.get(f"attack_{at}", False):
                vec[24 + i] = 1.0

        return vec

    def _label_to_vector(self, label: str) -> List[float]:
        """تحويل اسم الثغرة إلى متجه (deterministic hash-like encoding)"""
        vec = [0.0] * self.dim
        for i, ch in enumerate(label):
            idx = (ord(ch) * (i + 1)) % self.dim
            vec[idx] += 1.0 / (i + 1)
        # Normalize
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

    def _extract_features(self, action: Any) -> Dict[str, Any]:
        """استخراج خصائص من كائن Action لتحويلها إلى متجه"""
        return {
            "has_cei_violation": getattr(action, "has_cei_violation", False),
            "sends_eth": getattr(action, "sends_eth", False),
            "reentrancy_guarded": getattr(action, "reentrancy_guarded", False),
            "requires_access": getattr(action, "requires_access", False),
            "moves_funds": True,  # default for actions
            "reads_oracle": False,
            "has_delegatecall": getattr(action, "has_delegatecall", False),
            "has_state_conflict": bool(getattr(action, "cross_function_risk", False)),
            "external_call_count": len(getattr(action, "external_calls", [])),
            "state_write_count": len(getattr(action, "state_writes", [])),
            "state_read_count": len(getattr(action, "state_reads", [])),
            "precondition_count": len(getattr(action, "preconditions", [])),
            "cei_violation_count": getattr(action, "cei_violation_count", 0),
            "parameter_count": len(getattr(action, "parameters", [])),
        }

    # ═══════════════════════════════════════════════════════
    #  Known Vulnerability Patterns
    # ═══════════════════════════════════════════════════════

    def _initialize_known_patterns(self) -> None:
        """تهيئة أنماط الثغرات المعروفة"""

        # 1. Classic Reentrancy (The DAO pattern)
        self.store_pattern(
            "classic_reentrancy",
            {
                "has_cei_violation": True,
                "sends_eth": True,
                "reentrancy_guarded": False,
                "requires_access": False,
                "moves_funds": True,
                "external_call_count": 1,
                "state_write_count": 2,
                "cei_violation_count": 1,
            },
            severity="CRITICAL",
            confidence=0.95,
            description="Classic reentrancy: ETH transfer before state update",
            description_ar="إعادة دخول كلاسيكية: تحويل ETH قبل تحديث الحالة",
        )

        # 2. Cross-function Reentrancy
        self.store_pattern(
            "cross_function_reentrancy",
            {
                "has_cei_violation": True,
                "sends_eth": True,
                "reentrancy_guarded": False,
                "has_state_conflict": True,
                "external_call_count": 1,
                "state_write_count": 3,
                "cross_function_count": 2,
            },
            severity="CRITICAL",
            confidence=0.85,
            description="Cross-function reentrancy via shared state",
            description_ar="إعادة دخول عبر الدوال عبر حالة مشتركة",
        )

        # 3. Flash Loan Attack
        self.store_pattern(
            "flash_loan_attack",
            {
                "moves_funds": True,
                "reads_oracle": True,
                "requires_access": False,
                "external_call_count": 3,
                "state_write_count": 4,
                "attack_flash_loan": True,
            },
            severity="HIGH",
            confidence=0.80,
            description="Flash loan price manipulation",
            description_ar="تلاعب بالأسعار عبر قرض فلاشي",
        )

        # 4. First Depositor Attack (ERC4626)
        self.store_pattern(
            "first_depositor",
            {
                "moves_funds": True,
                "requires_access": False,
                "state_write_count": 2,
                "state_read_count": 3,
                "attack_first_depositor": True,
                "fund_flow_ratio": 0.8,
            },
            severity="HIGH",
            confidence=0.75,
            description="Vault share inflation / first depositor attack",
            description_ar="هجوم المودع الأول — تضخم أسهم الخزنة",
        )

        # 5. Oracle Manipulation
        self.store_pattern(
            "oracle_manipulation",
            {
                "reads_oracle": True,
                "moves_funds": True,
                "requires_access": False,
                "external_call_count": 2,
                "oracle_dependency_ratio": 0.7,
                "attack_price_manipulation": True,
            },
            severity="HIGH",
            confidence=0.70,
            description="Oracle price manipulation without TWAP",
            description_ar="تلاعب بأسعار الأوراكل بدون TWAP",
        )

        # 6. Access Control Bypass
        self.store_pattern(
            "access_bypass",
            {
                "requires_access": False,
                "moves_funds": True,
                "state_write_count": 3,
                "attack_access_control": True,
                "attack_surface_ratio": 0.6,
            },
            severity="CRITICAL",
            confidence=0.85,
            description="Admin function without access control",
            description_ar="دالة إدارية بدون حماية صلاحيات",
        )

        # 7. Read-Only Reentrancy
        self.store_pattern(
            "read_only_reentrancy",
            {
                "has_cei_violation": False,
                "sends_eth": False,
                "reentrancy_guarded": False,
                "has_state_conflict": True,
                "state_read_count": 4,
                "external_call_count": 1,
                "cross_function_count": 1,
            },
            severity="HIGH",
            confidence=0.65,
            description="Read-only reentrancy via view function",
            description_ar="إعادة دخول القراءة فقط عبر دوال view",
        )

        # 8. Donation Attack
        self.store_pattern(
            "donation_attack",
            {
                "moves_funds": True,
                "requires_access": False,
                "state_read_count": 3,
                "fund_flow_ratio": 0.5,
                "attack_donation_attack": True,
            },
            severity="HIGH",
            confidence=0.70,
            description="Direct transfer changes exchange rate",
            description_ar="تحويل مباشر يغيّر سعر الصرف",
        )
