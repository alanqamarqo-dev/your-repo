import sys
import os
import time

# Set up paths
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_PATH = os.path.join(PROJECT_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from agl.core.super_intelligence import AGL_Super_Intelligence

def run_mission():
    print("="*60)
    print("🚀 STARTING ASI MISSION: SELF-EVOLUTION OF MATHEMATICAL BRAIN")
    print("="*60)
    
    # Initialize ASI
    asi = AGL_Super_Intelligence()
    
    # Enable capabilities
    asi.enable_super_intelligence_capabilities(
        recursive_improvement=True,
        live_knowledge=True,
        deep_causal=True
    )

    improver = asi.engine_registry.get("Recursive_Improver")
    
    if improver:
        print("\n🧬 [RSI] Recursive Improver Found. Launching Mutation Cycle...")
        # Goal: Optimize for NumPy and Matrix operations
        goal = "Optimize the MathematicalBrain class to use NumPy for matrix operations where possible, and add a performance boost for complex calculations using vectorized operations. Also, add support for Tensor-based math if possible."
        
        result = improver.analyze_and_improve(
            engine_name="agl.engines.mathematical_brain",
            improvement_goal=goal,
            apply_changes=True
        )
        
        print(f"\n📊 [RSI] Mission Result: {result.get('status')}")
        print(f"   -> Message: {result.get('message', 'N/A')}")
        
    else:
        print("\n❌ [RSI] Error: Recursive Improver mission failed (Engine not found in registry).")

if __name__ == "__main__":
    run_mission()
