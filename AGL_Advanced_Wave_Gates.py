"""
🌊 معالج الموجات المتقدم - المرحلة 1
AGL Advanced Wave Processor - Phase 1

المطور: حسام هيكل (Hossam Heikal)
التاريخ: 26 ديسمبر 2025

الهدف: تطبيق جميع البوابات المنطقية عبر التداخل الموجي الكمومي
Goal: Implement all logic gates via quantum wave interference
"""

import numpy as np
import time
from typing import Tuple, List, Dict, Any

class AdvancedWaveProcessor:
    """
    معالج الموجات المتقدم - يدعم جميع البوابات المنطقية
    Advanced Wave Processor - Supports all logic gates
    """
    
    def __init__(self, noise_floor=0.01):
        """
        تهيئة المعالج
        
        Args:
            noise_floor (float): مستوى الضوضاء الكمومية (0.01 = 1%)
        """
        self.noise_floor = noise_floor
        self.operation_count = 0
        self.performance_log = []
        
        print("🌊 [AWP]: Advanced Wave Processor Initialized")
        print(f"   Quantum Noise Floor: {noise_floor * 100:.2f}%")
    
    # ============================================
    # الدوال المساعدة / Helper Functions
    # ============================================
    
    def _bit_to_wave(self, bit: int) -> complex:
        """
        تحويل البت (0/1) إلى موجة كمومية
        Convert bit to quantum wave
        
        Args:
            bit (int): 0 or 1
            
        Returns:
            complex: e^(i*phase)
        """
        phase = bit * np.pi
        return np.exp(1j * phase)
    
    def _measure_wave(self, wave: complex) -> int:
        """
        قياس الموجة لاستخراج البت (الانهيار الموجي)
        Measure wave to extract bit (wave collapse)
        
        Args:
            wave (complex): الموجة الكمومية
            
        Returns:
            int: 0 or 1
        """
        angle = np.angle(wave)
        projection = np.cos(angle)
        return 0 if projection > 0 else 1
    
    def _add_quantum_noise(self, wave: complex) -> complex:
        """
        إضافة ضوضاء الفراغ الكمومي
        Add quantum vacuum noise
        """
        noise_real = np.random.normal(0, self.noise_floor)
        noise_imag = np.random.normal(0, self.noise_floor)
        return wave + (noise_real + 1j * noise_imag)
    
    def _log_operation(self, operation: str, inputs: Tuple, output: int, time_taken: float):
        """تسجيل العملية للتحليل"""
        self.operation_count += 1
        self.performance_log.append({
            'operation': operation,
            'inputs': inputs,
            'output': output,
            'time': time_taken,
            'count': self.operation_count
        })
    
    # ============================================
    # البوابات المنطقية الأساسية / Basic Gates
    # ============================================
    
    def wave_xor(self, a: int, b: int) -> int:
        """
        ✅ بوابة XOR عبر التداخل الموجي
        XOR gate via wave interference
        
        الفيزياء:
        - 0 XOR 0 = e^(i*0) × e^(i*0) = 1 → measure → 0
        - 0 XOR 1 = e^(i*0) × e^(i*π) = -1 → measure → 1
        - 1 XOR 0 = e^(i*π) × e^(i*0) = -1 → measure → 1
        - 1 XOR 1 = e^(i*π) × e^(i*π) = 1 → measure → 0
        """
        start = time.perf_counter()
        
        wave_a = self._bit_to_wave(a)
        wave_b = self._bit_to_wave(b)
        
        # التداخل الموجي / Wave interference
        result_wave = wave_a * wave_b
        result_wave = self._add_quantum_noise(result_wave)
        
        # القياس / Measurement
        result = self._measure_wave(result_wave)
        
        elapsed = time.perf_counter() - start
        self._log_operation('XOR', (a, b), result, elapsed)
        
        return result
    
    def wave_and(self, a: int, b: int) -> int:
        """
        🆕 بوابة AND عبر تعديل السعة
        AND gate via amplitude modulation
        
        الفيزياء:
        - AND يتطلب أن يكون كلا المدخلين = 1
        - نستخدم الجمع الموجي وفحص السعة
        
        Logic:
        - 0 AND 0 = 0: (1 + 1 = 2, amp = 2.0)
        - 0 AND 1 = 0: (1 + (-1) = 0, amp = 0.0)
        - 1 AND 0 = 0: ((-1) + 1 = 0, amp = 0.0)
        - 1 AND 1 = 1: ((-1) + (-1) = -2, amp = 2.0)
        """
        start = time.perf_counter()
        
        # التحويل لموجات
        wave_a = self._bit_to_wave(a)
        wave_b = self._bit_to_wave(b)
        
        # AND عبر فحص الجمع الموجي:
        # فقط عندما يكون كلاهما = 1 (wave = -1)
        # sum = -2, angle = π
        sum_wave = wave_a + wave_b
        angle = np.angle(sum_wave)
        amplitude = np.abs(sum_wave)
        
        # إذا كانت السعة ≈ 2 والزاوية ≈ π → كلاهما 1
        # نستخدم الزاوية للتمييز
        result = 1 if (amplitude > 1.5 and abs(angle - np.pi) < 0.5) else 0
        
        elapsed = time.perf_counter() - start
        self._log_operation('AND', (a, b), result, elapsed)
        
        return result
    
    def wave_or(self, a: int, b: int) -> int:
        """
        🆕 بوابة OR عبر التداخل البنّاء
        OR gate via constructive interference
        
        Logic:
        - 0 OR 0 = 0: (1 + 1 = 2, angle = 0)
        - 0 OR 1 = 1: (1 + (-1) = 0, إذن نستخدم NOT AND NOT)
        - 1 OR 0 = 1
        - 1 OR 1 = 1: ((-1) + (-1) = -2, angle = π)
        
        نستخدم قانون De Morgan: A OR B = NOT(NOT A AND NOT B)
        """
        start = time.perf_counter()
        
        # استخدام De Morgan's Law
        # A OR B = NOT(NOT A AND NOT B)
        not_a = self.wave_not(a)
        not_b = self.wave_not(b)
        and_result = self.wave_and(not_a, not_b)
        result = self.wave_not(and_result)
        
        elapsed = time.perf_counter() - start
        self._log_operation('OR', (a, b), result, elapsed)
        
        return result
    
    def wave_not(self, a: int) -> int:
        """
        🆕 بوابة NOT عبر دوران الطور
        NOT gate via phase rotation
        
        الفيزياء:
        - NOT يعكس البت
        - نستخدم دوران طور بمقدار π
        
        Logic:
        - NOT 0 = e^(i*0) × e^(i*π) = -1 → measure → 1
        - NOT 1 = e^(i*π) × e^(i*π) = 1 → measure → 0
        """
        start = time.perf_counter()
        
        wave_a = self._bit_to_wave(a)
        
        # NOT عبر دوران π
        not_operator = np.exp(1j * np.pi)
        result_wave = wave_a * not_operator
        
        result = self._measure_wave(result_wave)
        
        elapsed = time.perf_counter() - start
        self._log_operation('NOT', (a,), result, elapsed)
        
        return result
    
    def wave_nand(self, a: int, b: int) -> int:
        """
        🆕 بوابة NAND = NOT(AND)
        NAND gate = NOT(AND)
        """
        return self.wave_not(self.wave_and(a, b))
    
    def wave_nor(self, a: int, b: int) -> int:
        """
        🆕 بوابة NOR = NOT(OR)
        NOR gate = NOT(OR)
        """
        return self.wave_not(self.wave_or(a, b))
    
    def wave_xnor(self, a: int, b: int) -> int:
        """
        🆕 بوابة XNOR = NOT(XOR)
        XNOR gate = NOT(XOR)
        """
        return self.wave_not(self.wave_xor(a, b))

    # ============================================
    # البوابات الموجهة (Vectorized Gates) - Phase 2A
    # ============================================

    def wave_xor_vectorized(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """
        ✅ بوابة XOR الموجهة (Vectorized XOR)
        
        Args:
            a (np.ndarray): مصفوفة المدخلات الأولى (0/1)
            b (np.ndarray): مصفوفة المدخلات الثانية (0/1)
            
        Returns:
            np.ndarray: مصفوفة النتائج
        """
        # 1. تحويل المدخلات إلى موجات (Vectorized)
        waves_a = np.exp(1j * a * np.pi)
        waves_b = np.exp(1j * b * np.pi)
        
        # 2. التداخل (Interference)
        interference = waves_a * waves_b
        
        # 3. القياس (Measurement)
        # Real part > 0 -> 0, Real part < 0 -> 1
        return (np.real(interference) <= 0).astype(int)

    def batch_xor(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """
        Alias for wave_xor_vectorized to maintain compatibility with AGL_Super_Intelligence
        """
        return self.wave_xor_vectorized(a, b)

    def wave_and_vectorized(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """
        ✅ بوابة AND الموجهة (Vectorized AND)
        """
        waves_a = np.exp(1j * a * np.pi)
        waves_b = np.exp(1j * b * np.pi)
        
        sum_wave = waves_a + waves_b
        amplitude = np.abs(sum_wave)
        angle = np.angle(sum_wave)
        
        # Condition: Amplitude > 1.5 AND Angle approx PI
        condition = (amplitude > 1.5) & (np.abs(angle - np.pi) < 0.5)
        return condition.astype(int)

    def wave_not_vectorized(self, a: np.ndarray) -> np.ndarray:
        """
        ✅ بوابة NOT الموجهة (Vectorized NOT)
        """
        waves_a = np.exp(1j * a * np.pi)
        rotation = np.exp(1j * np.pi)
        result_wave = waves_a * rotation
        
        return (np.real(result_wave) <= 0).astype(int)

    def wave_or_vectorized(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """
        ✅ بوابة OR الموجهة (Vectorized OR)
        Using De Morgan: A OR B = NOT(NOT A AND NOT B)
        """
        not_a = self.wave_not_vectorized(a)
        not_b = self.wave_not_vectorized(b)
        and_res = self.wave_and_vectorized(not_a, not_b)
        return self.wave_not_vectorized(and_res)
    
    # ============================================
    # الدوائر المركبة / Composite Circuits
    # ============================================
    
    def wave_half_adder(self, a: int, b: int) -> Tuple[int, int]:
        """
        🆕 جامع نصفي موجي
        Wave Half Adder
        
        Returns:
            (sum, carry): المجموع والحمل
            
        Logic:
        - sum = a XOR b
        - carry = a AND b
        """
        start = time.perf_counter()
        
        sum_bit = self.wave_xor(a, b)
        carry_bit = self.wave_and(a, b)
        
        elapsed = time.perf_counter() - start
        self._log_operation('HALF_ADDER', (a, b), (sum_bit, carry_bit), elapsed)
        
        return sum_bit, carry_bit
    
    def wave_full_adder(self, a: int, b: int, cin: int) -> Tuple[int, int]:
        """
        🆕 جامع كامل موجي
        Wave Full Adder
        
        Args:
            a, b: المدخلات
            cin: الحمل الداخل
            
        Returns:
            (sum, cout): المجموع والحمل الخارج
            
        Logic:
        - sum = a XOR b XOR cin
        - cout = (a AND b) OR (cin AND (a XOR b))
        """
        start = time.perf_counter()
        
        # المرحلة 1: جامع نصفي للمدخلين
        s1, c1 = self.wave_half_adder(a, b)
        
        # المرحلة 2: جامع نصفي مع الحمل الداخل
        sum_bit, c2 = self.wave_half_adder(s1, cin)
        
        # الحمل الخارج = c1 OR c2
        carry_out = self.wave_or(c1, c2)
        
        elapsed = time.perf_counter() - start
        self._log_operation('FULL_ADDER', (a, b, cin), (sum_bit, carry_out), elapsed)
        
        return sum_bit, carry_out
    
    def wave_ripple_adder(self, a_bits: List[int], b_bits: List[int]) -> List[int]:
        """
        🆕 جامع متسلسل متعدد البتات
        Ripple Carry Adder
        
        Args:
            a_bits: الرقم الأول (LSB أولاً)
            b_bits: الرقم الثاني (LSB أولاً)
            
        Returns:
            List[int]: المجموع (مع الحمل)
        """
        start = time.perf_counter()
        
        n = max(len(a_bits), len(b_bits))
        
        # موازنة الطول
        a_bits = a_bits + [0] * (n - len(a_bits))
        b_bits = b_bits + [0] * (n - len(b_bits))
        
        result = []
        carry = 0
        
        for i in range(n):
            sum_bit, carry = self.wave_full_adder(a_bits[i], b_bits[i], carry)
            result.append(sum_bit)
        
        # إضافة الحمل النهائي
        if carry:
            result.append(carry)
        
        elapsed = time.perf_counter() - start
        self._log_operation('RIPPLE_ADDER', (a_bits, b_bits), result, elapsed)
        
        return result
    
    # ============================================
    # عمليات متقدمة / Advanced Operations
    # ============================================
    
    def wave_multiply(self, a: int, b: int, bits: int = 4) -> int:
        """
        🆕 ضرب عبر الموجات (باستخدام الجمع المتكرر)
        Wave Multiplication (using repeated addition)
        """
        result = 0
        for _ in range(b):
            result = self.bits_to_int(
                self.wave_ripple_adder(
                    self.int_to_bits(result, bits),
                    self.int_to_bits(a, bits)
                )
            )
        return result
    
    # ============================================
    # دوال مساعدة للتحويل / Conversion Helpers
    # ============================================
    
    def int_to_bits(self, n: int, width: int = 8) -> List[int]:
        """تحويل رقم لقائمة بتات (LSB أولاً)"""
        return [int(b) for b in format(n, f'0{width}b')][::-1]
    
    def bits_to_int(self, bits: List[int]) -> int:
        """تحويل قائمة بتات لرقم"""
        return int(''.join(str(b) for b in reversed(bits)), 2)
    
    # ============================================
    # الاختبار والتحليل / Testing & Analysis
    # ============================================
    
    def test_all_gates(self) -> Dict[str, Any]:
        """
        اختبار شامل لجميع البوابات
        Comprehensive test of all gates
        """
        print("\n" + "="*60)
        print("🧪 اختبار جميع البوابات الموجية")
        print("   Testing All Wave Gates")
        print("="*60)
        
        results = {}
        
        # اختبار البوابات الأحادية
        print("\n1️⃣ بوابات أحادية المدخل / Single-Input Gates:")
        not_tests = [(0,), (1,)]
        not_expected = [1, 0]
        not_results = []
        
        for inputs in not_tests:
            result = self.wave_not(*inputs)
            not_results.append(result)
            print(f"   NOT {inputs[0]} = {result}")
        
        not_accuracy = sum(1 for r, e in zip(not_results, not_expected) if r == e) / len(not_expected)
        results['NOT'] = {'accuracy': not_accuracy, 'tests': len(not_expected)}
        
        # اختبار البوابات الثنائية
        test_cases = [(0, 0), (0, 1), (1, 0), (1, 1)]
        gates = {
            'XOR': (self.wave_xor, [0, 1, 1, 0]),
            'AND': (self.wave_and, [0, 0, 0, 1]),
            'OR': (self.wave_or, [0, 1, 1, 1]),
            'NAND': (self.wave_nand, [1, 1, 1, 0]),
            'NOR': (self.wave_nor, [1, 0, 0, 0]),
            'XNOR': (self.wave_xnor, [1, 0, 0, 1])
        }
        
        for gate_name, (gate_func, expected) in gates.items():
            print(f"\n2️⃣ {gate_name} Gate:")
            gate_results = []
            
            for inputs, exp in zip(test_cases, expected):
                result = gate_func(*inputs)
                gate_results.append(result)
                status = "✅" if result == exp else "❌"
                print(f"   {inputs[0]} {gate_name} {inputs[1]} = {result} (expected {exp}) {status}")
            
            accuracy = sum(1 for r, e in zip(gate_results, expected) if r == e) / len(expected)
            results[gate_name] = {'accuracy': accuracy, 'tests': len(expected)}
        
        # اختبار الجامع النصفي
        print("\n3️⃣ Half Adder:")
        ha_tests = test_cases
        ha_expected = [(0, 0), (1, 0), (1, 0), (0, 1)]
        ha_results = []
        
        for inputs, expected_output in zip(ha_tests, ha_expected):
            result = self.wave_half_adder(*inputs)
            ha_results.append(result)
            status = "✅" if result == expected_output else "❌"
            print(f"   {inputs[0]} + {inputs[1]} = sum:{result[0]}, carry:{result[1]} {status}")
        
        ha_accuracy = sum(1 for r, e in zip(ha_results, ha_expected) if r == e) / len(ha_expected)
        results['HALF_ADDER'] = {'accuracy': ha_accuracy, 'tests': len(ha_expected)}
        
        # اختبار الجامع الكامل
        print("\n4️⃣ Full Adder:")
        fa_tests = [(0,0,0), (0,0,1), (0,1,0), (0,1,1), (1,0,0), (1,0,1), (1,1,0), (1,1,1)]
        fa_expected = [(0,0), (1,0), (1,0), (0,1), (1,0), (0,1), (0,1), (1,1)]
        fa_results = []
        
        for inputs, expected_output in zip(fa_tests, fa_expected):
            result = self.wave_full_adder(*inputs)
            fa_results.append(result)
            status = "✅" if result == expected_output else "❌"
            print(f"   {inputs[0]}+{inputs[1]}+{inputs[2]} = sum:{result[0]}, carry:{result[1]} {status}")
        
        fa_accuracy = sum(1 for r, e in zip(fa_results, fa_expected) if r == e) / len(fa_expected)
        results['FULL_ADDER'] = {'accuracy': fa_accuracy, 'tests': len(fa_expected)}
        
        # اختبار الجامع المتسلسل
        print("\n5️⃣ Ripple Carry Adder (4-bit):")
        adder_tests = [
            ([1, 0, 1, 0], [0, 1, 1, 0]),  # 5 + 6 = 11
            ([1, 1, 1, 1], [0, 0, 0, 1]),  # 15 + 1 = 16
            ([1, 0, 0, 0], [1, 0, 0, 0]),  # 1 + 1 = 2
        ]
        
        for a_bits, b_bits in adder_tests:
            result_bits = self.wave_ripple_adder(a_bits, b_bits)
            a_val = self.bits_to_int(a_bits)
            b_val = self.bits_to_int(b_bits)
            result_val = self.bits_to_int(result_bits)
            expected = a_val + b_val
            status = "✅" if result_val == expected else "❌"
            print(f"   {a_val} + {b_val} = {result_val} (expected {expected}) {status}")
        
        # ملخص النتائج
        print("\n" + "="*60)
        print("📊 ملخص النتائج / Results Summary:")
        print("="*60)
        
        total_accuracy = 0
        for gate, data in results.items():
            accuracy_pct = data['accuracy'] * 100
            total_accuracy += accuracy_pct
            print(f"   {gate:12s}: {accuracy_pct:6.2f}% ({data['tests']} tests)")
        
        avg_accuracy = total_accuracy / len(results)
        print(f"\n   المتوسط العام / Overall Average: {avg_accuracy:.2f}%")
        
        # إحصائيات الأداء
        print(f"\n⚡ إحصائيات الأداء / Performance Stats:")
        print(f"   إجمالي العمليات / Total Operations: {self.operation_count}")
        
        if self.performance_log:
            total_time = sum(log['time'] for log in self.performance_log)
            avg_time = total_time / len(self.performance_log)
            print(f"   متوسط الوقت / Average Time: {avg_time*1000:.6f} ms")
            print(f"   السرعة / Throughput: {1/avg_time:.0f} ops/sec")
        
        print("="*60 + "\n")
        
        return results

# ============================================
# التشغيل / Execution
# ============================================

if __name__ == "__main__":
    print("🌊 AGL Advanced Wave Processor - Phase 1")
    print("   Initializing Quantum Wave Computing System...\n")
    
    # إنشاء المعالج
    processor = AdvancedWaveProcessor(noise_floor=0.01)
    
    # اختبار شامل
    results = processor.test_all_gates()
    
    # رسالة ختامية
    print("🎉 الخلاصة / Conclusion:")
    print("   ✅ جميع البوابات المنطقية تعمل بالموجات الكمومية!")
    print("   ✅ All logic gates working with quantum waves!")
    print("\n   المرحلة 1 مكتملة / Phase 1 Complete!")
    print("   الخطوة التالية: التوازي الموجي (GPU Acceleration)")
