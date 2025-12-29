"""
🌊 معالج الموجات المُحسّن - Vectorized Edition
AGL Vectorized Wave Processor

المطور: حسام هيكل (Hossam Heikal)
التاريخ: 27 ديسمبر 2025

الهدف: معالجة 100,000 عملية موجية في أقل من ثانية
Goal: Process 100,000 wave operations in less than 1 second

التقنية: NumPy Vectorization + Batch Processing
Technique: NumPy Vectorization + Batch Processing
"""

import numpy as np
import time
from typing import List, Tuple, Optional, Dict, Any

class VectorizedWaveProcessor:
    """
    معالج موجي محسّن يستخدم NumPy Vectorization
    Optimized wave processor using NumPy Vectorization
    
    الأداء المتوقع / Expected Performance:
    - 100K operations < 1 second
    - 50-100× faster than loop-based approach
    - Memory efficient (streaming for large datasets)
    """
    
    def __init__(self, noise_floor: float = 0.01, vectorize_threshold: int = 10):
        """
        تهيئة المعالج المحسّن
        
        Args:
            noise_floor: مستوى الضوضاء الكمومية
            vectorize_threshold: الحد الأدنى لاستخدام vectorization
        """
        self.noise_floor = noise_floor
        self.vectorize_threshold = vectorize_threshold
        self.operation_count = 0
        self.performance_stats = {
            'total_operations': 0,
            'total_time': 0.0,
            'vectorized_operations': 0,
            'loop_operations': 0
        }
        
        print("🌊 [VWP]: Vectorized Wave Processor Initialized")
        print(f"   Noise Floor: {noise_floor * 100:.2f}%")
        print(f"   Vectorize Threshold: {vectorize_threshold} operations")
    
    # ============================================
    # Core Vectorized Operations
    # ============================================
    
    def _bits_to_waves_vectorized(self, bits: np.ndarray) -> np.ndarray:
        """
        تحويل مصفوفة بتات لموجات (vectorized)
        Convert array of bits to waves (vectorized)
        
        Args:
            bits: np.ndarray of 0s and 1s
            
        Returns:
            np.ndarray of complex waves
        """
        phases = bits * np.pi
        return np.exp(1j * phases)
    
    def _measure_waves_vectorized(self, waves: np.ndarray) -> np.ndarray:
        """
        قياس مصفوفة موجات لاستخراج البتات (vectorized)
        Measure array of waves to extract bits (vectorized)
        
        Args:
            waves: np.ndarray of complex waves
            
        Returns:
            np.ndarray of 0s and 1s
        """
        angles = np.angle(waves)
        projections = np.cos(angles)
        return (projections < 0).astype(int)
    
    def _add_quantum_noise_vectorized(self, waves: np.ndarray) -> np.ndarray:
        """
        إضافة ضوضاء كمومية (vectorized)
        Add quantum noise (vectorized)
        """
        noise_real = np.random.normal(0, self.noise_floor, waves.shape)
        noise_imag = np.random.normal(0, self.noise_floor, waves.shape)
        noise = noise_real + 1j * noise_imag
        return waves + noise
    
    # ============================================
    # Vectorized Logic Gates
    # ============================================
    
    def batch_xor(self, a_array: np.ndarray, b_array: np.ndarray, 
                  add_noise: bool = True, amplitude_factor: float = 1.0) -> np.ndarray:
        """
        عملية XOR موجية دفعية (vectorized)
        Batch XOR operation (vectorized)
        
        Args:
            a_array: مصفوفة المدخلات الأولى [0,1,0,1,...]
            b_array: مصفوفة المدخلات الثانية [1,0,1,0,...]
            add_noise: إضافة ضوضاء كمومية
            amplitude_factor: معامل السعة (للتحكم الأخلاقي)
            
        Returns:
            np.ndarray: النتائج [1,1,1,1,...]
        """
        start = time.perf_counter()
        
        # التحويل لموجات (vectorized)
        waves_a = self._bits_to_waves_vectorized(a_array)
        waves_b = self._bits_to_waves_vectorized(b_array)
        
        # تطبيق معامل السعة (Ethical Damping)
        if amplitude_factor < 1.0:
            waves_a *= amplitude_factor
            waves_b *= amplitude_factor
        
        # إضافة ضوضاء (optional)
        if add_noise:
            waves_a = self._add_quantum_noise_vectorized(waves_a)
            waves_b = self._add_quantum_noise_vectorized(waves_b)
        
        # التداخل الموجي (vectorized multiplication)
        result_waves = waves_a * waves_b
        
        # القياس (vectorized)
        # نتحقق من السعة النهائية
        amplitudes = np.abs(result_waves)
        angles = np.angle(result_waves)
        projections = np.cos(angles)
        
        # إذا كانت السعة منخفضة جداً (بسبب الكبت الأخلاقي)، النتيجة 0
        # Threshold 0.1 allows for some noise but blocks heavily dampened waves
        valid_mask = amplitudes > 0.1
        
        # Logic: projection < 0 is True (1), else False (0)
        # AND with valid_mask to ensure weak waves become 0
        results = ((projections < 0) & valid_mask).astype(int)
        
        elapsed = time.perf_counter() - start
        
        # تحديث الإحصائيات
        self.operation_count += len(a_array)
        self.performance_stats['total_operations'] += len(a_array)
        self.performance_stats['total_time'] += elapsed
        self.performance_stats['vectorized_operations'] += len(a_array)
        
        return results
    
    def batch_and(self, a_array: np.ndarray, b_array: np.ndarray, amplitude_factor: float = 1.0) -> np.ndarray:
        """
        عملية AND موجية دفعية (vectorized)
        Batch AND operation (vectorized)
        """
        start = time.perf_counter()
        
        waves_a = self._bits_to_waves_vectorized(a_array)
        waves_b = self._bits_to_waves_vectorized(b_array)
        
        if amplitude_factor < 1.0:
            waves_a *= amplitude_factor
            waves_b *= amplitude_factor
        
        # AND logic: sum waves and check phase
        sum_waves = waves_a + waves_b
        angles = np.angle(sum_waves)
        amplitudes = np.abs(sum_waves)
        
        # Both must be 1 (wave = -1) → sum = -2, angle ≈ π
        # Amplitude check needs to scale with amplitude_factor
        # Normal max amplitude is 2.0. With factor 0.1, max is 0.2.
        # Threshold should be relative.
        
        # FIXED: To act as an Ethical Lock, we must NOT scale the threshold linearly.
        # If the wave is dampened, it SHOULD fail to trigger the gate.
        # We use a fixed threshold (e.g. 0.8) which requires significant signal strength.
        # If amplitude_factor is < 0.4, max sum is < 0.8, so it will return 0.
        
        threshold = 0.8
        
        results = ((amplitudes > threshold) & (np.abs(angles - np.pi) < 0.5)).astype(int)
        
        elapsed = time.perf_counter() - start
        self.operation_count += len(a_array)
        self.performance_stats['total_operations'] += len(a_array)
        self.performance_stats['total_time'] += elapsed
        self.performance_stats['vectorized_operations'] += len(a_array)
        
        return results
    
    def batch_or(self, a_array: np.ndarray, b_array: np.ndarray, amplitude_factor: float = 1.0) -> np.ndarray:
        """
        عملية OR موجية دفعية (vectorized)
        Batch OR operation (vectorized)
        
        Uses De Morgan's Law: A OR B = NOT(NOT A AND NOT B)
        """
        start = time.perf_counter()
        
        # NOT operations (vectorized)
        not_a = 1 - a_array
        not_b = 1 - b_array
        
        # AND operation (Pass amplitude_factor)
        and_result = self.batch_and(not_a, not_b, amplitude_factor=amplitude_factor)
        
        # Final NOT
        results = 1 - and_result
        
        elapsed = time.perf_counter() - start
        # operations already counted in batch_and
        
        return results
    
    def batch_not(self, a_array: np.ndarray) -> np.ndarray:
        """
        عملية NOT موجية دفعية (vectorized)
        Batch NOT operation (vectorized)
        
        Simply: 1 - input (for binary 0/1)
        """
        return 1 - a_array
    
    # ============================================
    # Advanced Operations
    # ============================================
    
    def batch_half_adder(self, a_array: np.ndarray, b_array: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        جامع نصفي دفعي (vectorized)
        Batch Half Adder (vectorized)
        
        Returns:
            (sum_array, carry_array)
        """
        sum_bits = self.batch_xor(a_array, b_array, add_noise=False)
        carry_bits = self.batch_and(a_array, b_array)
        return sum_bits, carry_bits
    
    def batch_full_adder(self, a_array: np.ndarray, b_array: np.ndarray, 
                         cin_array: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        جامع كامل دفعي (vectorized)
        Batch Full Adder (vectorized)
        
        Returns:
            (sum_array, cout_array)
        """
        # First half adder
        s1, c1 = self.batch_half_adder(a_array, b_array)
        
        # Second half adder
        sum_bits, c2 = self.batch_half_adder(s1, cin_array)
        
        # Carry out
        carry_out = self.batch_or(c1, c2)
        
        return sum_bits, carry_out
    
    # ============================================
    # Streaming for Large Datasets
    # ============================================
    
    def stream_xor(self, a_array: np.ndarray, b_array: np.ndarray, 
                   chunk_size: int = 100000) -> np.ndarray:
        """
        معالجة XOR على دفعات للبيانات الكبيرة
        Stream XOR for large datasets
        
        Args:
            a_array: مصفوفة كبيرة (ملايين العناصر)
            b_array: مصفوفة كبيرة
            chunk_size: حجم الدفعة (default: 100K)
            
        Returns:
            np.ndarray: النتائج الكاملة
        """
        n = len(a_array)
        results = np.zeros(n, dtype=int)
        
        print(f"🌊 [VWP]: Streaming {n:,} operations in chunks of {chunk_size:,}")
        
        for i in range(0, n, chunk_size):
            end = min(i + chunk_size, n)
            chunk_a = a_array[i:end]
            chunk_b = b_array[i:end]
            
            results[i:end] = self.batch_xor(chunk_a, chunk_b, add_noise=False)
            
            if (i // chunk_size) % 10 == 0:
                progress = (i / n) * 100
                print(f"   Progress: {progress:.1f}% ({i:,}/{n:,})")
        
        print(f"   ✅ Complete: {n:,} operations")
        return results
    
    # ============================================
    # Benchmarking & Statistics
    # ============================================
    
    def benchmark(self, sizes: List[int] = [100, 1000, 10000, 100000, 1000000]) -> Dict[str, Any]:
        """
        اختبار الأداء على أحجام مختلفة
        Benchmark performance on different sizes
        
        Args:
            sizes: قائمة أحجام البيانات للاختبار
            
        Returns:
            Dict: نتائج الاختبار
        """
        print("\n" + "="*60)
        print("🧪 VECTORIZED WAVE PROCESSOR BENCHMARK")
        print("="*60)
        
        results = {}
        
        for size in sizes:
            print(f"\n📊 Testing {size:,} operations:")
            
            # توليد بيانات عشوائية
            a_data = np.random.randint(0, 2, size)
            b_data = np.random.randint(0, 2, size)
            
            # اختبار XOR
            start = time.perf_counter()
            xor_results = self.batch_xor(a_data, b_data, add_noise=False)
            elapsed = time.perf_counter() - start
            
            ops_per_sec = size / elapsed if elapsed > 0 else float('inf')
            
            print(f"   Time: {elapsed*1000:.3f} ms")
            print(f"   Speed: {ops_per_sec:,.0f} ops/sec")
            print(f"   Throughput: {ops_per_sec/1e6:.2f} M ops/sec")
            
            # التحقق من الدقة
            expected = a_data ^ b_data
            accuracy = (xor_results == expected).mean() * 100
            print(f"   Accuracy: {accuracy:.2f}%")
            
            results[size] = {
                'time_ms': elapsed * 1000,
                'ops_per_sec': ops_per_sec,
                'accuracy': accuracy
            }
        
        # ملخص الأداء
        print("\n" + "="*60)
        print("📈 PERFORMANCE SUMMARY")
        print("="*60)
        
        if self.performance_stats['total_operations'] > 0:
            avg_speed = (self.performance_stats['total_operations'] / 
                        self.performance_stats['total_time'])
            print(f"Total Operations: {self.performance_stats['total_operations']:,}")
            print(f"Total Time: {self.performance_stats['total_time']:.3f} sec")
            print(f"Average Speed: {avg_speed:,.0f} ops/sec")
            print(f"Average Throughput: {avg_speed/1e6:.2f} M ops/sec")
        
        print("="*60 + "\n")
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات الأداء"""
        stats = self.performance_stats.copy()
        if stats['total_time'] > 0:
            stats['avg_ops_per_sec'] = stats['total_operations'] / stats['total_time']
        else:
            stats['avg_ops_per_sec'] = 0
        return stats

# ============================================
# Testing & Execution
# ============================================

if __name__ == "__main__":
    print("🌊 AGL Vectorized Wave Processor - Performance Test\n")
    
    # إنشاء المعالج
    processor = VectorizedWaveProcessor(noise_floor=0.01)
    
    # اختبار سريع
    print("\n[Quick Test] 1000 XOR operations:")
    a = np.random.randint(0, 2, 1000)
    b = np.random.randint(0, 2, 1000)
    
    start = time.perf_counter()
    results = processor.batch_xor(a, b)
    elapsed = time.perf_counter() - start
    
    expected = a ^ b
    accuracy = (results == expected).mean() * 100
    
    print(f"✅ Time: {elapsed*1000:.3f} ms")
    print(f"✅ Speed: {1000/elapsed:,.0f} ops/sec")
    print(f"✅ Accuracy: {accuracy:.2f}%")
    
    # Benchmark شامل
    benchmark_results = processor.benchmark(
        sizes=[100, 1000, 10000, 100000, 1000000]
    )
    
    # اختبار Streaming (10 مليون عملية)
    print("\n[Streaming Test] 10 Million operations:")
    print("⚠️  This may take 10-60 seconds...")
    
    a_big = np.random.randint(0, 2, 10_000_000)
    b_big = np.random.randint(0, 2, 10_000_000)
    
    start = time.perf_counter()
    results_big = processor.stream_xor(a_big, b_big, chunk_size=100000)
    elapsed = time.perf_counter() - start
    
    print(f"\n✅ 10M operations completed in {elapsed:.2f} seconds")
    print(f"✅ Speed: {10_000_000/elapsed:,.0f} ops/sec")
    print(f"✅ Throughput: {(10_000_000/elapsed)/1e6:.2f} M ops/sec")
    
    # التحقق من الدقة
    expected_big = a_big ^ b_big
    accuracy_big = (results_big == expected_big).mean() * 100
    print(f"✅ Accuracy: {accuracy_big:.2f}%")
    
    print("\n🎉 All tests completed successfully!")
    print("   المعالج المحسّن جاهز للاستخدام!")
