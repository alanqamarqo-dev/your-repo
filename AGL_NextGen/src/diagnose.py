import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'agl', 'core'))
sys.path.append(os.path.abspath("src"))

print("Testing Imports...")

try:
    from agl.engines.quantum_core import HeikalQuantumCore
    print("✅ HeikalQuantumCore imported successfully")
except ImportError as e:
    print(f"❌ HeikalQuantumCore failed: {e}")

try:
    from agl.engines.holographic_memory import HeikalHolographicMemory
    print("✅ HeikalHolographicMemory imported successfully")
except ImportError as e:
    print(f"❌ HeikalHolographicMemory failed: {e}")

try:
    from agl.core.consciousness import AGL_Core_Consciousness
    print("✅ AGL_Core_Consciousness imported successfully")
except ImportError as e:
    print(f"❌ AGL_Core_Consciousness failed: {e}")
