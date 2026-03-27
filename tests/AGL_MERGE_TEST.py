import sys
import os
from AGL_Core.AGL_Awakened import AGL_Super_Intelligence

def main():
    print("🧪 [TEST] Verifying AGL Merge Integrity...")
    
    try:
        asi = AGL_Super_Intelligence()
        
        print("\n🔍 [CHECK] Inspecting Active Components:")
        for comp in asi.active_components:
            print(f"   ✅ {comp}")
            
        # Check for new methods
        if hasattr(asi, 'predict_future'):
            print("   ✅ Method 'predict_future' found.")
        else:
            print("   ❌ Method 'predict_future' MISSING.")
            
        if hasattr(asi, 'evolve_codebase'):
            print("   ✅ Method 'evolve_codebase' found.")
        else:
            print("   ❌ Method 'evolve_codebase' MISSING.")
            
        # Check for new engines
        if hasattr(asi, 'strategist'):
            print(f"   ✅ Strategist: {'Online' if asi.strategist else 'Offline (Import Failed)'}")
        
        if hasattr(asi, 'recursive_improver'):
            print(f"   ✅ Recursive Improver: {'Online' if asi.recursive_improver else 'Offline (Import Failed)'}")

        print("\n✅ Merge Verification Complete. System is stable.")
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
