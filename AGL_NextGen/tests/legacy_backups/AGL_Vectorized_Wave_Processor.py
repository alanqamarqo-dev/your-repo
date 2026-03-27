"""
AGL_Vectorized_Wave_Processor.py - Compatibility Shim
"""
import sys
import os

# Ensure AGL_NextGen is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
nextgen_path = os.path.join(current_dir, 'AGL_NextGen', 'src')
if nextgen_path not in sys.path:
    sys.path.insert(0, nextgen_path)

try:
    from agl.engines.vectorized_wave_processor import VectorizedWaveProcessor
    print("✅ [Shim] AGL_Vectorized_Wave_Processor redirected to AGL_NextGen")
except ImportError:
    print("⚠️ [Shim] Could not load VectorizedWaveProcessor. Using Dummy.")
    class VectorizedWaveProcessor:
        def __init__(self, noise_floor=0.01):
            pass
