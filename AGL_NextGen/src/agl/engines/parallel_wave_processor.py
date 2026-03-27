"""
🌊 معالج الموجات المتوازي - المرحلة 2B
AGL Parallel Wave Processor - Phase 2B

المطور: حسام هيكل (Hossam Heikal)
التاريخ: 27 ديسمبر 2025

الهدف: توزيع المعالجة الموجية على جميع أنوية المعالج (Multi-core Processing)
Goal: Distribute wave processing across all CPU cores
"""

import numpy as np
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
import time
import sys
import os

# Ensure we can import the gate processor
sys.path.append(os.getcwd())
try:
    from agl.engines.vectorized_wave_processor import VectorizedWaveProcessor as AdvancedWaveProcessor
except ImportError:
    # Fallback for when running from different directories
    try:
        from vectorized_wave_processor import VectorizedWaveProcessor as AdvancedWaveProcessor
    except ImportError:
         print("Warning: Could not import VectorizedWaveProcessor. Parallel Executor disabled.")
         AdvancedWaveProcessor = None

def _worker_task(chunk_a, chunk_b, operation, noise_floor):
    """
    وظيفة العامل (Worker Function) التي يتم تنفيذها في عملية منفصلة.
    يجب أن تكون دالة عليا (Top-level) لكي تعمل مع Pickle.
    """
    # كتم الطباعة داخل العمليات الفرعية لتجنب الفوضى في الكونسول
    # Suppress stdout in workers
    sys.stdout = open(os.devnull, 'w')
    
    try:
        if AdvancedWaveProcessor is None:
            return None
            
        processor = AdvancedWaveProcessor(noise_floor=noise_floor)
        
        if operation == "XOR":
            return processor.batch_xor(chunk_a, chunk_b)
        elif operation == "AND":
            return processor.batch_and(chunk_a, chunk_b)
        elif operation == "OR":
            return processor.batch_or(chunk_a, chunk_b)
        elif operation == "NOT":
            return processor.batch_not(chunk_a)
        else:
            return processor.batch_xor(chunk_a, chunk_b)
    finally:
        sys.stdout = sys.__stdout__

class ParallelWaveExecutor:
    """
    منفذ العمليات المتوازي.
    يقوم بتقسيم البيانات وتوزيعها على الأنوية المتاحة.
    """
    
    _has_printed_init = False

    def __init__(self, max_workers=None):
        self.max_workers = max_workers or multiprocessing.cpu_count()
        if not ParallelWaveExecutor._has_printed_init:
            print(f"🌊 [Parallel]: Initialized Parallel Executor with {self.max_workers} CPU cores.")
            ParallelWaveExecutor._has_printed_init = True

    def execute_batch(self, inputs_a, inputs_b, operation="XOR", noise_floor=0.01):
        """
        تنفيذ دفعة عمليات بالتوازي.
        """
        total_size = len(inputs_a)
        
        # إذا كانت الدفعة صغيرة، لا داعي لتكلفة تعدد العمليات (Overhead)
        # If batch is small (< 500k), run in main process
        if total_size < 500000:
            # print(f"   ℹ️ [Parallel]: Batch size {total_size} too small for multi-core. Running sequentially.")
            return _worker_task(inputs_a, inputs_b, operation, noise_floor)

        # تقسيم البيانات (Splitting Data)
        chunk_size = int(np.ceil(total_size / self.max_workers))
        chunks_a = [inputs_a[i:i + chunk_size] for i in range(0, total_size, chunk_size)]
        
        if operation == "NOT":
             chunks_b = [None] * len(chunks_a)
        else:
             chunks_b = [inputs_b[i:i + chunk_size] for i in range(0, total_size, chunk_size)]

        print(f"   🚀 [Parallel]: Distributing {total_size} ops across {len(chunks_a)} workers...")
        
        results = []
        start_time = time.time()
        
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for ca, cb in zip(chunks_a, chunks_b):
                futures.append(executor.submit(_worker_task, ca, cb, operation, noise_floor))
            
            for f in futures:
                results.append(f.result())
        
        # تجميع النتائج (Concatenation)
        final_result = np.concatenate(results)
        
        elapsed = time.time() - start_time
        print(f"   ✅ [Parallel]: Finished in {elapsed:.4f}s")
        
        return final_result
