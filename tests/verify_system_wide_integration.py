import sys
import os

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), "repo-copy"))

from dynamic_modules.mission_control_enhanced import EnhancedMissionController

def verify_system_wide_integration():
    print("🔍 VERIFYING SYSTEM-WIDE METAPHYSICS INTEGRATION")
    print("================================================")
    
    try:
        mc = EnhancedMissionController()
        
        if hasattr(mc, 'metaphysics_engine') and mc.metaphysics_engine is not None:
            print("   ✅ Metaphysics Engine Detected in Mission Control.")
            
            # Test a capability via Mission Control instance
            print("   🧪 Testing Capability via Mission Control...")
            mass = mc.metaphysics_engine.compress_matter_to_info("System Integration Test")
            print(f"      Calculated Info-Mass: {mass:.4f}")
            
            if mass > 0:
                print("   ✅ Integration Verified: Engine is Active and Callable.")
            else:
                print("   ❌ Integration Warning: Engine returned zero mass.")
        else:
            print("   ❌ FAILED: Metaphysics Engine NOT found in Mission Control.")
            
    except Exception as e:
        print(f"   ❌ CRITICAL ERROR: {e}")

if __name__ == "__main__":
    verify_system_wide_integration()
