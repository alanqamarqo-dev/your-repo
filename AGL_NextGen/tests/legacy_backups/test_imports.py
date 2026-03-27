import sys
import os

# Add paths similar to AGL_Enterprise_System_Test.py
sys.path.insert(0, os.path.join(os.getcwd(), 'AGL_NextGen', 'src'))

print(f"Paths: {sys.path}")

try:
    from agl.engines.vectorized_wave_processor import VectorizedWaveProcessor
    print("✅ Successfully imported VectorizedWaveProcessor via package")
except ImportError as e:
    print(f"❌ Failed to import VectorizedWaveProcessor via package: {e}")

try:
    from agl.engines.parallel_wave_processor import ParallelWaveExecutor
    print("✅ Successfully imported ParallelWaveExecutor via package")
except ImportError as e:
    print(f"❌ Failed to import ParallelWaveExecutor via package: {e}")
