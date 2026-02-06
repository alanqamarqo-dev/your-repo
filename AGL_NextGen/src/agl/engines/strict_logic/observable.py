"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    OBSERVABLE - الطبقة المُراقَبة                             ║
║══════════════════════════════════════════════════════════════════════════════║
║  كل شيء يبدأ من هنا:                                                         ║
║  - تعريف الإشارات (0/1 أو قيم متعددة)                                        ║
║  - فضاء الحالات (State Space)                                                ║
║  - لا قرار بدون Observable واضحة                                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union, Tuple
from enum import Enum, auto
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import threading


class SignalType(Enum):
    """نوع الإشارة"""
    BINARY = auto()      # 0 or 1
    DISCRETE = auto()    # Finite set of values
    CONTINUOUS = auto()  # Real number in range
    VECTOR = auto()      # Multi-dimensional


@dataclass(frozen=True)
class Signal:
    """
    إشارة منطقية واحدة - الوحدة الأساسية للنظام
    
    Attributes:
        name: اسم الإشارة (مثل "threat_level", "ethical_violation")
        value: القيمة الحالية
        signal_type: نوع الإشارة
        valid_range: النطاق الصالح للقيم
        metadata: بيانات إضافية
    """
    name: str
    value: Union[int, float, np.ndarray]
    signal_type: SignalType = SignalType.BINARY
    valid_range: Tuple[float, float] = (0.0, 1.0)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """التحقق من صحة الإشارة"""
        if self.signal_type == SignalType.BINARY:
            if self.value not in (0, 1, 0.0, 1.0, True, False):
                raise ValueError(f"Binary signal '{self.name}' must be 0 or 1, got {self.value}")
    
    def as_binary(self) -> int:
        """تحويل الإشارة إلى ثنائية"""
        if self.signal_type == SignalType.BINARY:
            return int(self.value)
        elif self.signal_type == SignalType.CONTINUOUS:
            threshold = (self.valid_range[0] + self.valid_range[1]) / 2
            return 1 if self.value >= threshold else 0
        elif self.signal_type == SignalType.DISCRETE:
            return 1 if self.value > 0 else 0
        else:
            # Vector - return 1 if norm > 0.5
            return 1 if np.linalg.norm(self.value) > 0.5 else 0
    
    def as_float(self) -> float:
        """تحويل الإشارة إلى عدد حقيقي [0, 1]"""
        if self.signal_type == SignalType.BINARY:
            return float(self.value)
        elif self.signal_type == SignalType.CONTINUOUS:
            # Normalize to [0, 1]
            lo, hi = self.valid_range
            if hi == lo:
                return 0.5
            return (float(self.value) - lo) / (hi - lo)
        elif self.signal_type == SignalType.VECTOR:
            return min(1.0, np.linalg.norm(self.value))
        return float(self.value)
    
    def invert(self) -> Signal:
        """عكس الإشارة"""
        if self.signal_type == SignalType.BINARY:
            return Signal(
                name=f"NOT_{self.name}",
                value=1 - int(self.value),
                signal_type=self.signal_type,
                valid_range=self.valid_range,
                metadata={**self.metadata, "inverted_from": self.name}
            )
        else:
            lo, hi = self.valid_range
            return Signal(
                name=f"NOT_{self.name}",
                value=hi - (self.value - lo),
                signal_type=self.signal_type,
                valid_range=self.valid_range,
                metadata={**self.metadata, "inverted_from": self.name}
            )


@dataclass
class Observable:
    """
    مجموعة إشارات مُراقَبة - المدخلات للنظام المنطقي
    
    كل محرك يصبح مجرد مدخلات لإشارات منطقية:
    - "خطر عسكري وجودي" → Signal("existential_threat", 1)
    - "انتهاك أخلاقي" → Signal("ethical_violation", 0)
    """
    
    def __init__(self, name: str = "default"):
        self.name = name
        self._signals: Dict[str, Signal] = {}
        self._lock = threading.RLock()
        self._history: List[Dict[str, Signal]] = []
    
    def add_signal(self, signal: Signal) -> None:
        """إضافة إشارة"""
        with self._lock:
            self._signals[signal.name] = signal
    
    def add_binary(self, name: str, value: Union[int, bool], **metadata) -> None:
        """إضافة إشارة ثنائية"""
        self.add_signal(Signal(
            name=name,
            value=1 if value else 0,
            signal_type=SignalType.BINARY,
            metadata=metadata
        ))
    
    def add_continuous(self, name: str, value: float, 
                       valid_range: Tuple[float, float] = (0.0, 1.0), **metadata) -> None:
        """إضافة إشارة مستمرة"""
        self.add_signal(Signal(
            name=name,
            value=value,
            signal_type=SignalType.CONTINUOUS,
            valid_range=valid_range,
            metadata=metadata
        ))
    
    def get(self, name: str) -> Optional[Signal]:
        """الحصول على إشارة"""
        with self._lock:
            return self._signals.get(name)
    
    def get_binary(self, name: str, default: int = 0) -> int:
        """الحصول على قيمة ثنائية"""
        signal = self.get(name)
        if signal is None:
            return default
        return signal.as_binary()
    
    def get_float(self, name: str, default: float = 0.0) -> float:
        """الحصول على قيمة حقيقية"""
        signal = self.get(name)
        if signal is None:
            return default
        return signal.as_float()
    
    def get_all(self) -> Dict[str, Signal]:
        """الحصول على جميع الإشارات"""
        with self._lock:
            return dict(self._signals)
    
    def as_binary_vector(self) -> np.ndarray:
        """تحويل كل الإشارات إلى متجه ثنائي"""
        with self._lock:
            if not self._signals:
                return np.array([], dtype=np.int8)
            return np.array([s.as_binary() for s in self._signals.values()], dtype=np.int8)
    
    def as_float_vector(self) -> np.ndarray:
        """تحويل كل الإشارات إلى متجه حقيقي"""
        with self._lock:
            if not self._signals:
                return np.array([], dtype=np.float32)
            return np.array([s.as_float() for s in self._signals.values()], dtype=np.float32)
    
    def snapshot(self) -> Dict[str, Signal]:
        """أخذ لقطة من الحالة الحالية"""
        with self._lock:
            snapshot = dict(self._signals)
            self._history.append(snapshot)
            return snapshot
    
    def signal_names(self) -> List[str]:
        """أسماء جميع الإشارات"""
        with self._lock:
            return list(self._signals.keys())
    
    def __len__(self) -> int:
        return len(self._signals)
    
    def __repr__(self) -> str:
        with self._lock:
            signals_str = ", ".join(f"{k}={v.value}" for k, v in self._signals.items())
            return f"Observable({self.name}: {signals_str})"


class StateSpace:
    """
    فضاء الحالات - يمثل جميع الحالات الممكنة للنظام
    
    المدخل يُسقط على هذا الفضاء قبل اتخاذ القرار.
    هذا يحول "احتمالات غامضة" إلى "حالات محددة".
    """
    
    def __init__(self, dimensions: int, states_per_dim: int = 2):
        """
        Args:
            dimensions: عدد الأبعاد (= عدد الإشارات)
            states_per_dim: عدد الحالات لكل بُعد (2 = binary)
        """
        self.dimensions = dimensions
        self.states_per_dim = states_per_dim
        self.total_states = states_per_dim ** dimensions
        
        # State probability distribution
        self._state_probs: np.ndarray = np.ones(self.total_states) / self.total_states
        
        # Lock for thread safety
        self._lock = threading.RLock()
    
    def project(self, observable: Observable) -> np.ndarray:
        """
        إسقاط Observable على فضاء الحالات
        
        Returns:
            توزيع احتمالي على الحالات
        """
        with self._lock:
            vec = observable.as_float_vector()
            
            if len(vec) != self.dimensions:
                raise ValueError(f"Observable dimension {len(vec)} != StateSpace dimension {self.dimensions}")
            
            # Convert to state index
            if self.states_per_dim == 2:
                # Binary: each signal maps to bit position
                binary_vec = observable.as_binary_vector()
                state_idx = int(np.dot(binary_vec, 2 ** np.arange(len(binary_vec))))
                
                # Create probability distribution (concentrated on this state)
                probs = np.zeros(self.total_states)
                probs[state_idx] = 1.0
                return probs
            else:
                # Multi-state: discretize continuous values
                discretized = np.floor(vec * self.states_per_dim).astype(int)
                discretized = np.clip(discretized, 0, self.states_per_dim - 1)
                
                state_idx = int(np.dot(discretized, self.states_per_dim ** np.arange(len(discretized))))
                
                probs = np.zeros(self.total_states)
                probs[state_idx] = 1.0
                return probs
    
    def project_fuzzy(self, observable: Observable, spread: float = 0.1) -> np.ndarray:
        """
        إسقاط ضبابي - يسمح بعدم اليقين المحسوب
        
        Args:
            observable: المدخلات
            spread: مدى الانتشار (0 = deterministic, 1 = uniform)
        
        Returns:
            توزيع احتمالي مع انتشار حول الحالة الأساسية
        """
        base_probs = self.project(observable)
        
        if spread <= 0:
            return base_probs
        
        # Add controlled uncertainty
        uniform = np.ones(self.total_states) / self.total_states
        return (1 - spread) * base_probs + spread * uniform
    
    def most_likely_state(self, probs: np.ndarray) -> int:
        """الحالة الأكثر احتمالاً"""
        return int(np.argmax(probs))
    
    def state_to_binary(self, state_idx: int) -> np.ndarray:
        """تحويل رقم الحالة إلى متجه ثنائي"""
        if self.states_per_dim != 2:
            raise ValueError("state_to_binary only works for binary state spaces")
        
        binary = np.zeros(self.dimensions, dtype=np.int8)
        for i in range(self.dimensions):
            binary[i] = (state_idx >> i) & 1
        return binary
    
    def entropy(self, probs: np.ndarray) -> float:
        """حساب الإنتروبيا - مقياس عدم اليقين"""
        # Avoid log(0)
        safe_probs = np.clip(probs, 1e-10, 1.0)
        return -np.sum(probs * np.log2(safe_probs))
    
    def confidence(self, probs: np.ndarray) -> float:
        """
        مقياس الثقة (عكس الإنتروبيا المُطبّعة)
        
        Returns:
            1.0 = ثقة كاملة (حالة واحدة محتملة)
            0.0 = لا ثقة (كل الحالات متساوية)
        """
        max_entropy = np.log2(self.total_states)
        if max_entropy == 0:
            return 1.0
        return 1.0 - (self.entropy(probs) / max_entropy)


# === Parallel Observable Processing ===

class ParallelObservableProcessor:
    """
    معالج متوازي للإشارات - يعمل على عدة Observable بالتوازي
    """
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def process_batch(self, observables: List[Observable], 
                      state_space: StateSpace) -> List[np.ndarray]:
        """معالجة مجموعة من Observable بالتوازي"""
        futures = [
            self._executor.submit(state_space.project, obs) 
            for obs in observables
        ]
        return [f.result() for f in futures]
    
    def shutdown(self):
        """إيقاف المعالج"""
        self._executor.shutdown(wait=True)
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.shutdown()


# === Factory Functions ===

def create_binary_observable(signals_dict: Dict[str, Union[int, bool]], 
                             name: str = "binary_obs") -> Observable:
    """
    إنشاء Observable من قاموس إشارات ثنائية
    
    Example:
        obs = create_binary_observable({
            "threat_level": 1,
            "ethical_violation": 0,
            "emergency_override": 0
        })
    """
    obs = Observable(name=name)
    for sig_name, value in signals_dict.items():
        obs.add_binary(sig_name, value)
    return obs


def create_state_space_for_observable(observable: Observable, 
                                       states_per_dim: int = 2) -> StateSpace:
    """إنشاء StateSpace مناسب لـ Observable"""
    return StateSpace(dimensions=len(observable), states_per_dim=states_per_dim)
