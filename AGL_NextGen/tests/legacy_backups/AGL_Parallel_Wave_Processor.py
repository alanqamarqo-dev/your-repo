"""
AGL_Parallel_Wave_Processor.py - Compatibility Shim
"""
import sys
import os

# Ensure AGL_NextGen is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
nextgen_path = os.path.join(current_dir, 'AGL_NextGen', 'src')
if nextgen_path not in sys.path:
    sys.path.insert(0, nextgen_path)

try:
    from agl.engines.parallel_wave_processor import ParallelWaveExecutor
    print("✅ [Shim] AGL_Parallel_Wave_Processor redirected to AGL_NextGen")
except ImportError:
    print("⚠️ [Shim] Could not load ParallelWaveExecutor. Using Dummy.")
    class ParallelWaveExecutor:
        def __init__(self, max_workers=None):
            pass
