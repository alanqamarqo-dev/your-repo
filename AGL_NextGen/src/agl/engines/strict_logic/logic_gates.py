"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    LOGIC GATES - البوابات المنطقية الثلاثية                   ║
║══════════════════════════════════════════════════════════════════════════════║
║                                                                               ║
║  🎯 الهدف الأساسي:                                                            ║
║  ───────────────                                                              ║
║  بناء نظام استدلال منطقي صارم - ليس "AI" تقليدي.                             ║
║  كل بوابة تُنتج: (output, trace)                                             ║
║  بدون trace = النظام أعمى (لا يستطيع التعلم أو التصحيح)                       ║
║                                                                               ║
║  ═══════════════════════════════════════════════════════════════════════════ ║
║                                                                               ║
║  ثلاث طبقات من البوابات:                                                     ║
║  ─────────────────────                                                        ║
║                                                                               ║
║  أ) بوابات حتمية (Deterministic Gates):                                      ║
║     ─────────────────────────────────                                         ║
║     • AND:  output = 1 ⟺ ∀i: input_i = 1                                     ║
║     • OR:   output = 1 ⟺ ∃i: input_i = 1                                     ║
║     • NOT:  output = 1 - input                                                ║
║     • XOR:  output = 1 ⟺ odd count of 1s                                     ║
║     • NAND: output = ¬AND (Universal Gate!)                                   ║
║     • NOR:  output = ¬OR  (Universal Gate!)                                   ║
║     • XNOR: output = ¬XOR (Equality Gate)                                     ║
║                                                                               ║
║  ب) بوابات موزونة (Weighted Gates):                                          ║
║     ───────────────────────────────                                           ║
║     • كل مدخل له وزن قابل للتعلم                                             ║
║     • out = activation(Σ(input_i × weight_i) + bias)                         ║
║     • دوال التنشيط: step, sigmoid, tanh, relu, linear                        ║
║                                                                               ║
║  ج) بوابات إسقاط موجي (Wave Projection Gates):                               ║
║     ─────────────────────────────────────────                                 ║
║     • ψ_out = Σ(ψ_in ⊗ φ_gate)                                               ║
║     • المخرج = WaveState (تراكب احتمالي)                                      ║
║     • الانهيار حتمي (يختار الأكثر احتمالاً)                                   ║
║                                                                               ║
║  ═══════════════════════════════════════════════════════════════════════════ ║
║                                                                               ║
║  🔗 شبكة البوابات (GateNetwork):                                              ║
║  ────────────────────────────                                                 ║
║  • ربط عدة بوابات معاً لبناء دوائر معقدة                                     ║
║  • تنفيذ متوازي للبوابات المستقلة (ThreadPoolExecutor)                        ║
║  • ترتيب طوبولوجي (Topological Sort) للتبعيات                                ║
║                                                                               ║
║  ═══════════════════════════════════════════════════════════════════════════ ║
║                                                                               ║
║  📊 GateTrace - أثر البوابة:                                                  ║
║  ────────────────────────                                                     ║
║  كل عملية تُسجل:                                                              ║
║  • gate_id: معرف فريد                                                         ║
║  • gate_type: نوع البوابة                                                     ║
║  • inputs: المدخلات                                                           ║
║  • output: المخرج                                                             ║
║  • weight: الوزن (للبوابات الموزونة)                                          ║
║  • confidence: ثقة هذه البوابة                                                ║
║                                                                               ║
║  ⚠️ لماذا Trace مهم؟                                                          ║
║  عند التعلم، نعدّل فقط البوابات المتورطة في الخطأ.                            ║
║  بدون trace = نعدّل كل شيء عشوائياً = نسيان كارثي!                           ║
║                                                                               ║
╚══════════════════════════════════════════════════════════════════════════════╝

المطور: Hussam Heikal - AGL System
الإصدار: 2.0.0
التاريخ: February 2026
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time
from uuid import uuid4


# ════════════════════════════════════════════════════════════════════════════════
# GATE TRACE - أثر المنطق (قلب نظام التعلم)
# ════════════════════════════════════════════════════════════════════════════════
#
# 🔍 لماذا الأثر ضروري؟
# ─────────────────────
# في الشبكات العصبية: Backpropagation يعدل كل الأوزان
# في المنطق الصارم: نعدل فقط البوابات التي شاركت في القرار!
#
# ┌─────────────────────────────────────────────────────────────────────────────┐
# │  مثال:                                                                      │
# │                                                                             │
# │      Input → [AND] → [OR] → [NOT] → Output = خطأ!                          │
# │                ↑        ↑       ↑                                           │
# │              trace₁   trace₂   trace₃                                      │
# │                                                                             │
# │  السؤال: أي بوابة نعدّل؟                                                    │
# │  الجواب: كل البوابات في الأثر (trace₁, trace₂, trace₃)                      │
# │         لكن البوابات خارج المسار لا نمسّها!                                  │
# └─────────────────────────────────────────────────────────────────────────────┘
#
# ════════════════════════════════════════════════════════════════════════════════

@dataclass
class GateTrace:
    """
    أثر البوابة المفردة - سجل تنفيذ واحد
    ═══════════════════════════════════════
    
    يسجل:
    ──────
    • gate_id: معرف فريد للبوابة
    • gate_type: نوع البوابة (AND, OR, Weighted, ...)
    • inputs: المدخلات بالضبط
    • output: المخرج الناتج
    • timestamp: وقت التنفيذ (للترتيب الزمني)
    • weight: وزن البوابة (للموزونة فقط)
    • confidence: ثقة القرار [0, 1]
    • metadata: بيانات إضافية
    
    الاستخدام:
    ───────────
        gate = ANDGate()
        output, trace = gate(1, 0)
        
        print(trace.inputs)     # (1, 0)
        print(trace.output)     # 0
        print(trace.confidence) # 1.0
        print(trace.gate_type)  # "AND"
    
    في التعلم:
    ───────────
        # الخطأ حدث؟ نعدل البوابات في الأثر
        for trace in compound_trace.traces:
            gate = gates[trace.gate_id]
            if hasattr(gate, 'adjust_weights'):
                gate.adjust_weights(delta)
    """
    gate_id: str
    gate_type: str
    inputs: Tuple[Any, ...]
    output: Any
    timestamp: float = field(default_factory=time.time)
    weight: float = 1.0
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __repr__(self) -> str:
        return f"Trace({self.gate_type}:{self.gate_id[:8]}... {self.inputs} → {self.output})"


@dataclass 
class CompoundTrace:
    """
    أثر مركب - سجل تنفيذ شبكة كاملة
    ═══════════════════════════════════
    
    يجمع كل الآثار من شبكة بوابات في تنفيذ واحد.
    
    المكونات:
    ─────────
    • traces: قائمة آثار البوابات المفردة
    • total_confidence: حاصل ضرب ثقات كل البوابات
    • execution_path: ترتيب التنفيذ (للتصحيح)
    
    حساب الثقة الكلية:
    ───────────────────
        total_confidence = ∏ trace_i.confidence
        
        مثال: 3 بوابات بثقة 0.9 لكل منها
        total = 0.9 × 0.9 × 0.9 = 0.729
    
    لماذا حاصل الضرب؟
    ──────────────────
        إذا أي بوابة غير واثقة → الثقة الكلية تنخفض
        (مثل سلسلة: أضعف حلقة تحدد القوة)
    
    الاستخدام:
    ───────────
        network = GateNetwork()
        # ... بناء الشبكة ...
        result = network.execute(inputs)
        compound = result["_compound_trace"]
        
        print(compound.total_confidence)    # 0.85
        print(compound.execution_path)      # ["gate1", "gate2", "gate3"]
        print(compound.get_gates_involved()) # ["id1", "id2", "id3"]
    """
    traces: List[GateTrace] = field(default_factory=list)
    total_confidence: float = 1.0
    execution_path: List[str] = field(default_factory=list)
    
    def add(self, trace: GateTrace) -> None:
        """إضافة أثر للمجموعة"""
        self.traces.append(trace)
        self.execution_path.append(trace.gate_id)
        # Confidence is product of all gate confidences
        self.total_confidence *= trace.confidence
    
    def get_gates_involved(self) -> List[str]:
        """قائمة معرفات البوابات التي شاركت"""
        return [t.gate_id for t in self.traces]
    
    def __len__(self) -> int:
        return len(self.traces)


# ════════════════════════════════════════════════════════════════════════════════
# BASE GATE - البوابة الأساسية (Abstract Base Class)
# ════════════════════════════════════════════════════════════════════════════════
#
# كل بوابة في النظام ترث من BaseGate
# هذا يضمن:
#   • واجهة موحدة (__call__ → (output, trace))
#   • إنتاج أثر تلقائي
#   • thread-safety مدمج
#   • عداد استدعاءات
#
# ════════════════════════════════════════════════════════════════════════════════

class BaseGate(ABC):
    """
    البوابة الأساسية - الفئة الأم لكل البوابات
    ═══════════════════════════════════════════
    
    الواجهة:
    ────────
        output, trace = gate(*inputs)
    
    كل بوابة يجب أن تُعرّف:
    ─────────────────────────
        @property
        def gate_type(self) -> str:
            return "MyGate"
        
        def _compute(self, *inputs) -> Any:
            # المنطق الفعلي
            return result
    
    اختياري:
    ─────────
        def _compute_confidence(self, inputs, output) -> float:
            # ثقة مخصصة
            return 0.95
    
    الميزات المدمجة:
    ─────────────────
    • gate_id: معرف UUID فريد
    • name: اسم قابل للقراءة
    • _lock: قفل للـ thread-safety
    • _call_count: عداد الاستدعاءات
    
    مثال تعريف بوابة جديدة:
    ────────────────────────
        class MyCustomGate(BaseGate):
            @property
            def gate_type(self) -> str:
                return "MyCustom"
            
            def _compute(self, *inputs: int) -> int:
                # منطق مخصص
                return sum(inputs) % 2
    """
    
    def __init__(self, name: Optional[str] = None):
        self.gate_id = str(uuid4())
        self.name = name or f"{self.__class__.__name__}_{self.gate_id[:8]}"
        self._lock = threading.RLock()
        self._call_count = 0
    
    @property
    @abstractmethod
    def gate_type(self) -> str:
        """نوع البوابة"""
        pass
    
    @abstractmethod
    def _compute(self, *inputs: Any) -> Any:
        """الحساب الفعلي - يُنفذ في الفئات الفرعية"""
        pass
    
    def __call__(self, *inputs: Any) -> Tuple[Any, GateTrace]:
        """
        تنفيذ البوابة مع إنتاج الأثر
        
        Returns:
            (output, trace)
        """
        with self._lock:
            self._call_count += 1
            output = self._compute(*inputs)
            
            trace = GateTrace(
                gate_id=self.gate_id,
                gate_type=self.gate_type,
                inputs=tuple(inputs),
                output=output,
                weight=getattr(self, 'weight', 1.0),
                confidence=self._compute_confidence(inputs, output),
                metadata={"call_count": self._call_count, "name": self.name}
            )
            
            return output, trace
    
    def _compute_confidence(self, inputs: Tuple, output: Any) -> float:
        """حساب الثقة - يمكن تخصيصه في الفئات الفرعية"""
        return 1.0
    
    def __repr__(self) -> str:
        return f"{self.gate_type}({self.name})"


# ════════════════════════════════════════════════════════════════════════════════
# أ) البوابات الحتمية (DETERMINISTIC GATES)
# ════════════════════════════════════════════════════════════════════════════════
#
# البوابات الحتمية لها خرج ثابت لنفس المدخلات دائماً.
# لا تحتوي على أوزان قابلة للتعلم.
# تُستخدم لبناء المنطق الأساسي.
#
# ┌───────────────────────────────────────────────────────────────────────────────┐
# │  جدول الحقيقة المختصر (لمدخلين A, B):                                        │
# │                                                                               │
# │  A  B │ AND │ OR  │ XOR │ NAND │ NOR │ XNOR │                                │
# │  ─────┼─────┼─────┼─────┼──────┼─────┼──────│                                │
# │  0  0 │  0  │  0  │  0  │  1   │  1  │  1   │                                │
# │  0  1 │  0  │  1  │  1  │  1   │  0  │  0   │                                │
# │  1  0 │  0  │  1  │  1  │  1   │  0  │  0   │                                │
# │  1  1 │  1  │  1  │  0  │  0   │  0  │  1   │                                │
# └───────────────────────────────────────────────────────────────────────────────┘
# ════════════════════════════════════════════════════════════════════════════════

class ANDGate(BaseGate):
    """
    بوابة AND - بوابة الـ "و"
    ═══════════════════════
    
    المعادلة:
    ─────────
        output = 1  ⟺  ∀i: input_i = 1
        
    بالعربي: المخرج = 1 فقط إذا كل المدخلات = 1
    
    جدول الحقيقة (مدخلين):
    ───────────────────────
        A │ B │ A∧B
        ──┼───┼────
        0 │ 0 │  0
        0 │ 1 │  0
        1 │ 0 │  0
        1 │ 1 │  1  ← الوحيدة التي تُخرج 1
    
    الاستخدامات:
    ────────────
    • التحقق من تلبية جميع الشروط
    • الأمان: (authorized AND valid_token AND not_expired)
    • القرارات التي تتطلب موافقة كاملة
    • شرط الإقلاع: (fuel_ok AND weather_ok AND crew_ready)
    
    مثال:
    ──────
        gate = ANDGate()
        output, trace = gate(1, 1, 1)  # → (1, trace)
        output, trace = gate(1, 0, 1)  # → (0, trace)
    """
    
    @property
    def gate_type(self) -> str:
        return "AND"
    
    def _compute(self, *inputs: int) -> int:
        return 1 if all(int(i) == 1 for i in inputs) else 0


class ORGate(BaseGate):
    """
    بوابة OR - بوابة الـ "أو"
    ═══════════════════════
    
    المعادلة:
    ─────────
        output = 1  ⟺  ∃i: input_i = 1
        
    بالعربي: المخرج = 1 إذا أي مدخل = 1
    
    جدول الحقيقة (مدخلين):
    ───────────────────────
        A │ B │ A∨B
        ──┼───┼────
        0 │ 0 │  0  ← الوحيدة التي تُخرج 0
        0 │ 1 │  1
        1 │ 0 │  1
        1 │ 1 │  1
    
    الاستخدامات:
    ────────────
    • الاكتفاء بشرط واحد
    • التنبيهات: (error OR warning OR critical)
    • البدائل: (path_A_clear OR path_B_clear)
    • أي طريقة للوصول: (door_open OR window_open)
    
    مثال:
    ──────
        gate = ORGate()
        output, trace = gate(0, 0, 0)  # → (0, trace)
        output, trace = gate(0, 1, 0)  # → (1, trace)
    """
    
    @property
    def gate_type(self) -> str:
        return "OR"
    
    def _compute(self, *inputs: int) -> int:
        return 1 if any(int(i) == 1 for i in inputs) else 0


class NOTGate(BaseGate):
    """
    بوابة NOT - بوابة العكس (النفي)
    ═══════════════════════════════
    
    المعادلة:
    ─────────
        output = 1 - input
        output = ¬input
        
    بالعربي: المخرج = عكس المدخل
    
    جدول الحقيقة:
    ─────────────
        A │ ¬A
        ──┼────
        0 │  1
        1 │  0
    
    الاستخدامات:
    ────────────
    • عكس الحالة
    • الشروط السالبة: NOT(ethical_violation)
    • التحويل: enabled = NOT(disabled)
    • إنشاء البوابات الكونية: NAND = NOT(AND)
    
    مثال:
    ──────
        gate = NOTGate()
        output, trace = gate(1)  # → (0, trace)
        output, trace = gate(0)  # → (1, trace)
    """
    
    @property
    def gate_type(self) -> str:
        return "NOT"
    
    def _compute(self, x: int) -> int:
        return 1 - int(x)


class XORGate(BaseGate):
    """
    بوابة XOR - بوابة الاختلاف (Exclusive OR)
    ═════════════════════════════════════════
    
    المعادلة:
    ─────────
        output = 1  ⟺  عدد فردي من المدخلات = 1
        output = A ⊕ B ⊕ C ⊕ ...
        
    بالعربي: المخرج = 1 إذا كان عدد المدخلات الفعّالة فردياً
    
    جدول الحقيقة (مدخلين):
    ───────────────────────
        A │ B │ A⊕B
        ──┼───┼─────
        0 │ 0 │  0   (0 فردي؟ لا)
        0 │ 1 │  1   (1 فردي؟ نعم)
        1 │ 0 │  1   (1 فردي؟ نعم)
        1 │ 1 │  0   (2 فردي؟ لا)
    
    الخصائص الرياضية:
    ─────────────────
    • A ⊕ A = 0  (التطبيق مرتين يُلغي)
    • A ⊕ 0 = A  (العنصر المحايد)
    • A ⊕ 1 = ¬A (عكس)
    • A ⊕ B = B ⊕ A (إبدالي)
    • (A ⊕ B) ⊕ C = A ⊕ (B ⊕ C) (تجميعي)
    
    الاستخدامات:
    ────────────
    • كشف الاختلاف: A ⊕ B = 1 يعني A ≠ B
    • التشفير: ciphertext = plaintext ⊕ key
    • التحقق من التماثل (Parity Check)
    • فك التشفير: plaintext = ciphertext ⊕ key
    
    مثال:
    ──────
        gate = XORGate()
        output, trace = gate(1, 1)  # → (0, trace)
        output, trace = gate(1, 0)  # → (1, trace)
    """
    
    @property
    def gate_type(self) -> str:
        return "XOR"
    
    def _compute(self, *inputs: int) -> int:
        result = 0
        for i in inputs:
            result ^= int(i)
        return result


class NANDGate(BaseGate):
    """
    بوابة NAND - البوابة الكونية الأولى (NOT AND)
    ═════════════════════════════════════════════
    
    المعادلة:
    ─────────
        output = ¬(A ∧ B) = NOT(AND(A, B))
        
    بالعربي: المخرج = عكس بوابة AND
    
    جدول الحقيقة (مدخلين):
    ───────────────────────
        A │ B │ A↑B
        ──┼───┼─────
        0 │ 0 │  1
        0 │ 1 │  1
        1 │ 0 │  1
        1 │ 1 │  0  ← الوحيدة التي تُخرج 0
    
    🔥 البوابة الكونية (UNIVERSAL GATE):
    ───────────────────────────────────
    يمكن بناء أي بوابة منطقية أخرى باستخدام NAND فقط!
    
    • NOT(A)     = A NAND A
    • AND(A,B)   = (A NAND B) NAND (A NAND B)
    • OR(A,B)    = (A NAND A) NAND (B NAND B)
    • XOR(A,B)   = [(A NAND (A NAND B)) NAND (B NAND (A NAND B))]
    
    الاستخدامات:
    ────────────
    • بناء دوائر رقمية كاملة بنوع بوابة واحد
    • تبسيط التصنيع
    • الدوائر المتكاملة (ICs)
    
    مثال:
    ──────
        gate = NANDGate()
        output, trace = gate(1, 1)  # → (0, trace)
        output, trace = gate(1, 0)  # → (1, trace)
    """
    
    @property
    def gate_type(self) -> str:
        return "NAND"
    
    def _compute(self, *inputs: int) -> int:
        return 0 if all(int(i) == 1 for i in inputs) else 1


class NORGate(BaseGate):
    """
    بوابة NOR - البوابة الكونية الثانية (NOT OR)
    ═════════════════════════════════════════════
    
    المعادلة:
    ─────────
        output = ¬(A ∨ B) = NOT(OR(A, B))
        
    بالعربي: المخرج = عكس بوابة OR
    
    جدول الحقيقة (مدخلين):
    ───────────────────────
        A │ B │ A↓B
        ──┼───┼─────
        0 │ 0 │  1  ← الوحيدة التي تُخرج 1
        0 │ 1 │  0
        1 │ 0 │  0
        1 │ 1 │  0
    
    🔥 البوابة الكونية الثانية:
    ─────────────────────────
    مثل NAND، يمكن بناء أي بوابة باستخدام NOR فقط!
    
    • NOT(A)     = A NOR A
    • OR(A,B)    = (A NOR B) NOR (A NOR B)
    • AND(A,B)   = (A NOR A) NOR (B NOR B)
    
    الاستخدامات:
    ────────────
    • نفس استخدامات NAND
    • بديل معماري في الدوائر
    • Apollo Guidance Computer استخدم NOR فقط!
    
    مثال:
    ──────
        gate = NORGate()
        output, trace = gate(0, 0)  # → (1, trace)
        output, trace = gate(1, 0)  # → (0, trace)
    """
    
    @property
    def gate_type(self) -> str:
        return "NOR"
    
    def _compute(self, *inputs: int) -> int:
        return 0 if any(int(i) == 1 for i in inputs) else 1


class XNORGate(BaseGate):
    """
    بوابة XNOR - بوابة التساوي (Equivalence Gate)
    ══════════════════════════════════════════════
    
    المعادلة:
    ─────────
        output = ¬(A ⊕ B) = NOT(XOR(A, B))
        output = 1  ⟺  A = B
        
    بالعربي: المخرج = 1 إذا كان المدخلان متساويين
    
    جدول الحقيقة (مدخلين):
    ───────────────────────
        A │ B │ A⊙B
        ──┼───┼─────
        0 │ 0 │  1   (متساويان ✓)
        0 │ 1 │  0   (مختلفان ✗)
        1 │ 0 │  0   (مختلفان ✗)
        1 │ 1 │  1   (متساويان ✓)
    
    الخصائص:
    ─────────
    • A XNOR B = 1  ⟺  A = B
    • A XNOR B = NOT(A XOR B)
    • يُسمى أيضاً: Equivalence Gate, ENOR, EXNOR
    
    الاستخدامات:
    ────────────
    • كشف التساوي: A XNOR B = 1 يعني A = B
    • التحقق من التطابق
    • مقارنة البتات
    • دوائر المقارنة (Comparators)
    
    مثال:
    ──────
        gate = XNORGate()
        output, trace = gate(1, 1)  # → (1, trace) - متساويان
        output, trace = gate(1, 0)  # → (0, trace) - مختلفان
    """
    
    @property
    def gate_type(self) -> str:
        return "XNOR"
    
    def _compute(self, *inputs: int) -> int:
        result = 0
        for i in inputs:
            result ^= int(i)
        return 1 - result


# ════════════════════════════════════════════════════════════════════════════════
# ب) البوابات الموزونة (WEIGHTED GATES)
# ════════════════════════════════════════════════════════════════════════════════
#
# الفرق الجوهري عن البوابات الحتمية:
# ────────────────────────────────────
#
#   البوابة الحتمية:  output = f(inputs)     ← ثابتة دائماً
#   البوابة الموزونة: output = f(inputs, W)  ← W قابل للتعلم!
#
# المعادلة الأساسية:
# ──────────────────
#
#   output = activation( Σ(input_i × weight_i) + bias )
#
# ┌─────────────────────────────────────────────────────────────────────────────┐
# │  دوال التنشيط (Activation Functions):                                      │
# │                                                                             │
# │  • step:    f(x) = 1 if x ≥ threshold else 0                               │
# │  • sigmoid: f(x) = 1 / (1 + e^(-x))       ← ناعمة، [0,1]                   │
# │  • tanh:    f(x) = tanh(x)                ← ناعمة، [-1,1]                  │
# │  • relu:    f(x) = max(0, x)              ← خطية للموجب                    │
# │  • linear:  f(x) = x                      ← بدون تحويل                      │
# └─────────────────────────────────────────────────────────────────────────────┘
#
# آلية التعلم:
# ────────────
# 1. نحسب الخطأ من trace
# 2. نعدل الأوزان فقط للبوابات المتورطة
# 3. adjust_weights(delta, learning_rate)
#
# ════════════════════════════════════════════════════════════════════════════════

class WeightedGate(BaseGate):
    """
    بوابة موزونة - بوابة قابلة للتعلم
    ═══════════════════════════════════
    
    المعادلة:
    ─────────
        weighted_sum = Σ(input_i × weight_i) + bias
        output = activation(weighted_sum)
    
    المكونات:
    ─────────
    • weights: مصفوفة أوزان (قابلة للتعلم)
    • bias: انحياز (قابل للتعلم)
    • threshold: عتبة القرار (لـ step activation)
    • activation: دالة التنشيط
    
    دوال التنشيط المدعومة:
    ───────────────────────
    • "step":    1 if x ≥ threshold else 0
    • "sigmoid": 1 / (1 + e^(-x))
    • "tanh":    tanh(x)
    • "relu":    max(0, x)
    • "linear":  x
    
    حساب الثقة:
    ───────────
    الثقة = مدى ابتعاد المجموع الموزون عن العتبة
    كلما ابتعد → زادت الثقة (القرار أوضح)
    
    مثال:
    ──────
        gate = WeightedGate(n_inputs=3, threshold=0.5, activation="sigmoid")
        output, trace = gate(0.8, 0.6, 0.3)
        
        # تعديل الأوزان (التعلم)
        gate.adjust_weights(delta=np.array([0.1, -0.05, 0.02]))
    """
    
    def __init__(self, n_inputs: int, threshold: float = 0.5, 
                 activation: str = "step", name: Optional[str] = None):
        super().__init__(name)
        self.n_inputs = n_inputs
        self.threshold = threshold
        self.activation = activation
        
        # Initialize weights (learnable)
        self.weights = np.ones(n_inputs, dtype=np.float64) / n_inputs
        self.bias = 0.0
        
        # Learning history
        self._weight_history: List[np.ndarray] = []
    
    @property
    def gate_type(self) -> str:
        return f"Weighted({self.activation})"
    
    @property
    def weight(self) -> float:
        """متوسط الأوزان للتتبع"""
        return float(np.mean(self.weights))
    
    def _activate(self, x: float) -> float:
        """دالة التنشيط"""
        if self.activation == "step":
            return 1.0 if x >= self.threshold else 0.0
        elif self.activation == "sigmoid":
            return 1.0 / (1.0 + np.exp(-x))
        elif self.activation == "tanh":
            return np.tanh(x)
        elif self.activation == "relu":
            return max(0.0, x)
        elif self.activation == "linear":
            return x
        else:
            return 1.0 if x >= self.threshold else 0.0
    
    def _compute(self, *inputs: float) -> float:
        if len(inputs) != self.n_inputs:
            raise ValueError(f"Expected {self.n_inputs} inputs, got {len(inputs)}")
        
        inputs_arr = np.array(inputs, dtype=np.float64)
        weighted_sum = np.dot(inputs_arr, self.weights) + self.bias
        return self._activate(weighted_sum)
    
    def _compute_confidence(self, inputs: Tuple, output: Any) -> float:
        """الثقة بناءً على مدى وضوح القرار"""
        inputs_arr = np.array(inputs, dtype=np.float64)
        weighted_sum = np.dot(inputs_arr, self.weights) + self.bias
        
        # Distance from threshold = confidence
        distance = abs(weighted_sum - self.threshold)
        return min(1.0, distance * 2)  # Scale to [0, 1]
    
    def adjust_weights(self, delta: np.ndarray, learning_rate: float = 0.1) -> None:
        """تعديل الأوزان"""
        with self._lock:
            self._weight_history.append(self.weights.copy())
            self.weights += learning_rate * delta
            # Normalize to prevent explosion
            norm = np.linalg.norm(self.weights)
            if norm > 1.0:
                self.weights /= norm
    
    def adjust_bias(self, delta: float, learning_rate: float = 0.1) -> None:
        """تعديل الانحياز"""
        with self._lock:
            self.bias += learning_rate * delta


class WeightedAND(WeightedGate):
    """
    بوابة AND موزونة - تجميع بالأوزان مع عتبة عالية
    ═══════════════════════════════════════════════
    
    المعادلة:
    ─────────
        weighted_sum = Σ(input_i × weight_i) + bias
        output = 1  ⟺  weighted_sum ≥ 0.9 (عتبة عالية)
        
    بالعربي: تتصرف مثل AND لكن مع أوزان قابلة للتعلم
    
    الفرق عن AND الحتمية:
    ─────────────────────
        AND الحتمية:
            يجب أن تكون جميع المدخلات = 1
        
        WeightedAND:
            يجب أن يتجاوز المجموع الموزون العتبة (0.9)
            بعض المدخلات قد تكون أهم من غيرها (أوزان أعلى)
    
    مثال عملي:
    ───────────
        # نظام تسجيل دخول
        gate = WeightedAND(n_inputs=3)  # كلمة سر، بصمة، وجه
        
        # افتراضياً: كل عامل له نفس الوزن (0.33)
        # بعد التعلم: كلمة السر أهم → وزن أعلى
        gate.weights = [0.5, 0.3, 0.2]
        
        # كلمة سر صحيحة + بصمة صحيحة = قد يكفي!
        output, trace = gate(1.0, 1.0, 0.0)  # 0.5+0.3 = 0.8 < 0.9 → رفض
        
    لماذا عتبة 0.9؟
    ────────────────
    عتبة عالية = محاكاة سلوك AND التقليدية
    (تتطلب جميع المدخلات أو معظمها)
    """
    
    def __init__(self, n_inputs: int, threshold: float = 0.9, name: Optional[str] = None):
        super().__init__(n_inputs, threshold, "step", name)
        # AND-like: high threshold
        self.threshold = threshold
    
    @property
    def gate_type(self) -> str:
        return "WeightedAND"


class WeightedOR(WeightedGate):
    """
    بوابة OR موزونة - تجميع بالأوزان مع عتبة منخفضة
    ═══════════════════════════════════════════════
    
    المعادلة:
    ─────────
        weighted_sum = Σ(input_i × weight_i) + bias
        output = 1  ⟺  weighted_sum ≥ 0.1 (عتبة منخفضة)
        
    بالعربي: تتصرف مثل OR لكن مع أوزان قابلة للتعلم
    
    الفرق عن OR الحتمية:
    ─────────────────────
        OR الحتمية:
            أي مدخل = 1 يكفي
        
        WeightedOR:
            أي مدخل ذو وزن كافٍ يكفي
            المدخلات ذات الأوزان العالية أكثر تأثيراً
    
    مثال عملي:
    ───────────
        # نظام تنبيه
        gate = WeightedOR(n_inputs=3)  # دخان، حرارة، إنذار يدوي
        
        # الإنذار اليدوي أهم (قرار بشري)
        gate.weights = [0.3, 0.3, 0.8]
        
        # إنذار يدوي فقط = كافي جداً!
        output, trace = gate(0.0, 0.0, 1.0)  # 0.8 > 0.1 → تنبيه!
        
        # دخان خفيف فقط
        output, trace = gate(0.4, 0.0, 0.0)  # 0.12 > 0.1 → تنبيه!
        
    لماذا عتبة 0.1؟
    ────────────────
    عتبة منخفضة = محاكاة سلوك OR التقليدية
    (أي مدخل كافٍ تقريباً)
    """
    
    def __init__(self, n_inputs: int, threshold: float = 0.1, name: Optional[str] = None):
        super().__init__(n_inputs, threshold, "step", name)
        # OR-like: low threshold
        self.threshold = threshold
    
    @property
    def gate_type(self) -> str:
        return "WeightedOR"


# ════════════════════════════════════════════════════════════════════════════════
# ج) بوابات الإسقاط الموجي (WAVE PROJECTION GATES)
# ════════════════════════════════════════════════════════════════════════════════
#
# 🌊 الفلسفة:
# ───────────
# مستوحاة من ميكانيكا الكم - الحالة ليست 0 أو 1 بل تراكب!
#
# الحالة الكلاسيكية:  state ∈ {0, 1}
# الحالة الموجية:     |ψ⟩ = α|0⟩ + β|1⟩   حيث |α|² + |β|² = 1
#
# ┌─────────────────────────────────────────────────────────────────────────────┐
# │  المفاهيم الأساسية:                                                        │
# │                                                                             │
# │  • WaveState: الحالة الموجية (amplitudes + states)                        │
# │  • Superposition: التراكب - وجود في حالات متعددة معاً                      │
# │  • Collapse: الانهيار - التحول لحالة واحدة عند القياس                       │
# │  • Projection: الإسقاط على فضاء فرعي                                       │
# │  • Phase: الطور - زاوية السعة المركبة                                       │
# └─────────────────────────────────────────────────────────────────────────────┘
#
# المعادلات:
# ──────────
#   |ψ_out⟩ = U |ψ_in⟩                  ← تحويل وحدوي
#   P(state_i) = |⟨state_i|ψ⟩|²        ← احتمال القياس
#   collapse → state_i مع احتمال P(state_i)
#
# ════════════════════════════════════════════════════════════════════════════════

@dataclass
class WaveState:
    """
    حالة موجية - تراكب كمي للحالات
    ═══════════════════════════════
    
    المعادلة:
    ─────────
        |ψ⟩ = Σ amplitude_i × |state_i⟩
        
        حيث: Σ |amplitude_i|² = 1 (التطبيع)
    
    المكونات:
    ─────────
    • amplitudes: سعات مركبة (complex)
      - المقدار |α|² = الاحتمال
      - الطور arg(α) = المعلومات الكمية
      
    • states: تسميات الحالات (0, 1, 2, ...)
    
    مثال:
    ──────
        # حالة تراكب متساوية بين 0 و 1
        state = WaveState(
            amplitudes=np.array([1/√2, 1/√2]),  # متساوية
            states=np.array([0, 1])
        )
        # P(0) = P(1) = 0.5
        
    انهيار الحالة:
    ──────────────
        # عند القياس، تنهار لحالة واحدة
        collapsed = state.collapse()  # → 0 أو 1 عشوائياً
        
    الاحتمالات:
    ───────────
        probs = state.probabilities  # [0.5, 0.5]
    """
    amplitudes: np.ndarray  # Complex amplitudes
    states: np.ndarray      # State labels
    
    @property
    def probabilities(self) -> np.ndarray:
        """احتمالات الحالات (|amplitude|²)"""
        return np.abs(self.amplitudes) ** 2
    
    @property
    def most_likely(self) -> int:
        """الحالة الأكثر احتمالاً"""
        return int(self.states[np.argmax(self.probabilities)])
    
    def collapse(self, deterministic: bool = True) -> int:
        """
        انهيار الموجة إلى حالة واحدة
        
        Args:
            deterministic: إذا True، اختر الأكثر احتمالاً
                          إذا False، عينة عشوائية (لا يُنصح)
        """
        if deterministic:
            return self.most_likely
        else:
            probs = self.probabilities
            probs /= probs.sum()  # Normalize
            return int(np.random.choice(self.states, p=probs))
    
    def confidence(self) -> float:
        """ثقة القرار - كلما زاد التركز، زادت الثقة"""
        probs = self.probabilities
        if len(probs) == 0:
            return 0.0
        max_prob = np.max(probs)
        return float(max_prob)
    
    def entropy(self) -> float:
        """إنتروبيا - مقياس عدم اليقين"""
        probs = self.probabilities
        probs = probs[probs > 0]  # Avoid log(0)
        if len(probs) == 0:
            return 0.0
        return -float(np.sum(probs * np.log2(probs)))


class WaveProjectionGate(BaseGate):
    """
    بوابة الإسقاط الموجي - تحويل كمي-إلهامي
    ═══════════════════════════════════════════
    
    🌊 الفلسفة:
    ───────────
    بدلاً من القرار الثنائي (0/1)، نمثل الحالة كتراكب موجي
    كل "حالة" لها سعة (amplitude) وطور (phase)
    
    المعادلة:
    ─────────
        |ψ_out⟩ = U |ψ_in⟩
        
        حيث U = e^(iθ) × Projection_Matrix
    
    المكونات:
    ─────────
    • n_states: عدد الحالات الممكنة
    • projection: مصفوفة الإسقاط (قابلة للتعلم)
    • phase: أطوار البوابة (قابلة للتعلم)
    
    ┌─────────────────────────────────────────────────────────────────────────┐
    │  مسار التنفيذ:                                                          │
    │                                                                         │
    │  inputs → _input_to_wave() → WaveState_in                              │
    │                                  ↓                                      │
    │                          projection × phase                             │
    │                                  ↓                                      │
    │                            WaveState_out → collapse() → decision       │
    └─────────────────────────────────────────────────────────────────────────┘
    
    مثال:
    ──────
        gate = WaveProjectionGate(n_states=4)
        
        # المدخلات تُحوّل لموجة
        wave_out = gate(0.8, 0.3, 0.1, 0.0)
        
        # الخرج حالة موجية
        print(wave_out.probabilities)  # [0.7, 0.2, 0.05, 0.05]
        print(wave_out.collapse())     # → 0 (الأكثر احتمالاً)
    
    التعلم:
    ───────
        # تعديل أطوار البوابة
        gate.adjust_phase(delta=np.array([0.1, -0.1, 0.0, 0.0]))
        
    لماذا مفيدة؟
    ─────────────
    1. قرارات ناعمة (soft decisions) بدلاً من 0/1
    2. تمثيل عدم اليقين (uncertainty)
    3. الاحتفاظ بمعلومات متعددة (superposition)
    4. الإنتروبيا كمقياس لعدم اليقين
    
    ملاحظة: هذا إلهام كمومي، ليس حوسبة كمومية حقيقية
    """
    
    def __init__(self, n_states: int = 4, 
                 projection_matrix: Optional[np.ndarray] = None,
                 name: Optional[str] = None):
        super().__init__(name)
        self.n_states = n_states
        self.states = np.arange(n_states)
        
        if projection_matrix is not None:
            self.projection = projection_matrix
        else:
            # Initialize with identity-like projection
            self.projection = np.eye(n_states, dtype=np.complex128)
        
        # Gate phase (learnable)
        self.phase = np.zeros(n_states, dtype=np.float64)
    
    @property
    def gate_type(self) -> str:
        return "WaveProjection"
    
    def _input_to_wave(self, inputs: Tuple[float, ...]) -> WaveState:
        """تحويل المدخلات إلى حالة موجية"""
        # Map inputs to amplitudes
        n = len(inputs)
        if n == 0:
            amplitudes = np.ones(self.n_states, dtype=np.complex128) / np.sqrt(self.n_states)
        else:
            # Pad or truncate to match n_states
            base_amps = np.array(inputs, dtype=np.float64)
            if len(base_amps) < self.n_states:
                base_amps = np.pad(base_amps, (0, self.n_states - len(base_amps)))
            else:
                base_amps = base_amps[:self.n_states]
            
            # Normalize
            norm = np.linalg.norm(base_amps)
            if norm > 0:
                base_amps /= norm
            
            amplitudes = base_amps.astype(np.complex128)
        
        return WaveState(amplitudes=amplitudes, states=self.states)
    
    def _compute(self, *inputs: float) -> WaveState:
        """
        تنفيذ الإسقاط الموجي
        
        Returns:
            WaveState representing output superposition
        """
        input_wave = self._input_to_wave(inputs)
        
        # Apply projection matrix
        projected = self.projection @ input_wave.amplitudes
        
        # Apply phase shift
        phase_shift = np.exp(1j * self.phase)
        projected *= phase_shift
        
        # Normalize
        norm = np.linalg.norm(projected)
        if norm > 0:
            projected /= norm
        
        return WaveState(amplitudes=projected, states=self.states)
    
    def _compute_confidence(self, inputs: Tuple, output: Any) -> float:
        """ثقة الإسقاط"""
        if isinstance(output, WaveState):
            return output.confidence()
        return 1.0
    
    def collapse_deterministic(self, *inputs: float) -> Tuple[int, GateTrace]:
        """
        إسقاط + انهيار حتمي
        
        Returns:
            (collapsed_state, trace)
        """
        wave_state, trace = self(*inputs)
        collapsed = wave_state.collapse(deterministic=True)
        trace.metadata["collapsed_to"] = collapsed
        trace.metadata["wave_entropy"] = wave_state.entropy()
        return collapsed, trace
    
    def adjust_projection(self, delta: np.ndarray, learning_rate: float = 0.01) -> None:
        """تعديل مصفوفة الإسقاط"""
        with self._lock:
            self.projection += learning_rate * delta
            # Re-normalize columns
            for i in range(self.n_states):
                norm = np.linalg.norm(self.projection[:, i])
                if norm > 0:
                    self.projection[:, i] /= norm
    
    def adjust_phase(self, delta: np.ndarray, learning_rate: float = 0.1) -> None:
        """تعديل الطور"""
        with self._lock:
            self.phase += learning_rate * delta
            # Keep phase in [-π, π]
            self.phase = np.mod(self.phase + np.pi, 2 * np.pi) - np.pi


# ════════════════════════════════════════════════════════════════════════════════
# GATE NETWORK - شبكة البوابات
# ════════════════════════════════════════════════════════════════════════════════
#
# 🔗 الفلسفة:
# ───────────
# البوابات المفردة محدودة القدرة، لكن عند ربطها في شبكة...
# نحصل على قوة تعبيرية هائلة!
#
# ┌─────────────────────────────────────────────────────────────────────────────┐
# │  مثال شبكة:                                                                 │
# │                                                                             │
# │      input.a ─────┬─────→ [AND1] ──┐                                       │
# │                   │                 ├──→ [OR1] ──→ output                  │
# │      input.b ─────┼─────→ [AND2] ──┘                                       │
# │                   │         ↑                                               │
# │      input.c ─────┴─────────┘                                              │
# └─────────────────────────────────────────────────────────────────────────────┘
#
# الميزات:
# ────────
# • ترتيب طوبولوجي (Topological Sort) للتنفيذ الصحيح
# • تنفيذ متوازي للبوابات المستقلة
# • تتبع مركب (CompoundTrace) للشبكة كاملة
# • اكتشاف الدورات (cycles)
#
# ════════════════════════════════════════════════════════════════════════════════

class GateNetwork:
    """
    شبكة بوابات منطقية - دائرة منطقية كاملة
    ═════════════════════════════════════════
    
    🏗️ البناء:
    ───────────
        network = GateNetwork("MyCircuit")
        
        # إضافة البوابات
        network.add_gate("and1", ANDGate())
        network.add_gate("and2", ANDGate())
        network.add_gate("or1", ORGate())
        
        # الربط
        network.connect("input.a", "and1.0")
        network.connect("input.b", "and1.1")
        network.connect("input.b", "and2.0")
        network.connect("input.c", "and2.1")
        network.connect("and1.out", "or1.0")
        network.connect("and2.out", "or1.1")
        
        # التنفيذ
        result = network.execute({"a": 1, "b": 1, "c": 0})
    
    📊 الخرج:
    ──────────
        {
            "and1": (output, trace),
            "and2": (output, trace),
            "or1": (output, trace),
            "_compound_trace": CompoundTrace(...)
        }
    
    الترتيب الطوبولوجي:
    ─────────────────────
        يضمن تنفيذ البوابات بالترتيب الصحيح:
        1. البوابات التي تعتمد فقط على المدخلات أولاً
        2. ثم البوابات التي تعتمد على مخرجات أخرى
        3. كشف الدورات (A→B→A) لمنع التكرار اللانهائي
    
    التنفيذ المتوازي:
    ──────────────────
        البوابات على نفس المستوى (لا تعتمد على بعضها)
        تُنفّذ بالتوازي باستخدام ThreadPool
    """
    
    def __init__(self, name: str = "GateNetwork", max_workers: int = 4):
        self.name = name
        self.gates: Dict[str, BaseGate] = {}
        self.connections: Dict[str, str] = {}  # target -> source
        self.max_workers = max_workers
        self._lock = threading.RLock()
        self._execution_order: List[str] = []
    
    def add_gate(self, name: str, gate: BaseGate) -> None:
        """إضافة بوابة للشبكة"""
        with self._lock:
            self.gates[name] = gate
            gate.name = name
    
    def connect(self, source: str, target: str) -> None:
        """
        ربط مخرج بوابة بمدخل بوابة أخرى
        
        Args:
            source: "gate_name.out" or "input.name"
            target: "gate_name.input_index"
        """
        with self._lock:
            self.connections[target] = source
    
    def _topological_sort(self) -> List[str]:
        """ترتيب البوابات حسب التبعية"""
        # Build dependency graph
        deps: Dict[str, set] = {name: set() for name in self.gates}
        
        for target, source in self.connections.items():
            target_gate = target.split(".")[0]
            if target_gate not in self.gates:
                continue
            
            source_gate = source.split(".")[0]
            if source_gate in self.gates:
                deps[target_gate].add(source_gate)
        
        # Kahn's algorithm
        order = []
        no_deps = [name for name, d in deps.items() if len(d) == 0]
        
        while no_deps:
            gate = no_deps.pop(0)
            order.append(gate)
            
            for name, d in deps.items():
                if gate in d:
                    d.remove(gate)
                    if len(d) == 0 and name not in order:
                        no_deps.append(name)
        
        return order
    
    def execute(self, inputs: Dict[str, Any]) -> Tuple[Dict[str, Any], CompoundTrace]:
        """
        تنفيذ الشبكة
        
        Args:
            inputs: قاموس المدخلات {"name": value}
        
        Returns:
            (outputs, compound_trace)
        """
        with self._lock:
            self._execution_order = self._topological_sort()
        
        # Store all values
        values: Dict[str, Any] = {f"input.{k}": v for k, v in inputs.items()}
        compound_trace = CompoundTrace()
        
        # Execute gates in order
        for gate_name in self._execution_order:
            gate = self.gates[gate_name]
            
            # Collect inputs for this gate
            gate_inputs = []
            for i in range(10):  # Max 10 inputs per gate
                target = f"{gate_name}.{i}"
                if target in self.connections:
                    source = self.connections[target]
                    if source in values:
                        gate_inputs.append(values[source])
                    else:
                        break
                else:
                    break
            
            if gate_inputs:
                output, trace = gate(*gate_inputs)
                values[f"{gate_name}.out"] = output
                compound_trace.add(trace)
        
        # Collect outputs
        outputs = {
            name: values.get(f"{name}.out")
            for name in self.gates
            if f"{name}.out" in values
        }
        
        return outputs, compound_trace
    
    def execute_parallel(self, inputs: Dict[str, Any]) -> Tuple[Dict[str, Any], CompoundTrace]:
        """
        تنفيذ متوازي للبوابات المستقلة
        
        البوابات التي ليس لها تبعية تُنفذ بالتوازي
        """
        with self._lock:
            execution_order = self._topological_sort()
        
        values: Dict[str, Any] = {f"input.{k}": v for k, v in inputs.items()}
        compound_trace = CompoundTrace()
        
        # Group gates by dependency level
        levels: List[List[str]] = []
        remaining = set(execution_order)
        executed = set()
        
        while remaining:
            # Find gates whose dependencies are all executed
            ready = []
            for gate_name in remaining:
                deps_met = True
                for target, source in self.connections.items():
                    if target.startswith(f"{gate_name}."):
                        source_gate = source.split(".")[0]
                        if source_gate in self.gates and source_gate not in executed:
                            deps_met = False
                            break
                if deps_met:
                    ready.append(gate_name)
            
            if not ready:
                break
            
            levels.append(ready)
            executed.update(ready)
            remaining -= set(ready)
        
        # Execute each level in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for level in levels:
                futures = {}
                
                for gate_name in level:
                    gate = self.gates[gate_name]
                    
                    # Collect inputs
                    gate_inputs = []
                    for i in range(10):
                        target = f"{gate_name}.{i}"
                        if target in self.connections:
                            source = self.connections[target]
                            if source in values:
                                gate_inputs.append(values[source])
                            else:
                                break
                        else:
                            break
                    
                    if gate_inputs:
                        futures[executor.submit(gate, *gate_inputs)] = gate_name
                
                # Collect results
                for future in as_completed(futures):
                    gate_name = futures[future]
                    output, trace = future.result()
                    values[f"{gate_name}.out"] = output
                    compound_trace.add(trace)
        
        outputs = {
            name: values.get(f"{name}.out")
            for name in self.gates
            if f"{name}.out" in values
        }
        
        return outputs, compound_trace
    
    def __repr__(self) -> str:
        return f"GateNetwork({self.name}, gates={len(self.gates)}, connections={len(self.connections)})"


# ════════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════════

def create_decision_circuit(
    threat: int, ethical_violation: int, emergency_override: int
) -> Tuple[int, CompoundTrace]:
    """
    دائرة قرار بسيطة:
    Decision = (Threat AND NOT EthicalViolation) OR EmergencyOverride
    
    Returns:
        (decision, trace)
    """
    network = GateNetwork("DecisionCircuit")
    
    # Add gates
    network.add_gate("not_ethics", NOTGate())
    network.add_gate("and_main", ANDGate())
    network.add_gate("or_final", ORGate())
    
    # Connect
    network.connect("input.threat", "and_main.0")
    network.connect("input.ethical_violation", "not_ethics.0")
    network.connect("not_ethics.out", "and_main.1")
    network.connect("and_main.out", "or_final.0")
    network.connect("input.emergency_override", "or_final.1")
    
    # Execute
    outputs, trace = network.execute({
        "threat": threat,
        "ethical_violation": ethical_violation,
        "emergency_override": emergency_override
    })
    
    return outputs.get("or_final", 0), trace
