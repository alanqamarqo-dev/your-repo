import sys
import os

# Add repo-copy to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'repo-copy'))

try:
    from dynamic_modules.mission_control_enhanced import EnhancedMissionController
    print("✅ Successfully imported EnhancedMissionController")
    
    mc = EnhancedMissionController(auto_collective=False)
    print("✅ Successfully instantiated EnhancedMissionController")
    
    if hasattr(mc, 'super_intelligence') and mc.super_intelligence is not None:
        print("✅ Super Intelligence is linked and active.")
        result = mc.process_with_super_intelligence("Test Link")
        print(f"Test Result: {result}")
    else:
        print("❌ Super Intelligence not linked.")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
