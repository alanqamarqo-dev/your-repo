import sys
import os

# Add repo-copy to path
sys.path.append(os.path.abspath("repo-copy"))

try:
    from dynamic_modules.agl_consciousness import (
        ConsciousnessTracker, 
        SelfEvolution,
        AutobiographicalMemory,
        TrueConsciousnessSystem
    )
    print("Import successful!")
    ct = ConsciousnessTracker()
    print(f"Consciousness Level: {ct.consciousness_level}")
except ImportError as e:
    print(f"Import failed: {e}")
except Exception as e:
    print(f"Error: {e}")
